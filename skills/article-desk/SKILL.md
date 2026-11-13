---
name: article-desk
description: 記事制作の入口（編集デスク）。依頼の種類を見分け、必要な工程だけを選び、専門エージェントを順に呼んで、中間成果物を案件フォルダに残しながら進める。「記事を作りたい」「この取材で記事にして」「先方のFBを反映して」「ここだけ直して」「事実確認だけ」「今どこまで進んだ？」「続きから」「この修正から学んで」と言われたら、記事制作の最初に使う。
argument-hint: "[案件スラッグ] [依頼の要約]"
---

# 編集デスク（入口）

案件と依頼：$ARGUMENTS

## 目的
依頼に合った工程だけを選び、正しい順に専門エージェントを呼んで進める。進行はこのスキル（メインの会話）が持つ。サブエージェントは別のサブエージェントを呼べないので、エージェントからエージェントへの受け渡しもここで行う。

## 使う場面
- 記事制作に関わる依頼の最初。案件の途中から再開するとき。

## 使わない場面
- 記事と関係のない作業。
- 一文の言い換え案を口頭で聞かれただけのとき（その場で答えてよい。原稿ファイルを書き換えるなら revision-control を通す）。

## 入力
- 依頼の原文（言い換えずに残す）
- 案件の `projects/<slug>/project.json` と `projects/<slug>/ledger.json`（あれば）
- 依頼に付いてきた資料（書き起こし・先方資料・前の記事・原稿）

## 手順
0. 最初に `${CLAUDE_PLUGIN_ROOT}/rules.md`（最上位のルールと場所の決まり）を読む。今のフォルダが作業フォルダでなければ（`aco.config.json` がない）、`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" init` で作業フォルダにしてよいか本人に一言聞いてから作る。
1. 案件を決める。
   - 引数か依頼から案件スラッグを決める。会社の案件は「会社/案件」（例 `japan-relief/no3-taidan`）にして、同じ会社の案件を一つの会社フォルダにまとめる。案件フォルダがなければ `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" new <会社>/<案件> --client <社名> --type <種類> --title <仮題>` で作る（会社フォルダもなければ作られる）。
   - 会社全体の決まり（表記・書かないこと・人名の扱い）は、案件ではなく会社の台帳に入れる：`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <会社> add …`。会社の資料（会社理解のメモなど）は `projects/<会社>/knowledge/` に置くか、`projects/<会社>/client.json` の `knowledge` に場所を書く。
   - 渡された資料は `projects/<slug>/sources/` に保存する。原本は書き換えない。
   - 途中からなら `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" status <slug>` で、済んだ工程・最新版・未解決の要確認・次の一手を見る。
   - 案件フォルダを作らない単発の作業（一回きりの添削・テスト）では、出力先に `history.md` と `*_notes.md` を置く。台帳がないので、次の手順の brief の代わりに `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" lessons list` を読む。
2. 制作の最初に `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` を読む。変更禁止・却下案・表記ルール・承認済みの全体ルールを、この後の全工程の前提にする。他の案件の台帳は読まない。
3. 依頼の種類を見分け、下の表で工程を選ぶ。迷ったら軽いほうを選び、足りなければ足す。見分け方の詳細は `${CLAUDE_PLUGIN_ROOT}/workflows/README.md`。

| 依頼の種類 | 工程（スキル） |
|---|---|
| 新規記事（取材済み） | STEP1 article-brief → STEP2 source-audit → STEP3 insight-discovery → STEP4 story-architecture（＋headline-craft）→ STEP5 article-writing → STEP6 レビュー → STEP7 修正 → STEP8 article-fact-check → STEP9 delivery-package → STEP10 feedback-learning |
| 取材前の案件 | STEP1 → STEP2（手元の資料だけ）→ interview-design → 取材のあと STEP2 からやり直す |
| 先方の FB 反映 | 指摘の意図の読み → revision-control → 直した所に関わるレビューだけ → delivery-package |
| 「ここだけ修正」「他は変えない」 | revision-control だけ（`aco scope` で範囲外の差分 0 を確かめる） |
| 既存原稿のブラッシュアップ | source-audit（原稿の中の事実と発言）→ ai-writing-audit・natural-japanese → editorial-critique → revision-control |
| 事実確認だけ | article-fact-check だけ |
| 学習だけ | feedback-learning だけ |

4. エージェントを呼ぶ。Agent ツールの `subagent_type` にエージェント名（`chief-editor` `research-editor` `interview-director` `story-architect` `feature-writer` `literary-editor` `brand-reputation-editor` `fact-checker` `adversarial-reviewer` `production-manager`）を入れる。渡すのは「案件スラッグ・この工程でやること・読むファイル・書くファイル」。担当と書く場所は `${CLAUDE_PLUGIN_ROOT}/docs/architecture.md` の §2〜§4。
5. STEP 6（レビュー）
   - 先に機械検査を回す：`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" audit <draft> --project <slug>`、`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" structure <draft>`（シリーズなら `--compare <前の記事>`）。
   - `literary-editor`・`brand-reputation-editor`・`fact-checker`・`adversarial-reviewer` を同時に呼ぶ。互いのレビュー票は読ませない（独立に見るため）。
   - そのあと `chief-editor` に全レビュー票を渡し、editorial-critique の chief モードで統合と 10 軸の採点をさせる。
6. STEP 7（修正）は、chief-editor が採った指摘だけを `feature-writer` に渡す。直したら全文を再評価する（STEP 6 に戻る。直した所だけを見ない）。
7. 工程が終わるたびに `projects/<slug>/project.json` の `stage` を更新する。ユーザーへの報告は一行で：終わった工程／できたファイル／本人が決めること（あれば一つ）。
8. 下の失敗条件に当たったら、その場で止めて報告する。

## 出力
- 各工程の中間成果物（置き場所は `${CLAUDE_PLUGIN_ROOT}/docs/architecture.md` §4）
- `projects/<slug>/project.json` の `stage`
- ユーザーへの短い報告

## 失敗条件（先へ進まずに止めて報告する）
止めたら `projects/<slug>/project.json` の `stage` を `blocked` にし、理由と誰の判断待ちかを `projects/<slug>/history.md` に書く。
- 未解決のブロッカー（根拠のない発言の創作・重要な事実の矛盾・未承認の機密・変更禁止違反・未解決の重大なブランドリスク）が残ったまま納品へ進もうとしている。`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" score <scores.json>` の結果とブロッカーを報告する。
- 修正を回しても点が伸びない（`aco score --history` が「頭打ち」）。追加取材・情報不足・判断待ちのどれかに分け、誰に何を聞くかを書いて止める。
- 中心の発見や必要な事実が素材にない。もっともらしい文で埋めず、追加で聞くことを挙げる。
- 依頼の範囲が読み取れない（どこを直すのか、誰の指示か）。狭いほうに取り、確認を一つだけ聞く。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/workflows/README.md`（依頼の種類ごとの工程選び）
- `${CLAUDE_PLUGIN_ROOT}/docs/architecture.md`（担当・ファイルの場所・スクリプト）
- `${CLAUDE_PLUGIN_ROOT}/philosophy/editorial-principles.md`
- `${CLAUDE_PLUGIN_ROOT}/philosophy/quality-standards.md`
