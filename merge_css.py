#!/usr/bin/env python3
"""
merge_css.py

Run inside your Codespace terminal, from the ROOT of the repo:
    python3 merge_css.py

Merges style.css and css/home.css into a single file (site.css, at the
repo root) -- cuts one render-blocking request per page. Any relative
url(...) paths inside home.css are automatically corrected since it's
moving out of the css/ folder into the root.

Then rewrites every HTML page: removes both old <link> tags and
inserts one link to /site.css (absolute path, works correctly from
every language subfolder) right before </head>.

Originals (style.css, css/home.css) are left in place, untouched --
nothing is deleted. Safe to re-run.
"""

import os
import re

ROOT = os.getcwd()
STYLE_PATH = os.path.join(ROOT, "style.css")
HOME_PATH = os.path.join(ROOT, "css", "home.css")
MERGED_PATH = os.path.join(ROOT, "site.css")

URL_RE = re.compile(r'url\(([^)]+)\)')


def adjust_urls(css_text, source_dir):
    def repl(match):
        raw = match.group(1).strip("'\" ")
        if raw.startswith(("http://", "https://", "data:", "/")):
            return match.group(0)
        new_path = os.path.normpath(
            os.path.join(os.path.relpath(source_dir, ROOT), raw)
        ).replace("\\", "/")
        return f'url({new_path})'
    return URL_RE.sub(repl, css_text)


def build_merged_css():
    if not os.path.isfile(STYLE_PATH):
        print(f"ERROR: {STYLE_PATH} not found.")
        return False
    if not os.path.isfile(HOME_PATH):
        print(f"ERROR: {HOME_PATH} not found.")
        return False

    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        style_css = f.read()
    with open(HOME_PATH, "r", encoding="utf-8") as f:
        home_css = f.read()

    home_css_adjusted = adjust_urls(home_css, os.path.dirname(HOME_PATH))

    merged = (
        "/* === style.css === */\n" + style_css.rstrip() + "\n\n"
        "/* === css/home.css (paths adjusted for new location) === */\n"
        + home_css_adjusted.rstrip() + "\n"
    )

    with open(MERGED_PATH, "w", encoding="utf-8") as f:
        f.write(merged)

    print(f"Wrote {os.path.relpath(MERGED_PATH, ROOT)} ({len(merged)} bytes)")
    return True


LINK_TAG_RE = re.compile(
    r'[ \t]*<link\b[^>]*href="[^"]*(?:style|home)\.css"[^>]*>\n?', re.IGNORECASE
)


def find_html_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "assets")]
        for f in filenames:
            if f.lower().endswith(".html"):
                yield os.path.join(dirpath, f)


def update_html_files():
    changed = []
    for path in find_html_files(ROOT):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        matches = LINK_TAG_RE.findall(content)
        if not matches:
            continue

        new_content = LINK_TAG_RE.sub("", content)
        new_content = new_content.replace(
            "</head>", '  <link rel="stylesheet" href="/site.css">\n</head>', 1
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        changed.append((os.path.relpath(path, ROOT), len(matches)))

    print(f"\nUpdated {len(changed)} HTML file(s):")
    for rel_path, count in changed:
        print(f"  {rel_path} (removed {count} old stylesheet link(s))")


def main():
    if build_merged_css():
        update_html_files()
        print("\nDone. Original style.css and css/home.css kept untouched as backup.")


if __name__ == "__main__":
    main()
