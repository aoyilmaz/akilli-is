"""
Akıllı İş - Geliştirme Modülü Services
Hata Yönetimi ve Loglama
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_

from database.base import get_session
from database.models.development import ErrorLog, ErrorSeverity


class ErrorLogService:
    """Hata kayıt servisi"""

    def __init__(self):
        self.session = get_session()

    def create(self, **data) -> ErrorLog:
        """Yeni hata kaydı oluştur"""
        error_log = ErrorLog(**data)
        self.session.add(error_log)
        self.session.commit()
        return error_log

    def get_all(
        self,
        module: str = None,
        severity: ErrorSeverity = None,
        is_resolved: bool = None,
        user_id: int = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ErrorLog]:
        """Hata kayıtlarını listele (filtreleme ile)"""
        query = self.session.query(ErrorLog)

        # Filtreler
        filters = []
        if module:
            filters.append(ErrorLog.module_name == module)
        if severity:
            filters.append(ErrorLog.severity == severity)
        if is_resolved is not None:
            filters.append(ErrorLog.is_resolved == is_resolved)
        if user_id:
            filters.append(ErrorLog.user_id == user_id)
        if start_date:
            filters.append(ErrorLog.created_at >= start_date)
        if end_date:
            filters.append(ErrorLog.created_at <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        return query.order_by(ErrorLog.created_at.desc()).offset(offset).limit(limit).all()

    def get_by_id(self, error_id: int) -> Optional[ErrorLog]:
        """ID ile hata kaydı getir"""
        return self.session.query(ErrorLog).filter(ErrorLog.id == error_id).first()

    def resolve(self, error_id: int, notes: str, user_id: int) -> Optional[ErrorLog]:
        """Hatayı çözüme işaretle"""
        error = self.get_by_id(error_id)
        if error:
            error.is_resolved = True
            error.resolved_at = datetime.now()
            error.resolved_by = user_id
            error.resolution_notes = notes
            self.session.commit()
        return error

    def unresolve(self, error_id: int) -> Optional[ErrorLog]:
        """Hata çözümünü geri al"""
        error = self.get_by_id(error_id)
        if error:
            error.is_resolved = False
            error.resolved_at = None
            error.resolved_by = None
            error.resolution_notes = None
            self.session.commit()
        return error

    def get_statistics(self, module: str = None, days: int = 7) -> dict:
        """İstatistikler (son N gün)"""
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)

        query = self.session.query(ErrorLog).filter(ErrorLog.created_at >= start_date)
        if module:
            query = query.filter(ErrorLog.module_name == module)

        all_errors = query.all()

        stats = {
            'total': len(all_errors),
            'resolved': len([e for e in all_errors if e.is_resolved]),
            'unresolved': len([e for e in all_errors if not e.is_resolved]),
            'by_severity': {
                'critical': len([e for e in all_errors if e.severity == ErrorSeverity.CRITICAL]),
                'error': len([e for e in all_errors if e.severity == ErrorSeverity.ERROR]),
                'warning': len([e for e in all_errors if e.severity == ErrorSeverity.WARNING]),
                'info': len([e for e in all_errors if e.severity == ErrorSeverity.INFO]),
            },
            'by_module': {},
        }

        # Modül bazında sayım
        for error in all_errors:
            module_name = error.module_name or 'unknown'
            if module_name not in stats['by_module']:
                stats['by_module'][module_name] = 0
            stats['by_module'][module_name] += 1

        return stats

    def delete(self, error_id: int) -> bool:
        """Hata kaydını sil"""
        error = self.get_by_id(error_id)
        if error:
            self.session.delete(error)
            self.session.commit()
            return True
        return False
