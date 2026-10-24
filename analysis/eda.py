import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for clean visual presentation
sns.set_theme(style="whitegrid")
plt.rcParams.update({"font.size": 10})

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================
BASE_DIR = r"d:\dl project"
INPUT_CSV = os.path.join(BASE_DIR, "dataset", "processed", "cleaned_dataset.csv")
FIGURES_DIR = os.path.join(BASE_DIR, "outputs", "figures")

# Ensure figures output directory exists
os.makedirs(FIGURES_DIR, exist_ok=True)


def main():
    print("=" * 80)
    print("PHASE 2.3: EXPLORATORY DATA ANALYSIS (EDA)")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # STEP 1: LOAD CLEANED DATASET
    # --------------------------------------------------------------------------
    print("\n[Step 1] Loading cleaned_dataset.csv...")
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Cleaned dataset not found at {INPUT_CSV}")
        return

    df = pd.read_csv(INPUT_CSV)

    # --------------------------------------------------------------------------
    # STEP 2: PRINT DATASET INFORMATION & SUMMARY
    # --------------------------------------------------------------------------
    print("\n[Step 2] Dataset Overview:")
    print(f" -> Shape (Rows, Columns): {df.shape}")
    
    print("\n -> Data Types:")
    print(df.dtypes)
    
    print("\n -> Missing Values Summary:")
    print(df.isnull().sum())
    
    print("\n -> Statistical Summary (Numerical Features):")
    print(df.describe().T[["count", "mean", "std", "min", "50%", "max"]])

    print("\n -> Unique Values in Key Categorical Columns:")
    cat_cols = ["final_result", "gender", "highest_education", "age_band", "imd_band", "disability"]
    for col in cat_cols:
        if col in df.columns:
            print(f"\nUnique values in '{col}' ({df[col].nunique()} categories):")
            print(df[col].value_counts())

    # --------------------------------------------------------------------------
    # STEP 3: VISUALIZATIONS & PLOT GENERATION
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("GENERATING & SAVING EDA VISUALIZATIONS")
    print("=" * 80)

    # Plot 1: Final Result Distribution
    plt.figure(figsize=(8, 5))
    ax = sns.countplot(data=df, x="final_result", palette="viridis")
    plt.title("Distribution of Student Final Results", fontsize=14, fontweight="bold")
    plt.xlabel("Final Result", fontsize=12)
    plt.ylabel("Student Count", fontsize=12)
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha="center", va="center", xytext=(0, 5), textcoords="offset points")
    plt.tight_layout()
    plot1_path = os.path.join(FIGURES_DIR, "final_result_distribution.png")
    plt.savefig(plot1_path, dpi=300)
    plt.close()
    print(f" -> Saved: {plot1_path}")

    # Plot 2: Gender Distribution
    plt.figure(figsize=(6, 5))
    ax = sns.countplot(data=df, x="gender", palette="Set2")
    plt.title("Gender Distribution of Students", fontsize=14, fontweight="bold")
    plt.xlabel("Gender", fontsize=12)
    plt.ylabel("Student Count", fontsize=12)
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha="center", va="center", xytext=(0, 5), textcoords="offset points")
    plt.tight_layout()
    plot2_path = os.path.join(FIGURES_DIR, "gender_distribution.png")
    plt.savefig(plot2_path, dpi=300)
    plt.close()
    print(f" -> Saved: {plot2_path}")

    # Plot 3: Highest Education Distribution
    plt.figure(figsize=(10, 5))
    ax = sns.countplot(data=df, y="highest_education", palette="mako", order=df["highest_education"].value_counts().index)
    plt.title("Distribution of Highest Prior Education", fontsize=14, fontweight="bold")
    plt.xlabel("Student Count", fontsize=12)
    plt.ylabel("Highest Education Level", fontsize=12)
    for p in ax.patches:
        ax.annotate(f"{int(p.get_width())}", (p.get_width(), p.get_y() + p.get_height() / 2.),
                    ha="left", va="center", xytext=(5, 0), textcoords="offset points")
    plt.tight_layout()
    plot3_path = os.path.join(FIGURES_DIR, "education_distribution.png")
    plt.savefig(plot3_path, dpi=300)
    plt.close()
    print(f" -> Saved: {plot3_path}")

    # Plot 4: Age Band Distribution
    plt.figure(figsize=(7, 5))
    ax = sns.countplot(data=df, x="age_band", palette="crest")
    plt.title("Distribution of Student Age Bands", fontsize=14, fontweight="bold")
    plt.xlabel("Age Band", fontsize=12)
    plt.ylabel("Student Count", fontsize=12)
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha="center", va="center", xytext=(0, 5), textcoords="offset points")
    plt.tight_layout()
    plot4_path = os.path.join(FIGURES_DIR, "age_band_distribution.png")
    plt.savefig(plot4_path, dpi=300)
    plt.close()
    print(f" -> Saved: {plot4_path}")

    # Plot 5: IMD Band Distribution
    plt.figure(figsize=(10, 5))
    ax = sns.countplot(data=df, x="imd_band", palette="magma")
    plt.title("Distribution of Index of Multiple Deprivation (IMD) Bands", fontsize=14, fontweight="bold")
    plt.xlabel("IMD Band (%)", fontsize=12)
    plt.ylabel("Student Count", fontsize=12)
    plt.xticks(rotation=45)
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha="center", va="center", xytext=(0, 5), textcoords="offset points")
    plt.tight_layout()
    plot5_path = os.path.join(FIGURES_DIR, "imd_band_distribution.png")
    plt.savefig(plot5_path, dpi=300)
    plt.close()
    print(f" -> Saved: {plot5_path}")

    # Plot 6: Total VLE Clicks Histogram (Log-Scale for skewness)
    plt.figure(figsize=(8, 5))
    sns.histplot(df["total_vle_clicks"], bins=50, kde=True, color="teal")
    plt.title("Distribution of Total VLE Clicks", fontsize=14, fontweight="bold")
    plt.xlabel("Total Clicks", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.tight_layout()
    plot6_path = os.path.join(FIGURES_DIR, "vle_clicks_histogram.png")
    plt.savefig(plot6_path, dpi=300)
    plt.close()
    print(f" -> Saved: {plot6_path}")

    # Plot 7: Mean Score Histogram
    plt.figure(figsize=(8, 5))
    sns.histplot(df["mean_score"], bins=40, kde=True, color="coral")
    plt.title("Distribution of Student Mean Assessment Scores", fontsize=14, fontweight="bold")
    plt.xlabel("Mean Score (0 - 100)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.tight_layout()
    plot7_path = os.path.join(FIGURES_DIR, "mean_score_histogram.png")
    plt.savefig(plot7_path, dpi=300)
    plt.close()
    print(f" -> Saved: {plot7_path}")

    # Plot 8: Numerical Feature Correlation Heatmap
    plt.figure(figsize=(10, 8))
    num_df = df.select_dtypes(include=[np.number])
    corr = num_df.corr()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5, cbar=True)
    plt.title("Correlation Heatmap of Numerical Features", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plot8_path = os.path.join(FIGURES_DIR, "correlation_heatmap.png")
    plt.savefig(plot8_path, dpi=300)
    plt.close()
    print(f" -> Saved: {plot8_path}")

    print("\nEDA completed successfully! All plots saved in outputs/figures/")


if __name__ == "__main__":
    main()
