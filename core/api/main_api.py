"""
Akıllı İş - REST API (FastAPI)
"""

from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI(title="Akıllı İş ERP API", version="1.0.0")


# === Modeller ===
class Token(BaseModel):
    access_token: str
    token_type: str


class ItemInfo(BaseModel):
    code: str
    name: str
    stock: float
    unit: str


# === Auth ===
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Gerçek uygulamada token doğrulama burada yapılır
    if token == "dev-token":
        return {"username": "admin"}
    raise HTTPException(status_code=401, detail="Geçersiz token")


# === Endpointler ===


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Geliştirme modu için basit login
    if form_data.username == "admin" and form_data.password == "admin":
        return {"access_token": "dev-token", "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Hatalı kullanıcı adı veya şifre")


@app.get("/inventory/stock/{code}", response_model=ItemInfo)
async def get_stock(code: str, user: dict = Depends(get_current_user)):
    """Stok durumunu sorgular"""
    # Veritabanından çekilecek
    return {"code": code, "name": "Örnek Ürün", "stock": 150.5, "unit": "ADET"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}


# Çalıştırmak için: uvicorn core.api.main_api:app --reload
