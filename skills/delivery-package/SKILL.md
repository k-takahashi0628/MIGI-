---
name: delivery-package
description: 納品物の作成（STEP 9）。納品前チェック（aco audit --final・ledger check・quotes・score）を通したうえで、そのまま貼れる清書、修正表（修正前→修正後→当たった負け筋。場所は章の見出しと問いの文）、要確認の一覧（コメントを付ける場所つき）、返信文（決裁者あて・進行担当あて）を作る。候補者に見せる成果物に社内メモを残さない。「納品用にまとめて」「清書して」「返信文を作って」「修正表を作って」「先方に送る形にして」と言われたときに使う。
argument-hint: "[案件スラッグ]"
---

# 納品（STEP 9）

案件：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグを使う）

## 目的
先方が迷わずに確認・判断・貼り付けできる形で渡す。どれが最終版か、何を直したか、何を確かめてほしいかが一目で分かるようにする。

## 使う場面
- STEP 9。先方の FB を反映した版を返すとき。

## 使わない場面
- チェックが通っていない原稿を「とりあえず」渡すとき（止めて報告する）。

## 入力
- 最新版の原稿、前に先方へ渡した版
- `projects/<slug>/history.md`、その版のレビュー票と scores.json
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力（要確認の一覧）

## 手順
1. 納品前チェックを回す（`${CLAUDE_PLUGIN_ROOT}/templates/delivery-checklist.md`）。
   - `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" audit <最新版> --final --project <slug>`（error が 0）
   - `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> check <最新版>`
   - `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" quotes <最新版> --transcript <書き起こし>`（D・E が 0。残るなら要確認に挙げ済みであること）
   - `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" score <最新の scores.json>`（公開不可でない）
   一つでも通らなければ清書を作らずに止めて報告する。
2. 出す順番は、修正前→修正後のテキストを先、説明は後。場所は必ず章の見出しと問いの文で示す。
3. 清書 `projects/<slug>/delivery/final_v<N>.md`：そのまま貼れる形。章のタイトルから、その章の最後の一文まで。【要確認】の印・社内メモ・出典名・版情報コメントは残さない（要確認は別の一覧へ）。【要取材】が残っているなら清書は作らない。
4. 修正表 `projects/<slug>/delivery/revision-table.md`：`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" revtable <前に渡した版> <最新版> --out <file>` で作り、各行に当たった負け筋の番号と理由を書き足す（`${CLAUDE_PLUGIN_ROOT}/templates/revision-table.md`）。
5. 要確認 `projects/<slug>/delivery/open-questions.md`：根拠のない所・書き足した所・公開してよいか確認が要る所と、ドキュメントでコメントを付ける場所（`${CLAUDE_PLUGIN_ROOT}/templates/open-questions.md`）。
6. 返信文 `projects/<slug>/delivery/reply.md`（`${CLAUDE_PLUGIN_ROOT}/templates/reply.md`）：決裁者あてと進行担当あてに分ける。直した要点は先方の案・指摘の項目どおりに並べる。案から変えた所は理由を一言。担当者の案を消したときは、その理由を添える。要確認と期日を書き、前日にこちらからリマインドする予定を書く。
7. どれが最終版かを明記する（ファイル名に版。返信に「最終版は〜」）。
8. チェックの結果を `projects/<slug>/delivery/checklist.md` に残し、`projects/<slug>/project.json` の `stage` を `09_delivered` にする。

## 出力
- `projects/<slug>/delivery/` の final_v<N>.md・revision-table.md・open-questions.md・reply.md・checklist.md

## 失敗条件（出さずに止めて報告する）
- 納品前チェックが通らない。
- 清書に社内メモ・【要確認】・【要取材】が残っている。
- 返信に期日がない。場所を「最後の問い」「締め」のように章の見出しなしで書いた。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/templates/delivery-checklist.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/revision-table.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/open-questions.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/reply.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/approved-lessons/LESSONS.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/official-article.md`（H1〜H5・A5）
