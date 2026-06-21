# Contour

[English](README.md) | [日本語](README.ja.md)

A stylish Hugo theme that blends contour-line motifs with typography.

- Built on Hugo's new template system (`baseof.html` / `home.html` /
  `page.html` / `section.html` / `taxonomy.html` / `term.html`, with the
  reserved `_partials` and `_markup` directories).
- Supports tags, archives, and full-text search out of the box.
- Bundles CSS and JavaScript with Hugo Pipes. Production builds are minified,
  fingerprinted, and served with SRI metadata.
- Automatically numbers h2 headings with `_markup/render-heading.html`.

## Requirements

Hugo **extended** v0.146.0 or later, required for the new template system.

## Live Demo

https://mobiusone-org.github.io/hugo-contour/

## Local Demo (exampleSite)

This repository includes an `exampleSite/`. Clone this repository as `contour`,
then preview the bundled example site from the repository root:

```bash
cd exampleSite
hugo server --themesDir ../..
```

## Installation

```bash
git submodule add https://github.com/mobiusone-org/hugo-contour.git themes/contour
```

Then set `theme = "contour"` in your `hugo.toml`.

> **Note:** The folder name must match `theme = "contour"`. The repository is
> named `hugo-contour`, but the theme folder must be `contour`:
>
> ```bash
> # ✅ correct — folder matches theme = "contour"
> git submodule add https://github.com/mobiusone-org/hugo-contour.git themes/contour
>
> # ❌ wrong — folder name does not match theme = "contour"
> git submodule add https://github.com/mobiusone-org/hugo-contour.git themes/hugo-contour
> ```

## Configuration

```toml
defaultContentLanguage = "en"
locale = "en-US"
title = "MobiusOne.org"
theme = "contour"

[taxonomies]               # Standard taxonomies. /tags/ is generated automatically.
  tag = "tags"
  category = "categories"

[outputs]                  # Generate /index.json for the search index.
  home = ["html", "json"]

[params]
  logoName = "MobiusOne"        # Bold part of the logo
  logoTLD = ".org"              # Lighter suffix shown after the logo name
  kicker = "Software Engineering - Est. 2014"
  description = "Site description."
  axis = "Elevation / Isoline Field - N=54"   # Map-style decorative label
  coords = "35.6812 deg N - 139.7671 deg E"   # Initial coordinates, refreshed on click

# Use pageRef to connect menu items to real pages.
[[menu.main]]
  name = "Posts"
  pageRef = "/posts"
  weight = 1
[[menu.main]]
  name = "Tags"
  pageRef = "/tags"
  weight = 5
```

## Content

| File | Layout | Purpose |
|---|---|---|
| `content/_index.md` | `home.html` | Landing page with full-screen contour lines and the menu |
| `content/posts/_index.md` | `section.html` | Post list |
| `content/posts/*.md` | `page.html` | Article pages with a left sidebar and body content |
| `content/feature.md` | `page.html` | Standalone page without date or reading time |
| `content/archives.md` | `archives.html` | Yearly article archive (`layout = "archives"`) |
| `content/search.md` | `search.html` | Full-text search (`layout = "search"`) |
| Generated automatically | `taxonomy.html` / `term.html` | `/tags/` and `/tags/<tag>/` |

For pages in the `posts/` section, `page.html` displays the date, reading time,
tags, and previous/next navigation. For standalone pages at the content root,
such as `feature.md`, it only displays the title and body.

### Search

Add `json` to the `home` output in `hugo.toml` to generate `/index.json` from
posts. The index contains each post's title, tags, summary, and body text.
`content/search.md` (`layout = "search"`) provides a dependency-free client-side
search UI, and `assets/js/search.js` is loaded only on the search page. You can
also pass an initial query with `?q=...`.

For larger search indexes, you can replace this with
[Pagefind](https://pagefind.app/) or a similar tool while keeping the same page
structure.

Post front matter:

```yaml
---
title: "Post title"
date: 2026-06-12
tags: ["graphics", "canvas"]
---
```

## Customizing Contour Lines

Pass options through data attributes on `canvas[data-contour]`:

- `data-color="--bg-rgb"`: Line color, either a CSS custom property name or an
  `"r, g, b"` value.
- `data-cell="10"`: Grid cell size in CSS pixels. Smaller values produce finer
  detail.

Change colors with `--bg` / `--fg` in `assets/css/base.css`. Their RGB
counterparts, `--bg-rgb` / `--fg-rgb`, are used by the canvas renderer and must
stay in sync.

## License

MIT
