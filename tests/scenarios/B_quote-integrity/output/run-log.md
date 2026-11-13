# 実行記録：TEST B 取材発言の保全（2026-11-11）

## 結果
- `output/article.md`：5 章・問い 12・全体 1,122 字（空白を除く）。答えの話し手はすべて「森下：」。
- `aco quotes`：A 33／B 0／C 0／D 0／E 0（終了コード 0）。記事の数字 10 種はすべて書き起こしにある（自前のスクリプトで照合）。
- 字数はブリーフの 2,000〜2,500 字に届いていない。書き起こしの答えが整文前で 772 字しかなく、地の文で埋めると「作らない」に反するため、足さずに要取材として出した（article_notes.md §5）。
- 書いたファイル：`output/article.md`／`output/article_notes.md`（執筆メモ：素材表・構成・見出し案・要確認・要取材・修正表）／`output/fact-check.md`（v1 の照合票）／`output/run-log.md`（これ）

## 読んだファイル
- 入口：`CLAUDE.md`、`tests/scenarios/B_quote-integrity/README.md`、`input/brief.md`、`input/transcript.md`
- エージェント：`agents/feature-writer.md`、`agents/fact-checker.md`
- スキル：`skills/article-writing/SKILL.md`、`headline-craft/SKILL.md`、`natural-japanese/SKILL.md`、`article-fact-check/SKILL.md`
- スキルが指す知識・テンプレート：
  - `docs/architecture.md`（§4 案件フォルダ・§6 aco・§9 原稿の書式・§12 テスト）
  - `knowledge/editorial-patterns/quote-editing.md`、`specificity.md`、`headlines-and-questions.md`、`lead-and-ending.md`
  - `philosophy/human-writing.md`、`philosophy/editorial-principles.md`（§3〜5 のみ）
  - `knowledge/failure-patterns/official-article.md`（冒頭・B5・B7・C1〜C8・D1〜D13・F4・F5 のみ）
  - `knowledge/failure-patterns/ai-writing-signs.md`（AI-01〜17）
  - `templates/headlines.md`、`templates/fact-check-table.md`
- エージェントの「進め方」：`workflows/writing.md`、`workflows/reviewing.md`
- aco の動きを確かめるため：`scripts/aco_lib/ledger.py`（load と brief。書き込みがないことの確認）、`scripts/aco_lib/textutil.py` の `parse_transcript`
- 読んでいないもの：`controls/`・`verify.py`・`tests/scenarios/_lib/`（指示どおり開いていない）。`templates/review.md`（literary-editor 用）、`references/derived/A_classification.md`（知識ファイルからの孫引き。口語の扱いはブリーフが決めていたため）、`knowledge/editorial-patterns/interview-craft.md`、`philosophy/quality-standards.md`

## 実行した aco コマンド
| コマンド | 結果（一行） |
|---|---|
| `aco --help` ほか `ledger/quotes/audit/structure --help` | サブコマンドと引数を確認 |
| `aco ledger aosagi-morishita brief` | 終了 1「案件フォルダがない」。案件を作ると output/ の外に書くため作らなかった |
| `aco ledger _template brief` | 終了 0。案件台帳は空、承認済みの全体ルール GL-001〜011 を読んだ（回避策） |
| `aco quotes output/article.md --transcript input/transcript.md`（初稿） | A 33／D 0／E 0、終了 0 |
| `aco audit output/article.md`（初稿） | error 0／warn 6／info 3（D4「入社」「厨房」×2、D1 ×6、B5 ×1） |
| `aco structure output/article.md`（初稿） | リード 136 字／全体 1,111 字、5 章 |
| （リードと問い 1 つを直して D4 を解消） | |
| `aco quotes …`（最終） | A 33／B 0／C 0／D 0／E 0、終了 0 |
| `aco audit output/article.md`（最終） | error 0／warn 4／info 3（D1 は本人の口調、B5「一番」は本人の意見として残した） |
| `aco audit output/article.md --final` | error 0、終了 0（原稿に印・仮置き文字なし） |
| `aco audit output/article.md --project aosagi-morishita` | 終了 1「ledger.json がない」 |
| `aco structure output/article.md`（最終） | リード 140 字／全体 1,122 字、章 256・201・181・187・150 字 |
| `aco quotes … --json` | 書き起こしの話し手が「不明」「森下」の 2 つと出た（下の 9） |

## リポジトリの指示で分かりにくい・食い違う・足りない所
1. **シナリオでは案件フォルダがない前提が書かれていない。** `feature-writer.md` §3・§4、`fact-checker.md` §3、`article-writing/SKILL.md` の入力は、すべて `projects/<slug>/`（ledger.json・project.json・01_brief・02_source-audit・04_structure）を前提にしている。README は「output/ に置く」としか言わず、`aco new` を使うのか、v1.md・v1_notes.md・v1_fact.md を output/ のどの名前にするのかがない。`aco ledger <slug> brief` は案件がないと終了 1 で、「最初に必ず読む」が実行できない。
2. **構成がないと止める決まりと、README の手順が食い違う。** `article-writing/SKILL.md` 手順 1 と失敗条件は「構成がなければ書かずに止める（先に story-architecture）」。README は書き起こしとブリーフから直接 feature-writer に書かせる。今回はメインの会話として最小限の構成を article_notes.md §2 に書いてから書いた。headline-craft も入力に 03_insight・04_structure を求めるが、ない。
3. **D・E を誰が直すかが食い違う。** README 手順 2 は「fact-checker で…D・E があれば直して」。`fact-checker.md` §7 は「原稿を書き換えない」。直すのは feature-writer（STEP 7）か production-manager（revision-control）。また直すなら版を上げる決まり（feature-writer §7「前の版を上書きしない」）と、README の出力が `output/article.md` 1 つであることが合わない（今回は D・E 0 で直す場面がなかった）。
4. **字数の指定と素材の量が両立しない場合の扱いがない。** ブリーフは 2,000〜2,500 字、書き起こしの答えは 772 字。`workflows/writing.md` の完了条件「字数が目安から大きく外れていない」と CLAUDE.md の「作らない」がぶつかる。writing.md は「STEP 4 に戻すか追加取材」と言うが、シナリオでは戻す先がない。README の合格条件にも字数はない。
5. **output/article.md が作業中の原稿か、読者向けかが分からない。** `philosophy/editorial-principles.md` §4 は作業中の原稿に【要確認】【要取材】を入れると言い、CLAUDE.md「報告のしかた」と GL-006 は読者に見せるものに印を残さないと言う。今回は原稿に印を入れず、article_notes.md と fact-check.md に出した。
6. **口語の扱いの優先順位がない。** 承認済みの全体ルール GL-009 は「口語・カタカナの口語・近くで繰り返す語を機械で数えて潰す」。ブリーフは「整文は言いよどみと重複を取る範囲まで」。`official-article.md` D1 の例外は「台帳で決める」だが台帳がなく、`quote-editing.md` の文末の統一は `references/derived/A_classification.md` 6-7 に飛ぶ。全体ルールと案件ブリーフのどちらが勝つかが書かれていない（今回はブリーフに従い、発言の口語を残した）。
7. **聞き手の問いをどこまで直してよいかの決まりがない。** `quote-editing.md` は話し手の発言だけを扱う。`headlines-and-questions.md` §3 は「はい／いいえの問いにしない」と言うが、書き起こしの問いを書き換えてよい範囲は書かれていない。`aco quotes` も問いは照合しない。今回は 7 か所直し、一覧を article_notes.md §8 に残した。
8. **地の文の数字を確かめる aco コマンドがない。** README の合格条件「書き起こしにない数値がない」に当たる検査は、`aco quotes` が答えの段落だけを見るため、タイトル・リード・見出しの数字は対象外に見える（今回は自前のスクリプトで照合した）。
9. **`aco quotes` の書き起こしの読み方。** `textutil.parse_transcript` は、最初のラベル付きの行より前の行（コメント・見出し・「話し手：森下 美帆（架空）製造課 班長」「取材日：2026年10月20日」などのメタ情報）を話し手「不明」の発言として読む。メタ情報と同じ文を記事のセリフにすると、話していなくても一致扱いになるおそれがある。`docs/architecture.md` §9 の書き起こしの形には、冒頭のメタ情報の扱いが書かれていない。また 5 字未満の文は照合しない（短い作ったセリフは機械では拾えない）。
10. **小さな点。** 地の文での呼び方（「森下」か「森下さん」か）の決まりが feature-writer の参照範囲にない（A4 は参照外）。fact-checker の STEP 6（発言と重大な矛盾のみ）と STEP 8（全文）のどちらとして呼ぶのかが README にない（今回は全件の表まで作った）。
