#!/usr/bin/env python3
"""Generate deterministic 1200x630 Open Graph PNG cards for Hugo posts using tools/og-image.html."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode


CHROME_CANDIDATES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)


def find_chrome() -> str:
    env_bin = os.environ.get("CHROME_BIN")
    if env_bin and (shutil.which(env_bin) or Path(env_bin).is_file()):
        return env_bin
    for candidate in CHROME_CANDIDATES:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        if Path(candidate).is_file():
            return candidate
    raise RuntimeError("Chrome/Chromium binary not found; set CHROME_BIN")


def unquote_scalar(val: str) -> str:
    val = val.strip()
    if val.startswith('"'):
        m = re.match(r'^"([^"]*)"', val)
        if m:
            return m.group(1)
    if val.startswith("'"):
        m = re.match(r"^'([^']*)'", val)
        if m:
            return m.group(1)
    val = re.sub(r"\s+#.*$", "", val).strip()
    return val


def parse_simple_kv(text: str) -> dict[str, str]:
    """Extract top-level / params scalar keys from YAML or TOML config/front matter."""
    data: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*[:=]\s*(.+)$", line)
        if not m:
            continue
        key, val = m.group(1), unquote_scalar(m.group(2))
        if key not in data and val and not val.startswith(("[", "{")):
            data[key] = val
    return data


def load_site_defaults(site_root: Path) -> dict[str, str]:
    for rel in ("config/_default/hugo.yaml", "hugo.yaml", "hugo.toml", "config.yaml", "config.toml"):
        cfg = site_root / rel
        if cfg.is_file():
            return parse_simple_kv(cfg.read_text(encoding="utf-8"))
    return {}


def parse_front_matter(md_path: Path) -> dict[str, str]:
    text = md_path.read_text(encoding="utf-8")
    if text.startswith("---\n") or text.startswith("---\r\n"):
        end = text.find("\n---", 3)
        if end != -1:
            return parse_simple_kv(text[4:end])
    elif text.startswith("+++\n") or text.startswith("+++\r\n"):
        end = text.find("\n+++", 3)
        if end != -1:
            return parse_simple_kv(text[4:end])
    return {}


def normalize_date(raw: str) -> str:
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", raw.strip())
    return m.group(1) if m else ""


def resolve_post_route(content_dir: Path, md_path: Path, default_lang: str) -> tuple[str, str, str] | None:
    """Return (section, rel_out_path, seed) for a post markdown file, or None if not a regular page."""
    rel = md_path.relative_to(content_dir)
    if len(rel.parts) < 2:
        return None
    section = rel.parts[0]
    stem = md_path.stem
    if stem == "_index" or stem.startswith("_index."):
        return None

    lang = ""
    if "." in stem:
        base_stem, maybe_lang = stem.rsplit(".", 1)
        if re.fullmatch(r"[a-z]{2}(?:-[a-zA-Z0-9]+)?", maybe_lang):
            stem = base_stem
            lang = maybe_lang

    if stem == "index":
        # Page bundle: content/posts/<slug>/index[.lang].md
        # Skip if bundle already has a cover/feature/thumbnail image
        for sibling in md_path.parent.iterdir():
            if sibling.is_file() and any(k in sibling.stem.lower() for k in ("feature", "cover", "thumbnail")):
                return None
        page_rel = rel.parent.as_posix()
    else:
        page_rel = (rel.parent / stem).as_posix()

    if lang and lang != default_lang:
        out_rel = f"{lang}/{page_rel}.png"
    else:
        out_rel = f"{page_rel}.png"
    return section, out_rel, page_rel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", type=Path, default=Path.cwd(), help="Hugo site root directory")
    parser.add_argument("--sections", nargs="+", default=["posts"], help="Content sections to generate OG images for")
    parser.add_argument("--include-drafts", action="store_true", help="Include draft posts")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated PNG files")
    args = parser.parse_args()

    site_root = args.site_root.resolve()
    content_dir = site_root / "content"
    out_root = site_root / "static" / "images" / "og"
    tool_html = (Path(__file__).resolve().parent / "og-image.html").resolve()

    if not tool_html.is_file():
        print(f"error: generator HTML not found: {tool_html}", file=sys.stderr)
        return 2
    if not content_dir.is_dir():
        print(f"error: content directory not found: {content_dir}", file=sys.stderr)
        return 2

    cfg = load_site_defaults(site_root)
    default_lang = cfg.get("defaultContentLanguage", "ja")
    fg = cfg.get("fg", "#f7faf9")
    bg = cfg.get("bg", "#05366e")
    logo_name = cfg.get("logoName", cfg.get("title", "Contour"))
    logo_tld = cfg.get("logoTLD", "")
    axis = cfg.get("axis", "Elevation / Isoline Field")
    author = cfg.get("author", "")

    chrome_bin = find_chrome()
    md_files: list[Path] = []
    for section in args.sections:
        sec_dir = content_dir / section
        if sec_dir.is_dir():
            md_files.extend(sorted(sec_dir.rglob("*.md")))

    generated = 0
    skipped = 0
    with tempfile.TemporaryDirectory(prefix="contour-og-chrome-") as profile_dir:
        for md_path in md_files:
            fm = parse_front_matter(md_path)
            if fm.get("draft", "").lower() == "true" and not args.include_drafts:
                skipped += 1
                continue
            if "image" in fm or "images" in fm:
                skipped += 1
                continue
            title = fm.get("title", "").strip()
            if not title:
                skipped += 1
                continue

            route = resolve_post_route(content_dir, md_path, default_lang)
            if route is None:
                skipped += 1
                continue
            section, out_rel, seed = route
            out_path = out_root / out_rel
            if out_path.is_file() and not args.force:
                skipped += 1
                continue

            out_path.parent.mkdir(parents=True, exist_ok=True)
            query = urlencode({
                "fg": fg,
                "bg": bg,
                "logoName": logo_name,
                "logoTLD": logo_tld,
                "axis": axis,
                "author": author,
                "section": section,
                "date": normalize_date(fm.get("date", "")),
                "title": title,
                "seed": seed,
            })
            url = f"{tool_html.as_uri()}?{query}"
            cmd = [
                chrome_bin,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--user-data-dir={profile_dir}",
                "--force-device-scale-factor=1",
                "--window-size=1200,630",
                "--virtual-time-budget=3000",
                f"--screenshot={out_path}",
                url,
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            generated += 1
            print(f"generated {out_path.relative_to(site_root)} (seed={seed})")

    print(f"done: {generated} generated, {skipped} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
