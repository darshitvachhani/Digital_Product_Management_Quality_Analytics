-- ============================================================================
-- QUALIQ PRODUCTION SUPABASE SCHEMA & INITIAL SEED DATA
-- ============================================================================

-- 1. Products Table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) UNIQUE NOT NULL,
    manufacturing_line VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Processes Table
CREATE TABLE IF NOT EXISTS processes (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    sequence INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Process Steps Table
CREATE TABLE IF NOT EXISTS process_steps (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL DEFAULT 1,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Checkpoints Table
CREATE TABLE IF NOT EXISTS checkpoints (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL DEFAULT 1,
    name VARCHAR(255) NOT NULL,
    upload_document_name VARCHAR(255) DEFAULT NULL,
    upload_document_path VARCHAR(500) DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'Configuration Complete',
    summary TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Quality Datasets Table
CREATE TABLE IF NOT EXISTS quality_datasets (
    id SERIAL PRIMARY KEY,
    checkpoint_id INTEGER NOT NULL REFERENCES checkpoints(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_size_kb INTEGER DEFAULT 250,
    uploaded_by_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Processed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Dashboard Versions Table
CREATE TABLE IF NOT EXISTS dashboard_versions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    dashboard_data_json TEXT NOT NULL,
    created_by VARCHAR(255) DEFAULT 'Alexander Wright (Quality Director)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SEED INITIAL MASTER DATA
-- ============================================================================

-- 1. Insert Products
INSERT INTO products (product_code, name, manufacturing_line, status) VALUES
('PRD-101', 'Tractor Engine Cover', 'Line 01 - Heavy Casting & Machining', 'Active'),
('PRD-102', 'Front Wheel Drum', 'Line 02 - Drum & Disc Line', 'Active'),
('PRD-103', 'Rear Wheel Drum', 'Line 02 - Drum & Disc Line', 'Active')
ON CONFLICT (product_code) DO NOTHING;

-- 2. Insert Processes
INSERT INTO processes (product_id, name, sequence, status) VALUES
(1, 'Foundry / Casting & Fettling', 1, 'Active'),
(1, 'CNC Rough & Finish Milling', 2, 'Complete'),
(1, 'Drilling, Tapping & Boring', 3, 'Incomplete'),
(1, 'Metrology & GNT Inspection', 4, 'Inactive'),
(1, 'Cleaning, Assembly & Final QC Leak Test', 5, 'Complete'),
(2, 'High-Pressure Die Casting', 1, 'Active'),
(2, 'Brake Surface Turning & Dynamic Balancing', 2, 'Complete'),
(3, 'Gravity Sand Casting & Annealing', 1, 'Active'),
(3, 'Precision Flange Boring & Hole Drilling', 2, 'Complete');

-- 3. Insert Process Steps
INSERT INTO process_steps (process_id, sequence, name) VALUES
(1, 1, 'Molten Ingot Pouring & Temperature Check'),
(1, 2, 'Sand Mold Shakeout & Surface Cleaning'),
(1, 3, 'Riser & Flash Fettling'),
(2, 1, 'Workpiece Fixturing & Datum Zeroing'),
(2, 2, 'High-Feed Face Rough Milling'),
(2, 3, 'Precision Finish Profile Contouring'),
(3, 1, 'Pilot Hole Multi-Spindle Drilling'),
(3, 2, 'M10x1.5 Thread Tapping'),
(3, 3, 'Bearing Journal Precision Boring'),
(4, 1, 'CMM Probe Routine Calibration'),
(4, 2, 'Geometric Flatness & True Position Audit'),
(4, 3, 'Surface Roughness Ra Optical Profiling'),
(5, 1, 'Ultrasonic Degreasing & Hot Air Dry'),
(5, 2, 'Gasket & Dowel Pin Fitment'),
(5, 3, 'Hydrostatic & Acoustic Leak Pressure Test');

-- 4. Insert Checkpoints
INSERT INTO checkpoints (process_id, sequence, name, upload_document_name, status, summary) VALUES
(1, 1, 'Casting Temperature', 'spec_cast_temp.pdf', 'Configuration Complete', 'Verify molten metal pouring temperature within 1380°C – 1420°C tolerance window before mold filling.'),
(1, 2, 'Visual Casting Inspection', 'visual_guide_v2.pdf', 'Configuration Complete', 'Optical visual scan verifying zero porosity, cold shuts, or shrinkage defects on external surfaces.'),
(1, 3, 'Fettling / Flash Removal', 'fettling_std.pdf', 'Configuration Complete', 'Mechanical flash removal ensuring all parting lines are trimmed flush within 0.5mm.'),
(2, 1, 'Machining Dimensions', 'cad_drawing_rev4.pdf', 'Configuration Complete', 'CNC dial gauge check verifying face milling flatness within ±0.025 mm across critical mounting surface.'),
(2, 2, 'Surface Finish', 'ra_spec_sheet.pdf', 'Configuration Complete', 'Surface profilometer verification confirming Ra <= 1.6 um across machined mating faces.'),
(2, 3, 'Tool / Machine Condition', 'spindle_log.pdf', 'Configuration Complete', 'Spindle vibration < 0.8 mm/s and tool wear threshold within certified lifetime limits.'),
(3, 1, 'Hole Diameter', 'pin_gauge_cert.pdf', 'Configuration Complete', 'Calibrated plug pin gauge check verifying bolt hole diameter within 10.02 +/- 0.01 mm.'),
(3, 2, 'Hole Position', 'cmm_pos_spec.pdf', 'Configuration Complete', 'Optical coordinate check verifying true position within 0.05 mm of nominal blueprint coordinates.'),
(3, 3, 'Thread Quality', 'thread_audit.pdf', 'Configuration Complete', 'Thread go/no-go plug gauge verification across all M10x1.5 tapped holes with 100% engagement.'),
(4, 1, 'Dimensional Accuracy', 'cmm_run_report.pdf', 'Configuration Complete', 'Full-part coordinate measuring machine scan matching CAD nominal envelope.'),
(4, 2, 'Geometric Tolerances (G&T)', 'gnt_summary.pdf', 'Configuration Complete', 'Parallelism, perpendicularity, and cylindricity within ISO 2768-mK industrial standards.'),
(4, 3, 'Final Dimensional Inspection', 'final_metrology.pdf', 'Configuration Complete', 'CMM probe coordinate report logging geometric true position, perpendicularity, and datum alignment.'),
(5, 1, 'Cleanliness', 'gravimetric_clean.pdf', 'Configuration Complete', 'Gravimetric particulate residue check confirming total contaminant mass < 15 mg per unit.'),
(5, 2, 'Assembly Fitment', 'torque_log.pdf', 'Configuration Complete', 'Flange bolts torqued to 85 Nm in star pattern with digital slip angle recording.'),
(5, 3, 'Leak Test', 'leak_cert_final.pdf', 'Configuration Complete', 'Differential pressure decay test at 2.5 bar dry air pressure with allowable leak rate < 0.01 bar/min.');

-- 5. Insert Users
INSERT INTO users (name, email, role, status) VALUES
('Alexander Wright', 'alex.wright@qualiq.io', 'Quality Director (Admin)', 'Active'),
('Elena Rostova', 'elena.rostova@qualiq.io', 'Lead Process Engineer', 'Active'),
('David Chang', 'david.chang@qualiq.io', 'Shopfloor Inspector', 'Active'),
('Sarah Jenkins', 'sarah.jenkins@qualiq.io', 'Senior Metrology Specialist', 'Active'),
('Marcus Vance', 'marcus.vance@qualiq.io', 'Quality Assurance Lead', 'Active')
ON CONFLICT (email) DO NOTHING;

-- 6. Insert Quality Datasets
INSERT INTO quality_datasets (checkpoint_id, file_name, file_size_kb, uploaded_by_name, status) VALUES
(1, 'foundry_temp_log_shiftA_aug26.xlsx', 340, 'Elena Rostova', 'Processed'),
(2, 'visual_defect_scan_batch44.xlsx', 520, 'David Chang', 'Processed'),
(3, 'fettling_dimensional_report_lot18.xlsx', 210, 'David Chang', 'Processed'),
(4, 'cnc_milling_dial_gauge_run12.xlsx', 810, 'Elena Rostova', 'Processed'),
(5, 'surface_roughness_profiling_lot9.xlsx', 290, 'David Chang', 'Processed'),
(6, 'spindle_vibration_telemetry_w34.xlsx', 670, 'Elena Rostova', 'Processed'),
(7, 'drilling_pin_gauge_audit_shiftB.xlsx', 410, 'Elena Rostova', 'Processed'),
(8, 'cmm_hole_true_position_dataset.xlsx', 920, 'Sarah Jenkins', 'Processed'),
(9, 'thread_go_nogo_plug_audit.xlsx', 180, 'David Chang', 'Processed'),
(10, 'cmm_full_inspection_data_w34.xlsx', 1250, 'Alexander Wright', 'Processed'),
(11, 'iso2768_gnt_coordinate_matrix.xlsx', 740, 'Sarah Jenkins', 'Processed'),
(12, 'final_metrology_qa_batch104.xlsx', 1100, 'Sarah Jenkins', 'Processed'),
(13, 'gravimetric_millipore_clean_log.xlsx', 310, 'David Chang', 'Processed'),
(14, 'torque_angle_digital_slip_log.xlsx', 480, 'Elena Rostova', 'Processed'),
(15, 'qc_pressure_decay_leak_test_final.xlsx', 380, 'David Chang', 'Processed');

-- 7. Insert Dashboard Presets
INSERT INTO dashboard_versions (name, prompt, dashboard_data_json, created_by) VALUES
('Executive Quality & Cpk Overview', 'Generate a quality analytics dashboard suitable to the uploaded data', '{"kpis": {"total_inspected": "5,420 Units", "first_pass_yield": "96.8%", "defect_rate": "3.2%", "cpk_index": "1.28"}, "ai_narrative": "### 📊 Executive Quality Overview\n\nOverall plant quality performance remains stable at **96.8% First-Pass Yield** across **18 production datasets**."}', 'Alexander Wright (Quality Director)'),
('Milling Line CNC-04 Anomaly Audit', 'Analyze Milling Station CNC-04 defect rate, dimensional drift, and tool wear correlation', '{"kpis": {"total_inspected": "1,840 Units", "first_pass_yield": "92.2%", "defect_rate": "7.8%", "cpk_index": "0.94"}, "ai_narrative": "### ⚠️ Milling Line CNC-04 Targeted Audit\n\nTargeted investigation of **Milling Station CNC-04** reveals an elevated defect rate of **7.8%**."}', 'Elena Rostova (Lead Process Engineer)'),
('Shift C Night Operation Quality Audit', 'Compare Shift A, Shift B, and Shift C defect rates', '{"kpis": {"total_inspected": "1,650 Units", "first_pass_yield": "93.6%", "defect_rate": "6.4%", "cpk_index": "1.08"}, "ai_narrative": "### 🌙 Shift C Quality & Operational Analysis\n\nComparative shift evaluation highlights a **6.4% defect rate during Shift C (Night)**."}', 'David Chang (Shopfloor Inspector)');
