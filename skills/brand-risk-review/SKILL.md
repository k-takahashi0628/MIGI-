---
name: brand-risk-review
description: 企業広報・レピュテーションの確認。社員の分断、誰かを下げる比較、挑戦の手柄の偏り、社員への過剰な敬語、過去が無策に見える書き方、苦労話への偏り、ゆるい・遅い会社に読める否定の対比、言い切れない宣言、出したくない話、公開してよいか分からない情報、関係者への目配りの抜けを、読む人ごとに読み直して検出する。ネガティブな事実は消さずに、事実を保った表現にする案を出す。「広報的に大丈夫？」「炎上しない？」「社員が読んでどう思う？」「ブランドチェック」「リスクを見て」と言われたとき、STEP 6 で使う。
argument-hint: "[案件スラッグ]"
---

# 広報・レピュテーションの確認

案件：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグを使う）

## 目的
公開したあとに、社内外の誰かが傷つく・会社の見え方が崩れる文を、公開前に見つけて直す。事実は変えない。

## 使う場面
- STEP 6 のレビュー（brand-reputation-editor）。人・組織・過去の経緯に触れる記事はすべて。

## 使わない場面
- 事実が正しいかの確認（article-fact-check）。

## 入力
- 原稿（`projects/<slug>/drafts/v<N>.md`）
- `projects/<slug>/work/01_brief.md`（読む人）
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力（公開禁止・却下案・承認済みの表現）

## 手順
1. 台帳の brief と目的設計を読む。
2. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" audit <draft> --project <slug>` で、A1・B1・B5・C4 の兆候と台帳違反（公開禁止語・却下案）を拾う。
3. 読む人ごとに読み直し、引っかかる文を拾う：経営者／広報／社員（とくに名前の出ない人・前からいる人）／取引先・パートナー／候補者／家族。
4. 負け筋の A（人と関係者）と B（会社の見え方）を上から順に当てる。
5. 意図しない比較（新旧・部署・前職との比較）、一部の人だけが優秀に見える書き方を探す。直すときは主語を会社・組織・全員にする。発言の意味が変わる直しはセリフに入れず、地の文や構成で対応するか、本人確認に回す。
6. ネガティブな事実は消して済ませない。意図した選択・いまの状態・それを支える仕組みとして書く案を出す（`${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/brand-voice-and-respect.md`）。事実そのものを出せない場合は、外す理由と判断する人を書く。
7. 公開してよいか分からない情報を全部挙げる（台帳の pending への登録は production-manager）。
8. 重大度を付ける（高＝公開を止める）。高が残るなら、scores.json のブロッカー（brand-risk・confidential）に挙げるよう chief-editor に伝える。

## 出力
- `projects/<slug>/work/reviews/v<N>_brand.md`（`${CLAUDE_PLUGIN_ROOT}/templates/review.md` の形。冒頭に結論、各指摘に箇所・根拠・修正案・副作用・判断が要る人）

## 失敗条件（出さずに止めて報告する）
- 事実を変えて印象を良くする修正案を出した。
- `aco audit` が error（公開禁止語・却下案）を出しているのに「問題なし」とした。
- 修正案に副作用の欄がない。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/official-article.md`（A1〜A6・B1〜B7）
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/brand-voice-and-respect.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/review.md`
