import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from database.models.dms import Document, DocumentRelation
from database.models.user import AuditLog
from modules.system.services.company_service import (
    CompanyService,
)  # Örnek kullanım için, gerekirse kaldırılabilir


class DMSService:
    UPLOAD_DIR = "assets/uploads"
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx"}
    MAX_FILE_SIZE_MB = 10

    @staticmethod
    def _ensure_upload_dir():
        """Upload klasörünün varlığından emin olur."""
        if not os.path.exists(DMSService.UPLOAD_DIR):
            os.makedirs(DMSService.UPLOAD_DIR)

    @staticmethod
    def _validate_file(filename: str, file_size: int):
        """Dosya uzantısı ve boyutunu kontrol eder."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in DMSService.ALLOWED_EXTENSIONS:
            raise ValueError(f"İzin verilmeyen dosya uzantısı: {ext}")

        if file_size > DMSService.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(
                f"Dosya boyutu çok büyük. Maksimum: {DMSService.MAX_FILE_SIZE_MB}MB"
            )

    @staticmethod
    def upload_document(
        session: Session,
        file_bytes: bytes,
        filename: str,
        target_table: str,
        target_id: int,
        user_id: int,
    ) -> Document:
        """
        Dosyayı diske kaydeder ve veritabanı kayıtlarını oluşturur.
        """
        DMSService._ensure_upload_dir()
        DMSService._validate_file(filename, len(file_bytes))

        # Benzersiz dosya ismi oluştur
        ext = os.path.splitext(filename)[1].lower()
        physical_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(DMSService.UPLOAD_DIR, physical_name)

        # Dosyayı diske yaz
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # DB Kaydı - Document
        new_doc = Document(
            filename=filename,
            physical_name=physical_name,
            file_path=file_path,
            file_size=len(file_bytes),
            mime_type=ext[1:],  # Basit mime type
            extension=ext,
            created_by=user_id,
        )
        session.add(new_doc)
        session.flush()  # ID alması için

        # DB Kaydı - DocumentRelation
        new_relation = DocumentRelation(
            document_id=new_doc.id, target_table=target_table, target_id=target_id
        )
        session.add(new_relation)

        # Audit Log
        audit = AuditLog(
            user_id=user_id,
            action="upload_document",
            table_name="documents",
            record_id=new_doc.id,
            details=f"Dosya yüklendi: {filename} -> {target_table}:{target_id}",
        )
        session.add(audit)

        return new_doc

    @staticmethod
    def get_documents_for_object(
        session: Session, target_table: str, target_id: int
    ) -> List[Document]:
        """
        İlgili nesneye bağlı dokümanları getirir.
        """
        return (
            session.query(Document)
            .join(DocumentRelation)
            .filter(
                DocumentRelation.target_table == target_table,
                DocumentRelation.target_id == target_id,
            )
            .all()
        )

    @staticmethod
    def delete_document(session: Session, doc_id: int, user_id: int):
        """
        Dokümanı sistemden siler (disk + db).
        """
        doc = session.query(Document).get(doc_id)
        if not doc:
            raise ValueError("Doküman bulunamadı")

        # İlişkileri ve dokümanı sil (Cascade delete varsa relations otomatik silinir,
        # ama dosya silme işlemi manuel yapılmalı)

        # Fiziksel dosyayı sil
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        # DB'den sil
        session.delete(doc)

        # Audit Log
        audit = AuditLog(
            user_id=user_id,
            action="delete_document",
            table_name="documents",
            record_id=doc_id,
            details=f"Dosya silindi: {doc.filename}",
        )
        session.add(audit)
