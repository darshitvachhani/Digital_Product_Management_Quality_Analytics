import sqlite3
import json
from db.connection import get_db_connection

CREATE_TABLES_SQL = """
-- 1. Products Table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) UNIQUE NOT NULL,
    manufacturing_line VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Processes Table
CREATE TABLE IF NOT EXISTS processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    sequence INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) DEFAULT 'Active' CHECK(status IN ('Active', 'Complete', 'Incomplete', 'Inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

-- 3. Process Steps Table
CREATE TABLE IF NOT EXISTS process_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id INTEGER NOT NULL,
    sequence INTEGER NOT NULL DEFAULT 1,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (process_id) REFERENCES processes (id) ON DELETE CASCADE
);

-- 4. Checkpoints Table
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id INTEGER NOT NULL,
    sequence INTEGER NOT NULL DEFAULT 1,
    name VARCHAR(255) NOT NULL,
    upload_document_name VARCHAR(255) DEFAULT NULL,
    upload_document_path VARCHAR(500) DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'Configuration Complete' CHECK(status IN ('Configuration Complete', 'Error', 'Incomplete', 'Pending')),
    summary TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (process_id) REFERENCES processes (id) ON DELETE CASCADE
);

-- 5. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Suspended')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Quality Datasets Table (Data Entry & Data Warehouse)
CREATE TABLE IF NOT EXISTS quality_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkpoint_id INTEGER NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size_kb INTEGER DEFAULT 250,
    uploaded_by_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Processed' CHECK(status IN ('Processed', 'Pending', 'Failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (checkpoint_id) REFERENCES checkpoints (id) ON DELETE CASCADE
);

-- 7. Dashboard Versions Table (Saved Presets & Analytics History)
CREATE TABLE IF NOT EXISTS dashboard_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    dashboard_data_json TEXT NOT NULL,
    created_by VARCHAR(255) DEFAULT 'Alexander Wright (Quality Director)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_processes_product_id ON processes(product_id);
CREATE INDEX IF NOT EXISTS idx_process_steps_process_id ON process_steps(process_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_process_id ON checkpoints(process_id);
CREATE INDEX IF NOT EXISTS idx_datasets_checkpoint_id ON quality_datasets(checkpoint_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_versions_name ON dashboard_versions(name);
"""

def init_db(force_reseed: bool = False):
    """Initializes the database schema and seeds initial master data."""
    with get_db_connection() as conn:
        conn.executescript(CREATE_TABLES_SQL)
        seed_master_data(conn, force_reseed)

def seed_master_data(conn: sqlite3.Connection, force_reseed: bool = False):
    cursor = conn.cursor()
    
    if force_reseed:
        cursor.execute("DELETE FROM dashboard_versions")
        cursor.execute("DELETE FROM quality_datasets")
        cursor.execute("DELETE FROM checkpoints")
        cursor.execute("DELETE FROM process_steps")
        cursor.execute("DELETE FROM processes")
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM users")
    else:
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] > 0:
            # Check if dashboard versions table is seeded
            cursor.execute("SELECT COUNT(*) FROM dashboard_versions")
            if cursor.fetchone()[0] == 0:
                seed_dashboard_presets(conn)
            return

    # 1. Seed 3 Products
    products = [
        ("PRD-101", "Tractor Engine Cover", "Line 01 - Heavy Casting & Machining", "Active"),
        ("PRD-102", "Front Wheel Drum", "Line 02 - Drum & Disc Line", "Active"),
        ("PRD-103", "Rear Wheel Drum", "Line 02 - Drum & Disc Line", "Active"),
    ]
    cursor.executemany(
        "INSERT INTO products (product_code, name, manufacturing_line, status) VALUES (?, ?, ?, ?)",
        products
    )
    
    # Fetch product IDs
    cursor.execute("SELECT id, name FROM products")
    prod_map = {row["name"]: row["id"] for row in cursor.fetchall()}
    tractor_id = prod_map["Tractor Engine Cover"]
    f_drum_id = prod_map["Front Wheel Drum"]
    r_drum_id = prod_map["Rear Wheel Drum"]

    # 2. Seed Processes
    processes = [
        (tractor_id, "Foundry / Casting & Fettling", 1, "Active"),
        (tractor_id, "CNC Rough & Finish Milling", 2, "Complete"),
        (tractor_id, "Drilling, Tapping & Boring", 3, "Incomplete"),
        (tractor_id, "Metrology & GNT Inspection", 4, "Inactive"),
        (tractor_id, "Cleaning, Assembly & Final QC Leak Test", 5, "Complete"),
        (f_drum_id, "High-Pressure Die Casting", 1, "Active"),
        (f_drum_id, "Brake Surface Turning & Dynamic Balancing", 2, "Complete"),
        (r_drum_id, "Gravity Sand Casting & Annealing", 1, "Active"),
        (r_drum_id, "Precision Flange Boring & Hole Drilling", 2, "Complete"),
    ]
    cursor.executemany(
        "INSERT INTO processes (product_id, name, sequence, status) VALUES (?, ?, ?, ?)",
        processes
    )

    cursor.execute("SELECT id, name FROM processes")
    proc_map = {row["name"]: row["id"] for row in cursor.fetchall()}

    # 3. Seed Steps
    steps = [
        (proc_map["Foundry / Casting & Fettling"], 1, "Molten Ingot Pouring & Temperature Check"),
        (proc_map["Foundry / Casting & Fettling"], 2, "Sand Mold Shakeout & Surface Cleaning"),
        (proc_map["Foundry / Casting & Fettling"], 3, "Riser & Flash Fettling"),
        (proc_map["CNC Rough & Finish Milling"], 1, "Workpiece Fixturing & Datum Zeroing"),
        (proc_map["CNC Rough & Finish Milling"], 2, "High-Feed Face Rough Milling"),
        (proc_map["CNC Rough & Finish Milling"], 3, "Precision Finish Profile Contouring"),
        (proc_map["Drilling, Tapping & Boring"], 1, "Pilot Hole Multi-Spindle Drilling"),
        (proc_map["Drilling, Tapping & Boring"], 2, "M10x1.5 Thread Tapping"),
        (proc_map["Drilling, Tapping & Boring"], 3, "Bearing Journal Precision Boring"),
        (proc_map["Metrology & GNT Inspection"], 1, "CMM Probe Routine Calibration"),
        (proc_map["Metrology & GNT Inspection"], 2, "Geometric Flatness & True Position Audit"),
        (proc_map["Metrology & GNT Inspection"], 3, "Surface Roughness Ra Optical Profiling"),
        (proc_map["Cleaning, Assembly & Final QC Leak Test"], 1, "Ultrasonic Degreasing & Hot Air Dry"),
        (proc_map["Cleaning, Assembly & Final QC Leak Test"], 2, "Gasket & Dowel Pin Fitment"),
        (proc_map["Cleaning, Assembly & Final QC Leak Test"], 3, "Hydrostatic & Acoustic Leak Pressure Test"),
        (proc_map["High-Pressure Die Casting"], 1, "Die Preheating & Thermal Spray Coating"),
        (proc_map["High-Pressure Die Casting"], 2, "Molten Aluminium Injection Cycle"),
        (proc_map["Brake Surface Turning & Dynamic Balancing"], 1, "Brake Track CNC Diamond Turning"),
        (proc_map["Brake Surface Turning & Dynamic Balancing"], 2, "Dual-Plane High-Speed Dynamic Balancing"),
        (proc_map["Gravity Sand Casting & Annealing"], 1, "Ductile Iron Furnace Charge Tapping"),
        (proc_map["Gravity Sand Casting & Annealing"], 2, "Controlled Furnace Stress-Relief Annealing"),
        (proc_map["Precision Flange Boring & Hole Drilling"], 1, "Wheel Hub Center Bore Machining"),
        (proc_map["Precision Flange Boring & Hole Drilling"], 2, "PCD Lug Bolt Hole CNC Drilling"),
    ]
    cursor.executemany(
        "INSERT INTO process_steps (process_id, sequence, name) VALUES (?, ?, ?)",
        steps
    )

    # 4. Seed Checkpoints
    checkpoints = [
        (proc_map["Foundry / Casting & Fettling"], 1, "Casting Temperature", "spec_cast_temp.pdf", "Configuration Complete", "Verify molten metal pouring temperature within 1380°C – 1420°C tolerance window before mold filling."),
        (proc_map["Foundry / Casting & Fettling"], 2, "Visual Casting Inspection", "visual_guide_v2.pdf", "Configuration Complete", "Optical visual scan verifying zero porosity, cold shuts, or shrinkage defects on external surfaces."),
        (proc_map["Foundry / Casting & Fettling"], 3, "Fettling / Flash Removal", "fettling_std.pdf", "Configuration Complete", "Mechanical flash removal ensuring all parting lines are trimmed flush within 0.5mm."),
        (proc_map["CNC Rough & Finish Milling"], 1, "Machining Dimensions", "cad_drawing_rev4.pdf", "Configuration Complete", "CNC dial gauge check verifying face milling flatness within ±0.025 mm across critical mounting surface."),
        (proc_map["CNC Rough & Finish Milling"], 2, "Surface Finish", "ra_spec_sheet.pdf", "Configuration Complete", "Surface profilometer verification confirming Ra <= 1.6 um across machined mating faces."),
        (proc_map["CNC Rough & Finish Milling"], 3, "Tool / Machine Condition", "spindle_log.pdf", "Configuration Complete", "Spindle vibration < 0.8 mm/s and tool wear threshold within certified lifetime limits."),
        (proc_map["Drilling, Tapping & Boring"], 1, "Hole Diameter", "pin_gauge_cert.pdf", "Configuration Complete", "Calibrated plug pin gauge check verifying bolt hole diameter within 10.02 +/- 0.01 mm."),
        (proc_map["Drilling, Tapping & Boring"], 2, "Hole Position", "cmm_pos_spec.pdf", "Configuration Complete", "Optical coordinate check verifying true position within 0.05 mm of nominal blueprint coordinates."),
        (proc_map["Drilling, Tapping & Boring"], 3, "Thread Quality", "thread_audit.pdf", "Error", "Thread go/no-go plug gauge verification across all M10x1.5 tapped holes with 100% engagement."),
        (proc_map["Metrology & GNT Inspection"], 1, "Dimensional Accuracy", "cmm_run_report.pdf", "Configuration Complete", "Full-part coordinate measuring machine scan matching CAD nominal envelope."),
        (proc_map["Metrology & GNT Inspection"], 2, "Geometric Tolerances (G&T)", "gnt_summary.pdf", "Configuration Complete", "Parallelism, perpendicularity, and cylindricity within ISO 2768-mK industrial standards."),
        (proc_map["Metrology & GNT Inspection"], 3, "Final Dimensional Inspection", "final_metrology.pdf", "Configuration Complete", "CMM probe coordinate report logging geometric true position, perpendicularity, and datum alignment."),
        (proc_map["Cleaning, Assembly & Final QC Leak Test"], 1, "Cleanliness", "gravimetric_clean.pdf", "Configuration Complete", "Gravimetric particulate residue check confirming total contaminant mass < 15 mg per unit."),
        (proc_map["Cleaning, Assembly & Final QC Leak Test"], 2, "Assembly Fitment", "torque_log.pdf", "Configuration Complete", "Flange bolts torqued to 85 Nm in star pattern with digital slip angle recording."),
        (proc_map["Cleaning, Assembly & Final QC Leak Test"], 3, "Leak Test", "leak_cert_final.pdf", "Configuration Complete", "Differential pressure decay test at 2.5 bar dry air pressure with allowable leak rate < 0.01 bar/min."),
        (proc_map["High-Pressure Die Casting"], 1, "Die Wall Thermal Profile", "die_thermal_spec.pdf", "Configuration Complete", "Thermal camera infrared scan verifying die surface temp > 220°C prior to shot injection."),
        (proc_map["Brake Surface Turning & Dynamic Balancing"], 1, "Brake Track Runout & Ra", "brake_track_tolerance.pdf", "Configuration Complete", "Total indicator reading (TIR) runout < 0.015 mm and surface roughness Ra < 0.8 um."),
        (proc_map["Gravity Sand Casting & Annealing"], 1, "Annealing Hardness Test", "brinell_hardness_std.pdf", "Configuration Complete", "Brinell hardness verification within 180 – 220 HBW range across cast rim."),
        (proc_map["Precision Flange Boring & Hole Drilling"], 1, "PCD Pitch & Bore Concentricity", "pcd_hole_spec.pdf", "Configuration Complete", "Optical gauge check verifying 5-hole PCD pitch diameter within +/- 0.02 mm of datum center."),
    ]
    cursor.executemany(
        """INSERT INTO checkpoints 
           (process_id, sequence, name, upload_document_name, status, summary) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        checkpoints
    )

    # 5. Seed Users
    users = [
        ("Alexander Wright", "alex.wright@qualiq.io", "Quality Director (Admin)", "Active"),
        ("Elena Rostova", "elena.rostova@qualiq.io", "Lead Process Engineer", "Active"),
        ("David Chang", "david.chang@qualiq.io", "Shopfloor Inspector", "Active"),
        ("Sarah Jenkins", "sarah.jenkins@qualiq.io", "Senior Metrology Specialist", "Active"),
        ("Marcus Vance", "marcus.vance@qualiq.io", "Quality Assurance Lead", "Active"),
    ]
    cursor.executemany(
        "INSERT INTO users (name, email, role, status) VALUES (?, ?, ?, ?)",
        users
    )

    # 6. Seed Quality Datasets
    cursor.execute("SELECT id, name FROM checkpoints")
    cp_map = {row[1]: row[0] for row in cursor.fetchall()}

    datasets = [
        (cp_map.get("Casting Temperature", 1), "foundry_temp_log_shiftA_aug26.xlsx", 340, "Elena Rostova", "Processed", "2026-08-28 08:30:00"),
        (cp_map.get("Visual Casting Inspection", 2), "visual_defect_scan_batch44.xlsx", 520, "David Chang", "Processed", "2026-08-28 09:15:00"),
        (cp_map.get("Fettling / Flash Removal", 3), "fettling_dimensional_report_lot18.xlsx", 210, "David Chang", "Processed", "2026-08-28 10:45:00"),
        (cp_map.get("Machining Dimensions", 4), "cnc_milling_dial_gauge_run12.xlsx", 810, "Elena Rostova", "Processed", "2026-08-28 11:20:00"),
        (cp_map.get("Surface Finish", 5), "surface_roughness_profiling_lot9.xlsx", 290, "David Chang", "Processed", "2026-08-28 13:10:00"),
        (cp_map.get("Tool / Machine Condition", 6), "spindle_vibration_telemetry_w34.xlsx", 670, "Elena Rostova", "Processed", "2026-08-28 14:00:00"),
        (cp_map.get("Hole Diameter", 7), "drilling_pin_gauge_audit_shiftB.xlsx", 410, "Elena Rostova", "Processed", "2026-08-29 08:00:00"),
        (cp_map.get("Hole Position", 8), "cmm_hole_true_position_dataset.xlsx", 920, "Sarah Jenkins", "Processed", "2026-08-29 09:40:00"),
        (cp_map.get("Thread Quality", 9), "thread_go_nogo_plug_audit.xlsx", 180, "David Chang", "Processed", "2026-08-29 11:00:00"),
        (cp_map.get("Dimensional Accuracy", 10), "cmm_full_inspection_data_w34.xlsx", 1250, "Alexander Wright", "Processed", "2026-08-29 14:30:00"),
        (cp_map.get("Geometric Tolerances (G&T)", 11), "iso2768_gnt_coordinate_matrix.xlsx", 740, "Sarah Jenkins", "Processed", "2026-08-29 16:15:00"),
        (cp_map.get("Final Dimensional Inspection", 12), "final_metrology_qa_batch104.xlsx", 1100, "Sarah Jenkins", "Processed", "2026-08-30 08:15:00"),
        (cp_map.get("Cleanliness", 13), "gravimetric_millipore_clean_log.xlsx", 310, "David Chang", "Processed", "2026-08-30 09:30:00"),
        (cp_map.get("Assembly Fitment", 14), "torque_angle_digital_slip_log.xlsx", 480, "Elena Rostova", "Processed", "2026-08-30 11:00:00"),
        (cp_map.get("Leak Test", 15), "qc_pressure_decay_leak_test_final.xlsx", 380, "David Chang", "Processed", "2026-08-30 13:45:00"),
        (cp_map.get("Die Wall Thermal Profile", 16), "fwd_die_thermal_ir_scan_run03.xlsx", 460, "Marcus Vance", "Processed", "2026-08-30 14:10:00"),
        (cp_map.get("Brake Track Runout & Ra", 17), "front_drum_brake_track_runout_log.xlsx", 540, "Marcus Vance", "Processed", "2026-08-30 14:35:00"),
        (cp_map.get("Annealing Hardness Test", 18), "rear_drum_brinell_hardness_test_b12.xlsx", 390, "Elena Rostova", "Processed", "2026-08-30 14:50:00"),
    ]
    cursor.executemany(
        """INSERT INTO quality_datasets 
           (checkpoint_id, file_name, file_size_kb, uploaded_by_name, status, created_at) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        datasets
    )

    # 7. Seed Dashboard Versions
    seed_dashboard_presets(conn)

def seed_dashboard_presets(conn: sqlite3.Connection):
    """Seeds default standard quality analytics presets."""
    cursor = conn.cursor()
    presets = [
        (
            "Executive Quality & Cpk Overview",
            "Generate a quality analytics dashboard suitable to the uploaded data",
            json.dumps({
                "kpis": {
                    "total_inspected": "5,420 Units",
                    "first_pass_yield": "96.8%",
                    "defect_rate": "3.2%",
                    "cpk_index": "1.28"
                },
                "ai_narrative": "### 📊 Executive Quality Overview\n\nOverall plant quality performance remains stable at **96.8% First-Pass Yield** across **18 production datasets**. Critical process capability (**Cpk = 1.28**) confirms acceptable statistical containment within specification limits, with primary defect concentrations residing in **Dimensional Drift (38.9%)** and **Surface Porosity (26.3%)**.\n\n#### Key Operational Focus Areas:\n1. **Milling Station CNC-04**: Exhibiting higher non-conformance rate (7.8%) compared to line baseline (2.4%).\n2. **Shift C Variance**: Night shift operations show increased dimensional variance (+1.2mm sigma drift).\n3. **Recommended Immediate Action**: Perform spindle alignment and recalibrate tool offsets on Milling Station CNC-04."
            }),
            "Alexander Wright (Quality Director)"
        ),
        (
            "Milling Line CNC-04 Anomaly Audit",
            "Analyze Milling Station CNC-04 defect rate, dimensional drift, and tool wear correlation",
            json.dumps({
                "kpis": {
                    "total_inspected": "1,840 Units",
                    "first_pass_yield": "92.2%",
                    "defect_rate": "7.8%",
                    "cpk_index": "0.94"
                },
                "ai_narrative": "### ⚠️ Milling Line CNC-04 Targeted Audit\n\nTargeted investigation of **Milling Station CNC-04** reveals an elevated defect rate of **7.8%** (Process Cpk = 0.94, below the 1.33 six-sigma standard). Non-conformance data indicates **thermal spindle expansion** after 4 hours of continuous operation is the primary driver of face milling flatness out-of-spec errors.\n\n#### Action Plan:\n1. Implement thermal stabilization warm-up cycles.\n2. Schedule immediate spindle runout verification and replace worn finishing inserts.\n3. Recalibrate Z-axis zero datum."
            }),
            "Elena Rostova (Lead Process Engineer)"
        ),
        (
            "Shift C Night Operation Quality Audit",
            "Compare Shift A, Shift B, and Shift C defect rates and identify root causes for night shift variation",
            json.dumps({
                "kpis": {
                    "total_inspected": "1,650 Units",
                    "first_pass_yield": "93.6%",
                    "defect_rate": "6.4%",
                    "cpk_index": "1.08"
                },
                "ai_narrative": "### 🌙 Shift C Quality & Operational Analysis\n\nComparative shift evaluation highlights a **6.4% defect rate during Shift C (Night)** versus **2.1% on Shift A (Morning)** and **2.7% on Shift B (Evening)**. Root cause data indicates **coolant concentration degradation** and manual measurement recording delays as primary contributors to night shift scrap rates.\n\n#### Recommendations:\n1. Automate refractive coolant concentration logging on night shifts.\n2. Mandate digital plug-gauge torque entry at hourly intervals."
            }),
            "David Chang (Shopfloor Inspector)"
        )
    ]

    cursor.executemany(
        """INSERT INTO dashboard_versions 
           (name, prompt, dashboard_data_json, created_by) 
           VALUES (?, ?, ?, ?)""",
        presets
    )
