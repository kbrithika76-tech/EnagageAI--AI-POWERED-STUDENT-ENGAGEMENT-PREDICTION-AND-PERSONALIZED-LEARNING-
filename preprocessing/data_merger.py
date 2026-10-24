import os
import pandas as pd
import numpy as np

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================
BASE_DIR = r"d:\dl project"
RAW_DATA_DIR = os.path.join(BASE_DIR, "extracted_data")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "dataset", "processed")

# Ensure output directory exists
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# Input raw file paths
student_info_path = os.path.join(RAW_DATA_DIR, "studentInfo.csv")
student_reg_path = os.path.join(RAW_DATA_DIR, "studentRegistration.csv")
student_vle_path = os.path.join(RAW_DATA_DIR, "studentVle.csv")
student_assess_path = os.path.join(RAW_DATA_DIR, "studentAssessment.csv")
assessments_path = os.path.join(RAW_DATA_DIR, "assessments.csv")
master_output_path = os.path.join(PROCESSED_DATA_DIR, "master_dataset.csv")


def main():
    print("=" * 80)
    print("PHASE 2.1: DATA MERGING PIPELINE FOR OULAD DATASET")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # STEP 1: LOAD RAW CSV FILES
    # --------------------------------------------------------------------------
    print("\n[Step 1] Loading Raw CSV Files...")
    df_info = pd.read_csv(student_info_path)
    df_reg = pd.read_csv(student_reg_path)
    df_vle = pd.read_csv(student_vle_path)
    df_assess = pd.read_csv(student_assess_path)
    df_assess_meta = pd.read_csv(assessments_path)

    print(f" -> studentInfo shape: {df_info.shape}")
    print(f" -> studentRegistration shape: {df_reg.shape}")
    print(f" -> studentVle shape: {df_vle.shape}")
    print(f" -> studentAssessment shape: {df_assess.shape}")
    print(f" -> assessments metadata shape: {df_assess_meta.shape}")

    # --------------------------------------------------------------------------
    # STEP 2: MERGE STUDENT INFO AND STUDENT REGISTRATION (STATIC BASE)
    # --------------------------------------------------------------------------
    print("\n[Step 2] Merging studentInfo with studentRegistration...")
    # Explanation:
    # studentInfo contains student demographics while studentRegistration contains
    # registration/unregistration dates. Both are student-level static datasets for
    # a specific module presentation. Joined on (code_module, code_presentation, id_student).
    
    df_static = pd.merge(
        df_info,
        df_reg,
        on=["code_module", "code_presentation", "id_student"],
        how="left"
    )
    print(f" -> Merged Static Profile Shape: {df_static.shape}")

    # --------------------------------------------------------------------------
    # STEP 3: PRE-AGGREGATE STUDENT VLE (10M+ ROWS -> STUDENT-MODULE SUMMARY)
    # --------------------------------------------------------------------------
    print("\n[Step 3] Aggregating studentVle interaction logs...")
    # Explanation:
    # studentVle has 10.6M+ raw click records across different days and site resources.
    # To build a master student-level dataset, we pre-aggregate VLE metrics per student
    # for each module presentation (total clicks, active interaction days, pre-course clicks).
    
    vle_agg = df_vle.groupby(["code_module", "code_presentation", "id_student"]).agg(
        total_vle_clicks=("sum_click", "sum"),
        active_vle_days=("date", "nunique"),
        precourse_vle_clicks=("sum_click", lambda x: x[df_vle.loc[x.index, "date"] < 0].sum()),
        first_interaction_day=("date", "min"),
        last_interaction_day=("date", "max")
    ).reset_index()

    print(f" -> Aggregated VLE Summary Shape: {vle_agg.shape}")

    # --------------------------------------------------------------------------
    # STEP 4: PRE-AGGREGATE STUDENT ASSESSMENT (STUDENT-MODULE SUMMARY)
    # --------------------------------------------------------------------------
    print("\n[Step 4] Aggregating studentAssessment marks and timeliness...")
    # Explanation:
    # studentAssessment links to assessments metadata to compute assessment metrics per student
    # (average score, total submitted assessments, late submission count).
    
    # Merge studentAssessment with assessments metadata to get module context and due dates
    df_assess_merged = pd.merge(
        df_assess,
        df_assess_meta,
        on="id_assessment",
        how="left"
    )

    # Compute submission delay relative to deadline (date_submitted - date)
    df_assess_merged["submission_delay"] = df_assess_merged["date_submitted"] - df_assess_merged["date"]
    df_assess_merged["is_late"] = (df_assess_merged["submission_delay"] > 0).astype(int)

    assess_agg = df_assess_merged.groupby(["code_module", "code_presentation", "id_student"]).agg(
        assessments_submitted=("id_assessment", "count"),
        mean_score=("score", "mean"),
        min_score=("score", "min"),
        max_score=("score", "max"),
        late_submissions=("is_late", "sum"),
        banked_assessments=("is_banked", "sum")
    ).reset_index()

    print(f" -> Aggregated Assessment Summary Shape: {assess_agg.shape}")

    # --------------------------------------------------------------------------
    # STEP 5: MERGE STATIC BASE WITH AGGREGATED VLE DATA
    # --------------------------------------------------------------------------
    print("\n[Step 5] Merging Static Base with Aggregated VLE Summary...")
    df_master_vle = pd.merge(
        df_static,
        vle_agg,
        on=["code_module", "code_presentation", "id_student"],
        how="left"
    )
    print(f" -> Master + VLE Shape: {df_master_vle.shape}")

    # --------------------------------------------------------------------------
    # STEP 6: MERGE MASTER DATASET WITH AGGREGATED ASSESSMENT DATA
    # --------------------------------------------------------------------------
    print("\n[Step 6] Merging Master Dataset with Aggregated Assessment Summary...")
    df_master_final = pd.merge(
        df_master_vle,
        assess_agg,
        on=["code_module", "code_presentation", "id_student"],
        how="left"
    )
    print(f" -> Final Master Dataset Shape: {df_master_final.shape}")

    # --------------------------------------------------------------------------
    # STEP 7: VALIDATION OF THE FINAL MASTER DATASET
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("VALIDATION OF THE FINAL MASTER DATASET")
    print("=" * 80)
    
    print(f"\n1. Final Dataset Shape (Rows, Columns):\n{df_master_final.shape}")
    
    print("\n2. Columns & Data Types:")
    print(df_master_final.dtypes)
    
    print("\n3. Missing Values Summary:")
    print(df_master_final.isnull().sum())
    
    print("\n4. Total Duplicate Rows (on Student-Module key):")
    duplicates = df_master_final.duplicated(subset=["code_module", "code_presentation", "id_student"]).sum()
    print(f" -> Total Duplicate Keys: {duplicates}")

    print("\n5. First 5 Rows Preview:")
    print(df_master_final.head())

    # --------------------------------------------------------------------------
    # STEP 8: SAVE FINAL MASTER DATASET
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"SAVING MASTER DATASET TO: {master_output_path}")
    print("=" * 80)
    df_master_final.to_csv(master_output_path, index=False)
    print(" -> File successfully saved!")


if __name__ == "__main__":
    main()
