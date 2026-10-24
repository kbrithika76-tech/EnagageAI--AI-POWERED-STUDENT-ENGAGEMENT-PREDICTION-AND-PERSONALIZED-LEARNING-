import os
import pandas as pd
import numpy as np

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================
BASE_DIR = r"d:\dl project"
INPUT_CLEANED_CSV = os.path.join(BASE_DIR, "dataset", "processed", "cleaned_dataset.csv")
COURSES_CSV = os.path.join(BASE_DIR, "extracted_data", "courses.csv")
ASSESSMENTS_CSV = os.path.join(BASE_DIR, "extracted_data", "assessments.csv")

OUTPUT_ENGINEERED_CSV = os.path.join(BASE_DIR, "dataset", "processed", "engineered_dataset.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "outputs", "reports")
SUMMARY_REPORT_TXT = os.path.join(REPORTS_DIR, "feature_engineering_summary.txt")

# Expected required columns in input cleaned_dataset.csv
REQUIRED_INPUT_COLUMNS = [
    "code_module", "code_presentation", "id_student",
    "gender", "region", "highest_education", "imd_band", "age_band",
    "num_of_prev_attempts", "studied_credits", "disability", "final_result",
    "date_registration", "date_unregistration",
    "total_vle_clicks", "active_vle_days", "precourse_vle_clicks",
    "first_interaction_day", "last_interaction_day",
    "assessments_submitted", "mean_score", "min_score", "max_score",
    "late_submissions", "banked_assessments"
]


def validate_input_columns(df: pd.DataFrame):
    """
    Validates that all expected input columns exist in the input DataFrame.
    Stops with a clear ValueError if any column is missing.
    """
    missing_cols = [col for col in REQUIRED_INPUT_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Input dataset is missing expected columns: {missing_cols}\n"
            f"Available columns: {list(df.columns)}"
        )
    print(" -> Input columns validation passed successfully.")


def load_and_merge_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Loads courses.csv and assessments.csv metadata to fetch module presentation length
    and total expected assessments per course module.
    """
    print("\n[Step 2] Loading metadata for course lengths and assessment counts...")
    
    # Load courses metadata
    if not os.path.exists(COURSES_CSV):
        raise FileNotFoundError(f"Courses metadata file not found at {COURSES_CSV}")
    df_courses = pd.read_csv(COURSES_CSV)
    
    # Load assessments metadata
    if not os.path.exists(ASSESSMENTS_CSV):
        raise FileNotFoundError(f"Assessments metadata file not found at {ASSESSMENTS_CSV}")
    df_assessments = pd.read_csv(ASSESSMENTS_CSV)
    
    # Calculate total expected assessments per module presentation
    assess_counts = df_assessments.groupby(["code_module", "code_presentation"])["id_assessment"].count().reset_index()
    assess_counts.rename(columns={"id_assessment": "total_module_assessments"}, inplace=True)
    
    # Merge course presentation length
    df_merged = pd.merge(
        df,
        df_courses[["code_module", "code_presentation", "module_presentation_length"]],
        on=["code_module", "code_presentation"],
        how="left"
    )
    
    # Merge total module assessments count
    df_merged = pd.merge(
        df_merged,
        assess_counts,
        on=["code_module", "code_presentation"],
        how="left"
    )
    
    # Fallback if any metadata missing (safe filling)
    df_merged["module_presentation_length"] = df_merged["module_presentation_length"].fillna(268)
    df_merged["total_module_assessments"] = df_merged["total_module_assessments"].fillna(5)
    
    print(f" -> Successfully merged metadata. Columns added: ['module_presentation_length', 'total_module_assessments']")
    return df_merged


def create_vle_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates VLE engagement features safely handling division by zero.
    Features created:
    - avg_clicks_per_active_day
    - clicks_per_course_day
    - vle_activity_ratio
    - interaction_intensity
    """
    print("\n[Step 3] Constructing VLE Engagement Features...")
    df = df.copy()

    # 1. Average clicks per active VLE day
    df["avg_clicks_per_active_day"] = np.where(
        df["active_vle_days"] > 0,
        df["total_vle_clicks"] / df["active_vle_days"],
        0.0
    )

    # 2. Clicks per total course day
    df["clicks_per_course_day"] = np.where(
        df["module_presentation_length"] > 0,
        df["total_vle_clicks"] / df["module_presentation_length"],
        0.0
    )

    # 3. VLE activity ratio (proportion of active days out of total course days)
    df["vle_activity_ratio"] = np.where(
        df["module_presentation_length"] > 0,
        np.minimum(1.0, df["active_vle_days"] / df["module_presentation_length"]),
        0.0
    )

    # 4. Interaction intensity (clicks per day within active span)
    interaction_span = np.maximum(1.0, df["last_interaction_day"] - df["first_interaction_day"] + 1)
    df["interaction_intensity"] = np.where(
        (df["active_vle_days"] > 0) & (df["last_interaction_day"] >= df["first_interaction_day"]),
        df["total_vle_clicks"] / interaction_span,
        0.0
    )

    print(" -> VLE engagement features created successfully.")
    return df


def create_registration_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates registration features safely respecting NaN in date_unregistration.
    Features created:
    - registration_delay
    - registered_before_course
    - late_registration_flag
    - withdrawn_flag
    - active_duration
    """
    print("\n[Step 4] Constructing Registration Features...")
    df = df.copy()

    # 1. Registration delay (raw registration day relative to course start)
    df["registration_delay"] = df["date_registration"]

    # 2. Registered before course start flag (1 if registered prior to day 0)
    df["registered_before_course"] = (df["date_registration"] < 0).astype(int)

    # 3. Late registration flag (1 if registered after day 0)
    df["late_registration_flag"] = (df["date_registration"] > 0).astype(int)

    # 4. Withdrawn flag (1 if date_unregistration is present, 0 otherwise)
    # Do NOT replace date_unregistration with 0 before creating withdrawn_flag!
    df["withdrawn_flag"] = df["date_unregistration"].notnull().astype(int)

    # 5. Active duration (days registered in module)
    # For withdrawn students: date_unregistration - date_registration
    # For non-withdrawn students: module_presentation_length - date_registration
    end_day = np.where(
        df["date_unregistration"].notnull(),
        df["date_unregistration"],
        df["module_presentation_length"]
    )
    df["active_duration"] = np.maximum(0.0, end_day - df["date_registration"])

    print(" -> Registration features created successfully.")
    return df


def create_assessment_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates assessment features using metadata and aggregate columns.
    Features created:
    - assessment_completion_rate
    - late_submission_ratio
    - assessment_score_normalized
    - failed_assessment_flag
    - high_score_flag
    """
    print("\n[Step 5] Constructing Assessment Features...")
    df = df.copy()

    # 1. Assessment completion rate
    df["assessment_completion_rate"] = np.where(
        df["total_module_assessments"] > 0,
        np.minimum(1.0, df["assessments_submitted"] / df["total_module_assessments"]),
        0.0
    )

    # 2. Late submission ratio
    df["late_submission_ratio"] = np.where(
        df["assessments_submitted"] > 0,
        np.minimum(1.0, df["late_submissions"] / df["assessments_submitted"]),
        0.0
    )

    # 3. Assessment score normalized (0.0 to 1.0)
    df["assessment_score_normalized"] = df["mean_score"] / 100.0

    # 4. Failed assessment flag (1 if student submitted assessments but min_score < 40)
    df["failed_assessment_flag"] = np.where(
        (df["assessments_submitted"] > 0) & (df["min_score"] < 40.0),
        1,
        0
    )

    # 5. High score flag (1 if student submitted assessments and mean_score >= 70)
    df["high_score_flag"] = np.where(
        (df["assessments_submitted"] > 0) & (df["mean_score"] >= 70.0),
        1,
        0
    )

    print(" -> Assessment features created successfully.")
    return df


def create_academic_history_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates academic history normalized and derived features.
    Features created:
    - is_repeat_student
    - credits_per_attempt
    - studied_credits_normalized
    """
    print("\n[Step 6] Constructing Academic History Features...")
    df = df.copy()

    # 1. Repeat student flag
    df["is_repeat_student"] = (df["num_of_prev_attempts"] > 0).astype(int)

    # 2. Credits per attempt
    df["credits_per_attempt"] = df["studied_credits"] / (df["num_of_prev_attempts"] + 1.0)

    # 3. Studied credits normalized (relative to standard max of 300)
    max_credits = max(300.0, df["studied_credits"].max())
    df["studied_credits_normalized"] = df["studied_credits"] / max_credits

    print(" -> Academic history features created successfully.")
    return df


def create_composite_engagement_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates composite engagement features useful for student engagement prediction.
    Features created:
    - click_activity_score
    - assessment_performance_score
    - overall_engagement_indicator
    """
    print("\n[Step 7] Constructing Composite Engagement Features...")
    df = df.copy()

    # 1. Click activity score (normalized combination of log-clicks and activity ratio)
    click_log = np.log1p(df["total_vle_clicks"])
    max_click_log = click_log.max() if click_log.max() > 0 else 1.0
    norm_click_log = click_log / max_click_log
    df["click_activity_score"] = 0.5 * norm_click_log + 0.5 * df["vle_activity_ratio"]

    # 2. Assessment performance score (combination of completion rate and score)
    df["assessment_performance_score"] = (
        0.5 * df["assessment_completion_rate"] + 0.5 * df["assessment_score_normalized"]
    )

    # 3. Overall engagement indicator (weighted combination of VLE & assessment performance)
    df["overall_engagement_indicator"] = (
        0.5 * df["click_activity_score"] + 0.5 * df["assessment_performance_score"]
    )

    print(" -> Composite engagement features created successfully.")
    return df


def run_data_quality_checks(df: pd.DataFrame, engineered_cols: list) -> dict:
    """
    Performs data quality validation on the engineered dataset.
    Returns diagnostic metrics dictionary.
    """
    print("\n[Step 8] Running Data Quality & Integrity Diagnostics...")
    
    # 1. Duplicate check on primary key: code_module + code_presentation + id_student
    key_cols = ["code_module", "code_presentation", "id_student"]
    duplicate_keys = df.duplicated(subset=key_cols).sum()
    
    # 2. Missing values check
    missing_summary = df.isnull().sum()
    missing_cols_count = (missing_summary > 0).sum()
    
    # 3. Infinite values check across numerical features
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    inf_count = np.isinf(df[num_cols]).sum().sum()
    
    # 4. Summary statistics for engineered columns
    stats_df = df[engineered_cols].describe().T[["min", "mean", "50%", "max", "std"]]

    quality_report = {
        "duplicate_key_count": duplicate_keys,
        "missing_summary": missing_summary,
        "missing_cols_count": missing_cols_count,
        "infinite_count": inf_count,
        "stats_df": stats_df
    }

    print(f" -> Duplicate keys count: {duplicate_keys}")
    print(f" -> Columns with missing values count: {missing_cols_count}")
    print(f" -> Infinite values count: {inf_count}")
    
    return quality_report


def save_output_and_report(
    df_original: pd.DataFrame,
    df_engineered: pd.DataFrame,
    engineered_cols: list,
    quality_report: dict
):
    """
    Saves the engineered dataset to CSV and generates the feature summary report TXT.
    """
    print("\n[Step 9] Saving Engineered Dataset and Generating Report...")
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(OUTPUT_ENGINEERED_CSV), exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # Save engineered dataset
    df_engineered.to_csv(OUTPUT_ENGINEERED_CSV, index=False)
    print(f" -> Engineered dataset saved to: {OUTPUT_ENGINEERED_CSV}")
    
    # Generate report text content
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("PHASE 2.3: FEATURE ENGINEERING SUMMARY REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"\nOriginal Dataset Shape (Rows, Columns) : {df_original.shape}")
    report_lines.append(f"Engineered Dataset Shape (Rows, Columns): {df_engineered.shape}")
    report_lines.append(f"\nTotal Newly Created Features            : {len(engineered_cols)}")
    report_lines.append("\nNewly Created Feature Names:")
    for col in engineered_cols:
        report_lines.append(f"  - {col}")
        
    report_lines.append(f"\nDuplicate Primary Keys Count (module+presentation+student): {quality_report['duplicate_key_count']}")
    report_lines.append(f"Total Infinite Values Count across Numerical Features     : {quality_report['infinite_count']}")
    
    report_lines.append("\nMissing Values Summary (Columns with NaNs):")
    missing_sum = quality_report["missing_summary"]
    missing_cols_with_nan = missing_sum[missing_sum > 0]
    if len(missing_cols_with_nan) > 0:
        for col, count in missing_cols_with_nan.items():
            report_lines.append(f"  - {col}: {count} NaNs (Expected: date_unregistration NaNs for non-withdrawn students)")
    else:
        report_lines.append("  - None (0 missing values across all columns)")
        
    report_lines.append("\n" + "=" * 80)
    report_lines.append("STATISTICAL SUMMARY OF ENGINEERED NUMERICAL FEATURES")
    report_lines.append("=" * 80)
    report_lines.append(quality_report["stats_df"].to_string())
    
    report_lines.append("\n" + "=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)
    
    report_content = "\n".join(report_lines)
    with open(SUMMARY_REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f" -> Feature summary report generated at: {SUMMARY_REPORT_TXT}")


def main():
    print("=" * 80)
    print("PHASE 2.3: FEATURE ENGINEERING FOR STUDENT ENGAGEMENT PREDICTION")
    print("=" * 80)
    
    # 1. Load cleaned dataset
    print(f"\n[Step 1] Loading cleaned dataset from: {INPUT_CLEANED_CSV}")
    if not os.path.exists(INPUT_CLEANED_CSV):
        raise FileNotFoundError(f"Cleaned dataset not found at {INPUT_CLEANED_CSV}")
    
    df_raw = pd.read_csv(INPUT_CLEANED_CSV)
    print(f" -> Input Shape: {df_raw.shape}")
    
    # Validate input columns
    validate_input_columns(df_raw)
    
    # 2. Merge metadata
    df_meta = load_and_merge_metadata(df_raw)
    
    # 3. Create Feature Sets
    df_feat = create_vle_features(df_meta)
    df_feat = create_registration_features(df_feat)
    df_feat = create_assessment_features(df_feat)
    df_feat = create_academic_history_features(df_feat)
    df_feat = create_composite_engagement_features(df_feat)
    
    # Define list of engineered columns
    engineered_cols = [
        # Metadata auxiliary columns
        "module_presentation_length", "total_module_assessments",
        # VLE Features
        "avg_clicks_per_active_day", "clicks_per_course_day", "vle_activity_ratio", "interaction_intensity",
        # Registration Features
        "registration_delay", "registered_before_course", "late_registration_flag", "withdrawn_flag", "active_duration",
        # Assessment Features
        "assessment_completion_rate", "late_submission_ratio", "assessment_score_normalized", "failed_assessment_flag", "high_score_flag",
        # Academic History Features
        "is_repeat_student", "credits_per_attempt", "studied_credits_normalized",
        # Composite Engagement Features
        "click_activity_score", "assessment_performance_score", "overall_engagement_indicator"
    ]
    
    # 4. Data Quality Diagnostics
    quality_report = run_data_quality_checks(df_feat, engineered_cols)
    
    # 5. Save Output CSV and TXT Report
    save_output_and_report(df_raw, df_feat, engineered_cols, quality_report)
    
    # 6. Final Validation Outputs (Printed as requested)
    print("\n" + "=" * 80)
    print("PHASE 2.3 VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Input shape          : {df_raw.shape}")
    print(f"Output shape         : {df_feat.shape}")
    print(f"Engineered Columns ({len(engineered_cols)}):")
    for col in engineered_cols:
        print(f" - {col}")
    print(f"Duplicate Key Count  : {quality_report['duplicate_key_count']}")
    print("Missing Value Summary:")
    missing_summary = quality_report["missing_summary"]
    print(missing_summary[missing_summary > 0])
    print(f"Infinite Value Count : {quality_report['infinite_count']}")
    print(f"Output File Path     : {OUTPUT_ENGINEERED_CSV}")
    print("=" * 80)
    print("PHASE 2.3 FEATURE ENGINEERING COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
