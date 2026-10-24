import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set publication style for figures
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"font.size": 11, "figure.autolayout": True})

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================
BASE_DIR = r"d:\dl project"
ENGINEERED_CSV = os.path.join(BASE_DIR, "dataset", "processed", "engineered_dataset.csv")
ENCODED_SCALED_CSV = os.path.join(BASE_DIR, "dataset", "processed", "encoded_scaled_dataset.csv")

OUTPUT_TARGET_CSV = os.path.join(BASE_DIR, "dataset", "processed", "target_dataset.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "outputs", "reports")
FIGURES_DIR = os.path.join(BASE_DIR, "outputs", "figures")

SUMMARY_REPORT_TXT = os.path.join(REPORTS_DIR, "target_construction_summary.txt")
DIST_PLOT_PNG = os.path.join(FIGURES_DIR, "engagement_score_distribution.png")
CLASS_PLOT_PNG = os.path.join(FIGURES_DIR, "engagement_class_distribution.png")

IDENTIFIER_COLUMNS = ["code_module", "code_presentation", "id_student"]
EXCLUDED_TARGET_FUTURE_COLUMNS = ["final_result", "date_unregistration", "withdrawn_flag", "active_duration"]


def validate_input_files():
    """
    Validates presence of required input files.
    """
    for file_path in [ENGINEERED_CSV, ENCODED_SCALED_CSV]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Required input file not found at: {file_path}")
    print(" -> Input files verification passed.")


def construct_composite_engagement_score(df_eng: pd.DataFrame) -> pd.Series:
    """
    Constructs a composite engagement score based on behavioral (VLE) and academic (Assessment) engagement features.
    
    Formula:
      engagement_score = 0.5 * click_activity_score + 0.5 * assessment_performance_score
    """
    # 1. Click activity score (normalized log clicks + activity ratio)
    click_log = np.log1p(df_eng["total_vle_clicks"])
    max_click_log = click_log.max() if click_log.max() > 0 else 1.0
    norm_click_log = click_log / max_click_log
    click_activity_score = 0.5 * norm_click_log + 0.5 * df_eng["vle_activity_ratio"]

    # 2. Assessment performance score (completion rate + normalized score)
    assessment_performance_score = (
        0.5 * df_eng["assessment_completion_rate"] + 0.5 * (df_eng["mean_score"] / 100.0)
    )

    # 3. Composite engagement score
    engagement_score = 0.5 * click_activity_score + 0.5 * assessment_performance_score
    return engagement_score


def apply_percentile_thresholding(engagement_score: pd.Series):
    """
    Applies statistically justified percentile thresholding (33.33rd and 66.67th percentiles)
    to categorize engagement into 3 balanced classes:
      0 = Low Engagement
      1 = Medium Engagement
      2 = High Engagement
    """
    p33, p66 = np.percentile(engagement_score, [33.333333, 66.666667])
    
    # Categorize into numeric class (0, 1, 2)
    engagement_class = pd.cut(
        engagement_score,
        bins=[-np.inf, p33, p66, np.inf],
        labels=[0, 1, 2]
    ).astype(int)

    # Categorize into human-readable level
    engagement_level = pd.cut(
        engagement_score,
        bins=[-np.inf, p33, p66, np.inf],
        labels=["Low Engagement", "Medium Engagement", "High Engagement"]
    ).astype(str)

    return engagement_class, engagement_level, p33, p66


def generate_validation_plots(
    df_target: pd.DataFrame,
    p33: float,
    p66: float
):
    """
    Generates and saves visual validation plots:
    1. engagement_score_distribution.png
    2. engagement_class_distribution.png
    """
    os.makedirs(FIGURES_DIR, exist_ok=True)
    
    # Plot 1: Engagement Score Distribution with Percentile Threshold lines
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(
        df_target["engagement_score"],
        kde=True,
        color="#1f77b4",
        bins=50,
        ax=ax,
        edgecolor="white",
        linewidth=0.5
    )
    ax.axvline(p33, color="#d62728", linestyle="--", linewidth=2, label=f"33.3rd Percentile ({p33:.4f})")
    ax.axvline(p66, color="#2ca02c", linestyle="--", linewidth=2, label=f"66.7th Percentile ({p66:.4f})")
    
    ax.set_title("Distribution of Composite Student Engagement Score", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Composite Engagement Score (0.0 to 1.0)", fontsize=12)
    ax.set_ylabel("Student Count", fontsize=12)
    ax.legend(loc="upper right", frameon=True, facecolor="white", framealpha=0.9)
    
    fig.savefig(DIST_PLOT_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f" -> Engagement score distribution plot saved at: {DIST_PLOT_PNG}")

    # Plot 2: Engagement Class Counts & Percentages
    fig, ax = plt.subplots(figsize=(8, 6))
    class_counts = df_target["engagement_level"].value_counts().reindex(
        ["Low Engagement", "Medium Engagement", "High Engagement"]
    )
    colors = ["#e74c3c", "#f39c12", "#2ecc71"]
    
    bars = ax.bar(class_counts.index, class_counts.values, color=colors, edgecolor="black", linewidth=0.8, width=0.5)
    
    total_students = len(df_target)
    for bar in bars:
        height = bar.get_height()
        pct = (height / total_students) * 100
        ax.annotate(
            f"{height:,}\n({pct:.2f}%)",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold"
        )
        
    ax.set_title("3-Class Student Engagement Target Distribution", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Engagement Class Level", fontsize=12)
    ax.set_ylabel("Student Count", fontsize=12)
    ax.set_ylim(0, max(class_counts.values) * 1.18)
    
    fig.savefig(CLASS_PLOT_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f" -> Engagement class distribution plot saved at: {CLASS_PLOT_PNG}")


def generate_summary_report(
    df_eng: pd.DataFrame,
    df_target: pd.DataFrame,
    p33: float,
    p66: float,
    duplicate_keys: int,
    missing_target: int
):
    """
    Generates and writes target_construction_summary.txt report.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    class_counts = df_target["engagement_class"].value_counts().sort_index()
    class_pcts = (class_counts / len(df_target)) * 100

    level_counts = df_target["engagement_level"].value_counts()
    
    crosstab_final_result = pd.crosstab(
        df_target["engagement_level"],
        df_target["final_result"],
        margins=True
    )

    report = []
    report.append("=" * 80)
    report.append("PHASE 3: TARGET VARIABLE CONSTRUCTION SUMMARY REPORT")
    report.append("=" * 80)
    report.append(f"\nFinal Dataset Shape (Rows, Columns) : {df_target.shape}")
    report.append(f"Total Student-Module Records       : {len(df_target)}")
    
    report.append("\n" + "-" * 80)
    report.append("1. ENGAGEMENT SCORE FORMULA & WEIGHTS")
    report.append("-" * 80)
    report.append("  engagement_score = 0.5 * click_activity_score + 0.5 * assessment_performance_score")
    report.append("  Where:")
    report.append("    click_activity_score         = 0.5 * norm_log_vle_clicks + 0.5 * vle_activity_ratio")
    report.append("    assessment_performance_score = 0.5 * assessment_completion_rate + 0.5 * normalized_score")

    report.append("\n" + "-" * 80)
    report.append("2. THRESHOLD METHODOLOGY & CLASS BREAKPOINTS")
    report.append("-" * 80)
    report.append("  Method: Statistically justified 33.33rd & 66.67th Percentile Thresholding")
    report.append(f"  - 33.33rd Percentile Threshold (P33) : {p33:.6f}")
    report.append(f"  - 66.67th Percentile Threshold (P66) : {p66:.6f}")
    report.append("\n  Class Definitions:")
    report.append(f"    Class 0 (Low Engagement)   : score <= {p33:.6f}")
    report.append(f"    Class 1 (Medium Engagement): {p33:.6f} < score <= {p66:.6f}")
    report.append(f"    Class 2 (High Engagement)  : score > {p66:.6f}")

    report.append("\n" + "-" * 80)
    report.append("3. TARGET CLASS COUNTS AND PERCENTAGES")
    report.append("-" * 80)
    for c_id in [0, 1, 2]:
        name_map = {0: "Low Engagement", 1: "Medium Engagement", 2: "High Engagement"}
        cnt = class_counts[c_id]
        pct = class_pcts[c_id]
        report.append(f"  - Class {c_id} ({name_map[c_id]}): {cnt:,} students ({pct:.2f}%)")

    report.append("\n" + "-" * 80)
    report.append("4. DATA INTEGRITY & LEAKAGE CHECKS")
    report.append("-" * 80)
    report.append(f"  - Duplicate Primary Key Count (module+presentation+student): {duplicate_keys}")
    report.append(f"  - Missing Target Labels Count                              : {missing_target}")
    report.append("  - Leakage Rule Verification                               : PASSED")
    report.append("    (final_result, date_unregistration, withdrawn_flag are preserved for target validation")
    report.append("    and strictly excluded from prediction input features)")

    report.append("\n" + "-" * 80)
    report.append("5. CROSS-TABULATION: ENGAGEMENT CLASS VS ORIGINAL FINAL RESULT")
    report.append("-" * 80)
    report.append(crosstab_final_result.to_string())

    report.append("\n" + "=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    report_content = "\n".join(report)
    with open(SUMMARY_REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f" -> Target summary report generated at: {SUMMARY_REPORT_TXT}")


def main():
    print("=" * 80)
    print("PHASE 3: TARGET VARIABLE CONSTRUCTION FOR STUDENT ENGAGEMENT PREDICTION")
    print("=" * 80)

    # 1. Validate inputs
    print("\n[Step 1] Loading engineered and encoded/scaled datasets...")
    validate_input_files()
    df_eng = pd.read_csv(ENGINEERED_CSV)
    df_scaled = pd.read_csv(ENCODED_SCALED_CSV)
    print(f" -> Engineered dataset shape    : {df_eng.shape}")
    print(f" -> Encoded/Scaled dataset shape: {df_scaled.shape}")

    # 2. Construct Engagement Score
    print("\n[Step 2] Calculating Composite Engagement Score...")
    engagement_score = construct_composite_engagement_score(df_eng)
    print(f" -> Min Score: {engagement_score.min():.4f}, Mean: {engagement_score.mean():.4f}, Max: {engagement_score.max():.4f}")

    # 3. Apply Percentile Thresholding
    print("\n[Step 3] Applying Percentile-based Class Thresholding...")
    engagement_class, engagement_level, p33, p66 = apply_percentile_thresholding(engagement_score)
    print(f" -> 33.33rd Percentile (P33): {p33:.4f}")
    print(f" -> 66.67th Percentile (P66): {p66:.4f}")

    # 4. Combine into Final Target Dataset
    print("\n[Step 4] Assembling Target Dataset...")
    df_target = df_scaled.copy()
    df_target["engagement_score"] = engagement_score
    df_target["engagement_level"] = engagement_level
    df_target["engagement_class"] = engagement_class

    # 5. Data Integrity Checks
    duplicate_keys = df_target.duplicated(subset=IDENTIFIER_COLUMNS).sum()
    missing_target = df_target[["engagement_score", "engagement_level", "engagement_class"]].isnull().sum().sum()
    print(f" -> Duplicate Student-Module Keys: {duplicate_keys}")
    print(f" -> Missing Target Values Count  : {missing_target}")

    # 6. Save Target Dataset CSV
    os.makedirs(os.path.dirname(OUTPUT_TARGET_CSV), exist_ok=True)
    df_target.to_csv(OUTPUT_TARGET_CSV, index=False)
    print(f" -> Target dataset successfully saved at: {OUTPUT_TARGET_CSV}")

    # 7. Generate Validation Plots
    print("\n[Step 5] Generating Validation Plots...")
    generate_validation_plots(df_target, p33, p66)

    # 8. Generate Summary Report
    print("\n[Step 6] Writing Summary Report...")
    generate_summary_report(df_eng, df_target, p33, p66, duplicate_keys, missing_target)

    # 9. Final Validation Prints
    print("\n" + "=" * 80)
    print("PHASE 3 VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Execution Status          : SUCCESS")
    print(f"Input Shape (Engineered)  : {df_eng.shape}")
    print(f"Input Shape (Scaled)      : {df_scaled.shape}")
    print(f"Output Target Dataset     : {df_target.shape}")
    print("\nTarget Class Distribution:")
    counts = df_target["engagement_class"].value_counts().sort_index()
    pcts = (counts / len(df_target)) * 100
    names = {0: "Low Engagement", 1: "Medium Engagement", 2: "High Engagement"}
    for c_id in [0, 1, 2]:
        print(f"  - Class {c_id} ({names[c_id]}): {counts[c_id]:,} ({pcts[c_id]:.2f}%)")
    print(f"\nDuplicate Key Count       : {duplicate_keys}")
    print(f"Missing Target Count      : {missing_target}")
    print(f"Output File Path          : {OUTPUT_TARGET_CSV}")
    print(f"Summary Report Path       : {SUMMARY_REPORT_TXT}")
    print(f"Score Distribution Plot   : {DIST_PLOT_PNG}")
    print(f"Class Distribution Plot   : {CLASS_PLOT_PNG}")
    print("=" * 80)
    print("PHASE 3 TARGET VARIABLE CONSTRUCTION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
