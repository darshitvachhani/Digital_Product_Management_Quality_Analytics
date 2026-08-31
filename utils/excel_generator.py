import io
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# Master checkpoint column schema definitions
CHECKPOINT_SCHEMAS: Dict[str, Dict[str, any]] = {
    "Casting Temperature": {
        "columns": ["Batch_ID", "Part_Serial_No", "Timestamp", "Pouring_Temperature_C", "Tolerance_Min_C", "Tolerance_Max_C", "Status_Pass_Fail", "Inspector_ID"],
        "sample_rows": [
            {"Batch_ID": "BATCH-2026-A1", "Part_Serial_No": "ENG-COV-1001", "Timestamp": "2026-08-31 08:30:00", "Pouring_Temperature_C": 1395.5, "Tolerance_Min_C": 1380.0, "Tolerance_Max_C": 1420.0, "Status_Pass_Fail": "PASS", "Inspector_ID": "INSP-04"},
            {"Batch_ID": "BATCH-2026-A1", "Part_Serial_No": "ENG-COV-1002", "Timestamp": "2026-08-31 08:35:00", "Pouring_Temperature_C": 1402.0, "Tolerance_Min_C": 1380.0, "Tolerance_Max_C": 1420.0, "Status_Pass_Fail": "PASS", "Inspector_ID": "INSP-04"},
            {"Batch_ID": "BATCH-2026-A1", "Part_Serial_No": "ENG-COV-1003", "Timestamp": "2026-08-31 08:40:00", "Pouring_Temperature_C": 1428.0, "Tolerance_Min_C": 1380.0, "Tolerance_Max_C": 1420.0, "Status_Pass_Fail": "FAIL", "Inspector_ID": "INSP-04"},
        ]
    },
    "Visual Casting Inspection": {
        "columns": ["Batch_ID", "Part_Serial_No", "Timestamp", "Porosity_Defect_Count", "Parting_Line_Flush_mm", "Status_Pass_Fail", "Inspector_ID"],
        "sample_rows": [
            {"Batch_ID": "BATCH-2026-A1", "Part_Serial_No": "ENG-COV-1001", "Timestamp": "2026-08-31 09:00:00", "Porosity_Defect_Count": 0, "Parting_Line_Flush_mm": 0.22, "Status_Pass_Fail": "PASS", "Inspector_ID": "INSP-09"},
            {"Batch_ID": "BATCH-2026-A1", "Part_Serial_No": "ENG-COV-1002", "Timestamp": "2026-08-31 09:05:00", "Porosity_Defect_Count": 0, "Parting_Line_Flush_mm": 0.35, "Status_Pass_Fail": "PASS", "Inspector_ID": "INSP-09"},
            {"Batch_ID": "BATCH-2026-A1", "Part_Serial_No": "ENG-COV-1003", "Timestamp": "2026-08-31 09:10:00", "Porosity_Defect_Count": 3, "Parting_Line_Flush_mm": 0.78, "Status_Pass_Fail": "FAIL", "Inspector_ID": "INSP-09"},
        ]
    },
    "Fettling / Flash Removal": {
        "columns": ["Batch_ID", "Part_Serial_No", "Timestamp", "Parting_Line_Flush_mm", "Max_Flush_Allowed_mm", "Status_Pass_Fail", "Inspector_ID"],
        "sample_rows": [
            {"Batch_ID": "BATCH-2026-A1", "Part_Serial_No": "ENG-COV-1001", "Timestamp": "2026-08-31 09:30:00", "Parting_Line_Flush_mm": 0.25, "Max_Flush_Allowed_mm": 0.50, "Status_Pass_Fail": "PASS", "Inspector_ID": "INSP-12"},
            {"Batch_ID": "BATCH-2026-A1", "Part_Serial_No": "ENG-COV-1002", "Timestamp": "2026-08-31 09:35:00", "Parting_Line_Flush_mm": 0.30, "Max_Flush_Allowed_mm": 0.50, "Status_Pass_Fail": "PASS", "Inspector_ID": "INSP-12"},
        ]
    },
    "Machining Dimensions": {
        "columns": ["Batch_ID", "Part_Serial_No", "Timestamp", "Measured_Dimension_mm", "USL_mm", "LSL_mm", "Tolerance_Deviation_mm", "Status_Pass_Fail", "Inspector_ID"],
        "sample_rows": [
            {"Batch_ID": "BATCH-2026-M4", "Part_Serial_No": "DRM-201-088", "Timestamp": "2026-08-31 10:15:00", "Measured_Dimension_mm": 125.008, "USL_mm": 125.025, "LSL_mm": 124.975, "Tolerance_Deviation_mm": 0.008, "Status_Pass_Fail": "PASS", "Inspector_ID": "INSP-02"},
            {"Batch_ID": "BATCH-2026-M4", "Part_Serial_No": "DRM-201-089", "Timestamp": "2026-08-31 10:20:00", "Measured_Dimension_mm": 125.031, "USL_mm": 125.025, "LSL_mm": 124.975, "Tolerance_Deviation_mm": 0.031, "Status_Pass_Fail": "FAIL", "Inspector_ID": "INSP-02"},
        ]
    },
    "Surface Finish": {
        "columns": ["Batch_ID", "Part_Serial_No", "Timestamp", "Surface_Roughness_Ra_um", "Max_Allowed_Ra_um", "Status_Pass_Fail", "Inspector_ID"],
        "sample_rows": [
            {"Batch_ID": "BATCH-2026-M4", "Part_Serial_No": "DRM-201-088", "Timestamp": "2026-08-31 10:45:00", "Surface_Roughness_Ra_um": 1.15, "Max_Allowed_Ra_um": 1.60, "Status_Pass_Fail": "PASS", "Inspector_ID": "INSP-02"},
            {"Batch_ID": "BATCH-2026-M4", "Part_Serial_No": "DRM-201-089", "Timestamp": "2026-08-31 10:50:00", "Surface_Roughness_Ra_um": 1.85, "Max_Allowed_Ra_um": 1.60, "Status_Pass_Fail": "FAIL", "Inspector_ID": "INSP-02"},
        ]
    },
    "Leak Test": {
        "columns": ["Batch_ID", "Part_Serial_No", "Timestamp", "Test_Pressure_bar", "Pressure_Drop_bar_per_min", "Max_Allowable_Drop", "Status_Pass_Fail", "Inspector_ID"],
        "sample_rows": [
            {"Batch_ID": "BATCH-2026-L1", "Part_Serial_No": "ENG-COV-1001", "Timestamp": "2026-08-31 14:00:00", "Test_Pressure_bar": 2.50, "Pressure_Drop_bar_per_min": 0.003, "Max_Allowable_Drop": 0.010, "Status_Pass_Fail": "PASS", "Inspector_ID": "INSP-07"},
            {"Batch_ID": "BATCH-2026-L1", "Part_Serial_No": "ENG-COV-1002", "Timestamp": "2026-08-31 14:05:00", "Test_Pressure_bar": 2.50, "Pressure_Drop_bar_per_min": 0.018, "Max_Allowable_Drop": 0.010, "Status_Pass_Fail": "FAIL", "Inspector_ID": "INSP-07"},
        ]
    }
}

DEFAULT_COLUMNS = ["Batch_ID", "Part_Serial_No", "Timestamp", "Measured_Value", "Lower_Spec_Limit", "Upper_Spec_Limit", "Status_Pass_Fail", "Inspector_Notes"]

def get_required_columns_for_checkpoint(checkpoint_name: str) -> List[str]:
    """Retrieves required column headers for any given checkpoint."""
    for key, spec in CHECKPOINT_SCHEMAS.items():
        if key.lower() in checkpoint_name.lower() or checkpoint_name.lower() in key.lower():
            return spec["columns"]
    return DEFAULT_COLUMNS

def generate_checkpoint_template_excel(checkpoint_name: str) -> bytes:
    """
    Generates a downloadable sample reference Excel template (.xlsx)
    with required column headers and sample rows.
    """
    cols = get_required_columns_for_checkpoint(checkpoint_name)
    
    # Check for custom sample rows
    sample_data = None
    for key, spec in CHECKPOINT_SCHEMAS.items():
        if key.lower() in checkpoint_name.lower() or checkpoint_name.lower() in key.lower():
            sample_data = spec["sample_rows"]
            break
            
    if not sample_data:
        sample_data = [
            {"Batch_ID": "BATCH-2026-DEMO", "Part_Serial_No": "SN-1001", "Timestamp": "2026-08-31 10:00:00", "Measured_Value": 45.2, "Lower_Spec_Limit": 44.0, "Upper_Spec_Limit": 46.0, "Status_Pass_Fail": "PASS", "Inspector_Notes": "Within spec"},
            {"Batch_ID": "BATCH-2026-DEMO", "Part_Serial_No": "SN-1002", "Timestamp": "2026-08-31 10:05:00", "Measured_Value": 46.5, "Lower_Spec_Limit": 44.0, "Upper_Spec_Limit": 46.0, "Status_Pass_Fail": "FAIL", "Inspector_Notes": "Exceeds upper limit"},
        ]
        
    df = pd.DataFrame(sample_data, columns=cols)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=checkpoint_name[:30])
    buffer.seek(0)
    return buffer.getvalue()

def validate_excel_columns(uploaded_file, checkpoint_name: str) -> Tuple[bool, List[str], List[str]]:
    """
    Strictly validates that the uploaded Excel file contains all required columns.
    Returns (is_valid, missing_columns, found_columns).
    """
    required_cols = get_required_columns_for_checkpoint(checkpoint_name)
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, nrows=2)
        else:
            df = pd.read_excel(uploaded_file, nrows=2)
        
        found_cols = [str(c).strip() for c in df.columns]
        
        # Case-insensitive column matching
        found_cols_lower = [c.lower() for c in found_cols]
        missing = []
        for req in required_cols:
            if req.lower() not in found_cols_lower:
                missing.append(req)
                
        is_valid = len(missing) == 0
        return is_valid, missing, found_cols
    except Exception as e:
        return False, [f"Corrupted or invalid spreadsheet: {str(e)}"], []
