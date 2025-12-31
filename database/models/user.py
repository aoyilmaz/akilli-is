"""
Akıllı İş - Kullanıcı ve Yetkilendirme Modelleri
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Table, Index, JSON
)
from sqlalchemy.orm import relationship

from database.base import Base, BaseModel


# Çoktan çoğa ilişki tabloları
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class User(BaseModel):
    """Kullanıcılar tablosu"""
    __tablename__ = 'users'
    
    # Kimlik bilgileri
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Kişisel bilgiler
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    avatar = Column(String(255), nullable=True)  # Avatar dosya yolu
    
    # Durum
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Tercihler
    language = Column(String(5), default='tr')
    theme = Column(String(20), default='dark')
    preferences = Column(JSON, nullable=True)  # Ek tercihler
    
    # İlişkiler
    roles = relationship('Role', secondary=user_roles, back_populates='users')
    audit_logs = relationship('AuditLog', back_populates='user')
    
    # Index'ler
    __table_args__ = (
        Index('idx_user_name', 'first_name', 'last_name'),
        Index('idx_user_active', 'is_active'),
    )
    
    @property
    def full_name(self) -> str:
        """Tam isim"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def initials(self) -> str:
        """Baş harfler (avatar için)"""
        return f"{self.first_name[0]}{self.last_name[0]}".upper()
    
    def has_permission(self, permission_code: str) -> bool:
        """Kullanıcının belirli bir izni var mı?"""
        if self.is_superuser:
            return True
        for role in self.roles:
            for perm in role.permissions:
                if perm.code == permission_code:
                    return True
        return False
    
    def has_role(self, role_code: str) -> bool:
        """Kullanıcının belirli bir rolü var mı?"""
        return any(role.code == role_code for role in self.roles)
    
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"


class Role(BaseModel):
    """Roller tablosu"""
    __tablename__ = 'roles'
    
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Hiyerarşi (opsiyonel)
    parent_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    level = Column(Integer, default=0)  # Yetki seviyesi
    
    # İlişkiler
    users = relationship('User', secondary=user_roles, back_populates='roles')
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')
    parent = relationship('Role', remote_side='Role.id', backref='children')
    
    def __repr__(self):
        return f"<Role(code={self.code}, name={self.name})>"


class Permission(BaseModel):
    """İzinler tablosu"""
    __tablename__ = 'permissions'
    
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    module = Column(String(50), nullable=False, index=True)  # inventory, sales, finance vb.
    
    # İlişkiler
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')
    
    def __repr__(self):
        return f"<Permission(code={self.code})>"


class AuditLog(BaseModel):
    """İşlem geçmişi tablosu"""
    __tablename__ = 'audit_logs'
    
    # Kim
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    username = Column(String(50), nullable=True)  # User silinse bile kayıt kalsın
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Ne
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    module = Column(String(50), nullable=False)  # inventory, sales vb.
    table_name = Column(String(100), nullable=True)
    record_id = Column(Integer, nullable=True)
    
    # Detay
    old_values = Column(JSON, nullable=True)  # Eski değerler
    new_values = Column(JSON, nullable=True)  # Yeni değerler
    description = Column(Text, nullable=True)
    
    # İlişkiler
    user = relationship('User', back_populates='audit_logs')
    
    # Index'ler
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_module', 'module'),
        Index('idx_audit_date', 'created_at'),
        Index('idx_audit_table_record', 'table_name', 'record_id'),
    )
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, module={self.module}, user={self.username})>"


class Setting(Base):
    """Sistem ayarları tablosu (key-value)"""
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default='string')  # string, integer, boolean, json
    category = Column(String(50), nullable=False, default='general')
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)  # API'de görünür mü
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Index
    __table_args__ = (
        Index('idx_setting_category', 'category'),
    )
    
    def get_typed_value(self):
        """Değeri doğru tipte döndür"""
        if self.value is None:
            return None
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'json':
            import json
            return json.loads(self.value)
        return self.value
    
    def __repr__(self):
        return f"<Setting(key={self.key})>"


class Sequence(Base):
    """Otomatik numara serileri tablosu"""
    __tablename__ = 'sequences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    prefix = Column(String(20), nullable=True)  # FTR, SIP, IE vb.
    suffix = Column(String(20), nullable=True)
    current_value = Column(Integer, default=0, nullable=False)
    step = Column(Integer, default=1)
    min_digits = Column(Integer, default=6)  # Minimum basamak sayısı
    reset_period = Column(String(20), nullable=True)  # yearly, monthly, never
    last_reset = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    def get_next(self) -> str:
        """Sonraki numarayı üret"""
        self.current_value += self.step
        number = str(self.current_value).zfill(self.min_digits)
        
        parts = []
        if self.prefix:
            parts.append(self.prefix)
        parts.append(number)
        if self.suffix:
            parts.append(self.suffix)
        
        return ''.join(parts)
    
    def __repr__(self):
        return f"<Sequence(code={self.code}, current={self.current_value})>"
