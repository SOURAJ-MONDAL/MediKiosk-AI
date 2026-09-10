import os
import uuid
from typing import Optional
from database.db import get_db

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".doc", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024


class DocumentService:
    @staticmethod
    def upload_document(patient_id: int, title: str, file_bytes: bytes,
                        filename: str, document_type: str = "other",
                        notes: str = "") -> dict:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return {"success": False, "error": f"File type {ext} is not allowed"}
        if len(file_bytes) > MAX_FILE_SIZE:
            return {"success": False, "error": "File size exceeds 10MB limit"}

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)

        try:
            with open(file_path, "wb") as f:
                f.write(file_bytes)
            conn = get_db()
            try:
                cursor = conn.execute(
                    """INSERT INTO documents (patient_id, title, document_type, file_path, file_size, notes)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (patient_id, title, document_type, file_path, len(file_bytes), notes)
                )
                conn.commit()
                return {"success": True, "document_id": cursor.lastrowid}
            finally:
                conn.close()
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_patient_documents(patient_id: int) -> list:
        conn = get_db()
        try:
            docs = conn.execute(
                "SELECT * FROM documents WHERE patient_id = ? ORDER BY uploaded_at DESC",
                (patient_id,)
            ).fetchall()
            return [dict(d) for d in docs]
        finally:
            conn.close()

    @staticmethod
    def delete_document(document_id: int, patient_id: int) -> dict:
        conn = get_db()
        try:
            doc = conn.execute(
                "SELECT * FROM documents WHERE id = ? AND patient_id = ?",
                (document_id, patient_id)
            ).fetchone()
            if not doc:
                return {"success": False, "error": "Document not found"}
            file_path = doc["file_path"]
            if os.path.exists(file_path):
                os.remove(file_path)
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            conn.commit()
            return {"success": True}
        finally:
            conn.close()
