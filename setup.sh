#!/bin/bash

# Akıllı İş - macOS Kurulum Scripti
# ===================================

set -e

echo "🔄 Akıllı İş - Kurulum Başlıyor..."
echo "=================================="

# Renk tanımları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python versiyonu kontrolü
echo -e "\n${YELLOW}[1/6]${NC} Python versiyonu kontrol ediliyor..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION bulundu"
    
    # Versiyon kontrolü (3.11+)
    REQUIRED_VERSION="3.11"
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        echo -e "${RED}✗${NC} Python 3.11 veya üzeri gerekli!"
        echo "  Homebrew ile yükleyebilirsiniz: brew install python@3.12"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} Python3 bulunamadı!"
    echo "  Homebrew ile yükleyebilirsiniz: brew install python@3.12"
    exit 1
fi

# Virtual environment oluştur
echo -e "\n${YELLOW}[2/6]${NC} Virtual environment oluşturuluyor..."
if [ -d ".venv" ]; then
    echo -e "${YELLOW}!${NC} .venv klasörü zaten mevcut, atlanıyor..."
else
    python3 -m venv .venv
    echo -e "${GREEN}✓${NC} Virtual environment oluşturuldu"
fi

# Activate
echo -e "\n${YELLOW}[3/6]${NC} Virtual environment aktifleştiriliyor..."
source .venv/bin/activate
echo -e "${GREEN}✓${NC} Aktifleştirildi"

# pip güncelle
echo -e "\n${YELLOW}[4/6]${NC} pip güncelleniyor..."
pip install --upgrade pip wheel setuptools --quiet
echo -e "${GREEN}✓${NC} pip güncellendi"

# Bağımlılıkları yükle
echo -e "\n${YELLOW}[5/6]${NC} Bağımlılıklar yükleniyor..."
echo "  Bu işlem birkaç dakika sürebilir..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓${NC} Tüm bağımlılıklar yüklendi"

# .env dosyası oluştur
echo -e "\n${YELLOW}[6/6]${NC} Ortam dosyası hazırlanıyor..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓${NC} .env dosyası oluşturuldu"
    echo -e "${YELLOW}!${NC} .env dosyasını düzenlemeyi unutmayın!"
else
    echo -e "${YELLOW}!${NC} .env dosyası zaten mevcut, atlanıyor..."
fi

# Tamamlandı
echo ""
echo "=================================="
echo -e "${GREEN}✓ Kurulum tamamlandı!${NC}"
echo "=================================="
echo ""
echo "Uygulamayı başlatmak için:"
echo ""
echo "  source .venv/bin/activate"
echo "  python main.py"
echo ""
echo "veya VSCode'da F5 tuşuna basın."
echo ""
