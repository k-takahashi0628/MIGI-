---
name: headline-craft
description: タイトル・見出し・リードの制作。章の答えを言い切る見出し、前の記事と対になるタイトル、本文で回収できるリードを作り、案ごとに狙い・回収する場所・弱点を書いて一つを推す。言い過ぎ・結果を約束する言い方・説明調・飾りを避ける。「タイトルを考えて」「見出しを直して」「リードを書いて」「キャッチを考えて」と言われたときに使う。
argument-hint: "[案件スラッグ]"
---

# タイトル・見出し・リード

案件：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグを使う）

## 目的
記事の中で回収できる言葉だけで、タイトル・見出し・リードを作る。

## 使う場面
- 構成のあと（STEP 4 の続き）。見出しと中身がずれていると言われたとき。

## 使わない場面
- 本文が決まっていない段階で、タイトルだけを先に固めること（仮題にとどめる）。

## 入力
- `projects/<slug>/work/01_brief.md`・`projects/<slug>/work/03_insight.md`・`projects/<slug>/work/04_structure.md`
- 原稿（あれば）、前の記事のタイトルと見出し
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力（承認済みの表現・却下案）

## 手順
1. 上の入力を読む。台帳の却下案は使わない。
2. タイトル案を 3〜5 出す。各案に、狙い（誰の何に響くか）・本文で回収する場所・弱点（言い過ぎ／抽象的／他社でも言える）を書く。
3. 避ける：言い切れない大きな宣言、結果を約束する言い方、一人の事例を全員に広げる言い方、どの会社にも使える言い方。
4. 見出しは、その章の答えを言い切る。章の中心と見出しがずれていないかを本文で確かめる。前の記事の見出しの型にそろえる。
5. 「AとB」型の見出しの連続・絵文字・記号の飾り・説明調を避ける。
6. リードは読者の疑問を一つ立て、本文の章が順に答える形にする。締めでどの言葉を回収するかを書いておく。
7. 推す案を一つ決め、理由を一行で書く。

## 出力
- `projects/<slug>/work/05_headlines.md`（`${CLAUDE_PLUGIN_ROOT}/templates/headlines.md` の形）
- 本文への反映は feature-writer が行う（範囲の決まった差し替えは revision-control）。

## 失敗条件（出さずに止めて報告する）
- 本文の中に回収する場所がないタイトル・リード。
- 見出しと章の中心がずれたまま。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/headlines-and-questions.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/lead-and-ending.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/official-article.md`（F4・F5・B5）
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/ai-writing-signs.md`（AI-16）
- `${CLAUDE_PLUGIN_ROOT}/templates/headlines.md`
