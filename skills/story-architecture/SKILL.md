---
name: story-architecture
description: 構成設計（STEP 4）。記事の背骨（読み手・一番の印象・中心の発見）から、リード・章立て・情報の順序・読者の疑問・山場・結末を設計し、各章が目的にどう効くかを書く。型はそのまま使わず、素材に合わせて選ぶか組む。既存原稿の立て直しでは、元の章ごとに残す／移す／まとめる／削るとその理由を出す。「構成を考えて」「章立てを作って」「構成を見直して」「並べ替えて」「構成案を作って」と言われたとき、STEP 4 と、目的からずれた原稿の立て直しに使う。
argument-hint: "[案件スラッグ]"
---

# 構成設計（STEP 4）

案件：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグを使う）

## 目的
読者の理解と興味の順に情報を並べ、すべての章を記事の目的に結びつける。

## 使う場面
- STEP 4。章立てが目的からずれた原稿を立て直すとき。先方から構成案が来たとき。

## 使わない場面
- 見出しの言い回しだけを直すとき（headline-craft、範囲が決まっていれば revision-control）。

## 入力
- `projects/<slug>/work/01_brief.md`・`projects/<slug>/work/02_source-audit.md`・`projects/<slug>/work/03_insight.md`
- 前の記事（シリーズのとき）、既存原稿（立て直しのとき）、先方の構成案（あれば）
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力

## 手順
1. 上の入力を読む。シリーズなら `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" structure <前の記事>` で字数と問いの数を見る。立て直しなら既存原稿にも `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" structure <原稿>` を回す。
2. 背骨を一文で書く（読み手 → 一番の印象 → 中心の発見）。
3. 先方の構成案があるときは、並べ替える前に、案の意図（誰が読んでどう感じるのを避けたいか）と項目どうしのつながりを 3〜5 行で書き出す。
4. `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/structure-types.md` から近い型を選ぶ。合わなければ、型を使わない理由を書いて素材から組む。
5. 章ごとに `${CLAUDE_PLUGIN_ROOT}/templates/structure.md` の表を埋める：見出し案（その章の答えを言い切る）／この章が答える読者の疑問／使う素材（素材分析の行）／一番の印象への効き方／字数の目安／問いの数（インタビューなら 1 章 2〜3 が目安。記事の性質で変えてよい）。
6. 並べ方を確かめる：理由 → 結論、全体 → 具体、変化 → それを支える仕組み。山場は終盤（章の順で数えて後半 3 分の 1。最後の問いの手前が基本。字数ではなく章の順で測る）。リードの問いに章が順に答えるか。締めはリードの言葉で回収し、本文にない枠を持ち込まないか。
7. 構成の検査を全部当てて、結果を書く。
   - 一番の印象に関係しない章はないか
   - 同じことを二つの章で言っていないか
   - 全章の主語が特定の人たちになっていないか
   - 山場はどこか。終盤にあるか
   - リードの問いと締めが対応しているか
   - 前の記事と同じ問いを繰り返していないか
8. 立て直しのときは、元の章ごとに「残す／移す／まとめる／削る」と理由（目的のどこに効く・効かない）を表にする。削る章の素材で惜しいものは、どこへ移すかを書く。

## 出力
- `projects/<slug>/work/04_structure.md`（`${CLAUDE_PLUGIN_ROOT}/templates/structure.md` の形）

## 失敗条件（出さずに止めて報告する）
- 背骨が一文で書けない。article-brief か insight-discovery に戻す。
- 山場にできる具体のエピソードがない。追加取材の候補を挙げる。
- 立て直しで、章の扱いに理由のない行がある。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/structure-types.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/lead-and-ending.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/headlines-and-questions.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/official-article.md`（F1〜F7・E7）
- `${CLAUDE_PLUGIN_ROOT}/templates/structure.md`
