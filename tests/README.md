# テスト

テストは 2 種類ある。どちらもリポジトリの直下で実行する。

| 種類 | 何を確かめるか | 場所 |
|---|---|---|
| 単体テスト | `scripts/aco` の各機能が決めたとおりに動くか | `tests/unit/` |
| シナリオテスト（TEST A〜F） | エージェントとスキルが、実際の制作の場面で正しくふるまうか | `tests/scenarios/` |

## 単体テスト

```bash
python3 -m unittest discover -s tests/unit -v
```

## シナリオテスト

| ID | 名前 | 主に使うエージェント・スキル |
|---|---|---|
| A | AI 的な文章の改善 | literary-editor／ai-writing-audit・natural-japanese |
| B | 取材発言の保全 | feature-writer・fact-checker／article-writing・article-fact-check |
| C | 構成の再設計 | story-architect・feature-writer／story-architecture |
| D | 局所修正 | production-manager／revision-control |
| E | 企業広報リスク | brand-reputation-editor・feature-writer／brand-risk-review |
| F | 知識の継承 | /article-desk・feature-writer／article-writing・`aco ledger`・`aco lessons` |

各フォルダの中身：
- `README.md`：目的・実行手順（Claude Code での頼み方）・合格条件
- `input/`：架空の素材（実在の会社・人は使わない）
- `verify.py`：`output/` を機械で検査する。合格 0／不合格 2／検査できず 1（`scripts/aco` やファイルが足りない）
- `controls/`：検査そのものを確かめるための出力。`good` は合格、`bad*` は不合格になるはず
- `output/`：実行結果を置く場所

### 1. 検査が正しく落とせるかを先に確かめる

```bash
python3 tests/scenarios/run.py controls
```
すべての行が「一致 ○」になることを確かめる。× があるときは、`verify.py` か `scripts/aco` の検出が甘い（または厳しすぎる）。

### 2. Claude Code で各テストを実行する

各 `README.md` の「実行手順」のとおりに頼み、結果を `output/` に書かせる。例：
```text
literary-editor で tests/scenarios/A_ai-writing/input/company-intro.md を ai-writing-audit → natural-japanese の順に見て。
事実は input/facts.md だけを使う。レビューは output/review.md、書き直しは output/rewrite.md に。
```
依頼文に答え（合格条件や台帳の中身）を書き写さない。システムが自分で読みに行けるかを見るため。

### 3. 出力を検査する

```bash
python3 tests/scenarios/run.py outputs          # 全部
python3 tests/scenarios/run.py outputs A D      # 一部
python3 tests/scenarios/D_local-edit/verify.py  # 一つずつ
```

機械の検査は最低限の条件だけを見る。文章の質（具体性・自然さ・構成の筋）は、`editorial-critique` スキルで別のエージェントに評価させ、結果に添える。

### 4. 結果を記録する

`tests/results/<YYYY-MM-DD>_report.md` に、テストごとの合否・不合格の原因・直したこと・未実施の項目を書く。
不合格になったら、原因（スキルの手順・エージェントの指示・スクリプトの検出）を特定して直し、もう一度回す。

## 環境

- Python 3.9 以上の標準ライブラリだけで動く（追加のインストールは要らない）
- `ACO_ROOT` を渡すと、`scripts/aco` が読む案件データと全体ルールの置き場を差し替えられる（TEST F で使う）
