---
name: article-brief
description: 記事の目的設計（STEP 1）。誰に向けるか、読み終えて一言で何と思ってほしいか、読んだ人に何をしてほしいか、決裁者と進行担当、シリーズの中の役割、媒体と長さを一文ずつ決めて残す。書けない項目は推測で埋めず本人に聞く。「記事の目的を決めて」「企画を固めて」「誰向けの記事？」「ブリーフを作って」と言われたとき、新規記事の最初に使う。
argument-hint: "[案件スラッグ]"
---

# 目的設計（STEP 1）

案件：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグを使う）

## 目的
記事の目的を一文ずつ決める。ここが書けないうちは構成を作らない。

## 使う場面
- 新規記事の最初。目的があいまいなまま原稿が来たとき（直す前に目的を確かめる）。

## 使わない場面
- 「ここだけ修正」など、範囲の決まった修正（revision-control を使う）。

## 入力
- `projects/<slug>/project.json`
- `projects/<slug>/sources/` の依頼メール・企画書・前の記事
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力

## 手順
1. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` を読む。
2. 依頼の原文を、言い換えずに引用して残す。自分の解釈はその下に分けて書く。
3. `${CLAUDE_PLUGIN_ROOT}/templates/brief.md` の項目を一文ずつ埋める。
   - 一番の読み手と、ほかに読む人（社員・取引先・家族・既存の顧客など）
   - 読み終えて一言で何と思ってほしいか（一番の印象）
   - 読んだ人にしてほしいこと
   - 最終の決裁者と、進行・品質の担当
   - シリーズの中の役割と、前の記事の締めで予告した言葉（あれば守る）
   - 媒体・長さの目安（前の記事があればその字数）・記事の種類
4. 一番の印象を、社名を別の会社に替えて読む。そのまま通じるなら、この会社・この人でしか言えない形に絞り直す（`${CLAUDE_PLUGIN_ROOT}/philosophy/editorial-principles.md`）。
5. 書けない項目は空けたまま「本人に聞くこと」に挙げる（3 つまで）。仮に置くなら【仮】と付ける。
6. 新規記事なら、本人の確認をもらってから次の工程へ進む。

## 出力
- `projects/<slug>/work/01_brief.md`（`${CLAUDE_PLUGIN_ROOT}/templates/brief.md` の形）
- 本人に聞くこと（3 つまで）

## 失敗条件（出さずに止めて報告する）
- 一番の読み手か一番の印象が一文で書けない。構成へ進まず、聞くことを挙げる。
- 決裁者が分からない。確認事項に挙げる（意見がぶつかったときの優先が決められないため）。
- 依頼の原文と自分の解釈が混ざっている。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/templates/brief.md`
- `${CLAUDE_PLUGIN_ROOT}/philosophy/editorial-principles.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/structure-types.md`（記事の種類）
- `${CLAUDE_PLUGIN_ROOT}/references/derived/A_classification.md`
