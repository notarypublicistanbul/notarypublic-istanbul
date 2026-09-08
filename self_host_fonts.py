#!/usr/bin/env python3
"""
self_host_fonts.py

Run inside your Codespace terminal, from the ROOT of the repo:
    python3 self_host_fonts.py

Downloads the actual .woff2 font files this site uses, saves them
under assets/fonts/, and writes two local stylesheets:

    assets/fonts/fonts-latin.css   (Inter + Cormorant Garamond)
    assets/fonts/fonts-arabic.css  (Inter + Markazi Text)

These fully replace the Google Fonts <link> tags -- after this, the
site makes zero requests to fonts.googleapis.com / fonts.gstatic.com.

Safe to re-run: it will just re-download and overwrite.
"""

import os
import re
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

FONT_SETS = {
    "fonts-latin.css": (
        "https://fonts.googleapis.com/css2?"
        "family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400"
        "&family=Inter:wght@400;500;600;700&display=swap"
    ),
    "fonts-arabic.css": (
        "https://fonts.googleapis.com/css2?"
        "family=Inter:wght@400;500;600;700"
        "&family=Markazi+Text:wght@400;500;600;700&display=swap"
    ),
}

OUT_DIR = os.path.join("assets", "fonts")


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def fetch_binary(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def slugify(family):
    return re.sub(r"[^a-z0-9]+", "-", family.lower()).strip("-")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for out_name, css_url in FONT_SETS.items():
        print(f"\nFetching {out_name} definitions from Google Fonts...")
        css = fetch_text(css_url)

        blocks = re.findall(
            r"/\*[^*]*\*/\s*@font-face\s*\{[^}]*\}|@font-face\s*\{[^}]*\}", css
        )

        new_css_parts = []
        seen_names = set()

        for block in blocks:
            family_match = re.search(r"font-family:\s*'([^']+)'", block)
            weight_match = re.search(r"font-weight:\s*(\d+)", block)
            style_match = re.search(r"font-style:\s*(\w+)", block)
            url_match = re.search(
                r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", block
            )
            subset_match = re.search(r"/\*\s*([\w-]+)\s*\*/", block)

            if not (family_match and weight_match and style_match and url_match):
                continue

            family = family_match.group(1)
            weight = weight_match.group(1)
            style = style_match.group(1)
            subset = subset_match.group(1) if subset_match else "default"
            font_url = url_match.group(1)

            slug = slugify(family)
            base_name = f"{slug}-{weight}-{style}-{subset}"
            filename = f"{base_name}.woff2"
            counter = 1
            while filename in seen_names:
                counter += 1
                filename = f"{base_name}-{counter}.woff2"
            seen_names.add(filename)

            local_path = os.path.join(OUT_DIR, filename)
            print(f"  downloading {family} {weight} {style} ({subset}) -> {filename}")
            data = fetch_binary(font_url)
            with open(local_path, "wb") as f:
                f.write(data)

            new_block = block.replace(font_url, filename)
            new_css_parts.append(new_block)

        out_path = os.path.join(OUT_DIR, out_name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(new_css_parts))
        print(f"Wrote {out_path} ({len(new_css_parts)} font-face rules)")

    print("\nDone. Fonts are now local under assets/fonts/.")
    print("Next: run update_html_fonts.py to point every page at the local stylesheet.")


if __name__ == "__main__":
    main()
