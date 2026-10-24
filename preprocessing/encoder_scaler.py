import os
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================
BASE_DIR = r"d:\dl project"
INPUT_ENGINEERED_CSV = os.path.join(BASE_DIR, "dataset", "processed", "engineered_dataset.csv")

OUTPUT_SCALED_CSV = os.path.join(BASE_DIR, "dataset", "processed", "encoded_scaled_dataset.csv")
SAVED_MODEL_DIR = os.path.join(BASE_DIR, "saved_model")
PREPROCESSOR_PKL = os.path.join(SAVED_MODEL_DIR, "feature_preprocessor.pkl")

REPORTS_DIR = os.path.join(BASE_DIR, "outputs", "reports")
SUMMARY_REPORT_TXT = os.path.join(REPORTS_DIR, "encoding_scaling_summary.txt")

# ==============================================================================
# FEATURE COLUMN DEFINITIONS & CATEGORIZATION
# ==============================================================================
IDENTIFIER_COLUMNS = [
    "code_module",
    "code_presentation",
    "id_student"
]

EXCLUDED_TARGET_FUTURE_COLUMNS = [
    "final_result",
    "date_unregistration",
    "withdrawn_flag",
    "active_duration"
]

CATEGORICAL_INPUT_FEATURES = [
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "disability"
]

LOG1P_SKEWED_FEATURES = [
    "total_vle_clicks",
    "precourse_vle_clicks",
    "avg_clicks_per_active_day",
    "clicks_per_course_day",
    "interaction_intensity",
    "active_vle_days"
]


class FeaturePreprocessor:
    """
    Custom Scikit-Learn compatible Preprocessor pipeline that encapsulates:
    1. Categorical OneHotEncoding (with handle_unknown='ignore' for inference safety).
    2. Selective log1p transformation for highly skewed continuous click/count metrics.
    3. StandardScaler transformation for numerical input features.
    
    This fitted preprocessor object is saved to disk and reused directly during
    real-time student engagement prediction to prevent data leakage and guarantee
    identical feature alignment.
    """
    def __init__(self, categorical_cols: list, numerical_cols: list, log1p_cols: list):
        self.categorical_cols = categorical_cols
        self.numerical_cols = numerical_cols
        self.log1p_cols = log1p_cols
        
        self.encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        self.scaler = StandardScaler()
        
        self.encoded_cat_feature_names_ = []
        self.feature_names_out_ = []
        self.is_fitted = False

    def fit(self, df: pd.DataFrame):
        """
        Fits the OneHotEncoder on categorical columns and StandardScaler on numerical columns.
        """
        # Fit OneHotEncoder
        self.encoder.fit(df[self.categorical_cols])
        self.encoded_cat_feature_names_ = list(
            self.encoder.get_feature_names_out(self.categorical_cols)
        )
        
        # Prepare numerical features (apply log1p before fitting scaler)
        df_num = df[self.numerical_cols].copy()
        for col in self.log1p_cols:
            if col in df_num.columns:
                df_num[col] = np.log1p(df_num[col])
                
        # Fit StandardScaler
        self.scaler.fit(df_num)
        
        # Save complete ordered list of model input feature names
        self.feature_names_out_ = self.encoded_cat_feature_names_ + list(self.numerical_cols)
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms input DataFrame using the fitted OneHotEncoder and StandardScaler.
        Returns a DataFrame containing transformed model input features.
        """
        if not self.is_fitted:
            raise RuntimeError("FeaturePreprocessor must be fitted before calling transform().")
            
        # Transform categorical features
        cat_array = self.encoder.transform(df[self.categorical_cols])
        df_cat_encoded = pd.DataFrame(cat_array, columns=self.encoded_cat_feature_names_, index=df.index)
        
        # Prepare and transform numerical features
        df_num = df[self.numerical_cols].copy()
        for col in self.log1p_cols:
            if col in df_num.columns:
                df_num[col] = np.log1p(df_num[col])
                
        num_array = self.scaler.transform(df_num)
        df_num_scaled = pd.DataFrame(num_array, columns=self.numerical_cols, index=df.index)
        
        # Combine transformed categorical and numerical features
        df_transformed = pd.concat([df_cat_encoded, df_num_scaled], axis=1)
        return df_transformed

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convenience method to fit preprocessor and transform DataFrame.
        """
        self.fit(df)
        return self.transform(df)


def validate_input_dataset(df: pd.DataFrame):
    """
    Validates presence of required columns and reports input dataset characteristics.
    """
    all_known_cols = IDENTIFIER_COLUMNS + EXCLUDED_TARGET_FUTURE_COLUMNS + CATEGORICAL_INPUT_FEATURES
    missing_expected = [c for c in all_known_cols if c not in df.columns]
    if missing_expected:
        raise ValueError(f"Input dataset is missing expected columns: {missing_expected}")
    print(" -> Input columns validation passed successfully.")


def run_diagnostics(df_output: pd.DataFrame, model_feature_names: list) -> dict:
    """
    Runs diagnostic checks on the encoded & scaled dataset.
    """
    # 1. Duplicate student-module keys check
    duplicate_keys = df_output.duplicated(subset=["code_module", "code_presentation", "id_student"]).sum()
    
    # 2. Missing values check across all columns
    missing_summary = df_output.isnull().sum()
    missing_count = missing_summary.sum()
    
    # 3. Infinite values check across numerical model input features
    inf_count = np.isinf(df_output[model_feature_names].values).sum()
    
    # 4. Scaled numerical features statistics verification (mean ≈ 0, std ≈ 1)
    num_stats = df_output[model_feature_names].describe().T[["mean", "std", "min", "50%", "max"]]

    return {
        "duplicate_keys": duplicate_keys,
        "missing_summary": missing_summary,
        "missing_count": missing_count,
        "inf_count": inf_count,
        "num_stats": num_stats
    }


def generate_summary_report(
    df_input: pd.DataFrame,
    df_output: pd.DataFrame,
    cat_cols: list,
    num_cols: list,
    log1p_cols: list,
    model_feature_names: list,
    diagnostics: dict
):
    """
    Generates and saves summary text report encoding_scaling_summary.txt.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    report = []
    report.append("=" * 80)
    report.append("PHASE 2.4: CATEGORICAL ENCODING & NUMERICAL FEATURE SCALING SUMMARY REPORT")
    report.append("=" * 80)
    report.append(f"\nInput Dataset Shape (Rows, Columns) : {df_input.shape}")
    report.append(f"Output Dataset Shape (Rows, Columns): {df_output.shape}")
    
    report.append("\n" + "-" * 80)
    report.append("COLUMN CATEGORIZATION & TRACKING")
    report.append("-" * 80)
    report.append(f"Identifier Columns ({len(IDENTIFIER_COLUMNS)}):")
    for col in IDENTIFIER_COLUMNS:
        report.append(f"  - {col}")
        
    report.append(f"\nExcluded Target / Future-Outcome Columns ({len(EXCLUDED_TARGET_FUTURE_COLUMNS)}):")
    for col in EXCLUDED_TARGET_FUTURE_COLUMNS:
        report.append(f"  - {col} (Preserved for Phase 3 target creation; excluded from predictor features)")
        
    report.append(f"\nCategorical Input Columns ({len(cat_cols)}):")
    for col in cat_cols:
        report.append(f"  - {col}")
        
    report.append(f"\nNumerical Input Columns ({len(num_cols)}):")
    for col in num_cols:
        is_log = " [Log1p Transformed]" if col in log1p_cols else ""
        report.append(f"  - {col}{is_log}")
        
    report.append("\n" + "-" * 80)
    report.append("TRANSFORMATION CONFIGURATION")
    report.append("-" * 80)
    report.append("Categorical Encoding Method : OneHotEncoder(sparse_output=False, handle_unknown='ignore')")
    report.append("Numerical Scaling Method    : StandardScaler()")
    report.append(f"Log1p Transformed Features   : {log1p_cols}")
    report.append(f"Total Model Input Features  : {len(model_feature_names)}")
    report.append(f"Saved Preprocessor Path     : {PREPROCESSOR_PKL}")
    
    report.append("\n" + "-" * 80)
    report.append("DATA INTEGRITY & QUALITY DIAGNOSTICS")
    report.append("-" * 80)
    report.append(f"Duplicate Primary Key Count (module+presentation+student): {diagnostics['duplicate_keys']}")
    report.append(f"Total Infinite Values Count across Model Features       : {diagnostics['inf_count']}")
    
    report.append("\nMissing Values Summary (Columns with NaNs):")
    missing_sum = diagnostics["missing_summary"]
    missing_nan = missing_sum[missing_sum > 0]
    if len(missing_nan) > 0:
        for col, cnt in missing_nan.items():
            report.append(f"  - {col}: {cnt} NaNs (Expected: date_unregistration NaNs for non-withdrawn students)")
    else:
        report.append("  - None (0 missing values across all columns)")

    report.append("\n" + "=" * 80)
    report.append("STATISTICAL SUMMARY OF MODEL INPUT FEATURES (FIRST 20 FEATURES)")
    report.append("=" * 80)
    report.append(diagnostics["num_stats"].head(20).to_string())

    report.append("\n\n" + "=" * 80)
    report.append("COMPLETE ORDERED MODEL FEATURE NAMES LIST")
    report.append("=" * 80)
    for idx, fname in enumerate(model_feature_names, 1):
        report.append(f"{idx:02d}. {fname}")
        
    report.append("\n" + "=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    report_content = "\n".join(report)
    with open(SUMMARY_REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f" -> Encoding & scaling summary report generated at: {SUMMARY_REPORT_TXT}")


def main():
    print("=" * 80)
    print("PHASE 2.4: CATEGORICAL ENCODING & NUMERICAL FEATURE SCALING")
    print("=" * 80)

    # Step 1: Load input engineered dataset
    print(f"\n[Step 1] Loading engineered dataset from: {INPUT_ENGINEERED_CSV}")
    if not os.path.exists(INPUT_ENGINEERED_CSV):
        raise FileNotFoundError(f"Engineered dataset file not found at {INPUT_ENGINEERED_CSV}")

    df_raw = pd.read_csv(INPUT_ENGINEERED_CSV)
    print(f" -> Input Shape: {df_raw.shape}")

    # Validate input dataset columns
    validate_input_dataset(df_raw)

    # Step 2: Determine numerical input features dynamically
    all_non_num = IDENTIFIER_COLUMNS + EXCLUDED_TARGET_FUTURE_COLUMNS + CATEGORICAL_INPUT_FEATURES
    numerical_input_features = [c for c in df_raw.columns if c not in all_non_num]
    
    print("\n[Step 2] Feature Categorization Summary:")
    print(f" -> Identifiers ({len(IDENTIFIER_COLUMNS)}): {IDENTIFIER_COLUMNS}")
    print(f" -> Excluded Target/Future Columns ({len(EXCLUDED_TARGET_FUTURE_COLUMNS)}): {EXCLUDED_TARGET_FUTURE_COLUMNS}")
    print(f" -> Categorical Input Features ({len(CATEGORICAL_INPUT_FEATURES)}): {CATEGORICAL_INPUT_FEATURES}")
    print(f" -> Numerical Input Features ({len(numerical_input_features)}): {numerical_input_features}")

    # Step 3: Instantiate, Fit and Save Preprocessor
    print("\n[Step 3] Fitting Preprocessor (OneHotEncoder + Log1p + StandardScaler)...")
    preprocessor = FeaturePreprocessor(
        categorical_cols=CATEGORICAL_INPUT_FEATURES,
        numerical_cols=numerical_input_features,
        log1p_cols=LOG1P_SKEWED_FEATURES
    )
    
    # Fit and transform model input features
    df_transformed = preprocessor.fit_transform(df_raw)
    model_feature_names = preprocessor.feature_names_out_
    print(f" -> Total Transformed Model Input Features: {len(model_feature_names)}")

    # Save fitted preprocessor object for real-time inference compatibility
    os.makedirs(SAVED_MODEL_DIR, exist_ok=True)
    joblib.dump(preprocessor, PREPROCESSOR_PKL)
    print(f" -> Saved fitted preprocessor to: {PREPROCESSOR_PKL}")

    # Step 4: Assemble Final Output Dataset
    print("\n[Step 4] Assembling Encoded & Scaled Dataset...")
    df_identifiers = df_raw[IDENTIFIER_COLUMNS].copy()
    df_target_future = df_raw[EXCLUDED_TARGET_FUTURE_COLUMNS].copy()
    
    # Concatenate Identifiers + Target/Future Outcomes + Model Features
    df_final = pd.concat([df_identifiers, df_target_future, df_transformed], axis=1)
    
    os.makedirs(os.path.dirname(OUTPUT_SCALED_CSV), exist_ok=True)
    df_final.to_csv(OUTPUT_SCALED_CSV, index=False)
    print(f" -> Encoded & Scaled dataset saved to: {OUTPUT_SCALED_CSV}")

    # Step 5: Diagnostics & Summary Report
    print("\n[Step 5] Running Diagnostics and Generating Report...")
    diagnostics = run_diagnostics(df_final, model_feature_names)
    generate_summary_report(
        df_input=df_raw,
        df_output=df_final,
        cat_cols=CATEGORICAL_INPUT_FEATURES,
        num_cols=numerical_input_features,
        log1p_cols=LOG1P_SKEWED_FEATURES,
        model_feature_names=model_feature_names,
        diagnostics=diagnostics
    )

    # Step 6: Print Validation Output
    print("\n" + "=" * 80)
    print("PHASE 2.4 VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Execution Status            : SUCCESS")
    print(f"Input Dataset Shape         : {df_raw.shape}")
    print(f"Output Dataset Shape        : {df_final.shape}")
    print(f"Selected Categorical Features: {CATEGORICAL_INPUT_FEATURES} ({len(CATEGORICAL_INPUT_FEATURES)} cols)")
    print(f"Selected Numerical Features  : {len(numerical_input_features)} cols")
    print(f"Log1p Transformed Features   : {LOG1P_SKEWED_FEATURES}")
    print(f"Excluded Columns            : {EXCLUDED_TARGET_FUTURE_COLUMNS}")
    print(f"Final Model Feature Count   : {len(model_feature_names)}")
    print(f"Duplicate Key Count         : {diagnostics['duplicate_keys']}")
    print(f"Infinite Values Count       : {diagnostics['inf_count']}")
    print("Missing Value Summary:")
    missing_nan = diagnostics['missing_summary'][diagnostics['missing_summary'] > 0]
    print(missing_nan)
    print(f"Saved Preprocessor Path     : {PREPROCESSOR_PKL}")
    print(f"Output File Path            : {OUTPUT_SCALED_CSV}")
    print(f"Summary Report Path         : {SUMMARY_REPORT_TXT}")
    print("=" * 80)
    print("PHASE 2.4 PREPROCESSING COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
