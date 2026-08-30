import sqlite3
from typing import List, Dict, Optional, Any, Tuple
from db.connection import get_db_connection

# ============================================================================
# 1. PRODUCTS CRUD & VALIDATION GUARDS
# ============================================================================

def get_all_products() -> List[Dict[str, Any]]:
    """Retrieves all products along with their active process count."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT 
                p.id, 
                p.product_code, 
                p.name, 
                p.manufacturing_line, 
                p.status,
                COUNT(proc.id) AS process_count
            FROM products p
            LEFT JOIN processes proc ON p.id = proc.product_id
            GROUP BY p.id
            ORDER BY p.id ASC
        """
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single product by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def can_delete_product(product_id: int) -> Tuple[bool, int, str]:
    """
    BUSINESS RULE: You CANNOT delete a product if it has ANY associated processes.
    Returns (can_delete: bool, process_count: int, message: str)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM processes WHERE product_id = ?", (product_id,))
        count = cursor.fetchone()["count"]
        if count > 0:
            return (
                False, 
                count, 
                f"Cannot delete product: There {'is' if count == 1 else 'are'} {count} process{'es' if count > 1 else ''} associated with this product. You must remove or reassign the processes first."
            )
        return (True, 0, "")

def insert_product(product_code: str, name: str, manufacturing_line: str, status: str = "Active") -> int:
    """Creates a new product record."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO products (product_code, name, manufacturing_line, status)
               VALUES (?, ?, ?, ?)""",
            (product_code.strip(), name.strip(), manufacturing_line.strip(), status)
        )
        return cursor.lastrowid

def update_product(product_id: int, product_code: str, name: str, manufacturing_line: str, status: str) -> bool:
    """Updates an existing product record."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE products 
               SET product_code = ?, name = ?, manufacturing_line = ?, status = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (product_code.strip(), name.strip(), manufacturing_line.strip(), status, product_id)
        )
        return cursor.rowcount > 0

def delete_product(product_id: int) -> Tuple[bool, str]:
    """Deletes a product only if it has 0 associated processes."""
    can_del, count, msg = can_delete_product(product_id)
    if not can_del:
        return (False, msg)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        return (True, "Product deleted successfully.")

# ============================================================================
# 2. PROCESSES CRUD & FULL WORKFLOW DETAILS
# ============================================================================

def get_all_processes(filter_product_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves processes, optionally filtered by product name."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if filter_product_name and filter_product_name != "All Products":
            query = """
                SELECT 
                    proc.id,
                    proc.sequence,
                    proc.name AS process_name,
                    proc.status,
                    proc.product_id,
                    prd.name AS product_name,
                    prd.product_code,
                    COUNT(cp.id) AS checkpoint_count
                FROM processes proc
                JOIN products prd ON proc.product_id = prd.id
                LEFT JOIN checkpoints cp ON proc.id = cp.process_id
                WHERE prd.name = ?
                GROUP BY proc.id
                ORDER BY proc.sequence ASC, proc.id ASC
            """
            cursor.execute(query, (filter_product_name,))
        else:
            query = """
                SELECT 
                    proc.id,
                    proc.sequence,
                    proc.name AS process_name,
                    proc.status,
                    proc.product_id,
                    prd.name AS product_name,
                    prd.product_code,
                    COUNT(cp.id) AS checkpoint_count
                FROM processes proc
                JOIN products prd ON proc.product_id = prd.id
                LEFT JOIN checkpoints cp ON proc.id = cp.process_id
                GROUP BY proc.id
                ORDER BY prd.id ASC, proc.sequence ASC, proc.id ASC
            """
            cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

def get_process_full_details(process_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetches full relational details for a process (Product, Name, Steps, Checkpoints).
    Used to hydrate the 4-Step Multi-Step Edit Wizard.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Process Info + Product
        cursor.execute("""
            SELECT proc.id, proc.name AS process_name, proc.status, proc.sequence,
                   prd.id AS product_id, prd.name AS product_name, prd.product_code
            FROM processes proc
            JOIN products prd ON proc.product_id = prd.id
            WHERE proc.id = ?
        """, (process_id,))
        proc_row = cursor.fetchone()
        if not proc_row:
            return None
        
        result = dict(proc_row)

        # 2. Steps
        cursor.execute("""
            SELECT id, sequence, name 
            FROM process_steps 
            WHERE process_id = ? 
            ORDER BY sequence ASC
        """, (process_id,))
        result["steps"] = [row["name"] for row in cursor.fetchall()]
        if not result["steps"]:
            result["steps"] = [f"{result['process_name']} Step 1", f"{result['process_name']} Step 2"]

        # 3. Checkpoints
        cursor.execute("""
            SELECT c.id, c.sequence, c.name, c.upload_document_name, c.status, c.summary
            FROM checkpoints c
            WHERE c.process_id = ?
            ORDER BY c.sequence ASC
        """, (process_id,))
        cp_rows = cursor.fetchall()
        result["checkpoints"] = []
        for cp in cp_rows:
            result["checkpoints"].append({
                "id": cp["id"],
                "sequence": cp["sequence"],
                "name": cp["name"],
                "process": result["steps"][0] if result["steps"] else result["process_name"],
                "doc": cp["upload_document_name"] or "spec_doc.pdf",
                "status": cp["status"] or "Configuration Complete",
                "summary": cp["summary"] or f"Standard quality parameters for {cp['name']}."
            })

        return result

def update_full_process_workflow(
    process_id: int, 
    process_name: str, 
    steps: List[str], 
    checkpoints: List[Dict[str, Any]]
) -> bool:
    """
    Atomically updates a process, its steps, and checkpoints in SQLite.
    Preserves existing checkpoint IDs to prevent breaking dataset relations.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Update Process Name
        cursor.execute("""
            UPDATE processes 
            SET name = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (process_name.strip(), process_id))

        # 2. Sync Process Steps (Replace steps for this process)
        cursor.execute("DELETE FROM process_steps WHERE process_id = ?", (process_id,))
        for idx, step_name in enumerate(steps, start=1):
            if step_name and step_name.strip():
                cursor.execute(
                    "INSERT INTO process_steps (process_id, sequence, name) VALUES (?, ?, ?)",
                    (process_id, idx, step_name.strip())
                )

        # 3. Sync Checkpoints
        for idx, cp in enumerate(checkpoints, start=1):
            cp_name = cp.get("name", "").strip()
            if cp_name:
                cp_id = cp.get("id")
                cp_doc = cp.get("doc") or cp.get("upload_document_name", None)
                cp_status = cp.get("status", "Configuration Complete")
                cp_summary = cp.get("summary", f"Quality gate for {cp_name}.")

                # Check if this is an existing integer checkpoint ID in DB
                if isinstance(cp_id, int):
                    cursor.execute("""
                        UPDATE checkpoints 
                        SET name = ?, sequence = ?, upload_document_name = ?, status = ?, summary = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND process_id = ?
                    """, (cp_name, idx, cp_doc, cp_status, cp_summary, cp_id, process_id))
                else:
                    # Insert new checkpoint
                    cursor.execute("""
                        INSERT INTO checkpoints (process_id, sequence, name, upload_document_name, status, summary)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (process_id, idx, cp_name, cp_doc, cp_status, cp_summary))

        return True

def create_full_process_workflow(
    product_name: str, 
    process_name: str, 
    steps: List[str], 
    checkpoints: List[Dict[str, Any]]
) -> int:
    """Creates a new process, its steps, and checkpoints atomically."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Look up or create product
        cursor.execute("SELECT id FROM products WHERE name = ?", (product_name,))
        product_row = cursor.fetchone()
        if not product_row:
            cursor.execute(
                "INSERT INTO products (product_code, name, manufacturing_line, status) VALUES (?, ?, ?, ?)",
                (f"PRD-{hash(product_name)%1000:03d}", product_name, "General Production Line", "Active")
            )
            product_id = cursor.lastrowid
        else:
            product_id = product_row["id"]

        # Get current highest sequence
        cursor.execute("SELECT MAX(sequence) AS max_seq FROM processes WHERE product_id = ?", (product_id,))
        max_seq = cursor.fetchone()["max_seq"] or 0
        new_sequence = max_seq + 1

        # Insert new Process
        cursor.execute(
            "INSERT INTO processes (product_id, name, sequence, status) VALUES (?, ?, ?, ?)",
            (product_id, process_name, new_sequence, "Active")
        )
        process_id = cursor.lastrowid

        # Insert Process Steps
        for idx, step_name in enumerate(steps, start=1):
            if step_name and step_name.strip():
                cursor.execute(
                    "INSERT INTO process_steps (process_id, sequence, name) VALUES (?, ?, ?)",
                    (process_id, idx, step_name.strip())
                )

        # Insert Checkpoints
        for idx, cp in enumerate(checkpoints, start=1):
            name = cp.get("name", "").strip()
            if name:
                doc = cp.get("upload_document_name", None) or cp.get("doc", None)
                status = cp.get("status", "Configuration Complete")
                summary = cp.get("summary", "")
                cursor.execute(
                    """INSERT INTO checkpoints 
                       (process_id, sequence, name, upload_document_name, status, summary) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (process_id, idx, name, doc, status, summary)
                )

        return process_id

# ============================================================================
# 3. CHECKPOINTS REPOSITORY
# ============================================================================

def get_checkpoints_for_table() -> List[Dict[str, Any]]:
    """Retrieves all master checkpoints with their associated process and product info."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT 
                c.id,
                c.sequence,
                c.name AS checkpoint_name,
                proc.name AS process_name,
                prd.name AS product_name,
                c.upload_document_name,
                c.status,
                c.summary
            FROM checkpoints c
            JOIN processes proc ON c.process_id = proc.id
            JOIN products prd ON proc.product_id = prd.id
            ORDER BY proc.sequence ASC, c.sequence ASC
        """
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

def get_all_checkpoints_list() -> List[Dict[str, Any]]:
    """Retrieves all checkpoints formatted for dropdown selection."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT 
                c.id,
                c.name AS checkpoint_name,
                proc.name AS process_name,
                prd.name AS product_name
            FROM checkpoints c
            JOIN processes proc ON c.process_id = proc.id
            JOIN products prd ON proc.product_id = prd.id
            ORDER BY prd.id ASC, proc.sequence ASC, c.sequence ASC
        """
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

# ============================================================================
# 4. QUALITY DATASETS CRUD (DATA ENTRY & DATA WAREHOUSE)
# ============================================================================

def insert_quality_dataset(
    checkpoint_name: str,
    file_name: str,
    file_size_kb: int = 350,
    uploaded_by_name: str = "Alexander Wright"
) -> int:
    """Inserts an uploaded dataset record tied to a checkpoint."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM checkpoints WHERE name = ?", (checkpoint_name,))
        cp_row = cursor.fetchone()
        checkpoint_id = cp_row["id"] if cp_row else 1

        cursor.execute(
            """INSERT INTO quality_datasets 
               (checkpoint_id, file_name, file_size_kb, uploaded_by_name, status) 
               VALUES (?, ?, ?, ?, ?)""",
            (checkpoint_id, file_name, file_size_kb, uploaded_by_name, "Processed")
        )
        return cursor.lastrowid

def update_quality_dataset(
    dataset_id: int, 
    file_name: str, 
    checkpoint_name: str, 
    uploaded_by_name: str
) -> bool:
    """Updates a quality dataset record."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM checkpoints WHERE name = ?", (checkpoint_name,))
        cp_row = cursor.fetchone()
        checkpoint_id = cp_row["id"] if cp_row else 1

        cursor.execute(
            """UPDATE quality_datasets 
               SET file_name = ?, checkpoint_id = ?, uploaded_by_name = ? 
               WHERE id = ?""",
            (file_name.strip(), checkpoint_id, uploaded_by_name.strip(), dataset_id)
        )
        return cursor.rowcount > 0

def delete_quality_dataset(dataset_id: int) -> bool:
    """Deletes a quality dataset record from SQLite."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quality_datasets WHERE id = ?", (dataset_id,))
        return cursor.rowcount > 0

def get_all_datasets(
    product_filter: Optional[str] = None,
    process_filter: Optional[str] = None,
    checkpoint_filter: Optional[str] = None,
    user_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves all quality datasets with full relational context and filtering."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT 
                d.id,
                d.file_name,
                d.file_size_kb,
                d.uploaded_by_name,
                d.status,
                d.created_at,
                c.name AS checkpoint_name,
                proc.name AS process_name,
                prd.name AS product_name
            FROM quality_datasets d
            JOIN checkpoints c ON d.checkpoint_id = c.id
            JOIN processes proc ON c.process_id = proc.id
            JOIN products prd ON proc.product_id = prd.id
            WHERE 1=1
        """
        params = []
        if product_filter and product_filter != "All Products":
            query += " AND prd.name = ?"
            params.append(product_filter)
        if process_filter and process_filter != "All Processes":
            query += " AND proc.name = ?"
            params.append(process_filter)
        if checkpoint_filter and checkpoint_filter != "All Checkpoints":
            query += " AND c.name = ?"
            params.append(checkpoint_filter)
        if user_filter and user_filter != "All Users":
            query += " AND d.uploaded_by_name LIKE ?"
            params.append(f"%{user_filter}%")

        query += " ORDER BY d.id DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

# ============================================================================
# 5. USERS CRUD & VALIDATION GUARDS
# ============================================================================

def get_all_users() -> List[Dict[str, Any]]:
    """Retrieves all platform users."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]

def can_delete_user(user_id: int) -> Tuple[bool, int, str]:
    """
    BUSINESS RULE: You CANNOT delete a user if they have uploaded ANY data entries / quality datasets.
    Returns (can_delete: bool, dataset_count: int, message: str)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return (False, 0, "User not found.")
        
        user_name = user_row["name"]
        cursor.execute(
            "SELECT COUNT(*) AS count FROM quality_datasets WHERE uploaded_by_name LIKE ?", 
            (f"%{user_name}%",)
        )
        count = cursor.fetchone()["count"]
        if count > 0:
            return (
                False, 
                count, 
                f"Cannot delete user '{user_name}': This user has {count} associated data entr{'y' if count == 1 else 'ies'}/uploaded datasets on the platform. Users with active data contributions cannot be deleted."
            )
        return (True, 0, "")

def insert_user(name: str, email: str, role: str, status: str = "Active") -> int:
    """Creates a new user record."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, role, status) VALUES (?, ?, ?, ?)",
            (name.strip(), email.strip(), role.strip(), status)
        )
        return cursor.lastrowid

def update_user(user_id: int, name: str, email: str, role: str, status: str) -> bool:
    """Updates an existing user record."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE users 
               SET name = ?, email = ?, role = ?, status = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            (name.strip(), email.strip(), role.strip(), status, user_id)
        )
        return cursor.rowcount > 0

def delete_user(user_id: int) -> Tuple[bool, str]:
    """Deletes a user only if they have not contributed any quality datasets."""
    can_del, count, msg = can_delete_user(user_id)
    if not can_del:
        return (False, msg)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return (True, "User deleted successfully.")

# ============================================================================
# 6. DASHBOARD VERSIONS CRUD
# ============================================================================

import json

def get_all_dashboard_versions() -> List[Dict[str, Any]]:
    """Retrieves all saved dashboard versions ordered by creation date descending."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dashboard_versions ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_dashboard_version_by_id(version_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single dashboard version by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dashboard_versions WHERE id = ?", (version_id,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        try:
            res["dashboard_data"] = json.loads(res["dashboard_data_json"])
        except Exception:
            res["dashboard_data"] = {}
        return res

def save_dashboard_version(
    name: str, 
    prompt: str, 
    dashboard_data: dict, 
    created_by: str = "Alexander Wright (Quality Director)"
) -> int:
    """Saves a new dashboard version with its prompt and analytics state."""
    # Strip Plotly figure objects before storing JSON string
    serialized_state = {
        "kpis": dashboard_data.get("kpis", {}),
        "ai_narrative": dashboard_data.get("ai_narrative", "")
    }
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO dashboard_versions 
               (name, prompt, dashboard_data_json, created_by) 
               VALUES (?, ?, ?, ?)""",
            (name.strip(), prompt.strip(), json.dumps(serialized_state), created_by.strip())
        )
        return cursor.lastrowid

def delete_dashboard_version(version_id: int) -> bool:
    """Deletes a saved dashboard version."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dashboard_versions WHERE id = ?", (version_id,))
        return cursor.rowcount > 0
