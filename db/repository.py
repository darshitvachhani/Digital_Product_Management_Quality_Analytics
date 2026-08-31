import os
import json
import sqlite3
from typing import List, Dict, Optional, Any, Tuple
from db.connection import get_db_connection
from db.supabase_client import get_supabase_client

# ============================================================================
# 1. PRODUCTS CRUD
# ============================================================================

def get_all_products() -> List[Dict[str, Any]]:
    """Retrieves all products along with their active process count."""
    sb = get_supabase_client()
    if sb:
        try:
            prods = sb.table("products").select("*, processes(id)").order("id").execute().data
            results = []
            for p in prods:
                proc_list = p.get("processes") or []
                results.append({
                    "id": p["id"],
                    "product_code": p["product_code"],
                    "name": p["name"],
                    "manufacturing_line": p["manufacturing_line"],
                    "status": p["status"],
                    "process_count": len(proc_list)
                })
            return results
        except Exception as e:
            print(f"Supabase get_all_products fallback: {e}")

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

def can_delete_product(product_id: int) -> Tuple[bool, int, str]:
    """You CANNOT delete a product if it has ANY associated processes."""
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("processes").select("id", count="exact").eq("product_id", product_id).execute()
            count = res.count or len(res.data)
            if count > 0:
                return (False, count, f"Cannot delete product: There {'is' if count == 1 else 'are'} {count} process{'es' if count > 1 else ''} associated with this product. You must remove or reassign the processes first.")
            return (True, 0, "")
        except Exception as e:
            print(f"Supabase can_delete_product fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM processes WHERE product_id = ?", (product_id,))
        count = cursor.fetchone()["count"]
        if count > 0:
            return (False, count, f"Cannot delete product: There {'is' if count == 1 else 'are'} {count} process{'es' if count > 1 else ''} associated with this product. You must remove or reassign the processes first.")
        return (True, 0, "")

def insert_product(product_code: str, name: str, manufacturing_line: str, status: str = "Active") -> int:
    """Creates a new product record."""
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("products").insert({
                "product_code": product_code.strip(),
                "name": name.strip(),
                "manufacturing_line": manufacturing_line.strip(),
                "status": status
            }).execute()
            return res.data[0]["id"]
        except Exception as e:
            print(f"Supabase insert_product fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (product_code, name, manufacturing_line, status) VALUES (?, ?, ?, ?)",
            (product_code.strip(), name.strip(), manufacturing_line.strip(), status)
        )
        return cursor.lastrowid

def update_product(product_id: int, product_code: str, name: str, manufacturing_line: str, status: str) -> bool:
    """Updates an existing product record."""
    sb = get_supabase_client()
    if sb:
        try:
            sb.table("products").update({
                "product_code": product_code.strip(),
                "name": name.strip(),
                "manufacturing_line": manufacturing_line.strip(),
                "status": status
            }).eq("id", product_id).execute()
            return True
        except Exception as e:
            print(f"Supabase update_product fallback: {e}")

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

    sb = get_supabase_client()
    if sb:
        try:
            sb.table("products").delete().eq("id", product_id).execute()
            return (True, "Product deleted successfully.")
        except Exception as e:
            print(f"Supabase delete_product fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        return (True, "Product deleted successfully.")

# ============================================================================
# 2. PROCESSES CRUD & FULL WORKFLOW
# ============================================================================

def get_all_processes(filter_product_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves processes, optionally filtered by product name."""
    sb = get_supabase_client()
    if sb:
        try:
            query = sb.table("processes").select("id, sequence, name, status, product_id, products(name, product_code), checkpoints(id)").order("sequence")
            data = query.execute().data
            results = []
            for p in data:
                prod_info = p.get("products") or {}
                prod_name = prod_info.get("name", "General")
                if filter_product_name and filter_product_name != "All Products" and prod_name != filter_product_name:
                    continue
                cp_list = p.get("checkpoints") or []
                results.append({
                    "id": p["id"],
                    "sequence": p["sequence"],
                    "process_name": p["name"],
                    "status": p["status"],
                    "product_id": p["product_id"],
                    "product_name": prod_name,
                    "product_code": prod_info.get("product_code", ""),
                    "checkpoint_count": len(cp_list)
                })
            return results
        except Exception as e:
            print(f"Supabase get_all_processes fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if filter_product_name and filter_product_name != "All Products":
            query = """
                SELECT 
                    proc.id, proc.sequence, proc.name AS process_name, proc.status, proc.product_id,
                    prd.name AS product_name, prd.product_code, COUNT(cp.id) AS checkpoint_count
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
                    proc.id, proc.sequence, proc.name AS process_name, proc.status, proc.product_id,
                    prd.name AS product_name, prd.product_code, COUNT(cp.id) AS checkpoint_count
                FROM processes proc
                JOIN products prd ON proc.product_id = prd.id
                LEFT JOIN checkpoints cp ON proc.id = cp.process_id
                GROUP BY proc.id
                ORDER BY prd.id ASC, proc.sequence ASC, proc.id ASC
            """
            cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

def get_process_full_details(process_id: int) -> Optional[Dict[str, Any]]:
    """Fetches full relational details for a process."""
    sb = get_supabase_client()
    if sb:
        try:
            proc_res = sb.table("processes").select("id, name, status, sequence, product_id, products(id, name, product_code)").eq("id", process_id).execute()
            if not proc_res.data:
                return None
            proc = proc_res.data[0]
            prod = proc.get("products") or {}
            
            steps_res = sb.table("process_steps").select("name").eq("process_id", process_id).order("sequence").execute()
            steps = [s["name"] for s in steps_res.data]
            if not steps:
                steps = [f"{proc['name']} Step 1", f"{proc['name']} Step 2"]

            cps_res = sb.table("checkpoints").select("*").eq("process_id", process_id).order("sequence").execute()
            checkpoints = []
            for cp in cps_res.data:
                checkpoints.append({
                    "id": cp["id"],
                    "sequence": cp["sequence"],
                    "name": cp["name"],
                    "process": steps[0] if steps else proc["name"],
                    "doc": cp.get("upload_document_name") or "spec_doc.pdf",
                    "status": cp.get("status") or "Configuration Complete",
                    "summary": cp.get("summary") or f"Quality parameters for {cp['name']}."
                })

            return {
                "id": proc["id"],
                "process_name": proc["name"],
                "status": proc["status"],
                "sequence": proc["sequence"],
                "product_id": proc["product_id"],
                "product_name": prod.get("name", "Product"),
                "product_code": prod.get("product_code", ""),
                "steps": steps,
                "checkpoints": checkpoints
            }
        except Exception as e:
            print(f"Supabase get_process_full_details fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
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
        res = dict(proc_row)
        cursor.execute("SELECT name FROM process_steps WHERE process_id = ? ORDER BY sequence ASC", (process_id,))
        res["steps"] = [r["name"] for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM checkpoints WHERE process_id = ? ORDER BY sequence ASC", (process_id,))
        res["checkpoints"] = [dict(r) for r in cursor.fetchall()]
        return res

def update_full_process_workflow(
    process_id: int, 
    process_name: str, 
    steps: List[str], 
    checkpoints: List[Dict[str, Any]]
) -> bool:
    """Updates process, steps, and checkpoints atomically."""
    sb = get_supabase_client()
    if sb:
        try:
            sb.table("processes").update({"name": process_name.strip()}).eq("id", process_id).execute()
            sb.table("process_steps").delete().eq("process_id", process_id).execute()
            step_inserts = [{"process_id": process_id, "sequence": i, "name": s.strip()} for i, s in enumerate(steps, start=1) if s.strip()]
            if step_inserts:
                sb.table("process_steps").insert(step_inserts).execute()
            
            for idx, cp in enumerate(checkpoints, start=1):
                cp_name = cp.get("name", "").strip()
                if cp_name:
                    cp_id = cp.get("id")
                    cp_doc = cp.get("doc") or cp.get("upload_document_name", None)
                    cp_status = cp.get("status", "Configuration Complete")
                    cp_summary = cp.get("summary", f"Quality gate for {cp_name}.")
                    if isinstance(cp_id, int):
                        sb.table("checkpoints").update({
                            "name": cp_name, "sequence": idx, "upload_document_name": cp_doc,
                            "status": cp_status, "summary": cp_summary
                        }).eq("id", cp_id).execute()
                    else:
                        sb.table("checkpoints").insert({
                            "process_id": process_id, "sequence": idx, "name": cp_name,
                            "upload_document_name": cp_doc, "status": cp_status, "summary": cp_summary
                        }).execute()
            return True
        except Exception as e:
            print(f"Supabase update_full_process_workflow fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE processes SET name = ? WHERE id = ?", (process_name.strip(), process_id))
        cursor.execute("DELETE FROM process_steps WHERE process_id = ?", (process_id,))
        for idx, step_name in enumerate(steps, start=1):
            if step_name.strip():
                cursor.execute("INSERT INTO process_steps (process_id, sequence, name) VALUES (?, ?, ?)", (process_id, idx, step_name.strip()))
        for idx, cp in enumerate(checkpoints, start=1):
            cp_name = cp.get("name", "").strip()
            if cp_name:
                cp_id = cp.get("id")
                cp_doc = cp.get("doc") or cp.get("upload_document_name", None)
                cp_status = cp.get("status", "Configuration Complete")
                cp_summary = cp.get("summary", "")
                if isinstance(cp_id, int):
                    cursor.execute("UPDATE checkpoints SET name=?, sequence=?, upload_document_name=?, status=?, summary=? WHERE id=?", (cp_name, idx, cp_doc, cp_status, cp_summary, cp_id))
                else:
                    cursor.execute("INSERT INTO checkpoints (process_id, sequence, name, upload_document_name, status, summary) VALUES (?, ?, ?, ?, ?, ?)", (process_id, idx, cp_name, cp_doc, cp_status, cp_summary))
        return True

def create_full_process_workflow(
    product_name: str, 
    process_name: str, 
    steps: List[str], 
    checkpoints: List[Dict[str, Any]]
) -> int:
    """Creates a new process, steps, and checkpoints."""
    sb = get_supabase_client()
    if sb:
        try:
            prod_res = sb.table("products").select("id").eq("name", product_name).execute()
            if prod_res.data:
                product_id = prod_res.data[0]["id"]
            else:
                new_prod = sb.table("products").insert({
                    "product_code": f"PRD-{hash(product_name)%1000:03d}",
                    "name": product_name, "manufacturing_line": "General Line", "status": "Active"
                }).execute()
                product_id = new_prod.data[0]["id"]

            max_seq_res = sb.table("processes").select("sequence").eq("product_id", product_id).order("sequence", desc=True).limit(1).execute()
            new_seq = (max_seq_res.data[0]["sequence"] + 1) if max_seq_res.data else 1

            new_proc = sb.table("processes").insert({
                "product_id": product_id, "name": process_name, "sequence": new_seq, "status": "Active"
            }).execute()
            process_id = new_proc.data[0]["id"]

            step_inserts = [{"process_id": process_id, "sequence": i, "name": s.strip()} for i, s in enumerate(steps, start=1) if s.strip()]
            if step_inserts:
                sb.table("process_steps").insert(step_inserts).execute()

            cp_inserts = [{
                "process_id": process_id, "sequence": i, "name": cp.get("name", "").strip(),
                "upload_document_name": cp.get("doc") or cp.get("upload_document_name"),
                "status": cp.get("status", "Configuration Complete"),
                "summary": cp.get("summary", "")
            } for i, cp in enumerate(checkpoints, start=1) if cp.get("name", "").strip()]
            if cp_inserts:
                sb.table("checkpoints").insert(cp_inserts).execute()

            return process_id
        except Exception as e:
            print(f"Supabase create_full_process_workflow fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products WHERE name = ?", (product_name,))
        row = cursor.fetchone()
        product_id = row["id"] if row else 1
        cursor.execute("INSERT INTO processes (product_id, name, sequence, status) VALUES (?, ?, 1, 'Active')", (product_id, process_name))
        return cursor.lastrowid

# ============================================================================
# 3. CHECKPOINTS REPOSITORY
# ============================================================================

def get_checkpoints_for_table() -> List[Dict[str, Any]]:
    """Retrieves all master checkpoints with process and product info."""
    sb = get_supabase_client()
    if sb:
        try:
            cps = sb.table("checkpoints").select("id, sequence, name, upload_document_name, status, summary, processes(name, products(name))").order("id").execute().data
            results = []
            for c in cps:
                proc = c.get("processes") or {}
                prd = proc.get("products") or {}
                results.append({
                    "id": c["id"],
                    "sequence": c["sequence"],
                    "checkpoint_name": c["name"],
                    "process_name": proc.get("name", "Process"),
                    "product_name": prd.get("name", "Product"),
                    "upload_document_name": c.get("upload_document_name"),
                    "status": c.get("status", "Configuration Complete"),
                    "summary": c.get("summary", "")
                })
            return results
        except Exception as e:
            print(f"Supabase get_checkpoints_for_table fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT c.id, c.sequence, c.name AS checkpoint_name, proc.name AS process_name,
                   prd.name AS product_name, c.upload_document_name, c.status, c.summary
            FROM checkpoints c
            JOIN processes proc ON c.process_id = proc.id
            JOIN products prd ON proc.product_id = prd.id
            ORDER BY proc.sequence ASC, c.sequence ASC
        """
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

def get_all_checkpoints_list() -> List[Dict[str, Any]]:
    """Retrieves all checkpoints formatted for dropdown selection."""
    sb = get_supabase_client()
    if sb:
        try:
            cps = sb.table("checkpoints").select("id, name, processes(name, products(name))").order("id").execute().data
            results = []
            for c in cps:
                proc = c.get("processes") or {}
                prd = proc.get("products") or {}
                results.append({
                    "id": c["id"],
                    "checkpoint_name": c["name"],
                    "process_name": proc.get("name", "Process"),
                    "product_name": prd.get("name", "Product")
                })
            return results
        except Exception as e:
            print(f"Supabase get_all_checkpoints_list fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT c.id, c.name AS checkpoint_name, proc.name AS process_name, prd.name AS product_name
            FROM checkpoints c
            JOIN processes proc ON c.process_id = proc.id
            JOIN products prd ON proc.product_id = prd.id
            ORDER BY prd.id ASC, proc.sequence ASC, c.sequence ASC
        """
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

# ============================================================================
# 4. QUALITY DATASETS CRUD (DATA ENTRY & DATA WAREHOUSE & SUPABASE STORAGE)
# ============================================================================

def upload_file_to_supabase_storage(file_name: str, file_bytes: bytes) -> str:
    """Uploads file to Supabase 'quality-files' storage bucket and returns its public URL."""
    sb = get_supabase_client()
    if not sb:
        return ""
    try:
        sb.storage.from_("quality-files").upload(file_name, file_bytes, file_options={"upsert": "true"})
        url = sb.storage.from_("quality-files").get_public_url(file_name)
        return url
    except Exception as e:
        print(f"Supabase storage upload error: {e}")
        return ""

def insert_quality_dataset(
    checkpoint_name: str,
    file_name: str,
    file_size_kb: int = 350,
    uploaded_by_name: str = "Alexander Wright"
) -> int:
    """Inserts an uploaded dataset record tied to a checkpoint."""
    sb = get_supabase_client()
    if sb:
        try:
            cp_res = sb.table("checkpoints").select("id").eq("name", checkpoint_name).limit(1).execute()
            cp_id = cp_res.data[0]["id"] if cp_res.data else 1
            res = sb.table("quality_datasets").insert({
                "checkpoint_id": cp_id,
                "file_name": file_name,
                "file_size_kb": file_size_kb,
                "uploaded_by_name": uploaded_by_name,
                "status": "Processed"
            }).execute()
            return res.data[0]["id"]
        except Exception as e:
            print(f"Supabase insert_quality_dataset fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM checkpoints WHERE name = ?", (checkpoint_name,))
        cp_row = cursor.fetchone()
        checkpoint_id = cp_row["id"] if cp_row else 1
        cursor.execute(
            "INSERT INTO quality_datasets (checkpoint_id, file_name, file_size_kb, uploaded_by_name, status) VALUES (?, ?, ?, ?, ?)",
            (checkpoint_id, file_name, file_size_kb, uploaded_by_name, "Processed")
        )
        return cursor.lastrowid

def update_quality_dataset(dataset_id: int, file_name: str, checkpoint_name: str, uploaded_by_name: str) -> bool:
    """Updates a quality dataset record."""
    sb = get_supabase_client()
    if sb:
        try:
            cp_res = sb.table("checkpoints").select("id").eq("name", checkpoint_name).limit(1).execute()
            cp_id = cp_res.data[0]["id"] if cp_res.data else 1
            sb.table("quality_datasets").update({
                "file_name": file_name.strip(),
                "checkpoint_id": cp_id,
                "uploaded_by_name": uploaded_by_name.strip()
            }).eq("id", dataset_id).execute()
            return True
        except Exception as e:
            print(f"Supabase update_quality_dataset fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM checkpoints WHERE name = ?", (checkpoint_name,))
        cp_row = cursor.fetchone()
        checkpoint_id = cp_row["id"] if cp_row else 1
        cursor.execute(
            "UPDATE quality_datasets SET file_name=?, checkpoint_id=?, uploaded_by_name=? WHERE id=?",
            (file_name.strip(), checkpoint_id, uploaded_by_name.strip(), dataset_id)
        )
        return cursor.rowcount > 0

def delete_quality_dataset(dataset_id: int) -> bool:
    """Deletes a quality dataset record."""
    sb = get_supabase_client()
    if sb:
        try:
            sb.table("quality_datasets").delete().eq("id", dataset_id).execute()
            return True
        except Exception as e:
            print(f"Supabase delete_quality_dataset fallback: {e}")

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
    """Retrieves all quality datasets with filtering."""
    sb = get_supabase_client()
    if sb:
        try:
            query = sb.table("quality_datasets").select("id, file_name, file_size_kb, uploaded_by_name, status, created_at, checkpoints(name, processes(name, products(name)))").order("id", desc=True)
            data = query.execute().data
            results = []
            for d in data:
                cp = d.get("checkpoints") or {}
                cp_name = cp.get("name", "Checkpoint")
                proc = cp.get("processes") or {}
                proc_name = proc.get("name", "Process")
                prd = proc.get("products") or {}
                prd_name = prd.get("name", "Product")

                if product_filter and product_filter != "All Products" and prd_name != product_filter:
                    continue
                if process_filter and process_filter != "All Processes" and proc_name != process_filter:
                    continue
                if checkpoint_filter and checkpoint_filter != "All Checkpoints" and cp_name != checkpoint_filter:
                    continue
                if user_filter and user_filter != "All Users" and user_filter.lower() not in d.get("uploaded_by_name", "").lower():
                    continue

                results.append({
                    "id": d["id"],
                    "file_name": d["file_name"],
                    "file_size_kb": d.get("file_size_kb", 250),
                    "uploaded_by_name": d["uploaded_by_name"],
                    "status": d.get("status", "Processed"),
                    "created_at": d.get("created_at"),
                    "checkpoint_name": cp_name,
                    "process_name": proc_name,
                    "product_name": prd_name
                })
            return results
        except Exception as e:
            print(f"Supabase get_all_datasets fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT d.id, d.file_name, d.file_size_kb, d.uploaded_by_name, d.status, d.created_at,
                   c.name AS checkpoint_name, proc.name AS process_name, prd.name AS product_name
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
    sb = get_supabase_client()
    if sb:
        try:
            return sb.table("users").select("*").order("id").execute().data
        except Exception as e:
            print(f"Supabase get_all_users fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]

def can_delete_user(user_id: int) -> Tuple[bool, int, str]:
    """You CANNOT delete a user if they have contributed quality datasets."""
    sb = get_supabase_client()
    if sb:
        try:
            u_res = sb.table("users").select("name").eq("id", user_id).execute()
            if not u_res.data:
                return (False, 0, "User not found.")
            user_name = u_res.data[0]["name"]
            ds_res = sb.table("quality_datasets").select("id", count="exact").ilike("uploaded_by_name", f"%{user_name}%").execute()
            count = ds_res.count or len(ds_res.data)
            if count > 0:
                return (False, count, f"Cannot delete user '{user_name}': This user has {count} associated data entr{'y' if count == 1 else 'ies'}/uploaded datasets on the platform. Users with active data contributions cannot be deleted.")
            return (True, 0, "")
        except Exception as e:
            print(f"Supabase can_delete_user fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return (False, 0, "User not found.")
        user_name = user_row["name"]
        cursor.execute("SELECT COUNT(*) AS count FROM quality_datasets WHERE uploaded_by_name LIKE ?", (f"%{user_name}%",))
        count = cursor.fetchone()["count"]
        if count > 0:
            return (False, count, f"Cannot delete user '{user_name}': This user has {count} associated data entr{'y' if count == 1 else 'ies'}/uploaded datasets on the platform. Users with active data contributions cannot be deleted.")
        return (True, 0, "")

def insert_user(name: str, email: str, role: str, status: str = "Active") -> int:
    """Creates a new user record."""
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("users").insert({
                "name": name.strip(), "email": email.strip(), "role": role.strip(), "status": status
            }).execute()
            return res.data[0]["id"]
        except Exception as e:
            print(f"Supabase insert_user fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, role, status) VALUES (?, ?, ?, ?)", (name.strip(), email.strip(), role.strip(), status))
        return cursor.lastrowid

def update_user(user_id: int, name: str, email: str, role: str, status: str) -> bool:
    """Updates an existing user record."""
    sb = get_supabase_client()
    if sb:
        try:
            sb.table("users").update({
                "name": name.strip(), "email": email.strip(), "role": role.strip(), "status": status
            }).eq("id", user_id).execute()
            return True
        except Exception as e:
            print(f"Supabase update_user fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET name=?, email=?, role=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (name.strip(), email.strip(), role.strip(), status, user_id))
        return cursor.rowcount > 0

def delete_user(user_id: int) -> Tuple[bool, str]:
    """Deletes a user only if they have no contributed datasets."""
    can_del, count, msg = can_delete_user(user_id)
    if not can_del:
        return (False, msg)

    sb = get_supabase_client()
    if sb:
        try:
            sb.table("users").delete().eq("id", user_id).execute()
            return (True, "User deleted successfully.")
        except Exception as e:
            print(f"Supabase delete_user fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return (True, "User deleted successfully.")

# ============================================================================
# 6. DASHBOARD VERSIONS CRUD
# ============================================================================

def get_all_dashboard_versions() -> List[Dict[str, Any]]:
    """Retrieves all saved dashboard versions."""
    sb = get_supabase_client()
    if sb:
        try:
            return sb.table("dashboard_versions").select("*").order("id", desc=True).execute().data
        except Exception as e:
            print(f"Supabase get_all_dashboard_versions fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dashboard_versions ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_dashboard_version_by_id(version_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single dashboard version by ID."""
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("dashboard_versions").select("*").eq("id", version_id).execute()
            if not res.data:
                return None
            ver = res.data[0]
            try:
                ver["dashboard_data"] = json.loads(ver["dashboard_data_json"])
            except Exception:
                ver["dashboard_data"] = {}
            return ver
        except Exception as e:
            print(f"Supabase get_dashboard_version_by_id fallback: {e}")

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
    """Saves a new dashboard version."""
    serialized_state = {
        "kpis": dashboard_data.get("kpis", {}),
        "ai_narrative": dashboard_data.get("ai_narrative", "")
    }
    
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("dashboard_versions").insert({
                "name": name.strip(),
                "prompt": prompt.strip(),
                "dashboard_data_json": json.dumps(serialized_state),
                "created_by": created_by.strip()
            }).execute()
            return res.data[0]["id"]
        except Exception as e:
            print(f"Supabase save_dashboard_version fallback: {e}")

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
    sb = get_supabase_client()
    if sb:
        try:
            sb.table("dashboard_versions").delete().eq("id", version_id).execute()
            return True
        except Exception as e:
            print(f"Supabase delete_dashboard_version fallback: {e}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dashboard_versions WHERE id = ?", (version_id,))
        return cursor.rowcount > 0
