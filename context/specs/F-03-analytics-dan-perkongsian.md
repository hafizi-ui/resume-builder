<!-- Disalin daripada 'Context Kit dan Spec – Automation Resume v1.1 (DILULUSKAN)', Google Drive › F05-Context-Kit-dan-Spec, 15 Nov 2026. -->

# F-03 Analytics minimum dan perkongsian

**What & Why:** pasukan perlu tahu sama ada pelajar benar-benar menggunakan apps (aktivasi, skor 80+, perkongsian) untuk gerbang validasi, tanpa mengumpul isi resume atau mengenal pasti pelajar.

| AC    | Kriteria                                                                                                                                                                                                                                             | Pengesahan |
|-------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| AC-1  | Acara `first_visit` dihantar sekali bagi setiap storan pelayar. Penanda "sudah dihantar" disimpan dalam localStorage; tiada pengenal pengguna atau peranti dihantar. Selepas storan dikosongkan atau Delete all data, `first_visit` dihantar semula. | ☐          |
| AC-2a | Muat turun PDF, Word atau Print yang pertama menghantar satu acara `activation` dengan `type` = pdf, docx atau print.                                                                                                                                | ☐          |
| AC-2b | Setiap muat turun selepas itu menghantar `download` dengan `type`; tiada `activation` kedua.                                                                                                                                                         | ☐          |
| AC-3a | Kali pertama skor mencapai 80 atau lebih pada storan pelayar itu, acara `score_80` dihantar sekali. (80 ialah pencetus produk untuk gesaan kongsi, bukan ukuran kualiti.)                                                                            | ☐          |
| AC-3b | Pada detik yang sama, mesej kongsi dipaparkan sekali dengan butang "Share with a friend". Ia tidak muncul lagi pada storan pelayar itu.                                                                                                              | ☐          |
| AC-4a | Menekan butang kongsi menghantar `share_clicked`.                                                                                                                                                                                                    | ☐          |
| AC-4b | Jika Web Share tersedia dan perkongsian selesai, `share_completed` dihantar. Jika pengguna membatalkan, tiada `share_completed` dan tiada mesej ralat.                                                                                               | ☐          |
| AC-4c | Jika Web Share tiada, pautan disalin ke papan klip, mesej "Link copied" dipaparkan, dan `link_copied` dihantar.                                                                                                                                      | ☐          |
| AC-5  | Pautan yang dikongsi ialah URL apps ditambah `?src=share` sahaja, tanpa sebarang data pengguna.                                                                                                                                                      | ☐          |
| AC-6  | Lawatan dengan `?src=share` atau `?src=qr` merekod `src` pada acara `first_visit`.                                                                                                                                                                   | ☐          |
| AC-7  | Setiap payload hanya mengandungi: nama acara, `type` (jika ada), `src` (jika ada) dan versi apps. Disemak pada tab Network: tiada isi medan, nama, emel, telefon, foto atau pengenal unik. Alat analytics tidak menetapkan cookie.                   | ☐          |
| AC-8  | Jika analytics disekat atau apps offline, acara dibuang (tidak dibaris gilir), dan apps berfungsi tanpa ralat di konsol yang menjejaskan pengguna.                                                                                                   | ☐          |
| AC-9  | Notis privasi (F-01 AC-2) menyenaraikan acara-acara di atas dan medan yang dihantar, sama dengan AC-7.                                                                                                                                               | ☐          |

**Dari mana nilai datang:** nama acara ditetapkan dalam spec ini; `src` daripada parameter URL; versi apps daripada pemalar dalam kod.

**Keputusan:** D-1 ❓ Alat analytics: mesti percuma atau dalam bajet diluluskan, tanpa cookie, tidak menyimpan alamat IP penuh, dan menyokong acara tersuai. Claude akan menyemak dua atau tiga pilihan selepas pemilik setuju dengan syarat ini. D-2 ✅ Tiada pengenal unik dihantar (RG-DEC-15). D-3 ✅ Print dikira sebagai aktivasi kerana ramai pelajar menyimpan PDF melalui Print.

**Luar skop:** ganjaran rujukan, papan pemuka analytics dalam apps, pengesanan merentas peranti.

**Nota tafsiran:** kerana tiada pengenal, satu pelajar yang memadam data atau menukar pelayar dikira sebagai peranti baharu. Angka ialah anggaran, bukan bilangan pelajar.
