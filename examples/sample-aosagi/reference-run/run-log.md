# 実行記録：/article-desk sample-aosagi（2026-11-11）

- 依頼：「/article-desk sample-aosagi 依頼メモと取材の記録から、社員インタビュー記事を作りたい」
- 依頼の種類：新規記事（取材済み）→ STEP 1〜9 ＋ STEP 10（候補だけ）。
- サブエージェントは使えないため、各エージェントの役をメインの会話で順に演じた（`.claude/agents/<name>.md` と、その `skills:` のスキル、スキルが指す知識ファイルだけを読んだ）。STEP 6 は 4 人の票を、他の票を読み返さずに 1 枚ずつ書いてから統合した。
- 書いたのは `projects/sample-aosagi/` の中だけ。

## 結論
- **最終判定：`aco score` v2 = 合計 60／100、公開不可（ブロッカー 4：未承認の機密 3〔氏名・2019 年の作り直しと 300 食分・冷凍麺のラインと時期〕、重要な事実の矛盾 1〔ノートの時期と「3年分」〕）。推移 57 → 60。**
- 納品前チェックが通らないため、清書（final_v2.md）は作らず、確認のお願い（reply・open-questions・revision-table・checklist）だけを `delivery/` に置いた。stage は `08_fact-check` のまま。
- 字数：森下さんの答えは約 770 字。記事は 1,372 字（空白を除く・印を含む）で、依頼の 2,000〜2,500 字に 600〜1,100 字ほど足りない。埋めずに、追加取材の質問 6 問（`work/03_interview-plan.md`）を出した。

## 工程と aco の結果（一行ずつ）
| 工程 | 担当（演じた役） | 成果物 | aco の結果 |
|---|---|---|---|
| 開始 | article-desk | — | `aco ledger sample-aosagi brief` 終了 0（RL-1・PD-1・GL-001〜011）／`aco status` 終了 0（00_new） |
| STEP 1 | chief-editor | `work/01_brief.md` | （コマンドなし）。してほしい行動は【仮】、本人に聞くこと 3 |
| STEP 2 | research-editor | `work/02_source-audit.md` | （コマンドなし）。素材 S-01〜S-17、使わない S-08、食い違い 3、確認候補 6。答えの字数は書き起こしを数えて 772 字（空白を除く） |
| STEP 3 | chief-editor（＋interview-director） | `work/03_insight.md`・`work/03_interview-plan.md` | （コマンドなし）。候補 5 → 1 つにまとめた。追加取材 5 問（のちに 6 問） |
| STEP 4 | story-architect | `work/04_structure.md`・`work/05_headlines.md` | （コマンドなし）。社員インタビューの型 6 章 → 4 章、山場 3 章 |
| STEP 5 | feature-writer | `drafts/v1.md`・`drafts/v1_notes.md` | 初回 `aco quotes` A 29／C 1／D 3／E 1（答えの段落の中の【要確認】の印が D・E）→ 印を見出しの下へ移して A 30／D 0／E 0。`aco audit` error 0・warn 5・info 2。`aco structure` 1,392 字・4 章。`aco numbers` 素材にない数値 0。`aco ledger check` 食い違いなし |
| STEP 6（v1） | literary・brand・fact・adversarial → chief | `work/reviews/v1_*.md`・`v1_scores.json` | `aco score` 57／100・公開不可（ブロッカー 4）・終了 2 |
| STEP 7 | feature-writer（chief へ 1 回差し戻し） | `drafts/v2.md`・`drafts/v2_notes.md`・`work/v2_revtable.md` | `aco scope v1 v2 --allow lines:4-4 --allow contains:…×4` 範囲内 5／範囲外 0。`aco quotes` A 30／D 0／E 0。`aco audit` error 0・warn 7・info 2。`aco structure` 1,372 字。`aco numbers` 0。`aco ledger check` 食い違いなし。`aco revtable` 5 件 |
| STEP 6（v2） | 同上（全文を再評価） | `work/reviews/v2_*.md`・`v2_scores.json` | `aco score v2 --history v1` 60／100・公開不可・推移 57 → 60・終了 2（版が 2 つなので頭打ちの判定は出ない） |
| STEP 8 | fact-checker（＋production-manager） | `work/reviews/v2_fact.md`（STEP 8 の節） | 主張 34：A 25・B 5・C 1・D 3・E 0。`aco ledger add pending` で PD-2〜PD-8 を登録 |
| STEP 9 | production-manager | `delivery/checklist.md`・`open-questions.md`・`revision-table.md`・`reply.md` | `aco audit --final` error 9・終了 2／`aco ledger check` 終了 0／`aco quotes` D・E 0／`aco score` 公開不可・終了 2 → 清書を作らずに止めた |
| STEP 10 | production-manager | `work/10_lesson-proposals.md`、台帳 PR-1 | `aco ledger add proposals` PR-1（proposed）。`aco lessons propose` は実行していない（下の 8）。承認は何もしていない |

## 本人・先方が決めること（ここで止まっている）
- 代表：2019 年の作り直しと 300 食分／冷凍麺のラインと 2027 年の春／社長の描写と頻度（PD-2・PD-3・PD-4）
- 森下さん：氏名の掲載（PD-1）、ノートを始めた時期（PD-6）、追加取材への回答
- 採用担当：短いまま出すか追加取材を待つか、読んだ人にしてほしい行動（PD-7）、伝聞の掲載（PD-5）、朝 6 時の表記（PD-8）、期日（【仮】11/18）
- 制作責任者：学習候補 PR-1・PL-案1・PL-案2 の承認／却下

## リポジトリの指示で分かりにくかった所・食い違っていた所
| No. | ファイル | 何が |
|---|---|---|
| 1 | `workflows/writing.md`（STEP 5 の成果物）／`docs/architecture.md` §9・`.claude/skills/article-writing/SKILL.md` 手順 2・`.claude/agents/feature-writer.md` 4 | writing.md は原稿の先頭に `<!-- version: v1 / based_on: … -->` を置けと書き、ほかの 3 つは「版情報は原稿に書かない」。設計書に従った |
| 2 | `scripts/aco_lib/quotes.py`（`textutil.parse_document`）／`CLAUDE.md`「報告のしかた」・`philosophy/editorial-principles.md` 4 章 | 作業中の原稿に【要確認】【要取材】を残してよいとあるが、答えの段落の中に置くと `aco quotes` が印を発言として照合し D・E（作った発言の疑い）にする。印を見出しの下に移して回避した。印の置き場所の決まりがどこにもない |
| 3 | `workflows/reviewing.md`・`docs/architecture.md` §4 | STEP 6 の fact レビューと STEP 8 の全文の事実確認が、同じ版なら同じファイル名 `v<N>_fact.md`。v2 では一つのファイルに「STEP 6」「STEP 8」の節を分けて書いた |
| 4 | `philosophy/quality-standards.md` §1／`.claude/agents/adversarial-reviewer.md` 2 | 品質基準は「chief-editor と adversarial-reviewer がそれぞれ独立に点を付け scores.json に書く」、エージェント定義は「10 軸の点数付けは担当しない」。scores.json の形も reviewer が一人分。chief だけが採点した |
| 5 | `.claude/agents/adversarial-reviewer.md` 3／`.claude/skills/editorial-critique/SKILL.md`（adversarial 手順 1・入力） | エージェントは `03_insight.md` を読む、スキルの手順は「原稿・目的設計・素材分析だけ」、スキルの入力欄は `03_insight.md`・`04_structure.md` も挙げる。エージェント定義に従った |
| 6 | `.claude/skills/article-brief/SKILL.md` 手順 6・`workflows/planning.md`（STEP 1・4 の「本人の同意」） | 新規記事は目的・構成で本人の同意を待つことになっているが、通しの実行では人がいない。【仮】を付けて進めた |
| 7 | `.claude/skills/delivery-package/SKILL.md`・`docs/architecture.md` §4（stage）・`scripts/aco_lib/project.py` | 納品前チェックが通らないと「清書を作らずに止める」が、そのときの stage の値がない（`09_delivered` しかない）。`aco status` は `delivery/final_v*.md` だけを納品物と数えるため、確認依頼を出しても「納品物：なし／次の一手：STEP 9」のまま |
| 8 | `.claude/skills/feedback-learning/SKILL.md` 手順 5 | 全体の候補は `aco lessons propose` で `knowledge/approved-lessons/proposed.json` に書くが、この実行では書き込みを案件フォルダの中に限ったため実行できない。候補は `work/10_lesson-proposals.md` に置いた。また STEP 10 の入力は「先方の指摘」だが、まだ指摘がない段階での扱いが書かれていない |
| 9 | `philosophy/quality-standards.md` §5・`scripts/aco_lib/score.py` | 頭打ちは 3 つの版の点が要る。初回の修正（v1→v2）のあとでは判定できず、「文章では直らない」を理由に止める根拠は chief の判断だけになる |
| 10 | `docs/architecture.md` §6 | `scope --allow contains:<語>` は前の版の文で段落を探す（新しい版の文を書くと「その語を含む段落が見つからない」で終了 1）ことが書かれていない。なお、最初に読んだ版の §6 には `aco numbers` と `chapter-heading:<N>` がなかったが、実行中に更新された今の版には載っている（下の「そのほか」） |
| 11 | `references/derived/A_classification.md`（H2 の行・5 章）／`templates/reply.md`・`templates/revision-table.md`・`aco revtable` | 色分け 🟥文言／🟦追加 は「案件K 固有」と分類されているのに、ひな形と revtable の出力は全案件で 🟥 を使う |
| 12 | `knowledge/approved-lessons/LESSONS.md` GL-009／`CLAUDE.md` ルール 4・`ledger.json` の decisions（`by` が要る） | GL-009 は「口語を残すかを決め、案件の台帳に書く」、ルール 4 は承認のない判断を規則にしない。決めた人がいないので decisions ではなく proposals（PR-1）にした |
| 13 | `philosophy/quality-standards.md` §3（`confidential`）／`knowledge/failure-patterns/official-article.md` B7 | 「未承認の機密」が、公開の了承待ちの情報（氏名・失敗の数量・次の事業）まで含むのかが書かれていない。3 件はブロッカー、社長の頻度と伝聞は要確認として分けた |
| 14 | `philosophy/quality-standards.md` §3（`fact-contradiction` は「E 判定」）／fact の判定 | fact-checker は時期の食い違いを C（疑い）とし、chief は山場の筋に関わるのでブロッカーにした。C をブロッカーにしてよいかの基準がない |
| 15 | `docs/architecture.md` §13「（架空）を付ける」／`aco audit --final` | サンプルの原稿の先頭に置いた `<!-- サンプル（架空）… -->` を `--final` が error にする。サンプルの清書ではこの注記を外すことになる |
| 16 | `.claude/agents/interview-director.md` 5（追加取材は 5 問程度）／`work/reviews/v1_chief.md` | 統合で 6 問目を足した。上限を超えるときの決め方がない |

## そのほか
- この実行の途中（16:14〜16:16）に、`README.md`・`docs/architecture.md`・`scripts/aco_lib/{guard,lessons,validate}.py`・`tests/results/2026-11-11_report.md` の更新時刻が変わっていた。この実行では書いていない（別の作業によるもの）。`docs/architecture.md` は最初に読んだ版に従った。
- `aco validate` と単体テストは、リポジトリを直していないため実行していない。
