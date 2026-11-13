# 実行ログ：TEST A（AI 的な文章の改善）

- 実行日：2026-11-11
- 進め方：メインの会話として実行。サブエージェントは呼べないため、literary-editor の役を自分で演じた（エージェント定義と、`skills:` の 2 スキル、そのスキルが指す知識ファイルだけを読んだ）。
- 書いたファイル：`output/review.md`（レビュー票＋追加取材の一覧＋対応表＋再検査）、`output/rewrite.md`（書き直し）、この `output/run-log.md`。ほかのファイルは変更していない。
- 開いていないもの：`tests/scenarios/*/controls/`、`verify.py`、`tests/scenarios/_lib/`。

## 1. 読んだファイル（読んだ順）

| ファイル | 読んだ範囲・理由 |
|---|---|
| `CLAUDE.md` | 全文（最初に） |
| `tests/scenarios/A_ai-writing/README.md` | 全文（実行手順） |
| `tests/scenarios/A_ai-writing/input/company-intro.md`・`input/facts.md` | 全文（素材） |
| `agents/literary-editor.md` | 全文（担当の役） |
| `skills/ai-writing-audit/SKILL.md` | 全文（`skills:` の 1） |
| `skills/natural-japanese/SKILL.md` | 全文（`skills:` の 2） |
| `knowledge/failure-patterns/ai-writing-signs.md` | 全文（ai-writing-audit の参照） |
| `references/derived/B_ai-writing-signs.md` | 全文（ai-writing-audit の参照） |
| `knowledge/editorial-patterns/specificity.md` | 全文（両スキル・README の指定） |
| `philosophy/human-writing.md` | 全文（両スキルの参照） |
| `templates/review.md` | 全文（両スキルの出力の形） |
| `knowledge/editorial-patterns/quote-editing.md` | 全文（natural-japanese の参照） |
| `knowledge/failure-patterns/official-article.md` | 冒頭と D1〜D13・E2・E3・G1〜G4 だけ（natural-japanese が範囲を指定） |
| `docs/architecture.md` | §5・§6・§7〜§10・§12（README がレビュー票の形として §10 を指定。§5 の ID 表と §6 の aco の説明も参照） |
| `philosophy/editorial-principles.md` | §4「原稿の中の印」の行だけを grep（CLAUDE.md が印の付け方の出典として指定） |
| `knowledge/editorial-patterns/interview-craft.md` | §4「追加取材の質問の作り方」だけ（specificity.md が要取材の質問の作り方として参照） |

読まなかったもの：`workflows/reviewing.md`（literary-editor.md §6 に「進め方」としてあるが、スキルが指す知識ファイルではないため、指示どおり読まなかった）。

## 2. 実行した aco コマンド

| コマンド | 結果（一行） |
|---|---|
| `python3 scripts/aco audit tests/scenarios/A_ai-writing/input/company-intro.md` | error 0／warn 11／info 6（AI-01・02・04×3・05×2・06・07・08×2・10×2・11・12×2・17） |
| `python3 scripts/aco --help`／`aco audit --help`／`aco ledger --help` | 使い方の確認だけ。`ledger` は slug が必須 |
| `python3 scripts/aco lessons list` | 承認済み GL-001〜GL-011 を確認。GL-001（対応表）・GL-002（修正前→後）・GL-006（印は社内だけ）・GL-008（推測で埋めない）を反映 |
| `python3 scripts/aco audit tests/scenarios/A_ai-writing/output/rewrite.md`（初版） | warn 3／info 5。【要取材】の印の中の「いつ・誰が・何を」が AI-07 に、印の語「要取材」が D4 に数えられた → 印を短くし、質問の中身は review.md の追加取材の一覧に移した |
| `python3 scripts/aco audit tests/scenarios/A_ai-writing/output/rewrite.md`（最終） | error 0／warn 2／info 2（D4「センサー」・D4「要取材」・D9・D1。どれも残す理由を review.md に記載） |
| `python3 scripts/aco quotes tests/scenarios/A_ai-writing/output/rewrite.md --transcript tests/scenarios/A_ai-writing/input/facts.md` | A 4／B〜E 0。facts.md が「名前：発言」の形でないため、話し手は「不明」と出る |
| `python3 scripts/aco audit tests/scenarios/A_ai-writing/output/rewrite.md --final` | error 2。拾ったのは 1 行目の HTML コメントの中の「【要取材】」「【要確認】」だけ |
| `aco audit --final` を、コメントを外した写し・試験用の小さな文書（scratchpad に作成）にかけた | 本文の「【要取材：…】」「【要確認：…】」は 0 件。印だけの「【要取材】」と「〇〇」は error になる |

実行しなかったもの：`aco ledger <slug> brief`（案件 slug がない）、`aco audit --project`（同じ理由）、`aco scope`（範囲の指定がなく、元の文書は書き換えずに新しいファイルを作ったため）、`aco validate`（リポジトリを変更していないため）。

## 3. リポジトリの指示で分かりにくかった所・食い違っていた所

1. **literary-editor に書き直しをさせてよいのか（食い違い）**：README の手順 2 は literary-editor に書き直し（rewrite.md）を頼む。一方で `agents/literary-editor.md` §2 は「担当しない：…原稿の書き換え（feature-writer・production-manager）」、§7 は「原稿を書き換えない」。`natural-japanese/SKILL.md` 手順 7 も、literary-editor はレビュー票だけ、修正後の原稿＋修正表は feature-writer、と分けている。→ README を優先し、入力は書き換えずに別ファイルに書き直し、feature-writer の出し方（対応表）も review.md に付けた。README の手順 2 を feature-writer にするか、エージェント側に例外を書くべき。
2. **出力ファイルの数と名前が合わない**：エージェントとスキルは `work/reviews/v<N>_ai-audit.md` と `v<N>_literary.md` の 2 枚を出すと定めるが、README は `output/review.md` 1 枚。2 枚分を 1 枚にまとめた。どちらを期待しているか書かれていない。
3. **案件 slug・台帳・素材分析がないときの扱いが書かれていない**：CLAUDE.md と literary-editor.md §3 は「最初に必ず `aco ledger <slug> brief`」、スキルの入力は `work/02_source-audit.md` と書き起こし。テストにはどれもない。facts.md を素材分析の代わりにし、ledger は飛ばした。媒体とトーン（brief）もないため、発言の口語（D1）を残すかが決められなかった。
4. **章も問いもない文章の「箇所」の書き方**：`templates/review.md`・architecture §10・GL-001 は「章の見出しと問いの文で示す」「最後の問い・締めだけでは書かない」とするが、入力は題名＋地の文 5 段落で章も問いもない。段落番号＋行番号＋該当文で示した。また、テンプレートには「判断（直す／残す）」の欄がないが、`ai-writing-audit` の出力は各指摘に判断と理由を求める。欄を足して書いた。表題の `v<N>` も入力に版がなく、決められない。
5. **追加取材の一覧と修正表の置き場所**：README は「【要取材】と追加取材の一覧に回す」と言うが、一覧をどのファイルに書くかは書いていない（specificity.md は「interview-director に回す」）。rewrite.md に書くと、一覧と修正表の旧文が `aco audit` の数に入ってしまうため、どちらも review.md に置いた。
6. **印を残してよいか（食い違い）**：CLAUDE.md「報告のしかた」は読者に見せる成果物に要確認などの社内メモを残さないと言い、README は rewrite.md に【要取材】を求める。`philosophy/editorial-principles.md` §4 の「作業中の原稿には印を使う」に従い、rewrite.md を作業中の原稿として扱った。
7. **`aco audit --final` が、定めた形の印を拾わない（不具合の疑い）**：editorial-principles.md §4・specificity.md が定める印は `【要取材：…】` `【要確認：…】` だが、`--final` は「：…」付きの印を拾わず、印だけの `【要取材】` しか止めない。さらに、architecture §9 は版情報の HTML コメントを「スクリプトは無視する」と書くのに、`--final` はコメントの中の印を拾った。このままだと、印が残った清書が `--final` を通る。
8. **`aco audit` が印の中身を本文として数える**：【要取材：…】の中の「いつ・誰が・何を」が AI-07、印の語そのものが D4、印を付けた発言が D9（長い文）として出る。作業中の原稿の warn が印の数で増える。印を除いて数えるオプションがない。
9. **書き起こしではない発言メモの扱いが書かれていない**：facts.md の発言は「人事担当が聞いた話。取材の書き起こしではない」。quote-editing.md と `aco quotes` は書き起こしを前提にしていて、伝聞のメモを「」で載せてよいか、どう印を付けるかの決まりがない。言葉どおりに載せ、【要確認：本人】を付けた。`aco quotes` は facts.md を書き起こしとして渡すと A と判定するので、A でも本人の確認が要ることは人が補う必要がある。
10. **重大度「高」の線引き**：templates の「高＝公開を止める」と CLAUDE.md ルール 8 の止める条件（作った発言など）の関係が書かれていない。出所のない「業界では『…』と言われています」と、社員の気持ちの代弁を「作った発言」に近いとみて高にしたが、根拠のない自画自賛（「重要な役割を果たしてきました」）を高にするかは決め手がなく、中にした。
11. **読む範囲の指定がずれる**：ai-writing-signs.md は負け筋 B4・B5・C4・C7・F5 を参照するが、natural-japanese は official-article.md の読む範囲を D・E2・E3・G に限っている。B・C・F の ID は ai-writing-signs.md の短い説明だけで引いた。また literary-editor.md §6 の `workflows/reviewing.md` を読むべきかも、「スキルが指す知識ファイルだけ」という読み込みの方針と合わない。

## 4. メモ
- 実行中に `docs/architecture.md` がディスク上で更新された（別の作業と思われる）。§10 を読み直し、内容が変わっていないことを確かめてから続けた。
- `aco audit` は入力の「武器に」「パートナー」「さまざまな現場」「ソリューション」、第3〜4段落の同じ形の文末（AI-09）を拾わなかった。人の目の点検で R-4・R-5・R-8・R-9・R-13 として足した。
