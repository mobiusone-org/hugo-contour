# Contour

[English](README.md) | [日本語](README.ja.md)

等高線をモチーフにTypographyを取り込んだスタイリッシュなHugoテーマ。

- Hugo の新しいテンプレートシステム（`baseof.html` / `home.html` / `page.html` /
  `section.html` / `taxonomy.html` / `term.html`、予約ディレクトリ `_partials` と `_markup`）に準拠。
- タグ（タクソノミー）・アーカイブ・全文検索を標準でサポート。
- CSS / JS は Hugo Pipes で結合。本番ビルドでは minify + fingerprint + SRI。
- 見出し（h2）の連番は `_markup/render-heading.html` が自動付与。

## 必要環境

Hugo **extended** v0.146.0 以降（新テンプレートシステムのため）。

## LiveDemo

https://mobiusone-org.github.io/hugo-contour/

## LocalDemo（exampleSite）

このリポジトリには `exampleSite/` が同梱されている。
このリポジトリを`contour`としてcloneした後、 リポジトリ直下からテーマを読み込んでプレビューできる:

```bash
cd exampleSite
hugo server --themesDir ../..
```

## インストール

```bash
git submodule add https://github.com/mobiusone-org/hugo-contour.git themes/contour
```

`hugo.toml` に `theme = "contour"` を設定する。

> **注意:** フォルダ名は `theme = "contour"` と一致させること。リポジトリ名は
> `hugo-contour` だが、テーマフォルダ名は `contour` にする必要がある:
>
> ```bash
> # ✅ 正: フォルダ名が theme = "contour" と一致
> git submodule add https://github.com/mobiusone-org/hugo-contour.git themes/contour
>
> # ❌ 誤: フォルダ名が theme = "contour" と一致しない
> git submodule add https://github.com/mobiusone-org/hugo-contour.git themes/hugo-contour
> ```

## 設定

```toml
defaultContentLanguage = "ja"
locale = "ja-JP"
title = "MobiusOne.org"
theme = "contour"

[taxonomies]               # 標準的な分類。タグ一覧 /tags/ が自動生成される。
  tag = "tags"
  category = "categories"

[outputs]                  # /index.json を検索インデックスとして出力する。
  home = ["html", "json"]

[params]
  logoName = "MobiusOne"        # ロゴの太字部分
  logoTLD = ".org"              # ロゴ末尾の細字（TLD）
  kicker = "Software Engineering — Est. 2014"
  description = "サイトの説明。"
  axis = "Elevation / Isoline Field — N=54"   # 地図ふう装飾ラベル
  coords = "35.6812° N — 139.7671° E"          # 座標表示の初期値（クリックで更新）

# メニューは pageRef で実ページに結ぶ（タグ一覧は /tags、検索は /search …）。
[[menu.main]]
  name = "Posts"
  pageRef = "/posts"
  weight = 1
[[menu.main]]
  name = "Tags"
  pageRef = "/tags"
  weight = 5
```

## コンテンツ

| ファイル | レイアウト | 用途 |
|---|---|---|
| `content/_index.md` | `home.html` | ランディング（全画面の等高線＋メニュー） |
| `content/posts/_index.md` | `section.html` | 記事一覧 |
| `content/posts/*.md` | `page.html` | 記事ページ（左サイドバー＋本文） |
| `content/feature.md` | `page.html` | 単体ページ（日付・読了時間は出さない） |
| `content/archives.md` | `archives.html` | 年ごとの記事アーカイブ（`layout = "archives"`） |
| `content/search.md` | `search.html` | 全文検索（`layout = "search"`） |
| 自動生成 | `taxonomy.html` / `term.html` | `/tags/`・`/tags/<tag>/` |

`page.html` はセクション内の記事（`posts/`）では日付・読了時間・タグ・前後ナビを出し、
ルート直下の単体ページ（`feature.md` など）では見出しと本文だけにする。

### 検索

`hugo.toml` の `[outputs]` で `home` に `json` を足すと、`posts` セクションの記事から
`/index.json`（タイトル・タグ・要約・本文）が生成される。`content/search.md`
（`layout = "search"`）が依存ライブラリ無しのクライアント検索 UI を提供し、検索ページの
ときだけ `assets/js/search.js` が読み込まれる。`?q=...` で初期クエリを渡せる。
より大規模な索引が必要なら、同じページ構造のまま [Pagefind](https://pagefind.app/)
等への差し替えも可能。

記事の front matter:

```yaml
---
title: "記事タイトル"
date: 2026-06-12
tags: ["graphics", "canvas"]
---
```

## 等高線のカスタマイズ

`canvas[data-contour]` に data 属性で渡す:

- `data-color="--bg-rgb"` — 線色（CSS カスタムプロパティ名、または `"r, g, b"`）
- `data-cell="10"` — グリッドセルの大きさ (css px、小さいほど高精細)

配色は `assets/css/base.css` の `--bg` / `--fg`（および `--bg-rgb` / `--fg-rgb`）で変える。
RGB 版は描画に使うので必ず一致させること。

## ライセンス

MIT
