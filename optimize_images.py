#!/usr/bin/env python3
"""
optimize_images.py

Run inside your Codespace terminal, from the ROOT of the repo:
    pip install Pillow --quiet
    python3 optimize_images.py

What it does:
1. Scans every .html file for <img> tags.
2. For each image actually referenced by an <img> tag, converts it to
   a WebP version alongside the original (same folder, same name,
   .webp extension) using Pillow. Originals are kept -- nothing is
   deleted, so nothing breaks if something goes wrong.
3. Rewrites every <img> tag to:
   - point at the new .webp file
   - include width/height attributes matching the image's real pixel
     size (prevents layout shift while it loads)
   - add loading="lazy" (except the very first <img> on each page,
     which gets loading="eager" so it isn't delayed)
   - add decoding="async"

Deliberately leaves og-image.jpg alone (and anything else only used
in <meta> tags, not <img> tags) since that's for social share
previews, not rendered on the page.

Safe to re-run.
"""

import os
import re
from PIL import Image

IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
SRC_RE = re.compile(r'src="([^"]+)"')
WIDTH_RE = re.compile(r'\s+width="[^"]*"')
HEIGHT_RE = re.compile(r'\s+height="[^"]*"')
LOADING_RE = re.compile(r'\s+loading="[^"]*"')
DECODING_RE = re.compile(r'\s+decoding="[^"]*"')

CONVERTIBLE_EXTS = (".jpg", ".jpeg", ".png")

converted_cache = {}  # abs original path -> (abs webp path, width, height)


def find_html_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "assets")]
        for f in filenames:
            if f.lower().endswith(".html"):
                yield os.path.join(dirpath, f)


def resolve_src_path(html_path, src, repo_root):
    if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
        return None
    if src.startswith("/"):
        return os.path.normpath(os.path.join(repo_root, src.lstrip("/")))
    return os.path.normpath(os.path.join(os.path.dirname(html_path), src))


def convert_to_webp(abs_path):
    if abs_path in converted_cache:
        return converted_cache[abs_path]

    if not os.path.isfile(abs_path):
        return None

    ext = os.path.splitext(abs_path)[1].lower()
    if ext not in CONVERTIBLE_EXTS:
        return None

    webp_path = os.path.splitext(abs_path)[0] + ".webp"

    with Image.open(abs_path) as im:
        width, height = im.size
        if ext == ".png":
            im = im.convert("RGBA")
        else:
            im = im.convert("RGB")
        im.save(webp_path, "WEBP", quality=82, method=6)

    result = (webp_path, width, height)
    converted_cache[abs_path] = result
    return result


def process_html(path, repo_root):
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    state = {"first_img_seen": False, "changed": False}

    def replace_img(match):
        tag = match.group(0)
        src_match = SRC_RE.search(tag)
        if not src_match:
            return tag

        src = src_match.group(1)
        abs_path = resolve_src_path(path, src, repo_root)
        if not abs_path:
            state["first_img_seen"] = True
            return tag

        result = convert_to_webp(abs_path)
        if not result:
            state["first_img_seen"] = True
            return tag

        webp_abs, width, height = result
        new_src = os.path.splitext(src)[0] + ".webp"

        new_tag = tag.replace(f'src="{src}"', f'src="{new_src}"')
        new_tag = WIDTH_RE.sub("", new_tag)
        new_tag = HEIGHT_RE.sub("", new_tag)
        new_tag = LOADING_RE.sub("", new_tag)
        new_tag = DECODING_RE.sub("", new_tag)

        loading_value = "eager" if not state["first_img_seen"] else "lazy"
        state["first_img_seen"] = True

        insertion = f' width="{width}" height="{height}" loading="{loading_value}" decoding="async"'
        new_tag = new_tag.replace("<img", "<img" + insertion, 1)

        state["changed"] = True
        return new_tag

    new_content = IMG_TAG_RE.sub(replace_img, content)

    if state["changed"]:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_content)
    return state["changed"]


def main():
    repo_root = os.getcwd()
    changed_files = []

    for html_path in find_html_files(repo_root):
        if process_html(html_path, repo_root):
            changed_files.append(os.path.relpath(html_path, repo_root))

    print(f"Updated {len(changed_files)} HTML file(s):")
    for f in changed_files:
        print(f"  {f}")

    print(f"\nConverted {len(converted_cache)} unique image(s) to WebP.")
    for orig, (webp, w, h) in converted_cache.items():
        print(f"  {os.path.relpath(orig, repo_root)} -> {os.path.relpath(webp, repo_root)} ({w}x{h})")


if __name__ == "__main__":
    main()
