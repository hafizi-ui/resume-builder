<!-- Disalin daripada 'Context Kit dan Spec – Automation Resume v1.1 (DILULUSKAN)', Google Drive › F05-Context-Kit-dan-Spec, 15 Nov 2026. -->

# F-02 PWA dan offline

**What & Why:** pelajar boleh memasang apps di telefon dan menggunakannya di makmal atau tempat tanpa internet stabil; apps tidak bergantung kepada CDN luar.

| AC    | Kriteria                                                                                                                                                                                                                                              | Pengesahan |
|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| AC-1a | Selepas satu lawatan dengan internet, apps dibuka dalam mod pesawat.                                                                                                                                                                                  | ☐          |
| AC-1b | Dalam mod pesawat, medan borang boleh disunting dan pratonton dikemas kini.                                                                                                                                                                           | ☐          |
| AC-2  | Dalam mod pesawat, PDF dan Word yang dijana mengandungi suntingan terakhir pengguna.                                                                                                                                                                  | ☐          |
| AC-3  | Semasa memuat apps, menyunting dan memuat turun, tab Network hanya menunjukkan permintaan ke origin apps sendiri dan endpoint analytics yang diluluskan. Tiada permintaan ke cdn.jsdelivr.net, fonts.googleapis.com, fonts.gstatic.com atau hos lain. | ☐          |
| AC-4a | Manifest sah: name "Automation Resume", short_name "A-RESUME", ikon 192 px dan 512 px (termasuk maskable), start_url, display standalone. Lighthouse tidak melaporkan ralat installability.                                                           | ☐          |
| AC-4b | Pada Chrome Android (versi stabil semasa, direkod), menu menawarkan Install app; ikon dan nama yang betul muncul di skrin utama.                                                                                                                      | ☐          |
| AC-4c | Apps yang dipasang dibuka tanpa bar alamat.                                                                                                                                                                                                           | ☐          |
| AC-5a | Prosedur kemas kini: terbitkan versi baharu → buka apps (dalam talian) → muat semula sekali → nombor versi baharu dipaparkan dalam tab How to Use, dan semua medan pengguna kekal.                                                                    | ☐          |
| AC-5b | Jika apps dibuka offline ketika versi baharu sudah diterbitkan, versi lama berfungsi sepenuhnya; versi baharu diambil pada lawatan dalam talian seterusnya.                                                                                           | ☐          |
| AC-5c | Data pengguna di bawah kunci semasa kekal selepas service worker baharu aktif.                                                                                                                                                                        | ☐          |
| AC-6  | Apps dicapai melalui HTTPS yang sah di domain yang diluluskan pemilik, tanpa amaran mixed content.                                                                                                                                                    | ☐          |

**Dari mana nilai datang:** fail pustaka dari pakej npm rasmi jsPDF 2.5.1 dan docx 8.5.0 (lesen MIT); fon Figtree dan Carlito (lesen SIL OFL); ikon ❓.

**Keputusan:** D-1 ⚠️ Hosting statik percuma (contoh GitHub Pages atau Cloudflare Pages) ❓ menunggu pemilik. D-2 ✅ Tiada Google Play/App Store dalam v1 (RG-DEC-08).

**Luar skop:** notifikasi push, segerak latar belakang, pembungkusan Google Play.
