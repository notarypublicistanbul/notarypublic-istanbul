#!/usr/bin/env python3
"""
Read-only site audit for notarypublic.istanbul. Changes NOTHING.
Run from the repo root:   python3 audit_site.py
"""
import os, re, json, sys
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
from collections import defaultdict, Counter

BASE = "https://notarypublic.istanbul"
LANGS = {"tr": "tr", "ru": "ru", "ar": "ar", "zh": "zh", "es": "es", "pt": "pt"}
EXPECTED_HREFLANG = {"en", "tr", "ru", "ar", "zh-Hans", "es", "pt", "x-default"}
SKIP_DIRS = {".git", "node_modules", ".github"}

class Page(HTMLParser):
    def __init__(s):
        super().__init__()
        s.title = ""; s.in_title = False; s.meta = {}; s.canonical = None
        s.hreflang = {}; s.refs = []; s.imgs_no_alt = 0; s.h1 = 0
        s.ld = []; s.in_ld = False; s.lang = None; s.dir = None
    def handle_starttag(s, t, a):
        d = dict(a)
        if t == "html": s.lang = d.get("lang"); s.dir = d.get("dir")
        if t == "title": s.in_title = True
        if t == "h1": s.h1 += 1
        if t == "meta":
            k = d.get("name") or d.get("property")
            if k: s.meta[k] = d.get("content", "")
        if t == "link":
            if d.get("rel") == "canonical": s.canonical = d.get("href")
            if d.get("rel") == "alternate" and d.get("hreflang"): s.hreflang[d["hreflang"]] = d.get("href")
            if d.get("rel") in ("stylesheet", "icon", "preload") and d.get("href"): s.refs.append(d["href"])
        if t == "a" and d.get("href"): s.refs.append(d["href"])
        if t in ("img", "script", "source") and d.get("src"): s.refs.append(d["src"])
        if t == "img" and not d.get("alt", "").strip(): s.imgs_no_alt += 1
        if t == "script" and d.get("type") == "application/ld+json": s.in_ld = True; s.ld.append("")
    def handle_endtag(s, t):
        if t == "title": s.in_title = False
        if t == "script": s.in_ld = False
    def handle_data(s, d):
        if s.in_title: s.title += d
        if s.in_ld: s.ld[-1] += d

def url_for(path):
    p = path.replace(os.sep, "/")
    if p.endswith("index.html"): p = p[:-10]
    return f"{BASE}/{p}"

files = []
for root, dirs, fs in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in fs: files.append(os.path.relpath(os.path.join(root, f), "."))
htmls = sorted(f for f in files if f.endswith(".html"))
fileset = set(f.replace(os.sep, "/") for f in files)
pages = {}
for h in htmls:
    p = Page(); p.feed(open(h, encoding="utf-8", errors="replace").read()); pages[h.replace(os.sep, "/")] = p

issues = defaultdict(list)
def add(cat, msg): issues[cat].append(msg)

def resolve(page, ref):
    r = urlparse(ref)
    if r.scheme or ref.startswith(("#", "mailto:", "tel:", "data:", "javascript:", "//")): return None
    path = unquote(r.path)
    if not path: return None
    full = path.lstrip("/") if path.startswith("/") else os.path.normpath(os.path.join(os.path.dirname(page), path)).replace(os.sep, "/")
    if full == "" or full.endswith("/"): full += "index.html"
    return full

titles = Counter(p.title.strip() for p in pages.values())
for name, p in pages.items():
    folder = name.split("/")[0] if "/" in name else ""
    # links / assets
    for ref in p.refs:
        t = resolve(name, ref)
        if t and t not in fileset and not (t + "/index.html") in fileset:
            add("Broken local links / missing files", f"{name} -> {ref}")
    # head basics
    if not p.title.strip(): add("SEO basics", f"{name}: no <title>")
    elif len(p.title.strip()) > 70: add("SEO basics", f"{name}: title is {len(p.title.strip())} chars (aim ≤ 65)")
    if titles[p.title.strip()] > 1: add("SEO basics", f"{name}: title shared with another page: {p.title.strip()[:60]}")
    d = p.meta.get("description", "")
    if not d: add("SEO basics", f"{name}: no meta description")
    elif len(d) > 165: add("SEO basics", f"{name}: description is {len(d)} chars (aim ≤ 160)")
    if p.h1 != 1: add("SEO basics", f"{name}: has {p.h1} <h1> (should be 1)")
    if p.imgs_no_alt: add("Accessibility", f"{name}: {p.imgs_no_alt} image(s) without alt text")
    for k in ("og:title", "og:description", "og:image", "twitter:card"):
        if k not in p.meta: add("Social sharing tags missing", f"{name}: no {k}")
    exp = url_for(name)
    if p.canonical != exp: add("Canonical URL", f"{name}: canonical is {p.canonical} (expected {exp})")
    exp_lang = LANGS.get(folder, "en")
    if (p.lang or "").split("-")[0] != exp_lang: add("Language attribute", f"{name}: html lang='{p.lang}' (expected {exp_lang})")
    if folder == "ar" and p.dir != "rtl": add("Language attribute", f"{name}: Arabic page without dir='rtl'")
    # hreflang
    missing = EXPECTED_HREFLANG - set(p.hreflang)
    if missing: add("hreflang", f"{name}: missing {sorted(missing)}")
    for lang, href in p.hreflang.items():
        if not href.startswith(BASE): continue
        tp = href[len(BASE):].lstrip("/")
        if tp == "" or tp.endswith("/"): tp += "index.html"
        if tp not in fileset: add("hreflang", f"{name}: {lang} points to missing file {tp}")
        elif lang != "x-default" and tp in pages and url_for(name) not in pages[tp].hreflang.values():
            add("hreflang", f"{name}: {tp} does not link back (not reciprocal)")
    # json-ld
    for blob in p.ld:
        try: json.loads(blob)
        except Exception as e: add("Structured data (JSON-LD)", f"{name}: invalid JSON-LD ({e})")
    # stale values
    txt = open(name, encoding="utf-8", errors="replace").read()
    for bad in ("tac_notary_ist", "5393708707", "539 370 87 07"):
        if bad.lower() in txt.lower(): add("Old handles / numbers still present", f"{name}: contains '{bad}'")

# sitemap
if "sitemap.xml" in fileset:
    sm = open("sitemap.xml", encoding="utf-8").read()
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    in_sm = set()
    for l in locs:
        tp = l[len(BASE):].lstrip("/") if l.startswith(BASE) else l
        if tp == "" or tp.endswith("/"): tp += "index.html"
        in_sm.add(tp)
        if tp not in fileset: add("Sitemap", f"lists a page that does not exist: {l}")
    for h in pages:
        if h not in in_sm and h != "404.html": add("Sitemap", f"page not in sitemap: {h}")
    if 'hreflang="zh"' in sm and any('zh-Hans' in p.hreflang for p in pages.values()):
        add("Sitemap", "sitemap uses hreflang=\"zh\" but pages use \"zh-Hans\" - make them match")
else:
    add("Sitemap", "no sitemap.xml found")
if "robots.txt" in fileset:
    if "sitemap" not in open("robots.txt", encoding="utf-8").read().lower(): add("robots.txt", "has no Sitemap: line")
else: add("robots.txt", "missing")
if "404.html" not in fileset: add("Site extras", "no custom 404.html page")

# files served publicly that probably should not be
for f in sorted(fileset):
    if f.endswith((".py", ".md", ".bak", ".log")) and "/" not in f:
        add("Public clutter (served on your live site)", f)

# possibly unused assets
ref_text = ""
for f in fileset:
    if f.endswith((".html", ".css", ".js", ".xml", ".webmanifest", ".json")):
        ref_text += open(f, encoding="utf-8", errors="replace").read()
for f in sorted(fileset):
    if f.endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")) and os.path.basename(f) not in ref_text:
        add("Possibly unused images (double-check before deleting)", f)
for f in sorted(fileset):
    if f.endswith(".css") and os.path.basename(f) not in ref_text:
        add("Possibly unused CSS (double-check before deleting)", f)
# big images
for f in sorted(fileset):
    if f.endswith((".png", ".jpg", ".jpeg", ".webp")) and os.path.getsize(f) > 300_000:
        add("Large images (> 300 KB)", f"{f}: {os.path.getsize(f)//1024} KB")

print(f"Checked {len(pages)} HTML pages, {len(fileset)} files.\n")
if not issues: print("No issues found.")
for cat in issues:
    print(f"== {cat} ({len(issues[cat])}) ==")
    for m in issues[cat][:25]: print("  -", m)
    if len(issues[cat]) > 25: print(f"  ... and {len(issues[cat]) - 25} more")
    print()
