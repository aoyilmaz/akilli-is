"""
Akıllı İş - Doküman Yönetim Sistemi Modelleri
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from database.base import BaseModel


class Document(BaseModel):
    """
    Sisteme yüklenen fiziksel dosyaların kayıtları.
    """

    __tablename__ = "documents"

    # Dosya Bilgileri
    filename = Column(String(255), nullable=False)  # Kullanıcının gördüğü isim
    physical_name = Column(String(255), nullable=False)  # Diskteki benzersiz isim
    file_path = Column(String(500), nullable=False)  # Diskteki tam yol (relative)
    file_size = Column(Integer, default=0)  # Byte cinsinden
    mime_type = Column(String(100), nullable=True)  # application/pdf, image/png vs.
    extension = Column(String(20), nullable=True)  # .pdf, .jpg vs.

    # Meta
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # İlişkiler
    uploader = relationship("User", foreign_keys=[created_by])
    relations = relationship(
        "DocumentRelation", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"


class DocumentRelation(BaseModel):
    """
    Bir dokümanın hangi nesneye ait olduğunu tutan ilişki tablosu.
    Polimorfik ilişki yapısı kullanılır.
    """

    __tablename__ = "document_relations"

    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )

    # Hedef Nesne (Polimorfik)
    target_table = Column(
        String(100), nullable=False
    )  # employees, stock_cards, invoices vs.
    target_id = Column(Integer, nullable=False)  # İlgili tablonun ID'si

    # İlişkiler
    document = relationship("Document", back_populates="relations")

    # İndeksler (Sorgu performansı için)
    __table_args__ = (
        Index("idx_doc_relation_target", "target_table", "target_id"),
        Index("idx_doc_relation_document", "document_id"),
    )

    def __repr__(self):
        return f"<DocumentRelation(doc={self.document_id} -> {self.target_table}:{self.target_id})>"
