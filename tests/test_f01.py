"""Ujian penerimaan F-01 (Sedia untuk pilot) - Automation Resume.

Guna: python3 -I test_f01.py <path/to/index.html>
Apps dihidangkan melalui http://127.0.0.1:<port>/ supaya localStorage berkelakuan seperti laman sebenar.
Pustaka jsPDF dan docx dihidangkan dari salinan npm tempatan (rangkaian sandbox tidak membenarkan CDN).
"""
import sys, os, json, re, threading, zipfile, io, http.server, socketserver, functools, datetime
from playwright.sync_api import sync_playwright

APP = os.path.abspath(sys.argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
VENDOR = os.environ.get("RG_VENDOR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_modules"))
CHROME = os.environ.get("CHROME_PATH") or None
KEYS = json.load(open(os.path.join(FIX, "keys.json")))
import hashlib
# Hashes (SHA-256, 16 hex) of identifying words from the old example. The words themselves are not stored here.
ORIGINAL_ID_HASHES = ['2e1ca453807dfe03', '723a481e40ff2d01', '12733c796a8dfa39']
FIXTURE = {"name": "NUR AISYAH BINTI CONTOH", "phone": "+60 12-000 0000",
           "email": "nur.aisyah.contoh@example.com", "linkedin": "linkedin.com/in/contoh-pelajar"}
WARN = "Using a lab or shared computer? Press Delete all data when you finish."

serve_dir = os.path.dirname(APP)
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=serve_dir)
Handler.log_message = lambda *a: None
httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
PORT = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/%s" % (PORT, os.path.basename(APP))

results = []
def check(ac, ok, detail=""):
    results.append((ac, bool(ok), detail))

def route_libs(page, block_cdn=False):
    def handle(route):
        u = route.request.url
        if block_cdn:
            return route.abort()
        if "jspdf" in u:
            return route.fulfill(path=VENDOR + "/jspdf/dist/jspdf.umd.min.js", content_type="application/javascript")
        if "docx" in u:
            return route.fulfill(path=VENDOR + "/docx/build/index.umd.js", content_type="application/javascript")
        return route.abort()
    page.route("https://cdn.jsdelivr.net/**", handle)
    page.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(body="", content_type="text/css"))
    page.route("https://fonts.gstatic.com/**", lambda r: r.abort())

def fresh(browser, block_cdn=False):
    ctx = browser.new_context(accept_downloads=True)
    page = ctx.new_page()
    route_libs(page, block_cdn)
    page.goto(URL); page.wait_for_timeout(500)
    return ctx, page

def ls_keys(page):
    return page.evaluate("Object.keys(localStorage)")

def profile_text(page):
    return page.inner_text("#paperFull .r-text") if page.query_selector("#paperFull .r-text") else ""

def set_field(page, key, value):
    page.evaluate("""([k,v]) => { const t = document.querySelector('[data-tab="form"]'); if (t) t.click(); }""", [key, value])
    page.fill("#f_" + key, value)
    page.wait_for_timeout(250)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    src = open(APP, encoding="utf-8").read()

    # ---------- AC-1 fixture ----------
    ctx, pg = fresh(b)
    nm = pg.inner_text("#paperFull .r-name")
    contact = pg.inner_text("#paperFull .r-contact")
    ok = nm == FIXTURE["name"] and all(FIXTURE[k] in contact for k in ("phone", "email", "linkedin"))
    leaked = sorted({h for h in (hashlib.sha256(w.encode()).hexdigest()[:16] for w in re.findall(r"\w+", src.lower())) if h in ORIGINAL_ID_HASHES})
    check("AC-1", ok and not leaked, "nama=%r; bilangan pengenal asal dalam kod=%d" % (nm, len(leaked)))
    check("Regresi: skor contoh 100", "100" in pg.inner_text("#scoreChipText"), pg.inner_text("#scoreChipText"))

    # ---------- AC-2 privacy ----------
    priv = pg.query_selector("header >> text=Privacy")
    txt = ""
    if priv:
        priv.click(); pg.wait_for_timeout(200)
        el = pg.query_selector("#panel-privacy")
        txt = el.inner_text() if el and el.is_visible() else ""
    need = ["only in this browser", "not sent to our server", "does not collect or send usage analytics", "may receive your internet (IP) address", "Delete all data on this device"]
    check("AC-2", priv is not None and all(n.lower() in txt.lower() for n in need), "pautan=%s; frasa hilang=%s" % (bool(priv), [n for n in need if n.lower() not in txt.lower()]))

    # ---------- AC-3a / 3b warning ----------
    w = pg.query_selector("#sharedWarn")
    check("AC-3a", w is not None and w.is_visible() and WARN in w.inner_text(), "")
    ok3b = False
    if w:
        pg.click("#sharedWarn [data-action='warn-ok']"); pg.wait_for_timeout(150)
        pg.reload(); pg.wait_for_timeout(400)
        hidden_after = not pg.is_visible("#sharedWarn")
        pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(400)
        back_after_clear = pg.is_visible("#sharedWarn")
        ok3b = hidden_after and back_after_clear
    check("AC-3b (tutup / kosongkan storan)", ok3b, "")
    ctx.close()

    # ---------- AC-4a / 4b delete all ----------
    ctx, pg = fresh(b)
    set_field(pg, "name", "PELAJAR UJIAN")
    pg.set_input_files("#photoInput", os.path.join(FIX, "..", "fixtures", "photo.png")) if os.path.exists(os.path.join(FIX, "photo.png")) else None
    pg.click('[data-tab="coach"]'); pg.wait_for_timeout(200)
    pg.click('[data-tab="form"]'); pg.wait_for_timeout(200)
    has_data_before = any(("automation-resume" in k) for k in ls_keys(pg))
    btn = pg.query_selector('[data-action="delete-all"]')
    ok4a = False; ok3b_del = False; ok4b = False
    if btn:
        btn.click(); pg.wait_for_timeout(100)
        armed = "again" in btn.inner_text().lower()
        with pg.expect_navigation():
            btn.click()
        pg.wait_for_timeout(400)
        # After reload the app may write the warning flag only when dismissed; data key must be absent until user types.
        keys_after = ls_keys(pg)
        sess = pg.evaluate("Object.keys(sessionStorage)")
        data_keys = [k for k in keys_after if ("automation-resume" in k)]
        ok4a = armed and has_data_before and not data_keys and not any("tab" in k for k in sess)
        ok3b_del = pg.is_visible("#sharedWarn")
        pg2 = ctx.new_page(); route_libs(pg2); pg2.goto(URL); pg2.wait_for_timeout(400)
        ok4b = pg2.inner_text("#paperFull .r-name") == FIXTURE["name"] and pg2.is_visible("#exampleNotice")
        check("AC-4a", ok4a, "minta pengesahan=%s; kunci tinggal=%s; session=%s" % (armed, data_keys, sess))
    else:
        check("AC-4a", False, "butang tiada")
    check("AC-3b (selepas Delete all data)", ok3b_del, "")
    check("AC-4b", ok4b, "")
    ctx.close()

    # ---------- AC-5a/5b/5c/5d branding ----------
    ctx, pg = fresh(b)
    check("AC-5a", pg.title() == "Automation Resume", pg.title())
    check("AC-5b", pg.inner_text(".brand").startswith("Automation Resume"), pg.inner_text(".brand")[:40])
    creator = None
    try:
        with pg.expect_download(timeout=15000) as dl:
            pg.click('#panel-form [data-action="docx"]')
        data = open(dl.value.path(), "rb").read()
        core = zipfile.ZipFile(io.BytesIO(data)).read("docProps/core.xml").decode()
        m = re.search(r"<dc:creator>(.*?)</dc:creator>", core); creator = m and m.group(1)
    except Exception as e:
        creator = "ralat: %s" % e
    check("AC-5c", creator == "Automation Resume", "dc:creator=%r" % creator)
    try:
        with pg.expect_download(timeout=10000) as dl:
            pg.click('[data-action="backup"]')
        fn = dl.value.suggested_filename
        js = json.load(open(dl.value.path()))
        check("AC-5d", fn.endswith("_Resume_backup.json") and js.get("app") == "automation-resume", "fail=%s app=%s" % (fn, js.get("app")))
    except Exception as e:
        check("AC-5d", False, str(e))
    try:
        with pg.expect_download(timeout=15000) as dl:
            pg.click('#panel-form [data-action="pdf"]')
        head = open(dl.value.path(), "rb").read(5)
        check("Regresi: PDF dijana", head == b"%PDF-", repr(head))
    except Exception as e:
        check("Regresi: PDF dijana", False, str(e))
    ctx.close()

    # ---------- AC-10 tiada rujukan institusi tertentu (disemak melalui hash perkataan) ----------
    inst = [w for w in re.findall(r"\w+", src.lower()) if hashlib.sha256(w.encode()).hexdigest()[:16] == '94a399ecdcbdf618']
    check("AC-10 Tiada rujukan institusi tertentu dalam apps", not inst, "jumpa=%d" % len(inst))

    # ---------- AC-6b / 6c backups ----------
    ctx, pg = fresh(b)
    pg.set_input_files("#jsonInput", os.path.join(FIX, "old_backup.json")); pg.wait_for_timeout(500)
    vals = {k: pg.input_value("#f_" + k) for k in KEYS}
    bad = [k for k, v in vals.items() if v != "v_" + k]
    photo_ok = pg.evaluate("!!document.querySelector('#paperFull .r-photo') === false")  # showPhoto false hides the photo box
    show_unchecked = not pg.is_checked("#showPhoto")
    check("AC-6b", not bad and show_unchecked and photo_ok, "medan salah=%d; showPhoto off=%s" % (len(bad), show_unchecked))
    pg.set_input_files("#jsonInput", os.path.join(FIX, "extra_backup.json")); pg.wait_for_timeout(400)
    ok_extra = pg.input_value("#f_name") == "v_name"
    pg.fill("#f_name", "KEEP ME"); pg.wait_for_timeout(250)
    pg.set_input_files("#jsonInput", os.path.join(FIX, "not_backup.json")); pg.wait_for_timeout(400)
    t1 = pg.inner_text("#toast"); keep1 = pg.input_value("#f_name") == "KEEP ME"
    pg.set_input_files("#jsonInput", os.path.join(FIX, "other_app.json")); pg.wait_for_timeout(400)
    t2 = pg.inner_text("#toast"); keep2 = pg.input_value("#f_name") == "KEEP ME"
    check("AC-6c", ok_extra and keep1 and keep2 and "isn't" in t1 and "isn't" in t2, "medan tambahan diabaikan=%s; fail bukan backup dikekal=%s; app lain dikekal=%s" % (ok_extra, keep1, keep2))
    ctx.close()

    # ---------- AC-7a / 7b score ----------
    ctx, pg = fresh(b)
    pg.click('[data-tab="coach"]'); pg.wait_for_timeout(200)
    card = pg.inner_text("#scoreCard")
    check("AC-7a", "Resume checklist score" in card and "Checks completeness. Not a guarantee of passing ATS or interviews." in card, card[:120].replace("\n", " | "))
    before = pg.inner_text("#scoreNum")
    pg.click('[data-tab="form"]'); pg.fill("#f_email", ""); pg.wait_for_timeout(1000)
    after = pg.inner_text("#scoreNum")
    check("AC-7b", before != after, "%s -> %s dalam 1 s" % (before, after))
    ctx.close()

    # ---------- AC-8a / 8b downloads ----------
    check("AC-8a", "sign in to claude" not in src.lower() and "sign in" not in src.lower(), "")
    ctx, pg = fresh(b, block_cdn=True)
    pg.evaluate("window.__printed = 0; window.print = () => { window.__printed++; }; true")
    pg.click('#panel-form [data-action="pdf"]'); pg.wait_for_timeout(1200)
    toast = pg.inner_text("#toast")
    pg.click('#panel-form [data-action="print"]'); pg.wait_for_timeout(500)
    printed = pg.evaluate("window.__printed")
    check("AC-8b", "Print / Save as PDF" in toast and printed == 1, "toast=%r; print dipanggil=%s" % (toast, printed))
    ctx.close()

    # ---------- AC-9 profile sentence ----------
    ctx, pg = fresh(b)
    pg.fill("#f_period", "1 March 2027 to 28 May 2027"); pg.fill("#f_aim", "support daily IT operations")
    pg.fill("#f_role", "IT Support"); pg.wait_for_timeout(300)
    t_it = profile_text(pg)
    pg.fill("#f_role", "Admin"); pg.wait_for_timeout(300)
    t_ad = profile_text(pg)
    pg.fill("#f_role", "Human Resource"); pg.wait_for_timeout(300)
    t_hr = profile_text(pg)
    pg.fill("#f_role", ""); pg.wait_for_timeout(300)
    t_none = profile_text(pg)
    ok9 = ("Seeking an internship in IT Support from 1 March 2027 to 28 May 2027 to support daily IT operations." in t_it
           and "Seeking an internship in Admin from" in t_ad and "Seeking an internship in Human Resource from" in t_hr
           and "Seeking" not in t_none and "Seeking a IT" not in t_it)
    m = re.search(r"Seeking[^.]*\.", t_it)
    check("AC-9", ok9, "IT Support -> %r" % (m.group(0) if m else t_it[-80:]))
    ctx.close()

    # ---------- Semakan kedua ChatGPT: ujian tambahan ----------
    # (a) storan lain kosong; klik kedua selepas tamat tempoh tidak memadam
    ctx, pg = fresh(b)
    set_field(pg, "name", "PELAJAR UJIAN")
    other = pg.evaluate("""async () => ({ idb: (indexedDB.databases ? (await indexedDB.databases()).length : 0),
                                          caches: ('caches' in window) ? (await caches.keys()).length : 0, cookie: document.cookie })""")
    check("Tambahan: tiada IndexedDB/Cache/cookie digunakan", other["idb"] == 0 and other["caches"] == 0 and other["cookie"] == "", str(other))
    btn = pg.query_selector('#panel-form [data-action="delete-all"]')
    btn.click(); pg.wait_for_timeout(3800); btn.click(); pg.wait_for_timeout(400)
    still = pg.input_value("#f_name") == "PELAJAR UJIAN" and "again" in btn.inner_text().lower()
    check("Tambahan: klik kedua selepas 3.5 s hanya meminta pengesahan semula", still, btn.inner_text())
    ctx.close()
    # (a) tutup dan buka semula pelayar sebenar (profil berterusan)
    import tempfile
    prof = tempfile.mkdtemp()
    pc = p.chromium.launch_persistent_context(prof, executable_path=CHROME, args=["--no-sandbox"])
    pp = pc.new_page(); route_libs(pp); pp.goto(URL); pp.wait_for_timeout(400)
    pp.fill("#f_name", "SIMPAN DULU"); pp.wait_for_timeout(300)
    bb = pp.query_selector('#panel-form [data-action="delete-all"]'); bb.click()
    with pp.expect_navigation(): bb.click()
    pc.close()
    pc = p.chromium.launch_persistent_context(prof, executable_path=CHROME, args=["--no-sandbox"])
    pp = pc.new_page(); route_libs(pp); pp.goto(URL); pp.wait_for_timeout(400)
    check("Tambahan: selepas tutup/buka pelayar, data hilang", pp.inner_text("#paperFull .r-name") == FIXTURE["name"], pp.inner_text("#paperFull .r-name"))
    pc.close()
    # (c) backup: struktur rosak ditolak tanpa mengubah borang
    ctx, pg = fresh(b)
    pg.fill("#f_name", "KEEP ME"); pg.wait_for_timeout(250)
    cases = {
        "data_array": {"app": "automation-resume", "data": ["x"]},
        "nilai_bukan_teks": {"app": "automation-resume", "data": {"name": 123}},
        "tiada_medan_dikenali": {"app": "automation-resume", "data": {"foo": "bar"}},
        "foto_tidak_sah": {"app": "automation-resume", "data": {"name": "X"}, "photo": "javascript:alert(1)"},
    }
    bad = []
    for nm_, obj in cases.items():
        fp = os.path.join(FIX, "bad_%s.json" % nm_); json.dump(obj, open(fp, "w"))
        pg.set_input_files("#jsonInput", fp); pg.wait_for_timeout(300)
        if pg.input_value("#f_name") != "KEEP ME" or "isn't" not in pg.inner_text("#toast"): bad.append(nm_)
    big = os.path.join(FIX, "big.json")
    with open(big, "w") as f: f.write('{"app":"automation-resume","data":{"name":"' + "x" * (6 * 1024 * 1024) + '"}}')
    pg.set_input_files("#jsonInput", big); pg.wait_for_timeout(600)
    if pg.input_value("#f_name") != "KEEP ME" or "too large" not in pg.inner_text("#toast"): bad.append("fail_6MB")
    check("Tambahan: backup rosak / terlalu besar ditolak, borang tidak berubah", not bad, "gagal=%s" % bad)
    ctx.close()
    b.close()

httpd.shutdown()
stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
print("Ujian F-01 pada %s · Chrome headless · %s" % (stamp, URL))
for ac, ok, d in results:
    print("%-34s %s  %s" % (ac, "LULUS" if ok else "GAGAL", d))
print("Jumlah: %d/%d lulus" % (sum(1 for r in results if r[1]), len(results)))
