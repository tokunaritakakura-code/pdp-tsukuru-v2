# Shopify に置く（手順12a）

読む人: 店を作る Claude。
読む時: 審査が PASS になった直後（手順12a）。
読まなくていい条件: ローカルで作っている途中。

website-copy スキルの Shopify 連携を、このスキルだけで回るように写した物。道具は `scripts/chunk.mjs`・`scripts/upload-gcs.mjs`・`scripts/CDNに替える.py`。Shopify への読み書きは、その Mac でつないだ Shopify の MCP（GraphQL を投げられる物）で行う。

## 関門

| 線 | 中身 |
|---|---|
| 置くのは非公開テーマだけ | ライブ（MAIN）テーマには書かない。テーマを公開しない |
| 商品は DRAFT | 作る商品は `status: DRAFT` |
| 動くかの確かめ | MCP で `shop { name }` が返る。返らなければ下の手順の 1 を始めない |

## 手順

道具は店のフォルダで叩く。下の表の `<道具>` は `~/.claude/skills/pdp-tsukuru/scripts` の事（フルパスで指す）。`<店の英字>` は `index.html` の `HANDLE` と同じ名前。

| # | やる事 | 道具・呼び方 | 終わりの形 |
|---|---|---|---|
| 1 | 置く先の非公開テーマを決める。無ければライブを複製した非公開テーマを1つ作る | `themes(first:20){ nodes{ id name role } }`。role が `UNPUBLISHED` の物 | テーマの ID |
| 2 | `img/` の画像と動画を Shopify の Files に上げる: `stagedUploadsCreate`（1ファイル1行。`resource: FILE`・拡張子に合う `mimeType`・`httpMethod: POST`）→ 返事を `_shopify/img_targets.json` に保存 → `node <道具>/upload-gcs.mjs _shopify/img_targets.json img` → 全部 `201` → `fileCreate`（`originalSource` に resourceUrl）→ `nodes(ids:)` で CDN の URL を取る（画像は `... on MediaImage { image { url } }`、動画は `... on Video { sources { url } }` の欄）（取れるまで2秒おきに待つ） | MCP・`upload-gcs.mjs` | `_shopify/画像のURL.json`（ファイル名 → CDN の URL） |
| 3 | `index.html` を `_shopify/index.html` に写し、`img/` を指す所（`src`・`poster`・CSS の `url()`・スクリプトの `setImg`）を全部 2 の CDN の URL に替える | `python3 <道具>/CDNに替える.py . _shopify/画像のURL.json` が終了コード 0（`img/` の残りが 0） | CDN だけを指す `_shopify/index.html` |
| 4 | テーマ用に分ける | `node <道具>/chunk.mjs _shopify <店の英字> index.html` | `_shopify/theme/`（スニペットとテンプレート） |
| 5 | テーマのファイルを上げる: `stagedUploadsCreate`（`theme/` の全ファイル。`mimeType: text/plain`）→ `_shopify/theme_targets.json` → `node <道具>/upload-gcs.mjs _shopify/theme_targets.json _shopify/theme` → 全部 `201` → `themeFilesUpsert`（`snippets/<名前>.liquid` と `templates/product.<店の英字>.liquid`。body は `{type:"URL", value:<resourceUrl>}`） | MCP・`upload-gcs.mjs` | userErrors 0 |
| 6 | 商品を DRAFT で作り、テンプレートを割り当てる。ハンドルは `index.html` の `HANDLE` と同じにし、型番はセットの数（`1<UNIT>`・`2<UNIT>`・`3<UNIT>` の名前）× `OPTS` の選ぶ物で作り、値段は `TIERS` の `price` にする（ページの JS が型番の名前の「<数><UNIT>」と選ぶ物の名前で型番を引く） | `productCreate`（`status: DRAFT`）→ `productUpdate`（`templateSuffix: <店の英字>`） | `onlineStorePreviewUrl` |
| 7 | プレビュー URL（`<onlineStorePreviewUrl>&preview_theme_id=<テーマの数値 ID>`）を `店の設計.md` の頭に書く | Edit | 手順12b へ |

同じファイル名で画像を差し替えると古い画像が出続ける（`dame-list.md` の事故の番号 D4）。作り直した画像は名前を変えて上げる。

## 直しの記録

| 日付 | 直した事 |
|---|---|
| 2026-11-13 | 監査: Shopifyに置く.md 3件・直した（手順の番号・商品のハンドルと型番の作り方・道具を叩く場所） |
| 2026-11-14 | 監査: Shopifyに置く.md 4件・直した（道具の欄が相対のパスで、店のフォルダで叩くと見つからなかった。`src` だけを数える確かめは、CSS の背景8つ・poster・`setImg` を見逃し、Shopify で 404 になる所だった。`CDNに替える.py` を足した。無い手順 13a を指していた） |
| 2026-11-14 | 監査（3回目・上げる前）: Shopifyに置く.md 1件・直した（動画の URL を読む欄が画像と違うのに書いていなかった） |

## 最後の確かめ（置いた後に毎回当てる。全部○か理由つき×）

- [ ] 1 書いたテーマが非公開 — 確かめ: `themeFilesUpsert` の先のテーマの role が `UNPUBLISHED`
- [ ] 2 商品が DRAFT で、ハンドルが `HANDLE` と同じ — 確かめ: 作った商品の `status` と `handle`
- [ ] 3 `_shopify/index.html` に `img/` を指す所が 0 — 確かめ: `python3 <道具>/CDNに替える.py . _shopify/画像のURL.json` が終了コード 0
- [ ] 4 上げたファイルが全部 `201` — 確かめ: `upload-gcs.mjs` が終了コード 0
