# Ujian penerimaan

Ujian Playwright untuk setiap acceptance criteria (AC) dalam `context/specs/`.

```bash
cd tests
npm install jspdf@2.5.1 docx@8.5.0   # salinan tempatan; ujian tidak bergantung pada CDN
pip install playwright && playwright install chromium
python3 test_f01.py ../index.html   # F-01 Sedia untuk pilot (25 ujian)
python3 test_f04.py ../index.html   # F-04 Resume atau CV (20 ujian)
```

`CHROME_PATH` boleh ditetapkan untuk menggunakan Chrome sedia ada. Keputusan terakhir: 15 Nov 2026, F-01 25/25, F-04 20/20 (Chrome headless, pelayan tempatan).
