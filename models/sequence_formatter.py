import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================
BASE_DIR = r"d:\dl project"
TARGET_DATASET_CSV = os.path.join(BASE_DIR, "dataset", "processed", "target_dataset.csv")
STUDENT_VLE_CSV = os.path.join(BASE_DIR, "extracted_data", "studentVle.csv")

SEQUENCES_DIR = os.path.join(BASE_DIR, "dataset", "processed", "sequences")
REPORTS_DIR = os.path.join(BASE_DIR, "outputs", "reports")
SUMMARY_REPORT_TXT = os.path.join(REPORTS_DIR, "sequence_preparation_summary.txt")
METADATA_JSON = os.path.join(SEQUENCES_DIR, "sequence_metadata.json")

# Excluded columns that must NEVER enter model input features (X_seq or X_static)
EXCLUDED_LEAKAGE_COLUMNS = [
    "final_result",
    "date_unregistration",
    "withdrawn_flag",
    "active_duration",
    "engagement_score",
    "engagement_level",
    "engagement_class"
]

IDENTIFIER_COLUMNS = [
    "code_module",
    "code_presentation",
    "id_student"
]

# Random seed for reproducibility
RANDOM_SEED = 42
MAX_TIMESTEPS = 40  # Week 0 (pre-course) + Weeks 1 to 39


def load_target_dataset() -> pd.DataFrame:
    """
    Loads target_dataset.csv and validates essential columns.
    """
    print(f"\n[Step 1] Loading target dataset from: {TARGET_DATASET_CSV}")
    if not os.path.exists(TARGET_DATASET_CSV):
        raise FileNotFoundError(f"Target dataset file not found at {TARGET_DATASET_CSV}")

    df_target = pd.read_csv(TARGET_DATASET_CSV)
    print(f" -> Loaded target dataset shape: {df_target.shape}")
    
    # Check for missing values in target
    missing_target = df_target["engagement_class"].isnull().sum()
    if missing_target > 0:
        raise ValueError(f"Found {missing_target} missing target labels in engagement_class!")
        
    # Check duplicate student-module keys
    dup_keys = df_target.duplicated(subset=IDENTIFIER_COLUMNS).sum()
    if dup_keys > 0:
        raise ValueError(f"Found {dup_keys} duplicate student-module keys!")
        
    print(f" -> Engagement Class Distribution:\n{df_target['engagement_class'].value_counts().sort_index()}")
    return df_target


def split_students(df_target: pd.DataFrame):
    """
    Splits dataset at UNIQUE STUDENT ID level to prevent data leakage.
    Ratios: 70% Train, 15% Validation, 15% Testing.
    Returns df_train, df_val, df_test, index arrays, and unique student DataFrames.
    """
    print("\n[Step 2] Performing Student-Level Data Splitting (70% Train, 15% Val, 15% Test)...")
    unique_student_ids = df_target["id_student"].unique()
    total_unique_students = len(unique_student_ids)
    print(f" -> Total Unique Students: {total_unique_students:,}")

    # First split: 70% train, 30% temp
    train_ids, temp_ids = train_test_split(
        unique_student_ids,
        test_size=0.30,
        random_state=RANDOM_SEED
    )
    
    # Second split: split temp 50/50 -> 15% val, 15% test
    val_ids, test_ids = train_test_split(
        temp_ids,
        test_size=0.50,
        random_state=RANDOM_SEED
    )

    train_set, val_set, test_set = set(train_ids), set(val_ids), set(test_ids)

    # Validate zero student overlap
    overlap_tr_val = len(train_set.intersection(val_set))
    overlap_tr_te = len(train_set.intersection(test_set))
    overlap_val_te = len(val_set.intersection(test_set))

    if overlap_tr_val > 0 or overlap_tr_te > 0 or overlap_val_te > 0:
        raise RuntimeError("CRITICAL ERROR: Student overlap detected between train/val/test splits!")

    print(" -> Student overlap check passed successfully (0 student overlap).")

    # Map student splits back to full dataset records using original DataFrame index masks
    train_mask = df_target["id_student"].isin(train_set)
    val_mask = df_target["id_student"].isin(val_set)
    test_mask = df_target["id_student"].isin(test_set)

    df_train = df_target[train_mask].copy()
    df_val = df_target[val_mask].copy()
    df_test = df_target[test_mask].copy()

    train_indices = df_target.index[train_mask].values
    val_indices = df_target.index[val_mask].values
    test_indices = df_target.index[test_mask].values

    print(f" -> Train Samples: {len(df_train):,} ({len(df_train)/len(df_target)*100:.2f}%) | Unique Students: {len(train_ids):,}")
    print(f" -> Val Samples  : {len(df_val):,} ({len(df_val)/len(df_target)*100:.2f}%) | Unique Students: {len(val_ids):,}")
    print(f" -> Test Samples : {len(df_test):,} ({len(df_test)/len(df_target)*100:.2f}%) | Unique Students: {len(test_ids):,}")

    df_train_studs = pd.DataFrame({"id_student": train_ids})
    df_val_studs = pd.DataFrame({"id_student": val_ids})
    df_test_studs = pd.DataFrame({"id_student": test_ids})

    return df_train, df_val, df_test, train_indices, val_indices, test_indices, df_train_studs, df_val_studs, df_test_studs


def create_temporal_sequences(df_target: pd.DataFrame) -> np.ndarray:
    """
    Constructs weekly temporal sequences from raw studentVle.csv log activity.
    Sequence features per week t in [0..39]:
      1. weekly_clicks (log1p transformed)
      2. active_days_in_week
      3. interaction_frequency
      4. inactivity_indicator
    Shape: (N_samples, 40, 4)
    """
    print("\n[Step 3] Constructing Weekly Temporal Sequences from studentVle.csv...")
    if not os.path.exists(STUDENT_VLE_CSV):
        raise FileNotFoundError(f"studentVle log file not found at {STUDENT_VLE_CSV}")

    # Read studentVle.csv efficiently
    df_vle = pd.read_csv(STUDENT_VLE_CSV, usecols=["code_module", "code_presentation", "id_student", "date", "sum_click"])
    
    # Calculate week index:
    # date < 0 -> Week 0 (precourse)
    # date >= 0 -> Week 1 + date // 7 (clip max week at MAX_TIMESTEPS - 1)
    week_idx = np.where(df_vle["date"] < 0, 0, 1 + (df_vle["date"] // 7))
    df_vle["week"] = np.minimum(MAX_TIMESTEPS - 1, week_idx)

    # Aggregate weekly metrics per student-module-presentation
    vle_weekly = df_vle.groupby(["code_module", "code_presentation", "id_student", "week"]).agg(
        weekly_clicks=("sum_click", "sum"),
        active_days_in_week=("date", "nunique")
    ).reset_index()

    vle_weekly["interaction_frequency"] = np.where(
        vle_weekly["active_days_in_week"] > 0,
        vle_weekly["weekly_clicks"] / vle_weekly["active_days_in_week"],
        0.0
    )
    vle_weekly["inactivity_indicator"] = (vle_weekly["weekly_clicks"] == 0).astype(float)
    vle_weekly["weekly_clicks_log"] = np.log1p(vle_weekly["weekly_clicks"])

    # Create key mapping dictionary for fast array populating
    vle_dict = {}
    for row in vle_weekly.itertuples(index=False):
        key = (row.code_module, row.code_presentation, int(row.id_student), int(row.week))
        vle_dict[key] = (row.weekly_clicks_log, float(row.active_days_in_week), row.interaction_frequency, row.inactivity_indicator)

    num_samples = len(df_target)
    num_features = 4  # weekly_clicks_log, active_days, interaction_frequency, inactivity_indicator
    X_seq = np.zeros((num_samples, MAX_TIMESTEPS, num_features), dtype=np.float32)

    # Default inactivity indicator to 1.0 for timesteps with zero activity
    X_seq[:, :, 3] = 1.0

    print(" -> Populating 3D temporal sequence tensor...")
    for i, row in enumerate(df_target.itertuples(index=False)):
        mod = row.code_module
        pres = row.code_presentation
        stud = int(row.id_student)
        
        for w in range(MAX_TIMESTEPS):
            key = (mod, pres, stud, w)
            if key in vle_dict:
                c_log, act_days, freq, inact = vle_dict[key]
                X_seq[i, w, 0] = c_log
                X_seq[i, w, 1] = act_days
                X_seq[i, w, 2] = freq
                X_seq[i, w, 3] = 0.0  # active in week

    print(f" -> Temporal sequence tensor created with shape: {X_seq.shape}")
    return X_seq


def scale_sequence_features(X_train_seq: np.ndarray, X_val_seq: np.ndarray, X_test_seq: np.ndarray):
    """
    Standardizes sequence continuous features (features 0, 1, 2) across timesteps
    using a scaler fitted ONLY on training sequence data to prevent leakage.
    Feature 3 (inactivity_indicator) remains binary (0/1).
    """
    print("\n[Step 4] Standardizing Sequence Continuous Features using Train Data Statistics...")
    N_tr, T, F = X_train_seq.shape
    N_va, _, _ = X_val_seq.shape
    N_te, _, _ = X_test_seq.shape

    scaler = StandardScaler()
    
    train_cont = X_train_seq[:, :, :3].reshape(-1, 3)
    val_cont = X_val_seq[:, :, :3].reshape(-1, 3)
    test_cont = X_test_seq[:, :, :3].reshape(-1, 3)

    scaler.fit(train_cont)

    train_scaled = scaler.transform(train_cont).reshape(N_tr, T, 3)
    val_scaled = scaler.transform(val_cont).reshape(N_va, T, 3)
    test_scaled = scaler.transform(test_cont).reshape(N_te, T, 3)

    X_train_seq_scaled = X_train_seq.copy()
    X_val_seq_scaled = X_val_seq.copy()
    X_test_seq_scaled = X_test_seq.copy()

    X_train_seq_scaled[:, :, :3] = train_scaled
    X_val_seq_scaled[:, :, :3] = val_scaled
    X_test_seq_scaled[:, :, :3] = test_scaled

    print(" -> Sequence continuous features standardized successfully.")
    return X_train_seq_scaled, X_val_seq_scaled, X_test_seq_scaled


def create_static_features(df_target: pd.DataFrame) -> tuple:
    """
    Extracts the 70 preprocessed baseline static features from target_dataset.csv.
    Strictly excludes identifier columns, target columns, and future outcome columns.
    Returns static feature matrix X_static and static feature names list.
    """
    print("\n[Step 5] Extracting Static Feature Matrix X_static...")
    exclude_cols = IDENTIFIER_COLUMNS + EXCLUDED_LEAKAGE_COLUMNS
    static_feature_names = [c for c in df_target.columns if c not in exclude_cols]

    print(f" -> Number of static input features: {len(static_feature_names)}")
    X_static = df_target[static_feature_names].values.astype(np.float32)

    return X_static, static_feature_names


def validate_data_leakage(static_feature_names: list, seq_feature_names: list):
    """
    Explicitly checks that no target, future outcome, or identifier column
    leakage exists inside static or sequential model features.
    """
    print("\n[Step 6] Running Strict Data Leakage Audit...")
    all_model_features = static_feature_names + seq_feature_names
    leakage_found = [c for c in EXCLUDED_LEAKAGE_COLUMNS if c in all_model_features]

    if leakage_found:
        raise RuntimeError(f"CRITICAL DATA LEAKAGE DETECTED: Features {leakage_found} found in model inputs!")

    print(" -> Leakage audit PASSED: Zero forbidden features present in X_seq or X_static.")


def save_datasets(
    X_train_seq: np.ndarray, X_val_seq: np.ndarray, X_test_seq: np.ndarray,
    X_train_static: np.ndarray, X_val_static: np.ndarray, X_test_static: np.ndarray,
    y_train: np.ndarray, y_val: np.ndarray, y_test: np.ndarray,
    df_train_studs: pd.DataFrame, df_val_studs: pd.DataFrame, df_test_studs: pd.DataFrame,
    seq_feature_names: list, static_feature_names: list
):
    """
    Saves generated sequence tensors, static matrices, target arrays, unique student splits,
    and metadata configuration to disk.
    """
    print("\n[Step 7] Saving Arrays and Metadata to Disk...")
    os.makedirs(SEQUENCES_DIR, exist_ok=True)

    np.save(os.path.join(SEQUENCES_DIR, "X_train_seq.npy"), X_train_seq)
    np.save(os.path.join(SEQUENCES_DIR, "X_val_seq.npy"), X_val_seq)
    np.save(os.path.join(SEQUENCES_DIR, "X_test_seq.npy"), X_test_seq)

    np.save(os.path.join(SEQUENCES_DIR, "X_train_static.npy"), X_train_static)
    np.save(os.path.join(SEQUENCES_DIR, "X_val_static.npy"), X_val_static)
    np.save(os.path.join(SEQUENCES_DIR, "X_test_static.npy"), X_test_static)

    np.save(os.path.join(SEQUENCES_DIR, "y_train.npy"), y_train)
    np.save(os.path.join(SEQUENCES_DIR, "y_val.npy"), y_val)
    np.save(os.path.join(SEQUENCES_DIR, "y_test.npy"), y_test)

    df_train_studs.to_csv(os.path.join(SEQUENCES_DIR, "train_students.csv"), index=False)
    df_val_studs.to_csv(os.path.join(SEQUENCES_DIR, "val_students.csv"), index=False)
    df_test_studs.to_csv(os.path.join(SEQUENCES_DIR, "test_students.csv"), index=False)

    metadata = {
        "random_seed": RANDOM_SEED,
        "max_timesteps": MAX_TIMESTEPS,
        "train_split_pct": 70,
        "val_split_pct": 15,
        "test_split_pct": 15,
        "seq_feature_names": seq_feature_names,
        "static_feature_names": static_feature_names,
        "shapes": {
            "X_train_seq": list(X_train_seq.shape),
            "X_val_seq": list(X_val_seq.shape),
            "X_test_seq": list(X_test_seq.shape),
            "X_train_static": list(X_train_static.shape),
            "X_val_static": list(X_val_static.shape),
            "X_test_static": list(X_test_static.shape),
            "y_train": list(y_train.shape),
            "y_val": list(y_val.shape),
            "y_test": list(y_test.shape)
        }
    }
    with open(METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    print(f" -> Arrays and metadata successfully saved in: {SEQUENCES_DIR}")


def generate_summary_report(
    total_samples: int,
    total_students: int,
    df_train: pd.DataFrame,
    df_val: pd.DataFrame,
    df_test: pd.DataFrame,
    X_train_seq: np.ndarray,
    X_val_seq: np.ndarray,
    X_test_seq: np.ndarray,
    X_train_static: np.ndarray,
    seq_feature_names: list,
    static_feature_names: list,
    nan_count: int,
    inf_count: int
):
    """
    Generates sequence_preparation_summary.txt report.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)

    report = []
    report.append("=" * 80)
    report.append("PHASE 4: STUDENT-LEVEL DATA SPLITTING & SEQUENCE PREPARATION SUMMARY REPORT")
    report.append("=" * 80)
    report.append(f"\nTotal Dataset Samples (Rows)   : {total_samples:,}")
    report.append(f"Total Unique Students          : {total_students:,}")

    report.append("\n" + "-" * 80)
    report.append("1. STUDENT-LEVEL DATA SPLITTING STATISTICS (Random Seed: 42)")
    report.append("-" * 80)
    report.append(f"  - Training Set   : {len(df_train):,} samples ({len(df_train)/total_samples*100:.2f}%) | {df_train['id_student'].nunique():,} unique students")
    report.append(f"  - Validation Set : {len(df_val):,} samples ({len(df_val)/total_samples*100:.2f}%) | {df_val['id_student'].nunique():,} unique students")
    report.append(f"  - Testing Set    : {len(df_test):,} samples ({len(df_test)/total_samples*100:.2f}%) | {df_test['id_student'].nunique():,} unique students")
    
    report.append("\n  Student Overlap Audit:")
    report.append("    - Train-Val Overlap  : 0 students")
    report.append("    - Train-Test Overlap : 0 students")
    report.append("    - Val-Test Overlap   : 0 students")

    report.append("\n" + "-" * 80)
    report.append("2. TARGET CLASS DISTRIBUTION PER SPLIT")
    report.append("-" * 80)
    for s_name, df_s in [("Training", df_train), ("Validation", df_val), ("Testing", df_test)]:
        report.append(f"\n  {s_name} Split Class Distribution:")
        counts = df_s["engagement_class"].value_counts().sort_index()
        pcts = (counts / len(df_s)) * 100
        for c_id in [0, 1, 2]:
            report.append(f"    - Class {c_id}: {counts[c_id]:,} ({pcts[c_id]:.2f}%)")

    report.append("\n" + "-" * 80)
    report.append("3. TENSOR SHAPES & FEATURE DIMENSIONS")
    report.append("-" * 80)
    report.append(f"  - Sequence Tensors Shape (X_seq)  : Train={X_train_seq.shape}, Val={X_val_seq.shape}, Test={X_test_seq.shape}")
    report.append(f"  - Static Matrices Shape (X_static): Train={X_train_static.shape}, Val={df_val.shape[0], X_train_static.shape[1]}, Test={df_test.shape[0], X_train_static.shape[1]}")
    report.append(f"  - Timesteps Count (MAX_TIMESTEPS) : {MAX_TIMESTEPS} (Week 0 to Week 39)")
    report.append(f"  - Sequence Feature Count          : {len(seq_feature_names)}")
    report.append(f"  - Static Feature Count            : {len(static_feature_names)}")

    report.append("\n" + "-" * 80)
    report.append("4. SEQUENCE FEATURES LIST")
    report.append("-" * 80)
    for idx, f in enumerate(seq_feature_names, 1):
        report.append(f"  {idx:02d}. {f}")

    report.append("\n" + "-" * 80)
    report.append("5. DATA INTEGRITY & LEAKAGE AUDIT")
    report.append("-" * 80)
    report.append(f"  - NaN Values Count across Inputs     : {nan_count}")
    report.append(f"  - Infinite Values Count across Inputs: {inf_count}")
    report.append("  - Data Leakage Rule Verification    : PASSED")
    report.append(f"    Forbidden columns {EXCLUDED_LEAKAGE_COLUMNS} strictly excluded from model inputs.")

    report.append("\n" + "=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    report_content = "\n".join(report)
    with open(SUMMARY_REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f" -> Sequence preparation summary report generated at: {SUMMARY_REPORT_TXT}")


def main():
    print("=" * 80)
    print("PHASE 4: STUDENT-LEVEL DATA SPLITTING & SEQUENCE PREPARATION")
    print("=" * 80)

    # 1. Load target dataset
    df_target = load_target_dataset()

    # 2. Split students
    df_train, df_val, df_test, train_indices, val_indices, test_indices, df_tr_s, df_va_s, df_te_s = split_students(df_target)

    # 3. Create temporal sequences for entire dataset
    X_seq_full = create_temporal_sequences(df_target)
    seq_feature_names = ["weekly_clicks_log", "active_days_in_week", "interaction_frequency", "inactivity_indicator"]

    # Slice sequences into train / val / test matching original student index masks
    X_train_seq_raw = X_seq_full[train_indices]
    X_val_seq_raw = X_seq_full[val_indices]
    X_test_seq_raw = X_seq_full[test_indices]

    # Standardize continuous sequence features using train statistics
    X_train_seq, X_val_seq, X_test_seq = scale_sequence_features(X_train_seq_raw, X_val_seq_raw, X_test_seq_raw)

    # 4. Create static feature matrices
    X_static_full, static_feature_names = create_static_features(df_target)
    X_train_static = X_static_full[train_indices]
    X_val_static = X_static_full[val_indices]
    X_test_static = X_static_full[test_indices]

    # 5. Extract targets
    y_train = df_train["engagement_class"].values.astype(np.int64)
    y_val = df_val["engagement_class"].values.astype(np.int64)
    y_test = df_test["engagement_class"].values.astype(np.int64)

    # 6. Validate Data Leakage
    validate_data_leakage(static_feature_names, seq_feature_names)

    # 7. Check NaN and Inf counts
    nan_count = np.isnan(X_train_seq).sum() + np.isnan(X_val_seq).sum() + np.isnan(X_test_seq).sum() + \
                np.isnan(X_train_static).sum() + np.isnan(X_val_static).sum() + np.isnan(X_test_static).sum()

    inf_count = np.isinf(X_train_seq).sum() + np.isinf(X_val_seq).sum() + np.isinf(X_test_seq).sum() + \
                np.isinf(X_train_static).sum() + np.isinf(X_val_static).sum() + np.isinf(X_test_static).sum()

    print(f"\n[Validation] Total NaN count across model inputs: {nan_count}")
    print(f"[Validation] Total Infinite count across model inputs: {inf_count}")

    # 8. Save datasets & metadata
    save_datasets(
        X_train_seq, X_val_seq, X_test_seq,
        X_train_static, X_val_static, X_test_static,
        y_train, y_val, y_test,
        df_tr_s, df_va_s, df_te_s,
        seq_feature_names, static_feature_names
    )

    # 9. Generate summary report
    generate_summary_report(
        total_samples=len(df_target),
        total_students=df_target["id_student"].nunique(),
        df_train=df_train,
        df_val=df_val,
        df_test=df_test,
        X_train_seq=X_train_seq,
        X_val_seq=X_val_seq,
        X_test_seq=X_test_seq,
        X_train_static=X_train_static,
        seq_feature_names=seq_feature_names,
        static_feature_names=static_feature_names,
        nan_count=nan_count,
        inf_count=inf_count
    )

    # 10. Print Final Validation Message
    print("\n" + "=" * 50)
    print("PHASE 4 COMPLETION SUMMARY")
    print("=" * 50)
    print("Phase 4 Status: SUCCESS\n")
    print(f"Training samples: {len(df_train):,}")
    print(f"Validation samples: {len(df_val):,}")
    print(f"Testing samples: {len(df_test):,}\n")
    print(f"Unique training students: {df_train['id_student'].nunique():,}")
    print(f"Unique validation students: {df_val['id_student'].nunique():,}")
    print(f"Unique testing students: {df_test['id_student'].nunique():,}\n")
    print(f"X_train_seq shape: {X_train_seq.shape}")
    print(f"X_val_seq shape: {X_val_seq.shape}")
    print(f"X_test_seq shape: {X_test_seq.shape}\n")
    print(f"X_train_static shape: {X_train_static.shape}")
    print(f"X_val_static shape: {X_val_static.shape}")
    print(f"X_test_static shape: {X_test_static.shape}\n")
    print(f"y_train shape: {y_train.shape}")
    print(f"y_val shape: {y_val.shape}")
    print(f"y_test shape: {y_test.shape}\n")
    print("Student overlap:")
    print("Train-Val: 0")
    print("Train-Test: 0")
    print("Val-Test: 0\n")
    print(f"NaN values: {nan_count}")
    print(f"Infinite values: {inf_count}\n")
    print("Data leakage check:")
    print("PASSED\n")
    print("Saved files:")
    print(" - sequence_formatter.py")
    print(" - X_train_seq.npy")
    print(" - X_val_seq.npy")
    print(" - X_test_seq.npy")
    print(" - X_train_static.npy")
    print(" - X_val_static.npy")
    print(" - X_test_static.npy")
    print(" - y_train.npy")
    print(" - y_val.npy")
    print(" - y_test.npy")
    print(" - train_students.csv")
    print(" - val_students.csv")
    print(" - test_students.csv")
    print(" - sequence_preparation_summary.txt")
    print("=" * 50)


if __name__ == "__main__":
    main()
