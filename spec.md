# spec.md — Discontinued Cosmetics Aggregator

## サービス名
discontinued-cosmetics (公開仮名: Holy Grail Archive)

## 一言で
海外 holy grail 探索層に廃番化粧品の発売年/廃番年/中古相場時系列/後継品を1サイトで提供する静的 aggregator。WatchCharts の化粧品版。

## 種類
静的サイト → GitHub Pages (humancronadmin 配下サブレポ)

---

## STEP 1 解法
- **何を**: 廃番化粧品の商品DB集約サイト (英語SEO+Reddit流入)
- **核機能 (MVP=1個のみ)**: 商品詳細ページ — `brand / product / category / launched_year / discontinued_year / original_price_USD / 中古相場時系列グラフ / successor / dupes / Reddit言及URL`
- **使う既存**: eBay Browse API 無料tier / PRAW (r/MakeupAddiction scrape) / Estée Lauder GBNF scrape / Temptalia archived scrape / Gemini Free (英語本文) / Buttondown 無料 / GA4

---

## STEP 2 GitHub探索結果

### 検索3パターン
1. `price tracker static site Next.js discontinued aggregator` → Pricewise系 (DB必須・静的化困難・不採用)
2. `watchcharts price history clone static HTML` → Mendiak/bitcoin.history (D3.js 静的・参考のみ)
3. `astro starter product catalog directory listing template MIT` → **採用候補ヒット**

### 候補
| URL | スター/更新/ライセンス | 使う部分 | 変更量 |
|---|---|---|---|
| https://github.com/masterkram/minted-directory-astro | 100+/2025/MIT | Markdown駆動 directory・SEOメタ・JSON/CSV取込・Tailwind | 中 |
| https://github.com/flamrdevs/astrobuckt | 30+/Astro+React+Tailwind | 商品カタログUI | 大 |
| https://github.com/Mendiak/bitcoin.history | 50+/D3.js | 相場グラフコード片移植 | 部分 |

### 採用
**masterkram/minted-directory-astro** (1次ベース) + **Mendiak/bitcoin.history** の D3.js グラフ移植。Markdown駆動=AI生成パイプ相性◎・GitHub Pages即デプロイ・SEO最適化済。

---

## STEP 2.5 デザイン参照 (WatchCharts/BAT/hwpriceguide/brickeconomy 分解)

### ヘッダ
左ロゴ・中央検索バー (商品名/ブランド)・右 Newsletter CTA。

### 商品詳細レイアウト
```
[Breadcrumb: Brands > MAC > Lipstick > Pink Friday]
[H1: MAC Pink Friday Lipstick (Discontinued 2010)]
[左: 公式画像 / 右: メタテーブル (発売年/廃番年/旧定価/カテゴリ)]
[相場グラフ D3.js 折れ線 (eBay sold 時系列)]
[直近 sold listings リスト (date/platform/price/link)]
[Successor / Dupes セクション]
[Reddit 言及リンク 3-5本]
[Newsletter CTA インライン]
[Related: 同ブランド廃番品 / 同カテゴリ廃番品]
```

### 配色 (WatchCharts系ニュートラル)
背景`#FAFAFA` / カード`#FFFFFF` / テキスト`#1A1A1A` / アクセント`#C9A961` / グラフ`#D4A574`。ダークモード非対応。

### CTA
- ヘッダ右: `Get Monthly TOP10 Holy Grails` (Newsletter)
- 商品ページ下: `Track this product (Premium)` プレースホルダ (Phase4まで非有効)

### SEOメタ
- title: `[Brand] [Product] - Discontinued [Year] | Price History & Successors`
- description ≤160字 (後継品・相場サマリ含む) / og:image 商品公式画像 / canonical

---

## STEP 3 仕様詳細

### 商品DBスキーマ (1商品=1 .md frontmatter)
```yaml
brand: MAC
product_name: Pink Friday
slug: mac-pink-friday
category: lipstick   # lipstick/eyeshadow/foundation/blush/mascara/fragrance/skincare
launched_year: 2010
discontinued_year: 2010
original_price_usd: 15.00
sold_history:
  - {date: 2024-03-15, platform: ebay, price_usd: 260, url: https://ebay.com/itm/...}
successor_product: null
dupes:
  - {brand: NYX, product: Pin-Up Pout}
reddit_mentions: [https://reddit.com/r/MakeupAddiction/...]
sources: [https://...]   # 必須・空は公開禁止
```

### MVP除外 (Phase1で作らない)
ユーザーアカウント / プレミアム課金 (Phase4) / B2Bレポ LP (Phase6) / 相場アラート (Phase4) / 真贋判定 (恒久作らない・User無資格) / レビュー投稿UGC (Phase6以降) / 多言語

### MVP形式
Astro 静的書き出し → GitHub Pages。100品 .md + 商品テンプレ1本 + トップ + ブランド一覧 + カテゴリ一覧。

### MVP検証
r/MakeupAddiction "holy grail discontinued" reply 5本 (URL付・Mom Test DM 10件並行) → GA4 で流入/滞在/CTR/Newsletter登録率計測。

### MVP判定 (KILL線)
- Day7: MVP公開未達=即見直し
- Day14: 100品DB未達=scrape設計見直し
- **Day28: 月1K PV未達=SEO pivot or KILL**
- Day90: 月1万PV+初アフィ成果未達=KILL
- Day180: ¥10K MRR未達=KILL

---

## デプロイ手順 (build エージェント向け)
```bash
gh repo create humancronadmin/discontinued-cosmetics --public
git clone https://github.com/masterkram/minted-directory-astro.git temp-base
# src/content/config.ts を上記スキーマに差し替え
# src/pages/[brand]/[slug].astro 商品テンプレ作成 (D3.js グラフ埋込)
# seed 100品 .md (eBay Browse API + r/MakeupAddiction scrape + GBNF + Temptalia archived)
npm run build  # → dist/
# gh-pages ブランチへ push → GitHub Pages 有効化
# GSC sitemap.xml 登録 / GA4 タグ
```

---

## 収益化 (MIX採用 / Day365 月¥20万)
- A2 アフィ (Amazon US / eBay Partner Network / Mercari申請可なら / Depop): ¥10万 (CV 67/月)
- B プレミアム ¥980/月: ¥7万 (71会員) — Phase4から
- C B2Bレポ ¥9,800/月: ¥3万 (3社) — Phase6・送信1,000通/月は受注NG抵触ゆえ要再設計

---

## publish 向け
- ターゲット: 海外 holy grail 探索層・25-50女性中心
- 訴求: "Find any discontinued lipstick / eyeshadow in 3 minutes"
- 投稿先: r/MakeupAddiction / r/MUAontheCheap / r/PanPorn / 匿名X
- Positioning: "The WatchCharts of discontinued cosmetics"

---

## 厳守事項
- 体験レビュー禁止・データ集約のみ (User無資格・当事者性なし)
- 真贋判定/医療助言ゼロ
- 一次情報源URL必須 (sources 空のエントリ公開禁止)
- ダミーデータ禁止 / アフィID事前確認 (Amazon Associates US / eBay Partner Network)
