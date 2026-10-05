#!/usr/bin/env python3
"""
Adds the ESPAÑOL / PORTUGUÊS buttons to the language switcher and the es/pt
hreflang tags to existing pages. Safe to run more than once.

Usage (from the repo root):
    python3 add_language_links.py index.html faq.html reviews.html e-apostille.html getting-married-in-turkey.html tr/*.html ru/*.html ar/*.html zh/*.html
"""
import re, sys, os

BASE = "https://notarypublic.istanbul"

def patch(html, filename):
    changed = False
    # 1) language switcher: insert after the 中文 link
    if 'lang-btn">ESPAÑOL</a>' not in html:
        m = re.search(r'^([ \t]*)<a href="/zh/"[^>]*>[^<]*</a>[ \t]*\n', html, re.M)
        if m:
            ind = m.group(1)
            add = (f'{ind}<a href="/es/" class="lang-btn">ESPAÑOL</a>\n'
                   f'{ind}<a href="/pt/" class="lang-btn">PORTUGUÊS</a>\n')
            html = html[:m.end()] + add + html[m.end():]
            changed = True
        else:
            print(f"  ! {filename}: no /zh/ switcher link found - add the two buttons by hand")
    # 2) hreflang
    if not re.search(r"hreflang=[\"']es[\"']", html):
        m = re.search(r"<link rel=([\"'])alternate\1 hreflang=\1x-default\1[^>]*>", html)
        if m:
            q = m.group(1)
            name = os.path.basename(filename)
            path = "/" if name == "index.html" else "/" + name
            links = "".join(
                f"<link rel={q}alternate{q} hreflang={q}{code}{q} href={q}{BASE}/{code}{path}{q} />\n"
                for code in ("es", "pt"))
            html = html[:m.start()] + links + html[m.start():]
            changed = True
        else:
            print(f"  ! {filename}: no x-default hreflang found - add es/pt hreflang by hand")
    return html, changed

if __name__ == "__main__":
    for f in sys.argv[1:]:
        s = open(f, encoding="utf-8").read()
        s2, ch = patch(s, f)
        if ch:
            open(f, "w", encoding="utf-8").write(s2)
            print("patched", f)
        else:
            print("unchanged", f)
