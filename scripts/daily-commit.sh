#!/bin/bash

# Akıllı İş - Günlük GitHub Güncelleme Scripti
# =============================================

set -e

# Renk tanımları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Tarih
TODAY=$(date +"%Y-%m-%d")
TIME=$(date +"%H:%M")

echo -e "${BLUE}🔄 Akıllı İş - GitHub Güncelleme${NC}"
echo "=================================="

# Git durumunu kontrol et
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}!${NC} Commit edilecek değişiklik yok."
    exit 0
fi

# Değişiklikleri göster
echo -e "\n${YELLOW}Değişiklikler:${NC}"
git status --short

# Commit mesajı
echo ""
read -p "Commit mesajı (boş bırakırsan otomatik): " COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="📅 Günlük güncelleme - $TODAY $TIME"
fi

# Stage all changes
git add -A

# Commit
git commit -m "$COMMIT_MSG"

# Push
echo -e "\n${YELLOW}GitHub'a gönderiliyor...${NC}"
git push origin main

echo ""
echo -e "${GREEN}✓ Başarıyla güncellendi!${NC}"
echo "  Commit: $COMMIT_MSG"
echo ""
