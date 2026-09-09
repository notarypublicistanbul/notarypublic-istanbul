#!/usr/bin/env python3
"""
fix_zh_showcase.py

Run inside your Codespace terminal, from the ROOT of the repo:
    python3 fix_zh_showcase.py

The English e-apostille.html wraps its sample image and its
description text in a two-column grid (.showcase-card containing
.showcase-image + .showcase-content). The Chinese version never got
that wrapper -- everything just flows in one column, which is why the
image looks oversized/stretched compared to the English page.

This script:
1. Finds the <img class="sample-img" ...> tag in zh/e-apostille.html
   and wraps it in <div class="showcase-image">.
2. Wraps everything between that image and the closing </section> in
   <div class="showcase-content">.
3. Wraps both of those in an outer <div class="showcase-card">.
4. Appends the matching CSS rules (copied from css/e-apostille.css)
   to css/zh-e-apostille.css, reusing the same class names so no new
   styling has to be invented -- just applied.

Safe to re-run (it checks whether the wrapper already exists first).
"""

import re
import os

HTML_PATH = "zh/e-apostille.html"
CSS_PATH = "css/zh-e-apostille.css"

CSS_BLOCK = """

/* === showcase-card layout, matched from css/e-apostille.css === */
.showcase-card {
    margin: 3rem auto 0;
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.95) 0%, rgba(10, 10, 10, 0.98) 100%);
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 20px;
    display: grid;
    grid-template-columns: 420px 1fr;
    align-items: stretch;
    overflow: hidden;
    text-align: left;
    box-shadow: 0 0 60px rgba(212, 175, 55, 0.15), 0 20px 60px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(212, 175, 55, 0.15);
    transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}

.showcase-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 0 80px rgba(212, 175, 55, 0.2), 0 30px 70px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(212, 175, 55, 0.2);
}

.showcase-image {
    position: relative;
    min-height: 420px;
    overflow: hidden;
    background: var(--darker);
}

.showcase-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.showcase-card:hover .showcase-image img { transform: scale(1.04); }

.showcase-image::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent 55%, rgba(10,10,10,0.55) 100%);
    pointer-events: none;
}

.showcase-content {
    padding: 3rem 3.5rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

@media (max-width: 768px) {
    .showcase-card { grid-template-columns: 1fr; }
    .showcase-image { min-height: 320px; }
    .showcase-content { padding: 2.5rem 2rem; }
}
"""

IMG_RE = re.compile(r'(<img\b[^>]*class="sample-img"[^>]*>)', re.IGNORECASE)


def fix_html():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if "showcase-card" in content:
        print(f"{HTML_PATH} already has showcase-card wrapper, skipping HTML edit.")
        return False

    match = IMG_RE.search(content)
    if not match:
        print(f"ERROR: could not find <img class=\"sample-img\"> in {HTML_PATH}")
        return False

    img_tag = match.group(1)
    start = match.start()

    section_end = content.find("</section>", start)
    if section_end == -1:
        print("ERROR: could not find closing </section> after the image")
        return False

    after_img = content[match.end():section_end]

    replacement = (
        f'<div class="showcase-card">\n'
        f'<div class="showcase-image">\n{img_tag}\n</div>\n'
        f'<div class="showcase-content">\n{after_img.strip()}\n</div>\n'
        f'</div>\n'
    )

    new_content = content[:start] + replacement + content[section_end:]

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated {HTML_PATH}: wrapped image + content in showcase-card layout.")
    return True


def fix_css():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if ".showcase-card" in content:
        print(f"{CSS_PATH} already has .showcase-card rules, skipping CSS edit.")
        return False

    with open(CSS_PATH, "a", encoding="utf-8") as f:
        f.write(CSS_BLOCK)

    print(f"Appended showcase-card CSS rules to {CSS_PATH}.")
    return True


def main():
    if not os.path.isfile(HTML_PATH):
        print(f"ERROR: {HTML_PATH} not found -- run this from the repo root.")
        return
    if not os.path.isfile(CSS_PATH):
        print(f"ERROR: {CSS_PATH} not found -- run this from the repo root.")
        return

    fix_html()
    fix_css()
    print("\nDone. Preview the page before committing.")


if __name__ == "__main__":
    main()
