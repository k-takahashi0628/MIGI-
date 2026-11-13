---
name: natural-japanese
description: 不自然な日本語の修正。口語・カタカナの口語・弱い文末と二重のぼかし・同じ語の近い繰り返し・類語の使い回し・ねじれ・指す先のあいまいさ・頭でっかちな文・論理の飛び・名詞だけで意味が分からない言葉を直す。話し手の口調と意味のある不均一さは残し、必要な所だけを最小の変更で直す。飾りは足さない。「日本語を自然にして」「読みにくい」「稚拙さを直して」「文章を整えて」「推敲して」と言われたときに使う。
argument-hint: "[案件スラッグ] [対象ファイル]"
---

# 自然な日本語

対象：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグと原稿を使う）

## 目的
読みにくさと稚拙さを、意味を変えずに取り除く。話し手の個性は消さない。

## 使う場面
- STEP 6 の文章レビュー（literary-editor）。執筆中・修正中の推敲（feature-writer）。

## 使わない場面
- 構成や中身の問題（story-architecture・editorial-critique）。事実の誤り（article-fact-check）。

## 入力
- 原稿（`projects/<slug>/drafts/v<N>.md`）
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力（表記ルール・変更禁止）
- 範囲の指定（あれば）

## 手順
1. 台帳の brief を読む。範囲の指定があれば、その範囲の外は見ても直さない（revision-control の手順で直す）。
2. 機械で拾う：`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" audit <file> --project <slug>`（D1〜D6・D9・D10・D13・G3 と表記ルール）。
3. 人の目で読む：ねじれ（主語と述語だけを抜き出して読む）、指示語の指す先、論理の飛び（間の一段が抜けていないか）、名詞だけの言葉、問いと答えのかみ合い。
4. 一つずつ、直すか残すかを決める。残すもの：
   - 話し手の口調・言葉の癖。地の文とセリフで基準を分ける。セリフの口語は、媒体のトーンと本人の話し方に合っていれば残す。
   - 意味のある繰り返し（強調・対句として効いているもの）。
   - 文の長さのばらつき（全部を同じ長さにそろえない）。
5. 直すときは最小の変更にする。言い換えで意味・範囲・強さが変わらないかを確かめる。変わるおそれがあれば、元の文と並べて要確認にする。
6. 飾りを足さない。比喩・強調語・決め台詞を新しく入れない。
7. 出し方を担当で分ける。
   - レビューとして使う（literary-editor）：原稿は書き換えず、`${CLAUDE_PLUGIN_ROOT}/templates/review.md` の形でレビュー票を書く。
   - 執筆者が使う（feature-writer）：直した所を修正表（今 → 直し → 理由）にして原稿と一緒に返す。

## 出力
- レビュー票：`projects/<slug>/work/reviews/v<N>_literary.md`
- または 修正後の原稿 ＋ 修正表

## 失敗条件（出さずに止めて報告する）
- 指定の範囲の外を直した。
- 話し手全員が同じ文体になった。
- 言い換えで発言の意味・範囲が変わったのに、要確認にしていない。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/philosophy/human-writing.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/official-article.md`（D1〜D13・E2・E3・G1〜G3）
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/quote-editing.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/review.md`
