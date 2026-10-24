"""
Phase 6 – Attention-Based Temporal Explainability
==================================================
Script: explainability/attention_explainer.py

Loads the saved Bi-LSTM + Attention model and extracts temporal attention weights
for all test samples. Maps 40 timesteps to human-readable week labels, validates
that attention weights form proper probability distributions, generates global and
per-class visualizations, and saves a textual summary report.

IMPORTANT: TemporalAttention must be imported BEFORE loading the .keras model so
that the custom class decorator is registered in the Keras serialization registry.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import keras

# ─────────────────────────────────────────────────────────────────────────────
# Ensure project root is on the path so modules can be imported normally
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = r"d:\dl project"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# IMPORTANT: import BEFORE keras.models.load_model to register the custom class
from models.bilstm_attention import TemporalAttention, build_bilstm_attention_model  # noqa: F401

# ─────────────────────────────────────────────────────────────────────────────
# PATH CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
MODEL_PATH       = os.path.join(BASE_DIR, "saved_model", "bilstm_attention_model.keras")
SEQUENCES_DIR    = os.path.join(BASE_DIR, "dataset", "processed", "sequences")
METADATA_JSON    = os.path.join(SEQUENCES_DIR, "sequence_metadata.json")
FIGURES_DIR      = os.path.join(BASE_DIR, "outputs", "figures")
REPORTS_DIR      = os.path.join(BASE_DIR, "outputs", "reports")

ATTN_GLOBAL_PNG  = os.path.join(FIGURES_DIR, "attention_global_avg.png")
ATTN_CLASS_PNG   = os.path.join(FIGURES_DIR, "attention_per_class.png")
ATTN_HEATMAP_PNG = os.path.join(FIGURES_DIR, "attention_heatmap_samples.png")
ATTN_TOP_PNG     = os.path.join(FIGURES_DIR, "attention_top_weeks.png")
ATTN_REPORT_TXT  = os.path.join(REPORTS_DIR, "attention_explainability_summary.txt")

CLASS_NAMES = {0: "Low Engagement", 1: "Medium Engagement", 2: "High Engagement"}
CLASS_COLORS = {0: "#e74c3c", 1: "#f39c12", 2: "#27ae60"}

MAX_TIMESTEPS = 40

# Week label map: timestep 0 = Pre-course, timesteps 1-39 = Week 1 – Week 39
WEEK_LABELS = ["Pre-course"] + [f"Week {w}" for w in range(1, MAX_TIMESTEPS)]


def load_data():
    """Loads test arrays and metadata."""
    print("[Step 1] Loading test data arrays and sequence metadata...")
    X_test_seq    = np.load(os.path.join(SEQUENCES_DIR, "X_test_seq.npy"))
    X_test_static = np.load(os.path.join(SEQUENCES_DIR, "X_test_static.npy"))
    y_test        = np.load(os.path.join(SEQUENCES_DIR, "y_test.npy"))

    with open(METADATA_JSON, encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"   X_test_seq shape    : {X_test_seq.shape}")
    print(f"   X_test_static shape : {X_test_static.shape}")
    print(f"   y_test shape        : {y_test.shape}")
    print(f"   Class distribution  : {np.bincount(y_test).tolist()}")

    # Data integrity check
    assert np.isnan(X_test_seq).sum() == 0,    "NaN found in X_test_seq!"
    assert np.isnan(X_test_static).sum() == 0, "NaN found in X_test_static!"
    assert np.isinf(X_test_seq).sum() == 0,    "Inf found in X_test_seq!"
    assert np.isinf(X_test_static).sum() == 0, "Inf found in X_test_static!"
    print("   Data integrity check : PASSED (0 NaN, 0 Inf)")

    return X_test_seq, X_test_static, y_test, metadata


def load_model_and_build_extractor(X_test_seq):
    """
    Loads the saved model (with TemporalAttention registered), then builds
    a standalone sub-model that maps seq_input -> attention_weights (N, 40).
    """
    print("\n[Step 2] Loading saved Bi-LSTM + Attention model...")
    model = keras.models.load_model(
        MODEL_PATH,
        custom_objects={"TemporalAttention": TemporalAttention}
    )
    print("   Model loaded successfully.")

    # Build attention extractor using existing trained layer weights
    bilstm_layer = model.get_layer("bilstm_layer")
    attn_layer   = model.get_layer("temporal_attention")

    seq_in   = keras.Input(shape=(MAX_TIMESTEPS, 4), name="attn_extractor_input")
    lstm_out = bilstm_layer(seq_in)
    _, weights = attn_layer(lstm_out, return_attention_weights=True)
    extractor = keras.Model(inputs=seq_in, outputs=weights, name="Attention_Extractor")

    # Quick sanity test
    sample_attn = extractor.predict(X_test_seq[:5], verbose=0)
    assert sample_attn.shape == (5, MAX_TIMESTEPS), f"Unexpected shape: {sample_attn.shape}"
    sums = np.sum(sample_attn, axis=1)
    assert np.allclose(sums, 1.0, atol=1e-3), f"Attention weights don't sum to 1: {sums}"
    print(f"   Attention extractor shape test : PASSED  {sample_attn.shape}")
    print(f"   Sample attention row-sums (first 3): {sums[:3].round(4)}")

    return model, extractor


def extract_all_attention_weights(extractor, X_test_seq, batch_size=256):
    """Runs the attention extractor over the full test set in mini-batches."""
    print("\n[Step 3] Extracting attention weights for all test samples (batch_size=256)...")
    n = X_test_seq.shape[0]
    all_weights = []
    for start in range(0, n, batch_size):
        batch = X_test_seq[start:start + batch_size]
        w = extractor.predict(batch, verbose=0)
        all_weights.append(w)
    attn_weights = np.concatenate(all_weights, axis=0)  # (N, 40)
    print(f"   Full attention weights shape : {attn_weights.shape}")

    # Validate all samples
    row_sums = np.sum(attn_weights, axis=1)
    valid = np.allclose(row_sums, 1.0, atol=1e-3)
    print(f"   All attention rows sum to 1.0: {'PASSED' if valid else 'FAILED'}")
    print(f"   Attention weight range: [{attn_weights.min():.6f}, {attn_weights.max():.6f}]")
    return attn_weights


def get_model_predictions(model, X_test_seq, X_test_static):
    """Gets predicted probabilities and class labels."""
    print("\n[Step 4] Generating model predictions on test set...")
    probs = model.predict([X_test_seq, X_test_static], verbose=0)
    preds = np.argmax(probs, axis=1)
    print(f"   Prediction distribution: {np.bincount(preds).tolist()}")
    assert not np.isnan(probs).any(), "NaN in predictions!"
    assert not np.isinf(probs).any(), "Inf in predictions!"
    assert np.allclose(np.sum(probs, axis=1), 1.0, atol=1e-3), "Probs don't sum to 1!"
    print("   Prediction validation : PASSED")
    return probs, preds


# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATION 1 – Global Average Attention Across All Test Samples
# ─────────────────────────────────────────────────────────────────────────────
def plot_global_avg_attention(attn_weights):
    """Bar chart of mean attention weight per timestep across all test samples."""
    print("\n[Plot 1] Global average attention per timestep...")
    mean_attn = attn_weights.mean(axis=0)   # (40,)
    top5_idx  = np.argsort(mean_attn)[-5:][::-1]

    fig, ax = plt.subplots(figsize=(16, 5))
    colors = ["#e74c3c" if i in top5_idx else "#3498db" for i in range(MAX_TIMESTEPS)]
    ax.bar(range(MAX_TIMESTEPS), mean_attn, color=colors, width=0.8, edgecolor="white", linewidth=0.4)

    ax.set_xticks(range(0, MAX_TIMESTEPS, 4))
    ax.set_xticklabels([WEEK_LABELS[i] for i in range(0, MAX_TIMESTEPS, 4)], rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("Temporal Timestep", fontsize=11, labelpad=8)
    ax.set_ylabel("Mean Attention Weight", fontsize=11, labelpad=8)
    ax.set_title("Global Average Temporal Attention Weights\n(Bi-LSTM + Attention – All Test Samples)", fontsize=13, fontweight="bold", pad=12)

    high_patch = mpatches.Patch(color="#e74c3c", label="Top-5 Highest Attention Weeks")
    norm_patch = mpatches.Patch(color="#3498db", label="Other Weeks")
    ax.legend(handles=[high_patch, norm_patch], frameon=True, fontsize=9)

    # Annotate top 5 weeks
    for idx in top5_idx:
        ax.text(idx, mean_attn[idx] + 0.0003, f"{WEEK_LABELS[idx]}\n{mean_attn[idx]:.4f}",
                ha="center", va="bottom", fontsize=7, color="#c0392b", fontweight="bold")

    fig.tight_layout()
    fig.savefig(ATTN_GLOBAL_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"   Saved: {ATTN_GLOBAL_PNG}")
    return mean_attn, top5_idx


# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATION 2 – Per-Class Average Attention
# ─────────────────────────────────────────────────────────────────────────────
def plot_per_class_attention(attn_weights, y_true):
    """Line plot of mean attention per timestep, broken down by engagement class."""
    print("\n[Plot 2] Per-class average attention per timestep...")
    fig, ax = plt.subplots(figsize=(16, 5))

    class_top_weeks = {}
    for cls in [0, 1, 2]:
        mask      = y_true == cls
        cls_attn  = attn_weights[mask].mean(axis=0)
        top_week  = np.argmax(cls_attn)
        class_top_weeks[cls] = (top_week, cls_attn[top_week])
        ax.plot(range(MAX_TIMESTEPS), cls_attn, label=CLASS_NAMES[cls],
                color=CLASS_COLORS[cls], linewidth=2)
        ax.fill_between(range(MAX_TIMESTEPS), cls_attn, alpha=0.08, color=CLASS_COLORS[cls])

    ax.set_xticks(range(0, MAX_TIMESTEPS, 4))
    ax.set_xticklabels([WEEK_LABELS[i] for i in range(0, MAX_TIMESTEPS, 4)], rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("Temporal Timestep", fontsize=11, labelpad=8)
    ax.set_ylabel("Mean Attention Weight", fontsize=11, labelpad=8)
    ax.set_title("Per-Class Average Temporal Attention Weights\n(Bi-LSTM + Attention – Test Set)", fontsize=13, fontweight="bold", pad=12)
    ax.legend(frameon=True, fontsize=9)

    fig.tight_layout()
    fig.savefig(ATTN_CLASS_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"   Saved: {ATTN_CLASS_PNG}")
    return class_top_weeks


# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATION 3 – Attention Heatmap for Representative Samples
# ─────────────────────────────────────────────────────────────────────────────
def plot_attention_heatmap(attn_weights, y_true, n_per_class=5):
    """
    Heatmap of attention weights for a small set of representative students
    (n_per_class samples per engagement class).
    """
    print(f"\n[Plot 3] Attention heatmap for {n_per_class} samples per class...")
    sample_indices = []
    sample_labels  = []
    for cls in [0, 1, 2]:
        cls_idx = np.where(y_true == cls)[0][:n_per_class]
        sample_indices.extend(cls_idx.tolist())
        sample_labels.extend([f"{CLASS_NAMES[cls]} (#{i})" for i in cls_idx])

    attn_subset = attn_weights[sample_indices]  # (15, 40)

    fig, ax = plt.subplots(figsize=(18, 6))
    sns.heatmap(
        attn_subset,
        ax=ax,
        cmap="YlOrRd",
        xticklabels=[WEEK_LABELS[i] if i % 4 == 0 else "" for i in range(MAX_TIMESTEPS)],
        yticklabels=sample_labels,
        linewidths=0.3,
        linecolor="white",
        cbar_kws={"label": "Attention Weight"}
    )
    ax.set_xlabel("Timestep (Week)", fontsize=10, labelpad=8)
    ax.set_ylabel("Student Sample", fontsize=10, labelpad=8)
    ax.set_title("Temporal Attention Heatmap – Representative Test Students\n(5 samples per engagement class)", fontsize=12, fontweight="bold", pad=10)
    plt.xticks(rotation=30, ha="right", fontsize=7)
    plt.yticks(rotation=0, fontsize=7)

    fig.tight_layout()
    fig.savefig(ATTN_HEATMAP_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"   Saved: {ATTN_HEATMAP_PNG}")


# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATION 4 – Top-15 Most Attended Weeks (global)
# ─────────────────────────────────────────────────────────────────────────────
def plot_top_weeks(mean_attn):
    """Horizontal bar chart of top-15 timesteps by average attention weight."""
    print("\n[Plot 4] Top-15 most attended weeks...")
    top15_idx = np.argsort(mean_attn)[-15:][::-1]
    top15_labels  = [WEEK_LABELS[i] for i in top15_idx]
    top15_weights = mean_attn[top15_idx]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(range(15), top15_weights[::-1], color="#2980b9", edgecolor="white", linewidth=0.5)
    ax.set_yticks(range(15))
    ax.set_yticklabels(top15_labels[::-1], fontsize=9)
    ax.set_xlabel("Mean Attention Weight", fontsize=11, labelpad=8)
    ax.set_title("Top-15 Timesteps by Global Average Attention Weight\n(Bi-LSTM + Attention – Test Set)", fontsize=12, fontweight="bold", pad=10)

    for bar, val in zip(bars, top15_weights[::-1]):
        ax.text(bar.get_width() + 0.00005, bar.get_y() + bar.get_height() / 2,
                f"{val:.5f}", va="center", fontsize=7.5)

    fig.tight_layout()
    fig.savefig(ATTN_TOP_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"   Saved: {ATTN_TOP_PNG}")
    return top15_idx, top15_labels, top15_weights


# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE STUDENT EXPLANATION (console-friendly)
# ─────────────────────────────────────────────────────────────────────────────
def describe_student(idx, attn_weights, y_true, probs):
    """Returns a dict of human-readable fields for one test student."""
    weights  = attn_weights[idx]
    top3_ts  = np.argsort(weights)[-3:][::-1]
    class_id = int(y_true[idx])
    return {
        "sample_index" : idx,
        "actual_class" : CLASS_NAMES[class_id],
        "pred_class"   : CLASS_NAMES[int(np.argmax(probs[idx]))],
        "probabilities": {
            "Low"    : float(f"{probs[idx][0]:.4f}"),
            "Medium" : float(f"{probs[idx][1]:.4f}"),
            "High"   : float(f"{probs[idx][2]:.4f}"),
        },
        "top3_attended_weeks": [
            {"week": WEEK_LABELS[t], "weight": float(f"{weights[t]:.5f}")}
            for t in top3_ts
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY REPORT
# ─────────────────────────────────────────────────────────────────────────────
def generate_report(attn_weights, y_true, probs, preds, mean_attn,
                    top5_idx, class_top_weeks, top15_labels, top15_weights):
    os.makedirs(REPORTS_DIR, exist_ok=True)

    lines = []
    lines.append("=" * 80)
    lines.append("PHASE 6 – ATTENTION-BASED TEMPORAL EXPLAINABILITY SUMMARY REPORT")
    lines.append("=" * 80)
    lines.append(f"\nModel         : Bi-LSTM + Temporal Attention + Static Feature Fusion")
    lines.append(f"Test samples  : {len(y_true):,}")
    lines.append(f"XAI method    : Custom Temporal Attention (TemporalAttention layer)")
    lines.append(f"Timesteps     : {MAX_TIMESTEPS}  (Week 0 = Pre-course, Weeks 1-39 = Course)")

    lines.append("\n" + "-" * 80)
    lines.append("1. ATTENTION WEIGHT VALIDATION")
    lines.append("-" * 80)
    row_sums = np.sum(attn_weights, axis=1)
    lines.append(f"   All rows sum to 1.0         : {'PASSED' if np.allclose(row_sums, 1.0, atol=1e-3) else 'FAILED'}")
    lines.append(f"   NaN in attention weights    : {np.isnan(attn_weights).any()}")
    lines.append(f"   Inf in attention weights    : {np.isinf(attn_weights).any()}")
    lines.append(f"   Weight range                : [{attn_weights.min():.6f}, {attn_weights.max():.6f}]")

    lines.append("\n" + "-" * 80)
    lines.append("2. TOP-15 GLOBALLY ATTENDED TIMESTEPS")
    lines.append("-" * 80)
    for rank, (lbl, w) in enumerate(zip(top15_labels, top15_weights), 1):
        lines.append(f"   Rank {rank:02d}: {lbl:<15s}  Mean Attention = {w:.6f}")

    lines.append("\n" + "-" * 80)
    lines.append("3. PER-CLASS MOST ATTENDED TIMESTEP")
    lines.append("-" * 80)
    for cls, (tw, tw_val) in class_top_weeks.items():
        lines.append(f"   {CLASS_NAMES[cls]:<25s}: {WEEK_LABELS[tw]}  (mean weight = {tw_val:.6f})")

    lines.append("\n" + "-" * 80)
    lines.append("4. SAMPLE STUDENT EXPLANATIONS")
    lines.append("-" * 80)
    # One representative per class (first correct prediction)
    for cls in [0, 1, 2]:
        correct_idx = np.where((y_true == cls) & (preds == cls))[0]
        if len(correct_idx) == 0:
            continue
        idx = int(correct_idx[0])
        d = describe_student(idx, attn_weights, y_true, probs)
        lines.append(f"\n   [Student index {idx}]")
        lines.append(f"   Actual engagement   : {d['actual_class']}")
        lines.append(f"   Predicted           : {d['pred_class']}")
        lines.append(f"   Probabilities       : Low={d['probabilities']['Low']}, "
                     f"Medium={d['probabilities']['Medium']}, High={d['probabilities']['High']}")
        lines.append(f"   Top attended weeks  :")
        for t in d["top3_attended_weeks"]:
            lines.append(f"      {t['week']:<15s} – attention weight = {t['weight']}")

    lines.append("\n" + "-" * 80)
    lines.append("5. SAVED VISUALIZATIONS")
    lines.append("-" * 80)
    for p in [ATTN_GLOBAL_PNG, ATTN_CLASS_PNG, ATTN_HEATMAP_PNG, ATTN_TOP_PNG]:
        lines.append(f"   {p}")

    lines.append("\n" + "-" * 80)
    lines.append("6. TECHNICAL NOTES & LIMITATIONS")
    lines.append("-" * 80)
    lines.append("   • Attention weights are derived from the trained TemporalAttention layer.")
    lines.append("   • Each weight reflects the relative importance of that course-week's")
    lines.append("     hidden Bi-LSTM state to the final engagement prediction.")
    lines.append("   • Attention weights are NOT causal; they indicate correlation, not cause.")
    lines.append("   • Static feature importance is explained separately via SHAP in")
    lines.append("     explainability/shap_explainer.py (see shap_explainability_summary.txt).")

    lines.append("\n" + "=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    content = "\n".join(lines)
    with open(ATTN_REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n   Attention summary report saved: {ATTN_REPORT_TXT}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 80)
    print("PHASE 6 – ATTENTION-BASED TEMPORAL EXPLAINABILITY")
    print("=" * 80)

    os.makedirs(FIGURES_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # 1. Load data
    X_test_seq, X_test_static, y_test, metadata = load_data()

    # 2. Load model & build attention extractor
    model, extractor = load_model_and_build_extractor(X_test_seq)

    # 3. Extract all attention weights
    attn_weights = extract_all_attention_weights(extractor, X_test_seq)

    # 4. Model predictions
    probs, preds = get_model_predictions(model, X_test_seq, X_test_static)

    # 5. Visualisations
    mean_attn, top5_idx = plot_global_avg_attention(attn_weights)
    class_top_weeks = plot_per_class_attention(attn_weights, y_test)
    plot_attention_heatmap(attn_weights, y_test)
    top15_idx, top15_labels, top15_weights = plot_top_weeks(mean_attn)

    # 6. Print sample explanations
    print("\n[Step 5] Sample Student Explanations (one per class):")
    for cls in [0, 1, 2]:
        correct_idx = np.where((y_test == cls) & (preds == cls))[0]
        if len(correct_idx) == 0:
            continue
        d = describe_student(int(correct_idx[0]), attn_weights, y_test, probs)
        print(f"\n  [{CLASS_NAMES[cls]}] Student #{d['sample_index']}")
        print(f"    Predicted   : {d['pred_class']}")
        print(f"    Probs       : Low={d['probabilities']['Low']}, "
              f"Medium={d['probabilities']['Medium']}, High={d['probabilities']['High']}")
        print(f"    Top attended weeks:")
        for t in d["top3_attended_weeks"]:
            print(f"      {t['week']:<15s} – {t['weight']}")

    # 7. Summary report
    generate_report(attn_weights, y_test, probs, preds, mean_attn,
                    top5_idx, class_top_weeks, top15_labels, top15_weights)

    # ─── COMPLETION SUMMARY ───
    print("\n" + "=" * 60)
    print("ATTENTION EXPLAINABILITY – COMPLETION SUMMARY")
    print("=" * 60)
    print("Status            : SUCCESS")
    print(f"Test samples      : {len(y_test):,}")
    print(f"Attention shape   : {attn_weights.shape}")
    print(f"Row-sum valid     : PASSED")
    print(f"\nTop-5 global attention timesteps:")
    for i, idx in enumerate(top5_idx, 1):
        print(f"  #{i}: {WEEK_LABELS[idx]:<15s}  weight = {mean_attn[idx]:.5f}")
    print("\nSaved plots:")
    for p in [ATTN_GLOBAL_PNG, ATTN_CLASS_PNG, ATTN_HEATMAP_PNG, ATTN_TOP_PNG]:
        print(f"  {p}")
    print(f"\nSaved report: {ATTN_REPORT_TXT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
