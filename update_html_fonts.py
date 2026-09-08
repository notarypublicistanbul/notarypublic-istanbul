#!/usr/bin/env python3
"""
update_html_fonts.py

Run AFTER self_host_fonts.py, from the repo root:
    python3 update_html_fonts.py

Removes the old Google Fonts <link rel="preconnect"> tags (no longer
needed -- we're not calling Google's servers anymore) and replaces the
Google Fonts stylesheet <link> with a single local stylesheet link:

    /assets/fonts/fonts-latin.css   on every page except ar/
    /assets/fonts/fonts-arabic.css  on every page under ar/

Safe to re-run.
"""

import os
import re

PRECONNECT_RE = re.compile(
    r'[ \t]*<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"[^>]*>\n?'
)
GOOGLE_STYLESHEET_RE = re.compile(
    r'<link href="https://fonts\.googleapis\.com/css2\?[^"]*" rel="stylesheet">'
)


def find_html_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "assets")]
        for f in filenames:
            if f.lower().endswith(".html"):
                yield os.path.join(dirpath, f)


def main():
    root = os.getcwd()
    changed = []
    skipped = []

    for path in find_html_files(root):
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()

        if not GOOGLE_STYLESHEET_RE.search(content):
            skipped.append(os.path.relpath(path, root))
            continue

        rel_path = os.path.relpath(path, root).replace("\\", "/")
        is_arabic = rel_path.startswith("ar/")
        local_href = "/assets/fonts/fonts-arabic.css" if is_arabic else "/assets/fonts/fonts-latin.css"

        new_content = PRECONNECT_RE.sub("", content)
        new_content = GOOGLE_STYLESHEET_RE.sub(
            f'<link rel="stylesheet" href="{local_href}">', new_content
        )

        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_content)

        changed.append((rel_path, "arabic" if is_arabic else "latin"))

    print(f"Updated {len(changed)} file(s):")
    for rel_path, kind in changed:
        print(f"  [{kind:6}] {rel_path}")

    if skipped:
        print(f"\n{len(skipped)} file(s) had no Google Fonts tag to replace (skipped):")
        for p in skipped:
            print(f"  - {p}")


if __name__ == "__main__":
    main()
