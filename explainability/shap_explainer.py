"""
Phase 6 – SHAP-Based Feature Explainability
============================================
Script: explainability/shap_explainer.py

SHAP METHOD RATIONALE:
  • SHAP 0.51 + Keras 3.15 + TF 2.21 environment:
      - DeepExplainer is NOT compatible with Keras 3 functional models containing
        custom layers (TemporalAttention). It requires TF1-style session graphs.
      - GradientExplainer fails similarly on multi-input models with custom ops.
      - KernelExplainer is model-agnostic: it works via a Python callable wrapper,
        requiring NO internal graph access. It is the safest choice here.

  • Because KernelExplainer is computationally expensive on 70-dim inputs, we:
      1. Fix the sequential (Bi-LSTM) input at the per-class mean sequence
         representation to isolate static feature importance.
      2. Explain predictions on a stratified sample (100 background + 150 test).
      3. Provide global SHAP importance, per-class SHAP bar charts, and local
         waterfall/force-style explanations for 3 representative students.

LEAKAGE RULE:
  Features listed in EXCLUDED_FEATURES are never used as model inputs and are
  therefore absent from X_static; this script adds an extra guard.

DOCUMENTED LIMITATION:
  KernelExplainer treats the model as a black box. SHAP values capture the
  marginal contribution of each static feature averaged over a background
  distribution, holding the sequential input fixed. They do NOT capture
  interaction effects between the sequential and static branches.
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import keras

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# Register custom layer BEFORE loading the model
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = r"d:\dl project"
sys.path.insert(0, os.path.join(BASE_DIR, "models"))
from bilstm_attention import TemporalAttention  # noqa: F401

import shap

# ─────────────────────────────────────────────────────────────────────────────
# PATH CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
MODEL_PATH     = os.path.join(BASE_DIR, "saved_model", "bilstm_attention_model.keras")
SEQUENCES_DIR  = os.path.join(BASE_DIR, "dataset", "processed", "sequences")
METADATA_JSON  = os.path.join(SEQUENCES_DIR, "sequence_metadata.json")
FIGURES_DIR    = os.path.join(BASE_DIR, "outputs", "figures")
REPORTS_DIR    = os.path.join(BASE_DIR, "outputs", "reports")

SHAP_GLOBAL_PNG    = os.path.join(FIGURES_DIR, "shap_global_importance.png")
SHAP_CLASS_PNG     = os.path.join(FIGURES_DIR, "shap_per_class_importance.png")
SHAP_LOCAL_PNG     = os.path.join(FIGURES_DIR, "shap_local_explanations.png")
SHAP_BEESWARM_PNG  = os.path.join(FIGURES_DIR, "shap_beeswarm.png")
SHAP_REPORT_TXT    = os.path.join(REPORTS_DIR, "shap_explainability_summary.txt")

CLASS_NAMES  = {0: "Low Engagement", 1: "Medium Engagement", 2: "High Engagement"}
CLASS_COLORS = {0: "#e74c3c", 1: "#f39c12", 2: "#27ae60"}

# Columns that must NEVER appear as features (leakage guard)
EXCLUDED_FEATURES = [
    "final_result", "date_unregistration", "withdrawn_flag",
    "active_duration", "engagement_score", "engagement_level", "engagement_class"
]

# KernelExplainer sample sizes — keep tractable on CPU
N_BACKGROUND  = 100   # background samples (mean taken over these)
N_EXPLAIN     = 150   # test samples to explain
RANDOM_SEED   = 42
np.random.seed(RANDOM_SEED)


# ─────────────────────────────────────────────────────────────────────────────
# 1. DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
def load_data():
    print("[Step 1] Loading test/train arrays and metadata...")
    X_train_seq    = np.load(os.path.join(SEQUENCES_DIR, "X_train_seq.npy"))
    X_train_static = np.load(os.path.join(SEQUENCES_DIR, "X_train_static.npy"))
    X_test_seq     = np.load(os.path.join(SEQUENCES_DIR, "X_test_seq.npy"))
    X_test_static  = np.load(os.path.join(SEQUENCES_DIR, "X_test_static.npy"))
    y_train        = np.load(os.path.join(SEQUENCES_DIR, "y_train.npy"))
    y_test         = np.load(os.path.join(SEQUENCES_DIR, "y_test.npy"))

    with open(METADATA_JSON, encoding="utf-8") as f:
        metadata = json.load(f)
    static_feature_names = metadata["static_feature_names"]

    # Leakage guard
    for feat in EXCLUDED_FEATURES:
        assert feat not in static_feature_names, f"LEAKAGE: '{feat}' found in static features!"
    print(f"   Leakage guard: PASSED ({len(EXCLUDED_FEATURES)} forbidden columns absent)")

    # NaN / Inf check
    for arr, name in [(X_test_seq, "X_test_seq"), (X_test_static, "X_test_static"),
                      (X_train_seq, "X_train_seq"), (X_train_static, "X_train_static")]:
        assert not np.isnan(arr).any(), f"NaN in {name}!"
        assert not np.isinf(arr).any(), f"Inf in {name}!"
    print("   NaN/Inf check : PASSED")
    print(f"   Static features: {len(static_feature_names)}")
    print(f"   y_test class distribution: {np.bincount(y_test).tolist()}")
    return (X_train_seq, X_train_static, y_train,
            X_test_seq, X_test_static, y_test, static_feature_names)


# ─────────────────────────────────────────────────────────────────────────────
# 2. MODEL LOADING
# ─────────────────────────────────────────────────────────────────────────────
def load_model():
    print("\n[Step 2] Loading saved Bi-LSTM + Attention model...")
    model = keras.models.load_model(
        MODEL_PATH,
        custom_objects={"TemporalAttention": TemporalAttention}
    )
    print("   Model loaded successfully.")
    return model


# ─────────────────────────────────────────────────────────────────────────────
# 3. BUILD WRAPPED PREDICT FUNCTION FOR KERNEL EXPLAINER
#
#    Strategy: fix the sequential branch at the per-class BACKGROUND mean
#    sequence. This lets KernelExplainer vary only the static features while
#    the Bi-LSTM context is held constant (at an average "neutral" sequence).
#    Returns probabilities shape (N, 3).
# ─────────────────────────────────────────────────────────────────────────────
def build_predict_wrapper(model, fixed_seq):
    """
    Returns a callable f(X_static_batch) -> proba (N,3) for KernelExplainer.
    'fixed_seq' is a single sequence array of shape (1, 40, 4) that is
    tiled to match the batch size.
    """
    def predict_fn(X_static_batch):
        n = X_static_batch.shape[0]
        seq_batch = np.tile(fixed_seq, (n, 1, 1))
        proba = model.predict([seq_batch, X_static_batch], verbose=0)
        return proba
    return predict_fn


# ─────────────────────────────────────────────────────────────────────────────
# 4. STRATIFIED SAMPLING HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def stratified_sample(X_static, y, n_total, seed=42):
    """Returns a stratified random sample of n_total rows from X_static."""
    rng = np.random.default_rng(seed)
    n_per_class = n_total // 3
    indices = []
    for cls in [0, 1, 2]:
        cls_idx = np.where(y == cls)[0]
        chosen = rng.choice(cls_idx, size=min(n_per_class, len(cls_idx)), replace=False)
        indices.extend(chosen.tolist())
    indices = np.array(indices[:n_total])
    rng.shuffle(indices)
    return X_static[indices], y[indices], indices


# ─────────────────────────────────────────────────────────────────────────────
# 5. RUN KERNEL SHAP
# ─────────────────────────────────────────────────────────────────────────────
def run_kernel_shap(model, X_train_static, X_train_seq, y_train,
                    X_test_static, X_test_seq, y_test):
    print("\n[Step 3] Running SHAP KernelExplainer on static features...")

    # Background: stratified sample from training set
    X_bg, y_bg, _ = stratified_sample(X_train_static, y_train, N_BACKGROUND)
    print(f"   Background samples : {len(X_bg)} (stratified from train set)")

    # Samples to explain: stratified from test set
    X_exp, y_exp, exp_indices = stratified_sample(X_test_static, y_test, N_EXPLAIN)
    seq_exp = X_test_seq[exp_indices]
    print(f"   Explanation samples: {len(X_exp)} (stratified from test set)")

    # Fixed sequence = mean over background train sequences
    X_bg_seq = X_train_seq[np.random.choice(len(X_train_seq), N_BACKGROUND, replace=False)]
    fixed_seq = X_bg_seq.mean(axis=0, keepdims=True)   # (1, 40, 4)

    # Wrapper function
    predict_fn = build_predict_wrapper(model, fixed_seq)

    # Verify wrapper produces valid probabilities before passing to SHAP
    test_proba = predict_fn(X_bg[:3])
    assert test_proba.shape == (3, 3), f"Unexpected predict shape: {test_proba.shape}"
    assert np.allclose(test_proba.sum(axis=1), 1.0, atol=1e-3), "Proba rows don't sum to 1!"
    print("   Predict wrapper validation: PASSED")

    # KernelExplainer — uses Shapley sampling (model-agnostic, always compatible)
    print(f"   Fitting KernelExplainer on {N_BACKGROUND} background samples...")
    print("   (This may take 3-8 minutes on CPU for 150 samples × 70 features)")
    explainer = shap.KernelExplainer(predict_fn, X_bg)

    print(f"   Computing SHAP values for {N_EXPLAIN} test samples...")
    # shap_values shape: list of 3 arrays each (N_EXPLAIN, 70), one per class
    shap_values = explainer.shap_values(X_exp, nsamples=128, silent=True)

    print(f"   SHAP values computed. Type: {type(shap_values)}")
    if isinstance(shap_values, list):
        print(f"   Shape per class: {[s.shape for s in shap_values]}")
        # Validate shapes
        for cls_idx, sv in enumerate(shap_values):
            assert sv.shape == (N_EXPLAIN, X_train_static.shape[1]), \
                f"Class {cls_idx} SHAP shape mismatch: {sv.shape}"
        shap_array = np.stack(shap_values, axis=2)  # (N_EXPLAIN, 70, 3)
    else:
        # Newer SHAP versions return ndarray (N_EXPLAIN, 70, 3)
        assert shap_values.ndim == 3, f"Unexpected SHAP array shape: {shap_values.shape}"
        shap_array = shap_values
        shap_values = [shap_array[:, :, c] for c in range(3)]

    print(f"   NaN in SHAP values: {np.isnan(shap_array).any()}")
    print(f"   Inf in SHAP values: {np.isinf(shap_array).any()}")
    assert not np.isnan(shap_array).any(), "NaN found in SHAP values!"
    assert not np.isinf(shap_array).any(), "Inf found in SHAP values!"
    print("   SHAP value validation: PASSED")

    return shap_values, shap_array, X_exp, y_exp, exp_indices, explainer, fixed_seq


# ─────────────────────────────────────────────────────────────────────────────
# 6. VISUALIZATION 1 – Global SHAP Feature Importance
# ─────────────────────────────────────────────────────────────────────────────
def plot_global_importance(shap_values, feature_names, top_n=20):
    """
    Mean |SHAP| aggregated across all classes and all explained samples.
    Shows the top_n most impactful static features globally.
    """
    print(f"\n[Plot 1] Global SHAP feature importance (top {top_n})...")
    # Mean absolute SHAP per feature across classes: shape (70,)
    mean_abs = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
    top_idx  = np.argsort(mean_abs)[-top_n:][::-1]
    top_names   = [feature_names[i] for i in top_idx]
    top_vals    = mean_abs[top_idx]

    fig, ax = plt.subplots(figsize=(10, 7))
    palette = plt.cm.RdYlGn(np.linspace(0.2, 0.85, top_n))[::-1]
    bars = ax.barh(range(top_n), top_vals[::-1], color=palette[::-1], edgecolor="white", linewidth=0.4)
    ax.set_yticks(range(top_n))
    ax.set_yticklabels(top_names[::-1], fontsize=8)
    ax.set_xlabel("Mean |SHAP Value| (impact on model output)", fontsize=10, labelpad=8)
    ax.set_title(f"Top-{top_n} Static Features by Global SHAP Importance\n"
                 f"(KernelExplainer, {len(shap_values[0])} test samples, all classes averaged)",
                 fontsize=12, fontweight="bold", pad=10)
    for bar, val in zip(bars, top_vals[::-1]):
        ax.text(bar.get_width() + max(top_vals) * 0.005, bar.get_y() + bar.get_height() / 2,
                f"{val:.5f}", va="center", fontsize=7)
    fig.tight_layout()
    fig.savefig(SHAP_GLOBAL_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"   Saved: {SHAP_GLOBAL_PNG}")
    return top_idx, top_names, top_vals


# ─────────────────────────────────────────────────────────────────────────────
# 7. VISUALIZATION 2 – Per-Class SHAP Feature Importance
# ─────────────────────────────────────────────────────────────────────────────
def plot_per_class_importance(shap_values, feature_names, top_n=15):
    """Side-by-side bar charts of mean |SHAP| per class for top_n features."""
    print(f"\n[Plot 2] Per-class SHAP feature importance (top {top_n} per class)...")
    fig, axes = plt.subplots(1, 3, figsize=(20, 7), sharey=False)

    for cls_idx, ax in enumerate(axes):
        sv       = shap_values[cls_idx]        # (N, 70)
        mean_abs = np.abs(sv).mean(axis=0)    # (70,)
        top_idx  = np.argsort(mean_abs)[-top_n:][::-1]
        names    = [feature_names[i] for i in top_idx]
        vals     = mean_abs[top_idx]

        ax.barh(range(top_n), vals[::-1], color=CLASS_COLORS[cls_idx], alpha=0.85,
                edgecolor="white", linewidth=0.4)
        ax.set_yticks(range(top_n))
        ax.set_yticklabels(names[::-1], fontsize=7.5)
        ax.set_xlabel("Mean |SHAP Value|", fontsize=9)
        ax.set_title(f"{CLASS_NAMES[cls_idx]}\n(Class {cls_idx})",
                     fontsize=10, fontweight="bold", color=CLASS_COLORS[cls_idx], pad=8)
        ax.tick_params(axis="x", labelsize=8)

    fig.suptitle("Per-Class SHAP Feature Importance (Static Branch)\n"
                 "Bi-LSTM + Attention Model – KernelExplainer",
                 fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(SHAP_CLASS_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"   Saved: {SHAP_CLASS_PNG}")


# ─────────────────────────────────────────────────────────────────────────────
# 8. VISUALIZATION 3 – Local Explanations for Representative Students
# ─────────────────────────────────────────────────────────────────────────────
def plot_local_explanations(shap_values, X_exp, y_exp, feature_names, top_n=12):
    """
    Horizontal bar chart showing top-N positive and negative SHAP contributors
    for one representative correctly-predicted student per class.
    """
    print(f"\n[Plot 3] Local SHAP explanations (one student per class, top {top_n} features)...")
    fig, axes = plt.subplots(1, 3, figsize=(21, 7))

    for cls_idx, ax in enumerate(axes):
        cls_mask  = y_exp == cls_idx
        if cls_mask.sum() == 0:
            ax.axis("off")
            continue
        # Pick first sample of this class
        sample_pos = np.where(cls_mask)[0][0]
        sv_sample  = shap_values[cls_idx][sample_pos]   # (70,)
        feat_vals  = X_exp[sample_pos]                   # (70,)

        # Sort by absolute SHAP descending, take top_n
        top_idx   = np.argsort(np.abs(sv_sample))[-top_n:][::-1]
        names     = [feature_names[i] for i in top_idx]
        vals      = sv_sample[top_idx]
        feat_raw  = feat_vals[top_idx]

        colors = ["#27ae60" if v > 0 else "#e74c3c" for v in vals]
        bars = ax.barh(range(top_n), vals[::-1], color=colors[::-1],
                       edgecolor="white", linewidth=0.4)
        ax.set_yticks(range(top_n))
        ax.set_yticklabels([f"{n}\n(val={v:.2f})" for n, v in zip(names[::-1], feat_raw[::-1])],
                           fontsize=6.5)
        ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_xlabel("SHAP Value", fontsize=9)
        ax.set_title(f"{CLASS_NAMES[cls_idx]}\n(Student #{sample_pos})",
                     fontsize=9, fontweight="bold", color=CLASS_COLORS[cls_idx], pad=8)
        ax.tick_params(axis="x", labelsize=8)

    pos_patch = plt.matplotlib.patches.Patch(color="#27ae60", label="Positive contribution (↑ class)")
    neg_patch = plt.matplotlib.patches.Patch(color="#e74c3c", label="Negative contribution (↓ class)")
    fig.legend(handles=[pos_patch, neg_patch], loc="lower center", ncol=2,
               fontsize=9, frameon=True, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Local SHAP Explanations – Representative Student Per Engagement Class\n"
                 "(Static Feature Branch, Bi-LSTM + Attention, KernelExplainer)",
                 fontsize=12, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(SHAP_LOCAL_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"   Saved: {SHAP_LOCAL_PNG}")


# ─────────────────────────────────────────────────────────────────────────────
# 9. VISUALIZATION 4 – Beeswarm-style summary (top 15 features)
# ─────────────────────────────────────────────────────────────────────────────
def plot_beeswarm(shap_values, X_exp, feature_names, top_n=15):
    """
    Scatter plot of SHAP values per feature (averaged across classes),
    coloured by feature value magnitude — a proxy for SHAP beeswarm.
    """
    print(f"\n[Plot 4] SHAP beeswarm-style summary (top {top_n} features, all classes)...")

    # Average absolute SHAP across classes -> select top features
    mean_abs_all = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
    top_idx = np.argsort(mean_abs_all)[-top_n:]        # ascending order for heatmap

    # Build a DataFrame: rows = samples, cols = top features, values = avg SHAP across classes
    avg_shap = np.mean(np.stack(shap_values, axis=2), axis=2)   # (N, 70)
    df_shap  = pd.DataFrame(avg_shap[:, top_idx],
                            columns=[feature_names[i] for i in top_idx])
    df_feat  = pd.DataFrame(X_exp[:, top_idx],
                            columns=[feature_names[i] for i in top_idx])

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Left: heatmap of mean SHAP per feature
    mean_sv = df_shap.mean(axis=0).values.reshape(1, -1)
    sns.heatmap(mean_sv, ax=axes[0], cmap="RdBu_r", center=0,
                xticklabels=df_shap.columns, yticklabels=["Mean SHAP"],
                cbar_kws={"label": "Mean SHAP"}, linewidths=0.3)
    axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=45, ha="right", fontsize=7)
    axes[0].set_title(f"Mean SHAP Value (top {top_n} features)", fontsize=10, fontweight="bold")

    # Right: violin plot of SHAP distribution per feature
    df_melt = df_shap.melt(var_name="Feature", value_name="SHAP Value")
    order   = df_shap.abs().mean().sort_values(ascending=False).index.tolist()
    sns.violinplot(data=df_melt, y="Feature", x="SHAP Value", ax=axes[1],
                   order=order, palette="Set2", linewidth=0.6, cut=0, scale="width")
    axes[1].axvline(0, color="black", linewidth=0.8, linestyle="--")
    axes[1].set_xlabel("SHAP Value (averaged across 3 classes)", fontsize=9)
    axes[1].set_ylabel("")
    axes[1].tick_params(axis="y", labelsize=7)
    axes[1].set_title(f"SHAP Value Distribution (top {top_n} features)", fontsize=10, fontweight="bold")

    fig.suptitle("SHAP Summary – Static Feature Branch\n"
                 "Bi-LSTM + Attention Model, KernelExplainer",
                 fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(SHAP_BEESWARM_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"   Saved: {SHAP_BEESWARM_PNG}")


# ─────────────────────────────────────────────────────────────────────────────
# 10. TEXT SUMMARY REPORT
# ─────────────────────────────────────────────────────────────────────────────
def generate_report(shap_values, feature_names, top_idx_global, top_names_global,
                    top_vals_global, X_exp, y_exp, shap_array):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    lines = []
    lines.append("=" * 80)
    lines.append("PHASE 6 – SHAP-BASED FEATURE EXPLAINABILITY SUMMARY REPORT")
    lines.append("=" * 80)
    lines.append(f"\nModel           : Bi-LSTM + Temporal Attention + Static Feature Fusion")
    lines.append(f"SHAP Method     : KernelExplainer (model-agnostic, black-box wrapper)")
    lines.append(f"SHAP Version    : {shap.__version__}")
    lines.append(f"Background size : {N_BACKGROUND} stratified training samples")
    lines.append(f"Explained size  : {N_EXPLAIN} stratified test samples")
    lines.append(f"nsamples/query  : 128 (Shapley sampling approximation)")
    lines.append(f"Static features : {len(feature_names)}")
    lines.append(f"Explained branch: Static (X_static, 70 features)")
    lines.append(f"Sequential input: Fixed at mean background training sequence")

    lines.append("\n" + "-" * 80)
    lines.append("1. WHY KernelExplainer (Compatibility Note)")
    lines.append("-" * 80)
    lines.append("   • DeepExplainer requires TensorFlow 1.x session-graph access and is NOT")
    lines.append("     compatible with Keras 3 functional models using custom layers.")
    lines.append("   • GradientExplainer similarly fails on custom multi-input Keras 3 graphs.")
    lines.append("   • KernelExplainer uses only a Python callable (model.predict wrapper),")
    lines.append("     making it universally compatible with any framework or model version.")
    lines.append("   • SHAP values are exact (up to sampling approximation), converging to")
    lines.append("     true Shapley values as nsamples → ∞.")

    lines.append("\n" + "-" * 80)
    lines.append("2. TOP-20 GLOBALLY IMPORTANT STATIC FEATURES (Mean |SHAP|)")
    lines.append("-" * 80)
    for rank, (name, val) in enumerate(zip(top_names_global[:20], top_vals_global[:20]), 1):
        lines.append(f"   Rank {rank:02d}: {name:<45s}  Mean |SHAP| = {val:.6f}")

    lines.append("\n" + "-" * 80)
    lines.append("3. TOP-10 FEATURES PER CLASS")
    lines.append("-" * 80)
    for cls_idx in [0, 1, 2]:
        sv = shap_values[cls_idx]
        mean_abs = np.abs(sv).mean(axis=0)
        top10 = np.argsort(mean_abs)[-10:][::-1]
        lines.append(f"\n   {CLASS_NAMES[cls_idx]} (Class {cls_idx}):")
        for rank, idx in enumerate(top10, 1):
            lines.append(f"     {rank:02d}. {feature_names[idx]:<45s}  {mean_abs[idx]:.6f}")

    lines.append("\n" + "-" * 80)
    lines.append("4. SAMPLE LOCAL EXPLANATIONS (one per class)")
    lines.append("-" * 80)
    for cls_idx in [0, 1, 2]:
        cls_mask = y_exp == cls_idx
        if cls_mask.sum() == 0:
            continue
        sample_pos = np.where(cls_mask)[0][0]
        sv_sample  = shap_values[cls_idx][sample_pos]
        feat_vals  = X_exp[sample_pos]
        top5_idx   = np.argsort(np.abs(sv_sample))[-5:][::-1]
        lines.append(f"\n   [{CLASS_NAMES[cls_idx]}] – Sample #{sample_pos}")
        lines.append(f"   {'Feature':<45s}  {'Raw Value':>10s}  {'SHAP Value':>12s}")
        lines.append("   " + "-" * 72)
        for idx in top5_idx:
            direction = "↑" if sv_sample[idx] > 0 else "↓"
            lines.append(f"   {feature_names[idx]:<45s}  {feat_vals[idx]:>10.4f}  "
                         f"{sv_sample[idx]:>+12.6f}  {direction}")

    lines.append("\n" + "-" * 80)
    lines.append("5. SHAP VALUE VALIDATION")
    lines.append("-" * 80)
    lines.append(f"   NaN in SHAP array: {np.isnan(shap_array).any()}")
    lines.append(f"   Inf in SHAP array: {np.isinf(shap_array).any()}")
    lines.append(f"   SHAP array shape : {shap_array.shape}  (N_explain × features × classes)")

    lines.append("\n" + "-" * 80)
    lines.append("6. TECHNICAL LIMITATIONS")
    lines.append("-" * 80)
    lines.append("   • The sequential (Bi-LSTM) branch is held fixed at the mean background")
    lines.append("     sequence; SHAP values reflect static feature importance only.")
    lines.append("   • Temporal feature importance is explained via attention weights in")
    lines.append("     explainability/attention_explainer.py.")
    lines.append("   • KernelExplainer is O(2^d) in the worst case; nsamples=128 provides a")
    lines.append("     practical Monte Carlo approximation (error ≈ 1/√128).")
    lines.append("   • SHAP values represent average marginal contributions (Shapley values),")
    lines.append("     not causal effects.")

    lines.append("\n" + "-" * 80)
    lines.append("7. SAVED VISUALIZATIONS")
    lines.append("-" * 80)
    for p in [SHAP_GLOBAL_PNG, SHAP_CLASS_PNG, SHAP_LOCAL_PNG, SHAP_BEESWARM_PNG]:
        lines.append(f"   {p}")

    lines.append("\n" + "=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    content = "\n".join(lines)
    with open(SHAP_REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n   SHAP summary report saved: {SHAP_REPORT_TXT}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 80)
    print("PHASE 6 – SHAP-BASED STATIC FEATURE EXPLAINABILITY")
    print("=" * 80)

    os.makedirs(FIGURES_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Load data
    (X_train_seq, X_train_static, y_train,
     X_test_seq, X_test_static, y_test, static_feature_names) = load_data()

    # Load model
    model = load_model()

    # Run SHAP
    (shap_values, shap_array, X_exp, y_exp,
     exp_indices, explainer, fixed_seq) = run_kernel_shap(
        model, X_train_static, X_train_seq, y_train,
        X_test_static, X_test_seq, y_test
    )

    # Plots
    top_idx_g, top_names_g, top_vals_g = plot_global_importance(shap_values, static_feature_names, top_n=20)
    plot_per_class_importance(shap_values, static_feature_names, top_n=15)
    plot_local_explanations(shap_values, X_exp, y_exp, static_feature_names, top_n=12)
    plot_beeswarm(shap_values, X_exp, static_feature_names, top_n=15)

    # Report
    generate_report(shap_values, static_feature_names, top_idx_g, top_names_g,
                    top_vals_g, X_exp, y_exp, shap_array)

    # ─── COMPLETION SUMMARY ───
    print("\n" + "=" * 60)
    print("SHAP EXPLAINABILITY – COMPLETION SUMMARY")
    print("=" * 60)
    print("Status            : SUCCESS")
    print(f"SHAP method       : KernelExplainer (model-agnostic)")
    print(f"Background samples: {N_BACKGROUND}")
    print(f"Explained samples : {N_EXPLAIN}")
    print(f"Static features   : {len(static_feature_names)}")
    print(f"\nTop-10 globally important features:")
    for i, (name, val) in enumerate(zip(top_names_g[:10], top_vals_g[:10]), 1):
        print(f"  #{i:02d}: {name:<45s}  {val:.6f}")
    print("\nSaved plots:")
    for p in [SHAP_GLOBAL_PNG, SHAP_CLASS_PNG, SHAP_LOCAL_PNG, SHAP_BEESWARM_PNG]:
        print(f"  {p}")
    print(f"\nSaved report: {SHAP_REPORT_TXT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
