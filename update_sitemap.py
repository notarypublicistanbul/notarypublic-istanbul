#!/usr/bin/env python3
"""
Upgrades sitemap.xml for the new Spanish/Portuguese pages:
  1. removes the 10 simple one-line entries pasted by hand (if present)
  2. adds es + pt xhtml:link alternates to every <url> that already has alternates
  3. adds full es/ and pt/ entries (same format as your other entries) for every English root page
Safe to run more than once. Makes a backup: sitemap.xml.bak
"""
import re, shutil

BASE = "https://notarypublic.istanbul"
TODAY = "2026-10-06"
FILE = "sitemap.xml"

xml = open(FILE, encoding="utf-8").read()
shutil.copy(FILE, FILE + ".bak")

# 1) remove hand-pasted one-line entries
xml = re.sub(r"[ \t]*<url><loc>" + re.escape(BASE) + r"/(?:es|pt)/[^<]*</loc></url>[ \t]*\n?", "", xml)

# 2) add es/pt alternates to blocks that have an x-default line
def add_alts(m):
    block = m.group(0)
    if 'hreflang="es"' in block:
        return block
    xd = re.search(r'^([ \t]*)<xhtml:link rel="alternate" hreflang="x-default" href="([^"]+)"\s*/>', block, re.M)
    if not xd:
        return block
    ind, href = xd.group(1), xd.group(2)
    path = href[len(BASE):] or "/"
    lines = "".join(
        f'{ind}<xhtml:link rel="alternate" hreflang="{c}" href="{BASE}/{c}{path}"/>\n' for c in ("es", "pt"))
    return block[:xd.start()] + lines + block[xd.start():]
xml = re.sub(r"[ \t]*<url>.*?</url>", add_alts, xml, flags=re.S)

# 3) clone English root entries into es/ and pt/
blocks = re.findall(r"[ \t]*<url>.*?</url>[ \t]*\n?", xml, flags=re.S)
existing = set(re.findall(r"<loc>([^<]+)</loc>", xml))
new = ""
for b in blocks:
    loc = re.search(r"<loc>([^<]+)</loc>", b).group(1)
    path = loc[len(BASE):]
    if re.match(r"/(?:tr|ru|ar|zh|es|pt)/", path):
        continue
    for lang in ("es", "pt"):
        target = f"{BASE}/{lang}{path}"
        if target in existing:
            continue
        c = b.replace(f"<loc>{loc}</loc>", f"<loc>{target}</loc>")
        c = re.sub(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{TODAY}</lastmod>", c)
        new += c if c.endswith("\n") else c + "\n"
if new:
    xml = xml.replace("</urlset>", new + "</urlset>")
open(FILE, "w", encoding="utf-8").write(xml)
print("done - new entries added:", new.count("<url>"))
