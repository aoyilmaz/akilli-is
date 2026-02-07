from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.base import get_session
from database.models.fixed_asset import (
    FixedAsset,
    DepreciationEntry,
    DepreciationMethod,
    AssetStatus,
)


class FixedAssetService:
    def __init__(self, session: Session = None):
        self.session = session or get_session()

    def create_asset(self, data: Dict[str, Any]) -> FixedAsset:
        """Yeni bir demirbaş kartı oluşturur."""
        asset = FixedAsset(**data)
        self.session.add(asset)
        self.session.flush()
        return asset

    def update_asset(self, asset_id: int, data: Dict[str, Any]) -> Optional[FixedAsset]:
        """Demirbaş kartını günceller."""
        asset = self.get_asset(asset_id)
        if not asset:
            return None

        for key, value in data.items():
            if hasattr(asset, key):
                setattr(asset, key, value)

        self.session.flush()
        return asset

    def delete_asset(self, asset_id: int) -> bool:
        """Demirbaş kartını siler."""
        asset = self.get_asset(asset_id)
        if not asset:
            return False

        self.session.delete(asset)
        self.session.flush()
        return True

    def get_asset(self, asset_id: int) -> Optional[FixedAsset]:
        """ID'ye göre demirbaş getirir."""
        return self.session.query(FixedAsset).get(asset_id)

    def get_all_assets(self) -> List[FixedAsset]:
        """Tüm demirbaşları listeler."""
        return (
            self.session.query(FixedAsset).order_by(desc(FixedAsset.created_at)).all()
        )

    def calculate_depreciation(
        self, asset_id: int, period_date: date
    ) -> Optional[DepreciationEntry]:
        """
        Belirtilen demirbaş için amortisman hesaplar.
        Şimdilik sadece 'Straight Line' (Eşit Tutarlı) yöntemi desteklenmektedir.
        """
        asset = self.get_asset(asset_id)
        if not asset or asset.status != AssetStatus.ACTIVE:
            return None

        if asset.depreciation_method == DepreciationMethod.NO_DEPRECIATION:
            return None

        # Daha önce bu dönem için hesaplanmış mı kontrol et
        existing = (
            self.session.query(DepreciationEntry)
            .filter_by(fixed_asset_id=asset.id, period=period_date)
            .first()
        )
        if existing:
            return existing

        # Toplam birikmiş amortismanı bul
        accumulated = sum(e.amount for e in asset.depreciation_entries)

        # Amortisman hesaplama (Yıllık basit hesap)
        # TODO: Aylık/Kıst amortisman mantığı eklenebilir.
        # Bu basit versiyonda yıllık tutar / 1 (Yıl sonu işlemi varsayıyoruz)

        cost = asset.purchase_price
        salvage = asset.salvage_value or 0.0
        life = asset.useful_life_years

        if life <= 0:
            return None

        annual_depreciation = (cost - salvage) / life

        # Bu yıl için kalan değer
        remaining_value = cost - accumulated

        amount = min(annual_depreciation, remaining_value)

        if amount <= 0:
            return None

        new_accumulated = accumulated + amount
        new_book_value = cost - new_accumulated

        entry = DepreciationEntry(
            fixed_asset_id=asset.id,
            period=period_date,
            amount=amount,
            accumulated_amount=new_accumulated,
            book_value=new_book_value,
            description=f"{period_date.year} Yılı Amortismanı",
        )

        self.session.add(entry)

        # Asset'in güncel değerini güncelle
        asset.current_value = new_book_value

        self.session.flush()
        return entry
