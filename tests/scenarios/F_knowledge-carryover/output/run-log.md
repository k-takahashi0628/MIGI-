# 実行ログ：TEST F（知識の継承）

- 実行日：2026-11-11
- 役：メインの会話（/article-desk）として進め、STEP 5 の feature-writer（article-writing）を自分で演じた（サブエージェントは使えないため）
- 書いたファイル：`output/article.md`（後編の初稿 v1）、`output/v1_notes.md`（執筆メモ）、`output/run-log.md`（これ）
- リポジトリ本体と `input/` は変えていない（`diff -r input <一時コピー>` で差分なしを確認）

## 1. 読んだファイル

| 順 | ファイル | 読んだ理由 |
|---|---|---|
| 1 | `CLAUDE.md` | 最初に読む |
| 2 | `tests/scenarios/F_knowledge-carryover/README.md`・`input/instruction.md`・`input/aco.config.json` | 実行手順と依頼 |
| 3 | `skills/article-desk/SKILL.md` | 手順 2 の /article-desk |
| 4 | `agents/feature-writer.md` | 手順 2 のエージェント |
| 5 | `skills/article-writing/SKILL.md`・`headline-craft/SKILL.md`・`natural-japanese/SKILL.md` | feature-writer の `skills:` の 3 つ |
| 6 | `workflows/writing.md` | feature-writer の「進め方」 |
| 7 | `knowledge/editorial-patterns/quote-editing.md`・`specificity.md` | article-writing・feature-writer が指す |
| 8 | `philosophy/human-writing.md` | 同上 |
| 9 | `knowledge/failure-patterns/official-article.md`（冒頭・B5・C 群・D 群・E7・F 群） | feature-writer（C・D 群）、headline-craft（F4・F5・B5） |
| 10 | `knowledge/failure-patterns/ai-writing-signs.md`（共通手順・AI-14〜17） | article-writing・headline-craft（AI-16） |
| 11 | `knowledge/editorial-patterns/headlines-and-questions.md`・`lead-and-ending.md`、`templates/headlines.md` | headline-craft が指す |
| 12 | `philosophy/editorial-principles.md`（3〜5 章・9 章） | CLAUDE.md が「印の付け方」として指す |
| 13 | `docs/architecture.md`（見出し一覧、§4〜§9） | instruction の「書式：§9」と出力の場所 |
| 14 | `input/projects/nagisa-logistics/project.json`・`sources/interview-notes.md`・`sources/previous-article.md` | 案件の素材 |

読まなかったもの：`controls/`・`verify.py`・`tests/scenarios/_lib/`（採点用）、`input/projects/hamanasu-shobo/`（別の案件。CLAUDE.md「別の案件フォルダは読まない」）、`input/projects/nagisa-logistics/ledger.json` と `input/knowledge/approved-lessons/*.json` の生ファイル（台帳は `aco ledger brief` からだけ読んだ。全体ルールの候補ファイルは開いていない）。

## 2. 実行した aco コマンド

| コマンド | 結果（一行） |
|---|---|
| `ACO_ROOT=tests/scenarios/F_knowledge-carryover/input python3 scripts/aco ledger nagisa-logistics brief` | 台帳（LK-1・RL-1〜3・AP-1・RJ-1〜2・CF-1〜2・DC-1・FC-1・PD-1・PR-1［承認待ち］）と承認済み GL-001 だけが出た。終了 0。input に変化なし |
| `aco --help`・`aco ledger --help`・`aco quotes --help`・`aco structure --help`・`aco audit --help` | 引数の確認 |
| （以降はすべて `ACO_ROOT=<scratchpad>/aco_root`＝input の一時コピー） | |
| `aco quotes output/article.md --transcript <一時コピー>/…/interview-notes.md --project nagisa-logistics`（初回） | A10／C2／E1（「メンバー」＝RL-1 の置き換え）。終了 2 |
| `aco audit output/article.md --project nagisa-logistics`（初回） | error 0／warn 10／info 1（B5×5・D4×5・AI-15×1） |
| `aco structure output/article.md --compare <一時コピー>/…/previous-article.md`（初回） | 全体 873 字・5 章。F5 info（締めとリードの言葉の重なりが少ない）、F7 info（前編の 3.44 倍） |
| `aco ledger nagisa-logistics check output/article.md`（初回） | 台帳との食い違いなし。終了 0 |
| `aco quotes <scratchpad>/t.md …`（区切り線 `---`・`＊` の試験） | どちらでも締めの段落は真鍋課長の発言として扱われた（C） |
| 直したあとの `aco quotes`（最終） | A10／B0／C2／D0／E1。終了 2（E は RL-1 の置き換え。【要確認】にした） |
| 直したあとの `aco audit --project`（最終） | error 0／warn 8／info 1。残した理由は v1_notes.md |
| 直したあとの `aco structure --compare`（最終） | リード 200 字／全体 944 字（印を除くと約 790 字）。F5 info は消えた。F7 info（3.72 倍） |
| 直したあとの `aco ledger nagisa-logistics check`（最終） | 台帳との食い違いなし。終了 0 |

実行しなかったもの：`aco lessons approve`（README の合格条件にはあるが「実行手順」にはなく、承認は本人の OK が要る操作のため）、`aco status`（新規の初稿で、台帳 brief で足りた）、`aco audit --final`（清書ではないため）。

## 3. 指示が不明確・食い違っていた所

1. **構成がない状態での初稿。** `article-writing/SKILL.md` 手順 1 と失敗条件は「構成（`work/04_structure.md`）がなければ書かずに止める」。`article-desk/SKILL.md` の表も新規記事は STEP 1〜4 を先に通す。一方、テスト README の実行手順は「feature-writer に article-writing で初稿」だけで、input に `work/01〜05` がない。README の手順を優先し、構成と素材の対応は `v1_notes.md` に書いた。どちらを優先するかの決まりがない。
2. **`aco quotes` が台帳の表記ルールを考えない。** RL-1 は「見出しとセリフも」と明記されているが、`--project` を付けても置き換えた語が E（固有名の不一致）になり終了 2 になる。`workflows/writing.md` の完了条件「D・E が 0 件」と台帳ルールが両立しない。例外の書き方（ルールによる置き換えを quotes に通す方法）がどこにもない。なお RL-2 の英字の大文字化は A 判定で通った（扱いが揃っていない）。
3. **最後の地の文の書き方が §9 にない。** `docs/architecture.md` §9 では、話し手のない段落は直前の話し手の続きとして読む。LK-1 は「最後の段落」に置く決まりなので、Q&A 形式では最後の答えの続き（真鍋課長のセリフ）として判定・読解される。`---` や `＊` でも区切れない。`lead-and-ending.md` にも、Q&A の後に地の文の締めを置く書き方がない。前編も同じ形。
4. **字数の指示と素材・F7 の食い違い。** instruction は 1,500〜2,000 字、素材は 5 発言（印を除いて約 790 字が上限）、`official-article.md` F7 は「シリーズの前の記事と同じくらい」（前編 254 字）。`workflows/writing.md` の完了条件「字数が目安から大きく外れていない」は、作らずには満たせない。どれを優先するかの決まりがない（「作らない」を優先した）。
5. **RL-2 の適用範囲。** RL-1 は「見出しとセリフも」と書いてあるが、RL-2・RL-3 は範囲がない。セリフにも当てるか分からない（前編の代表のセリフに合わせてセリフにも当てた）。
6. **セリフの口語の扱いが台帳にない。** `quote-editing.md` は文末をそろえるのを「台帳で口語の扱いを決めた範囲で」、`official-article.md` D1 も「台帳で決める」とするが、台帳に該当の項目がなく、決める工程・担当も書かれていない（最小限の「〜てます→〜ています」だけにして修正表に残した）。
7. **出力先の食い違い。** feature-writer・article-writing の出力は `projects/<slug>/drafts/v1.md` と `v1_notes.md`、headline-craft は `work/05_headlines.md`、article-desk は `project.json` の `stage` 更新。テストは `output/article.md` だけを指定し、input の変更は不可。執筆メモ・見出し案の置き場所が指定されていないため、`output/v1_notes.md` にまとめた。`stage` は更新していない。
8. **`aco` のどの操作が台帳を書き換えるかが書かれていない。** README は手順 1 で `ACO_ROOT=input` を直接使い、合格条件では「一時フォルダに複製した台帳で check」と書く。`docs/architecture.md` §6 にも、`brief`・`audit --project`・`check` が読み取り専用かどうかの記載がない（安全のため一時コピーで回した）。`ACO_ROOT` を付けたとき `--transcript` などの相対パスがどこから解決されるかも書かれていない（絶対パスで渡した）。
9. **素材の形。** article-writing の失敗条件は「インタビュー記事なのに書き起こしがない」。今回の素材は「取材メモ」の中の「書き起こしの抜粋（整文前）」で、同じファイルに広報担当のメモ（却下案と同じ文言）が入っている。`aco quotes` はファイル全体を書き起こしとして照合する（話し手「不明」の行ができる）。抜粋を書き起こしとして扱ってよいか、メモ部分を外すべきかの決まりがない。
10. **承認済みの表現（approved）の使い方。** AP-1 を「次の記事でも使うべきもの」か「使ってもよいもの」かが、`docs/architecture.md` §4・`article-writing` 手順 6（「承認済みの表現を使い」）のどちらからも読み切れない（リードで前編の見出しとして一度だけ引いた）。
11. **README の合格条件にある `aco lessons approve` を誰がいつ行うか。** 実行手順には入っておらず、CLAUDE.md ルール 4 では本人の明示の OK が要る。テストの中でメインの会話が行うべきかが分からない（行っていない）。
12. **前編の見出しの扱い。** 台帳の AP-1 は「前編の見出しで承認」だが、前編のファイルではこの文はタイトル（`# `）にある。「見出し」がタイトルを指すのか、§9 の「章の見出し」を指すのかが揃っていない（リードでは「見出しにした言葉」と書いた）。
