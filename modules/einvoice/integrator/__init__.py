from .base import BaseIntegrator
from .mock import MockIntegrator

__all__ = ["BaseIntegrator", "MockIntegrator"]


def get_integrator(integrator_name: str, settings: any) -> BaseIntegrator:
    """
    Ayarlara göre doğru entegratör sınıfını döndürür.
    """
    if integrator_name.upper() == "MOCK":
        return MockIntegrator(settings)
    elif integrator_name.upper() == "LOGO":
        # return LogoIntegrator(settings)
        raise NotImplementedError("Logo entegratörü henüz desteklenmiyor.")
    else:
        # Fallback to Mock for development if unknown
        # or raise error
        return MockIntegrator(settings)
