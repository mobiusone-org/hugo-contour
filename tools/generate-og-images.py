#!/usr/bin/env python3
"""Generate deterministic 1200x630 Open Graph PNG cards for Hugo posts using tools/og-image.html."""

from __future__ import annotations

import argparse
import csv
import io
import json
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


def hugo_base_cmd(site_root: Path, tool_html: Path, environment: str | None) -> list[str]:
    hugo_bin = os.environ.get("HUGO_BIN", "hugo")
    cmd = [hugo_bin, "--source", str(site_root), "--logLevel", "error", "--noBuildLock"]
    if environment:
        cmd.extend(["--environment", environment])
    theme_dir = tool_html.parent.parent
    if not (site_root / "themes" / theme_dir.name).exists() and theme_dir.name == "contour":
        cmd.extend(["--themesDir", str(theme_dir.parent)])
    return cmd


def load_site_config(site_root: Path, tool_html: Path, environment: str | None) -> dict:
    cmd = hugo_base_cmd(site_root, tool_html, environment) + ["config", "--format", "json"]
    res = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(res.stdout)


def run_hugo_list(site_root: Path, tool_html: Path, environment: str | None, subcommand: str) -> list[dict[str, str]]:
    cmd = hugo_base_cmd(site_root, tool_html, environment) + ["list", subcommand]
    res = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
    reader = csv.DictReader(io.StringIO(res.stdout))
    return list(reader)


def list_eligible_pages(
    site_root: Path,
    tool_html: Path,
    environment: str | None,
    include_drafts: bool,
    include_future: bool,
    include_expired: bool,
) -> list[dict[str, str]]:
    if not include_drafts and not include_future and not include_expired:
        return run_hugo_list(site_root, tool_html, environment, "published")

    all_rows = run_hugo_list(site_root, tool_html, environment, "all")
    excluded_paths: set[str] = set()
    if not include_drafts:
        excluded_paths.update(r["path"] for r in run_hugo_list(site_root, tool_html, environment, "drafts"))
    if not include_future:
        excluded_paths.update(r["path"] for r in run_hugo_list(site_root, tool_html, environment, "future"))
    if not include_expired:
        excluded_paths.update(r["path"] for r in run_hugo_list(site_root, tool_html, environment, "expired"))
    return [r for r in all_rows if r["path"] not in excluded_paths]


def has_explicit_front_matter_image(md_path: Path) -> bool:
    if not md_path.is_file():
        return False
    text = md_path.read_text(encoding="utf-8")
    if text.startswith("---\n") or text.startswith("---\r\n"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[4:end]
            return bool(re.search(r"^(?:image|images)\s*:\s*(?:\S|\n\s+-)", block, re.MULTILINE))
    elif text.startswith("+++\n") or text.startswith("+++\r\n"):
        end = text.find("\n+++", 3)
        if end != -1:
            block = text[4:end].split("\n[", 1)[0]
            return bool(re.search(r"^(?:image|images)\s*=\s*\S", block, re.MULTILINE))
    elif text.lstrip().startswith("{"):
        try:
            obj = json.loads(text)
            return bool(obj.get("image") or obj.get("images"))
        except ValueError:
            return False
    return False


def normalize_date(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("0001-01-01"):
        return ""
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", raw)
    return m.group(1) if m else ""


def resolve_post_route(content_dir: Path, md_path: Path, default_lang: str) -> tuple[str, str] | None:
    """Return (out_rel_png, seed) for a post markdown file, or None if bundle has a cover image."""
    rel = md_path.relative_to(content_dir)
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
    return out_rel, page_rel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", type=Path, default=Path.cwd(), help="Hugo site root directory")
    parser.add_argument("--environment", default=None, help="Hugo build environment")
    parser.add_argument("--sections", nargs="+", default=None, help="Content sections to generate OG images for")
    parser.add_argument("--include-drafts", action="store_true", help="Include draft posts (matches hugo --buildDrafts)")
    parser.add_argument("--include-future", action="store_true", help="Include future-dated posts (matches hugo --buildFuture)")
    parser.add_argument("--include-expired", action="store_true", help="Include expired posts (matches hugo --buildExpired)")
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

    cfg = load_site_config(site_root, tool_html, args.environment)
    params = cfg.get("params") or {}
    default_lang = cfg.get("defaultcontentlanguage") or "ja"
    fg = params.get("fg") or "#f7faf9"
    bg = params.get("bg") or "#05366e"
    logo_name = params.get("logoname") or cfg.get("title") or "Contour"
    logo_tld = params.get("logotld") or ""
    axis = params.get("axis") or "Elevation / Isoline Field"
    author = params.get("author") or ""
    target_sections = set(args.sections or params.get("mainsections") or ["posts"])

    rows = list_eligible_pages(
        site_root,
        tool_html,
        args.environment,
        include_drafts=args.include_drafts,
        include_future=args.include_future,
        include_expired=args.include_expired,
    )

    chrome_bin = find_chrome()
    generated = 0
    skipped = 0
    expected_outputs: set[Path] = set()

    with tempfile.TemporaryDirectory(prefix="contour-og-chrome-") as profile_dir:
        for row in rows:
            if row.get("kind") != "page":
                continue
            section = row.get("section", "")
            if section not in target_sections:
                continue
            title = row.get("title", "").strip()
            if not title:
                skipped += 1
                continue

            md_path = (site_root / row["path"]).resolve()
            if has_explicit_front_matter_image(md_path):
                skipped += 1
                continue

            route = resolve_post_route(content_dir, md_path, default_lang)
            if route is None:
                skipped += 1
                continue
            out_rel, seed = route
            out_path = (out_root / out_rel).resolve()
            expected_outputs.add(out_path)

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
                "date": normalize_date(row.get("date", "")),
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

    removed = 0
    if out_root.is_dir():
        for existing in sorted(out_root.rglob("*.png")):
            if existing.resolve() not in expected_outputs:
                existing.unlink()
                removed += 1

    print(f"done: {generated} generated, {skipped} skipped, {removed} stale removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
