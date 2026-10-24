import os
import pandas as pd

# Define data directory path
DATA_DIR = r"d:\dl project\extracted_data"

# List of files to inspect for Phase 1
files_to_load = {
    "studentInfo": "studentInfo.csv",
    "studentVle": "studentVle.csv",
    "studentAssessment": "studentAssessment.csv",
    "studentRegistration": "studentRegistration.csv"
}

def inspect_dataset(file_key, filename):
    file_path = os.path.join(DATA_DIR, filename)
    print("=" * 80)
    print(f"LOADING AND INSPECTING: {filename}")
    print("=" * 80)
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return
    
    # Load dataset
    df = pd.read_csv(file_path)
    
    # 1. Dataset Shape
    print(f"\n1. Dataset Shape (Rows, Columns):\n{df.shape}")
    
    # 2. Column Names
    print(f"\n2. Column Names:\n{list(df.columns)}")
    
    # 3. Data Types
    print(f"\n3. Data Types:\n{df.dtypes}")
    
    # 4. Missing Values
    print(f"\n4. Missing Values per Column:\n{df.isnull().sum()}")
    
    # 5. Duplicate Rows
    print(f"\n5. Total Duplicate Rows:\n{df.duplicated().sum()}")
    
    # 6. First 5 Rows
    print(f"\n6. First 5 Rows:\n{df.head()}")
    print("\n" + "-" * 80 + "\n")

if __name__ == "__main__":
    for key, name in files_to_load.items():
        inspect_dataset(key, name)
