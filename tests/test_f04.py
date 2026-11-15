"""Ujian penerimaan F-04 (Resume atau CV) - Automation Resume. Guna: python3 -I test_f04.py <index.html>"""
import sys, os, json, re, threading, zipfile, io, http.server, socketserver, functools, datetime
from playwright.sync_api import sync_playwright

APP = os.path.abspath(sys.argv[1]); HERE = os.path.dirname(os.path.abspath(__file__)); FIX = os.path.join(HERE, "fixtures")
VENDOR = os.environ.get("RG_VENDOR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_modules"))
CHROME = os.environ.get("CHROME_PATH") or None
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=os.path.dirname(APP))
class Quiet(Handler.func):
    def log_message(self, *a): pass
httpd = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=os.path.dirname(APP)))
threading.Thread(target=httpd.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/%s" % (httpd.server_address[1], os.path.basename(APP))

RESUME_ORDER = ["PROFESSIONAL SUMMARY", "EDUCATION", "WORK EXPERIENCE", "ACADEMIC PROJECTS", "LEADERSHIP & ACTIVITIES",
                "AWARDS & ACHIEVEMENTS", "SKILLS", "CERTIFICATIONS", "ADDITIONAL INFORMATION"]
CV_ORDER = ["RESEARCH & ACADEMIC SUMMARY", "EDUCATION", "RESEARCH EXPERIENCE", "TEACHING EXPERIENCE", "PRESENTATIONS",
            "GRANTS, SCHOLARSHIPS & FELLOWSHIPS", "HONOURS & AWARDS", "PROFESSIONAL MEMBERSHIPS & LICENCES", "WORK EXPERIENCE",
            "ACADEMIC PROJECTS", "LEADERSHIP & ACTIVITIES", "SKILLS", "CERTIFICATIONS", "ADDITIONAL INFORMATION", "REFERENCES"]
results = []
def check(ac, ok, d=""): results.append((ac, bool(ok), d))

def route_libs(page):
    def h(route):
        u = route.request.url
        if "jspdf" in u: return route.fulfill(path=VENDOR + "/jspdf/dist/jspdf.umd.min.js", content_type="application/javascript")
        if "docx" in u: return route.fulfill(path=VENDOR + "/docx/build/index.umd.js", content_type="application/javascript")
        return route.abort()
    page.route("https://cdn.jsdelivr.net/**", h)
    page.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(body="", content_type="text/css"))
    page.route("https://fonts.gstatic.com/**", lambda r: r.abort())

def fresh(b):
    ctx = b.new_context(accept_downloads=True); pg = ctx.new_page(); route_libs(pg); pg.goto(URL); pg.wait_for_timeout(500); return ctx, pg
def headings(pg): return [h.inner_text() for h in pg.query_selector_all("#paperFull .r-sec h2")]
def download(pg, sel):
    with pg.expect_download(timeout=15000) as dl: pg.click(sel)
    return dl.value.suggested_filename, open(dl.value.path(), "rb").read()
def docx_parts(data):
    z = zipfile.ZipFile(io.BytesIO(data)); return {n: z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.endswith(".xml")}

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

    # AC-1 switch, persistence, file names
    ctx, pg = fresh(b)
    sw = pg.query_selector_all('#panel-form [data-doctype]')
    check("AC-1a Pilihan Resume / CV wujud, Resume lalai", len(sw) == 2 and pg.get_attribute('#panel-form [data-doctype="resume"]', "aria-pressed") == "true")
    pg.fill("#f_certifications", "Microsoft Excel for Business (online course), 2025"); pg.wait_for_timeout(300)
    fn_r, pdf_r = download(pg, '#panel-form [data-action="pdf"]')
    fnw_r, docx_r = download(pg, '#panel-form [data-action="docx"]')
    h_resume = headings(pg)
    pg.click('#panel-form [data-doctype="cv"]'); pg.wait_for_timeout(300)
    h_cv = headings(pg)
    fn_c, pdf_c = download(pg, '#panel-form [data-action="pdf"]')
    fnw_c, docx_c = download(pg, '#panel-form [data-action="docx"]')
    pg.reload(); pg.wait_for_timeout(400)
    persisted = pg.get_attribute('#panel-form [data-doctype="cv"]', "aria-pressed") == "true" and headings(pg) == h_cv
    check("AC-1b Pilihan disimpan selepas muat semula", persisted)
    check("AC-1c Nama fail ikut jenis", fn_r.endswith("_Resume.pdf") and fnw_r.endswith("_Resume.docx") and fn_c.endswith("_CV.pdf") and fnw_c.endswith("_CV.docx"),
          "%s, %s, %s, %s" % (fn_r, fnw_r, fn_c, fnw_c))
    # AC-2 / AC-3 headings & order (example data)
    check("AC-2 Tajuk dan susunan Resume", h_resume == RESUME_ORDER, " > ".join(h_resume))
    check("AC-3 Tajuk dan susunan CV", h_cv == CV_ORDER, " > ".join(h_cv))
    # AC-4 formatting: black, >= 10pt, single column, contact in body, no table without photo
    pg.click('[data-tab="resume"]'); pg.wait_for_timeout(200)
    style = pg.evaluate("""() => { const g = s => getComputedStyle(document.querySelector('#paperFull ' + s));
      return { name: g('.r-name').color, h2: g('.r-sec h2').color, border: g('.r-sec h2').borderBottomColor,
               contact: parseFloat(g('.r-contact div').fontSize), body: parseFloat(g('.page').fontSize) }; }""")
    black = all(style[k] == "rgb(17, 17, 17)" for k in ("name", "h2", "border"))
    pt = lambda px: px * 0.75
    check("AC-4a Pratonton hitam-putih, teks >= 10 pt", black and pt(style["contact"]) >= 10 and pt(style["body"]) >= 10, str(style))
    pdf_txt = pdf_r.decode("latin-1")
    navy = "0.122 0.220 0.392" in pdf_txt or "0.12 0.22 0.39" in pdf_txt
    sizes = [float(x) for x in re.findall(r"/F\d+ ([\d.]+) Tf", pdf_txt)]
    check("AC-4b PDF hitam-putih, saiz fon >= 10 pt (kecuali placeholder foto)", not navy and sizes and min(sizes) >= 10, "saiz=%s" % sorted(set(sizes)))
    parts_r = docx_parts(docx_r); parts_c = docx_parts(docx_c)
    doc_r = parts_r["word/document.xml"]
    no_table = "<w:tbl>" not in doc_r and "<w:tbl " not in doc_r
    no_hdr = not any(n.startswith("word/header") or n.startswith("word/footer") for n in parts_r)
    colours = set(re.findall(r'w:color w:val="([0-9A-Fa-f]{6})"', doc_r))
    sz = [int(x) for x in re.findall(r'<w:sz w:val="(\d+)"', doc_r)]
    check("AC-4c Word: satu lajur, tiada jadual, kenalan dalam badan, hitam/kelabu, >= 10 pt", no_table and no_hdr and colours <= {"111111", "333333"} and min(sz) >= 20,
          "warna=%s saiz(half-pt)=%s" % (colours, sorted(set(sz))))
    title_c = re.search(r"<dc:title>(.*?)</dc:title>", parts_c.get("docProps/core.xml", ""))
    check("AC-4d Word CV bertajuk 'Curriculum Vitae'", title_c and title_c.group(1) == "Curriculum Vitae", str(title_c and title_c.group(1)))
    ctx.close()

    # AC-5 photo off by default
    ctx, pg = fresh(b)
    tip = pg.inner_text('label[for="photoBtn"] ~ .tip')
    check("AC-5 Foto off secara lalai, nota ATS", not pg.is_checked("#showPhoto") and not pg.query_selector("#paperFull .r-photo") and "ATS" in tip, tip[:60])
    # AC-6 page count + resume > 2 pages fails check
    info = pg.inner_text("#pageInfo")
    long_text = " ".join(["Coordinated weekly reporting for the department and improved accuracy by 20 percent through checklists."] * 6)
    for k in ["job1B1", "job1B2", "job1B3", "projB1", "projB2", "lead1B1", "lead1B2"]:
        pg.fill("#f_" + k, long_text)
    for k in ["job2", "lead2", "lead3"]:
        pg.fill("#f_" + k, "Extra role with a long title for testing page length")
    for k in ["job2B1", "job2B2", "job2B3", "lead2B1"]:
        pg.fill("#f_" + k, long_text)
    pg.wait_for_timeout(400)
    info_long = pg.inner_text("#pageInfo")
    pg.click('[data-tab="coach"]'); pg.wait_for_timeout(200)
    rows = pg.inner_text("#checkBody")
    fits_fail = re.search(r"Fits on 1–2 pages\s+✗", rows) is not None
    check("AC-6 Kiraan muka dipaparkan; resume > 2 muka gagal semakan", info.startswith("Resume · about 1 page") and re.search(r"about [3-9] pages", info_long) and fits_fail,
          "%r -> %r" % (info, info_long))
    ctx.close()

    # AC-7 coach per type
    ctx, pg = fresh(b)
    pg.click('[data-tab="coach"]'); pg.wait_for_timeout(200)
    note_r = pg.inner_text("#meterNote"); score_r = pg.inner_text("#scoreNum")
    pg.click('[data-tab="form"]'); pg.click('#panel-form [data-doctype="cv"]'); pg.wait_for_timeout(300)
    pg.click('[data-tab="coach"]'); pg.wait_for_timeout(200)
    note_c = pg.inner_text("#meterNote"); score_c = pg.inner_text("#scoreNum"); rows_c = pg.inner_text("#checkBody")
    check("AC-7a Semakan berbeza: 18 resume, 12 CV; contoh 100 bagi kedua-dua", "18 resume checks" in note_r and "12 CV checks" in note_c and score_r == "100" and score_c == "100",
          "%s / %s; %s / %s" % (note_r, score_r, note_c, score_c))
    pg.click('[data-tab="form"]'); pg.click('#panel-form [data-doctype="resume"]'); pg.wait_for_timeout(200)
    pg.fill("#f_summary", " ".join(["word"] * 120)); pg.wait_for_timeout(300)
    pg.click('[data-tab="coach"]'); pg.wait_for_timeout(200)
    check("AC-7b Ringkasan > 100 patah perkataan gagal semakan", re.search(r"about 100 words or fewer\s+✗", pg.inner_text("#checkBody")) is not None)
    ctx.close()

    # AC-8 CV lists: one entry per line, blank lines ignored, in preview and Word
    ctx, pg = fresh(b)
    pg.click('#panel-form [data-doctype="cv"]'); pg.wait_for_timeout(200)
    pg.fill("#f_cvPublications", "Paper one (2025).\n\n  Paper two (2026).  \nPaper three (2026).\n")
    pg.wait_for_timeout(300)
    sec = pg.evaluate("""() => { const s = [...document.querySelectorAll('#paperFull .r-sec')].find(x => x.querySelector('h2').innerText === 'PUBLICATIONS');
                         return s ? [...s.querySelectorAll('.r-bul')].map(x => x.innerText) : null; }""")
    _, dx = download(pg, '#panel-form [data-action="docx"]')
    dxml = docx_parts(dx)["word/document.xml"]
    ok8 = sec == ["Paper one (2025).", "Paper two (2026).", "Paper three (2026)."] and all(s in dxml for s in ("Paper one (2025).", "Paper two (2026).", "Paper three (2026)."))
    check("AC-8 Senarai CV: satu baris = satu entri", ok8, str(sec))
    # AC-9 form shows only relevant sections
    vis = lambda sel: pg.is_visible(sel)
    cv_mode = vis('details[data-mode="cv"]') and not vis('details[data-mode="resume"]')
    pg.click('#panel-form [data-doctype="resume"]'); pg.wait_for_timeout(200)
    rs_mode = vis('details[data-mode="resume"]') and not vis('details[data-mode="cv"]')
    check("AC-9 Borang: seksyen 2 untuk Resume, seksyen 10 untuk CV", cv_mode and rs_mode)
    # AC-10 backup keeps type and CV fields; restore sets them
    pg.click('#panel-form [data-doctype="cv"]'); pg.wait_for_timeout(200)
    fnb, raw = download(pg, '[data-action="backup"]')
    js = json.loads(raw)
    path = os.path.join(FIX, "cv_backup.json"); open(path, "wb").write(raw)
    pg.fill("#f_cvPublications", ""); pg.click('#panel-form [data-doctype="resume"]'); pg.wait_for_timeout(300)
    pg.set_input_files("#jsonInput", path); pg.wait_for_timeout(500)
    restored = pg.get_attribute('#panel-form [data-doctype="cv"]', "aria-pressed") == "true" and "Paper two (2026)." in pg.input_value("#f_cvPublications")
    check("AC-10 Backup menyimpan jenis dokumen dan medan CV", js.get("docType") == "cv" and "cvReferences" in js["data"] and restored, "docType=%s" % js.get("docType"))
    ctx.close()

    # ---------- Semakan kedua ChatGPT (F-04): ujian tambahan ----------
    # Kiraan muka dibandingkan dengan PDF sebenar pada 1, 2 dan 3 muka
    ctx, pg = fresh(b)
    txt = "Coordinated weekly reporting for the department and improved accuracy by 20 percent through simple checklists and reviews."
    keys = ["job1B1", "job1B2", "job1B3", "projB1", "projB2", "lead1B1", "lead1B2", "job2B1", "job2B2", "job2B3", "lead2B1"]
    pg.fill("#f_job2", "Second job title"); pg.fill("#f_lead2", "Second role")
    pairs = []
    for reps in (0, 2, 7):
        for k in keys: pg.fill("#f_" + k, " ".join([txt] * reps) if reps else "")
        pg.wait_for_timeout(300)
        est = int(re.search(r"about (\d+)", pg.inner_text("#pageInfo")).group(1))
        _, pdf = download(pg, '#panel-form [data-action="pdf"]')
        pairs.append((est, len(re.findall(rb"/Type /Page\b", pdf))))
    check("Tambahan: anggaran muka = muka PDF sebenar (1, 2, 3)", [a for a, _ in pairs] == [1, 2, 3] and all(a == b_ for a, b_ in pairs), str(pairs))
    ctx.close()
    # Semakan CV lebih ketat: rujukan perlu jawatan/institusi + emel/telefon; alamat akademik wajib; emel sah
    ctx, pg = fresh(b)
    pg.click('#panel-form [data-doctype="cv"]'); pg.wait_for_timeout(200)
    pg.fill("#f_cvReferences", "Dr. Contoh\nEncik Contoh"); pg.fill("#f_cvAddress", ""); pg.fill("#f_email", "nama@contoh"); pg.wait_for_timeout(300)
    pg.click('[data-tab="coach"]'); pg.wait_for_timeout(200)
    rows = pg.inner_text("#checkBody")
    fails = [n for n in ("At least two full references", "Academic or professional address", "Phone and email present") if re.search(re.escape(n) + r"\s+✗", rows)]
    check("Tambahan: semakan CV menolak rujukan nama sahaja, tiada alamat akademik, emel tidak sah", len(fails) == 3, "gagal seperti dijangka=%s" % fails)
    ctx.close()
    # X-Y-Z: kurang separuh peluru ada nombor -> gagal
    ctx, pg = fresh(b)
    for k in ["job1B1", "job1B2", "job1B3", "projB1", "projB2", "lead1B1"]: pg.fill("#f_" + k, "Helped the team with daily tasks")
    pg.wait_for_timeout(300); pg.click('[data-tab="coach"]'); pg.wait_for_timeout(200)
    check("Tambahan: semakan X-Y-Z gagal jika kurang separuh peluru ada nombor", re.search(r"measurable result \(X-Y-Z\)\s+✗", pg.inner_text("#checkBody")) is not None)
    ctx.close()
    # Backup CV v4 lengkap dengan foto; docType / foto tidak sah ditolak
    ctx, pg = fresh(b)
    pg.click('#panel-form [data-doctype="cv"]'); pg.wait_for_timeout(200)
    pg.set_input_files("#photoInput", os.path.join(FIX, "photo.png")); pg.wait_for_timeout(600)
    _, raw = download(pg, '[data-action="backup"]')
    js = json.loads(raw); path = os.path.join(FIX, "cv_photo_backup.json"); open(path, "wb").write(raw)
    pg.click('#panel-form [data-action="clear"]'); pg.click('#panel-form [data-action="clear"]'); pg.click('[data-action="photo-remove"]')
    pg.click('#panel-form [data-doctype="resume"]'); pg.wait_for_timeout(300)
    pg.set_input_files("#jsonInput", path); pg.wait_for_timeout(600)
    ok_full = (pg.get_attribute('#panel-form [data-doctype="cv"]', "aria-pressed") == "true" and pg.is_checked("#showPhoto")
               and pg.query_selector("#paperFull .r-photo img") is not None and pg.input_value("#f_cvReferences") != "")
    bad = []
    for nm_, obj in {"docType_salah": dict(js, docType="poster"), "foto_svg": dict(js, photo="data:image/svg+xml;base64,PHN2Zz4=")}.items():
        fp = os.path.join(FIX, "bad_%s.json" % nm_); json.dump(obj, open(fp, "w"))
        before = pg.input_value("#f_name")
        pg.fill("#f_name", "KEEP ME"); pg.wait_for_timeout(250)
        pg.set_input_files("#jsonInput", fp); pg.wait_for_timeout(400)
        if pg.input_value("#f_name") != "KEEP ME": bad.append(nm_)
    check("Tambahan: backup CV v4 dengan foto dipulihkan penuh; docType/foto tidak sah ditolak", ok_full and not bad and js.get("version") == 4, "penuh=%s gagal=%s" % (ok_full, bad))
    ctx.close()
    b.close()
httpd.shutdown()
print("Ujian F-04 pada %s · Chrome headless · %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), URL))
for ac, ok, d in results: print("%-62s %s  %s" % (ac, "LULUS" if ok else "GAGAL", d))
print("Jumlah: %d/%d lulus" % (sum(1 for r in results if r[1]), len(results)))
