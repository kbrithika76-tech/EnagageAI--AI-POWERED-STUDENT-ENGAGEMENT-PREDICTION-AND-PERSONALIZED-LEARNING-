import os
import pandas as pd
import numpy as np

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================
BASE_DIR = r"d:\dl project"
INPUT_CSV = os.path.join(BASE_DIR, "dataset", "processed", "master_dataset.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "dataset", "processed", "cleaned_dataset.csv")


def main():
    print("=" * 80)
    print("PHASE 2.2: DATA CLEANING & MISSING VALUE IMPUTATION")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # STEP 1: LOAD MASTER DATASET
    # --------------------------------------------------------------------------
    print("\n[Step 1] Loading master_dataset.csv...")
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Master dataset not found at {INPUT_CSV}")
        return

    df = pd.read_csv(INPUT_CSV)

    # --------------------------------------------------------------------------
    # STEP 2: BEFORE-CLEANING DIAGNOSTICS
    # --------------------------------------------------------------------------
    print("\n[Step 2] Initial Dataset Diagnostics (Before Cleaning):")
    print(f" -> Shape (Rows, Columns): {df.shape}")
    print(f" -> Total Duplicate Rows: {df.duplicated().sum()}")
    print("\n -> Data Types & Missing Values Count:")
    missing_before = df.isnull().sum()
    print(missing_before[missing_before > 0])

    print("\n -> Statistical Summary (Numerical Features):")
    print(df.describe().T[["count", "mean", "std", "min", "50%", "max"]])

    # --------------------------------------------------------------------------
    # STEP 3: DUPLICATE REMOVAL
    # --------------------------------------------------------------------------
    print("\n[Step 3] Checking and Removing Duplicate Rows...")
    initial_rows = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    rows_dropped = initial_rows - len(df)
    print(f" -> Dropped {rows_dropped} exact duplicate rows.")

    # --------------------------------------------------------------------------
    # STEP 4: MISSING VALUE IMPUTATION & STRATEGY EXPLANATIONS
    # --------------------------------------------------------------------------
    print("\n[Step 4] Handling Missing Values...")

    # Strategy 1: imd_band -> Categorical string "Unknown"
    # Explanation: Index of Multiple Deprivation (imd_band) is a categorical socioeconomic status.
    # Filling missing entries with "Unknown" preserves the rows without distorting actual deprivation bands.
    df["imd_band"] = df["imd_band"].fillna("Unknown")
    print(" -> Imputed 'imd_band' missing values with 'Unknown'.")

    # Strategy 2: date_registration -> Median registration day
    # Explanation: Registration date is a numerical offset relative to course start.
    # Median is robust against extreme outliers (e.g., students registering very early).
    median_reg_date = df["date_registration"].median()
    df["date_registration"] = df["date_registration"].fillna(median_reg_date)
    print(f" -> Imputed 'date_registration' missing values with median ({median_reg_date}).")

    # Strategy 3: VLE Activity Columns -> 0 Fill
    # Explanation: Students with NaN in VLE activity (total_vle_clicks, active_vle_days, etc.)
    # simply had ZERO recorded interactions in the VLE system during the course.
    # Therefore, 0 is the true domain value for these non-interactive students.
    vle_cols = [
        "total_vle_clicks",
        "active_vle_days",
        "precourse_vle_clicks",
        "first_interaction_day",
        "last_interaction_day"
    ]
    for col in vle_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    print(" -> Imputed missing VLE interaction metrics with 0 (indicating 0 clicks/activity).")

    # Strategy 4: Assessment Summary Columns -> Appropriate Domain Fill
    # Explanation:
    # - 'assessments_submitted', 'late_submissions', 'banked_assessments' -> 0 (0 submitted/late/banked).
    # - 'mean_score', 'min_score', 'max_score' -> 0.0 (0 grade received due to no submissions).
    assess_count_cols = ["assessments_submitted", "late_submissions", "banked_assessments"]
    for col in assess_count_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    assess_score_cols = ["mean_score", "min_score", "max_score"]
    for col in assess_score_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)
    print(" -> Imputed missing Assessment counts and score statistics with 0.0 (indicating non-submission).")

    # Strategy 5: date_unregistration -> KEPT AS NaN
    # Explanation: A missing value in 'date_unregistration' is MEANINGFUL information!
    # It signifies that the student DID NOT WITHDRAW and remained registered through course completion.
    # Thus, keeping NaN in date_unregistration is intentional domain behavior.
    print(" -> Retained 'date_unregistration' NaNs as intentional indicator of course completion.")

    # --------------------------------------------------------------------------
    # STEP 5: BEFORE-AND-AFTER COMPARISON & VALIDATION
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("BEFORE-AND-AFTER MISSING VALUES COMPARISON")
    print("=" * 80)

    missing_after = df.isnull().sum()

    comparison_df = pd.DataFrame({
        "Missing Before": missing_before,
        "Missing After": missing_after
    })
    print(comparison_df[comparison_df["Missing Before"] > 0])

    # --------------------------------------------------------------------------
    # STEP 6: SAVE CLEANED DATASET
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"SAVING CLEANED DATASET TO: {OUTPUT_CSV}")
    print("=" * 80)
    df.to_csv(OUTPUT_CSV, index=False)
    print(" -> Cleaned dataset successfully saved!")


if __name__ == "__main__":
    main()
