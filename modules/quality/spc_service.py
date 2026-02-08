"""
Akıllı İş - SPC (İstatistiksel Proses Kontrol) Servisi
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from database.base import get_session
from database.models.quality import (
    InspectionCriteria,
    InspectionResult,
    SPCObservation,
    SPCControlLimit,
)


class SPCService:
    """
    İstatistiksel Proses Kontrol (SPC) hesaplamaları ve veri yönetimi.
    """

    def __init__(self, db: Session = None):
        self.db = db or get_session()

    def add_observations(self, result_id: int, values: List[float]):
        """
        Bir kontrol sonucuna ait çoklu gözlem değerlerini kaydeder.
        """
        # Mevcut gözlemleri temizle (eğer güncelleme ise)
        self.db.query(SPCObservation).filter(
            SPCObservation.result_id == result_id
        ).delete()

        for idx, val in enumerate(values):
            obs = SPCObservation(result_id=result_id, observation_no=idx + 1, value=val)
            self.db.add(obs)
        self.db.commit()

    def get_process_stats(self, criteria_id: int) -> Optional[Dict]:
        """
        Cp, Cpk ve temel istatistikleri hesaplar.
        """
        criteria = self.db.query(InspectionCriteria).get(criteria_id)
        if not criteria:
            return None

        # Son gözlemleri al
        observations = (
            self.db.query(SPCObservation.value)
            .join(InspectionResult)
            .filter(InspectionResult.criteria_id == criteria_id)
            .order_by(desc(InspectionResult.created_at))
            .limit(250)  # Son 250 ölçüm noktası
            .all()
        )

        if not observations or len(observations) < 10:
            return None

        all_values = [float(v[0]) for v in observations]
        data = np.array(all_values)

        mean = np.mean(data)
        std = np.std(data, ddof=1)  # Örneklem standart sapması

        # Tolerans limitleri
        usl = (
            float(criteria.tolerance_max)
            if criteria.tolerance_max is not None
            else None
        )
        lsl = (
            float(criteria.tolerance_min)
            if criteria.tolerance_min is not None
            else None
        )

        # Cp: (USL - LSL) / 6s
        cp = None
        if usl is not None and lsl is not None:
            if std > 0:
                cp = (usl - lsl) / (6 * std)
            else:
                cp = 0

        # Cpk: min( (USL - mean)/3s , (mean - LSL)/3s )
        cpk = None
        if std > 0:
            if usl is not None and lsl is not None:
                cpk_u = (usl - mean) / (3 * std)
                cpk_l = (mean - lsl) / (3 * std)
                cpk = min(cpk_u, cpk_l)
            elif usl is not None:
                cpk = (usl - mean) / (3 * std)
            elif lsl is not None:
                cpk = (mean - lsl) / (3 * std)
        else:
            cpk = 0

        return {
            "mean": round(mean, 4),
            "std": round(std, 4),
            "min": round(np.min(data), 4),
            "max": round(np.max(data), 4),
            "cp": round(cp, 3) if cp is not None else None,
            "cpk": round(cpk, 3) if cpk is not None else None,
            "count": len(all_values),
        }

    def get_control_chart_data(self, criteria_id: int, limit: int = 30) -> List[Dict]:
        """
        X-bar (Ortalama) ve R (Range) grafiği için veri hazırlar.
        """
        # Sonuçları ve onlara bağlı gözlemleri getir
        results = (
            self.db.query(InspectionResult)
            .filter(InspectionResult.criteria_id == criteria_id)
            .order_by(desc(InspectionResult.created_at))
            .limit(limit)
            .all()
        )
        results.reverse()  # Kronolojik sıra

        chart_points = []
        for r in results:
            vals = [float(o.value) for o in r.observations]
            if not vals:
                continue

            x_bar = np.mean(vals)
            r_val = np.ptp(vals)  # Peak-to-peak (max - min)

            chart_points.append(
                {
                    "inspection_no": (
                        r.inspection.inspection_no if r.inspection else str(r.id)
                    ),
                    "timestamp": r.created_at.strftime("%d.%m %H:%M"),
                    "x_bar": round(x_bar, 4),
                    "r": round(r_val, 4),
                    "is_passed": r.is_passed,
                }
            )

        return chart_points

    def calculate_control_limits(self, criteria_id: int):
        """
        Geçmiş verilere dayanarak kontrol limitlerini (UCL, LCL) hesaplar.
        """
        data = self.get_control_chart_data(criteria_id, limit=50)
        if len(data) < 10:
            return None

        x_bars = [p["x_bar"] for p in data]
        ranges = [p["r"] for p in data]

        grand_mean = np.mean(x_bars)
        avg_range = np.mean(ranges)

        # Basit X-bar kontrol limitleri (A2 katsayısı yaklaşık 0.577, n=5 için)
        # Gerçek uygulamada n (örneklem büyüklüğü) değişken olabilir.
        # Şimdilik standart s (sigma/3) yaklaşımı kullanalım.
        all_obs = []
        results = (
            self.db.query(InspectionResult)
            .filter(InspectionResult.criteria_id == criteria_id)
            .all()
        )
        for r in results:
            all_obs.extend([float(o.value) for o in r.observations])

        if not all_obs:
            return None

        sigma = np.std(all_obs, ddof=1)
        ucl = grand_mean + (3 * sigma)
        lcl = grand_mean - (3 * sigma)

        return {"ucl": round(ucl, 4), "lcl": round(lcl, 4), "cl": round(grand_mean, 4)}
