#!/bin/bash
# Test çalıştırma scripti

# Sanal ortam kontrolü (opsiyonel)
# source venv/bin/activate

# Rapor klasorunu olustur
mkdir -p reports

echo "Running tests with coverage..."
source venv/bin/activate
python -m pytest --cov=. --cov-report=html:reports/coverage --cov-report=term-missing

echo "Test run completed. Check reports/coverage/index.html for coverage details."
