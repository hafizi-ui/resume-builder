<!-- Disalin daripada 'Context Kit dan Spec – Automation Resume v1.1 (DILULUSKAN)', Google Drive › F05-Context-Kit-dan-Spec, 15 Nov 2026. -->

# code-standards

- Kekalkan JavaScript biasa dalam satu IIFE dan gaya kod sedia ada (ES5, `var`, fungsi kecil bernama). Tiada framework baharu tanpa keputusan dalam log.
- Setiap teks pengguna melalui `esc()` sebelum ke `innerHTML`.
- Pustaka luar disimpan dalam `vendor/` dengan versi tetap dan fail lesen.
- Setiap pembetulan pepijat bermula dengan langkah ujian yang gagal dahulu, direkod dalam laporan semakan AC.
- Ujian: tahap Alpha memerlukan setiap AC disemak pada URL sebenar dengan tarikh dan pelayar. Ujian automatik (contoh Playwright) dicadang apabila naik ke Beta.
- Susunan fail selepas F-02: `index.html`, `manifest.webmanifest`, `sw.js`, `icons/`, `vendor/`, `context/`, `README.md`, `LICENSE` ❓ (lesen bergantung pada RG-DEC-10).
- Commit kecil dengan mesej yang menyebut feature dan AC (contoh: "F-01 AC-4: padam semua data").
