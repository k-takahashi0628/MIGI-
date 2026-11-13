---
name: feedback-learning
description: 修正履歴と先方の指摘から、次の制作で使える判断を「承認待ちの候補」として取り出す（STEP 10）。案件固有のものは案件台帳の proposals に、同じ会社の全案件に使えるものは会社の台帳（projects/<会社>/client-ledger.json）の proposals に、全案件に使えるものは knowledge/approved-lessons/proposed.json に入れ、本人の明示の承認があってから規則にする。案件固有のルールを全体に広げない。社名・人名は全体の候補に入れない。「この修正から学んで」「次から気をつけることをまとめて」「ナレッジにして」「指摘を蓄積して」と言われたとき、納品後に使う。
argument-hint: "[案件スラッグ]"
---

# 修正からの学習（STEP 10）

案件：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグを使う）

## 目的
同じ指摘を二度受けないために、判断を再利用できる形で残す。承認のない判断は規則にしない。

## 使う場面
- 納品後。先方から大きな指摘を受けたあと。

## 使わない場面
- 制作の途中で、思いつきを規則にしたいとき（候補として残すだけにする）。

## 入力
- `projects/<slug>/history.md`、先方の指摘の原文、版ごとの差分（`aco revtable`）
- その案件のレビュー票、`projects/<slug>/ledger.json`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/approved-lessons/LESSONS.md`、`${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/official-article.md`

## 手順
1. 指摘を一つずつ分ける：何を言われたか（原文）／何を直したか／なぜそう言われたか（読む人がどう感じるのを避けたかったか）。理由が分からないものは「推測」と書く。
2. 分類する。
   - その案件だけのこと（表記・呼称・その会社の言い方・決裁者の好み）→ 案件の候補
   - 公式記事全般・インタビュー記事全般・修正の進め方・納品の出し方に使えること → 全体の候補
   - 一度きりの判断・理由が分からないもの → 候補にしない（history に残すだけ）
3. 既存の知識と重ならないか確かめる。重なるなら新しい候補にせず、既存の項目の実例として挙げる。
4. 案件の候補：`projects/<slug>/ledger.json` の proposals に、status を proposed にして加える。同じ会社のほかの案件にも効かせたい候補（表記・書かないこと・人名の扱いなど）は、会社の台帳 `projects/<会社>/client-ledger.json` の proposals に入れる（承認は `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <会社> approve PR-n --by <名前>`）。kind（rules／approved／rejected／locked／decisions）・payload・根拠（evidence）を書く。`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> add` で proposals を扱えなければ、ledger.json に直接書く。
5. 全体の候補：`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" lessons propose …`（引数は `--help` で確かめる）。社名・人名・未公開の語・その案件でしか通じない言葉を入れない。一般化できないものは全体に上げない。
6. 候補を `${CLAUDE_PLUGIN_ROOT}/templates/lesson-proposal.md` の形で本人に見せ、一つずつ判断をもらう。明示の OK があったものだけ承認する。
   - 案件：`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> approve <PR-id> --by <名前>`
   - 全体：`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" lessons approve <PL-id> --by <名前>` のあと `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" lessons render`
   却下されたものは reject して理由を残す。返事がないものは proposed のまま置き、規則として使わない。
7. `projects/<slug>/project.json` の `stage` を `10_learned` にする。

## 出力
- 候補の一覧（`${CLAUDE_PLUGIN_ROOT}/templates/lesson-proposal.md` の形）
- `projects/<slug>/ledger.json` の proposals
- `${CLAUDE_PLUGIN_ROOT}/knowledge/approved-lessons/proposed.json`

## 失敗条件（出さずに止めて報告する）
- 承認のない候補を規則にした。
- 全体の候補に社名・人名・案件でしか通じない言葉が入った（`aco lessons approve` も拒否する）。
- 一つの案件の好みを、全体の原則として書いた。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/knowledge/approved-lessons/README.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/approved-lessons/LESSONS.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/lesson-proposal.md`
- `${CLAUDE_PLUGIN_ROOT}/docs/architecture.md`（§8 学習の仕組み）
