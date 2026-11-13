# 承認済みの全体ルール

全案件に通用する、承認された編集判断を置く場所。案件ごとの決まりは、その案件の `projects/<slug>/ledger.json` に置き、ここには入れない。

| ファイル | 中身 | 直し方 |
|---|---|---|
| `knowledge/approved-lessons/lessons.json` | 承認済みのルール（GL-001〜） | `python3 scripts/aco lessons approve` で追加。手で直したら `render` を走らせる |
| `knowledge/approved-lessons/proposed.json` | 承認待ち・却下の候補（PL-001〜）。**規則として使わない** | `python3 scripts/aco lessons propose` / `reject` |
| `knowledge/approved-lessons/LESSONS.md` | 人が読むための一覧 | `python3 scripts/aco lessons render` で作る。直接編集しない |

形は `docs/architecture.md` §13。

---

## 1. ルールが入るまで

1. **候補を出す**：feedback-learning スキルが、修正履歴・先方の指摘・制作責任者の指摘から「次も使える判断」を候補として挙げる。
   - その案件だけの判断 → 案件の台帳の `proposals`
   - どの案件でも通用しそうな判断 → `aco lessons propose` で `knowledge/approved-lessons/proposed.json`
2. **承認を取る**：制作責任者（または決裁権のある人）の明示の OK があるまで、候補は規則として使わない。エージェントが自分で承認しない。
3. **昇格する**：`aco lessons approve <PL-id> --by <承認した人>`。このとき、どの案件の社名・人名・公開禁止の語も入っていないかを確かめ、入っていれば拒否する（`projects/<slug>/project.json` と `.aco/blocklist.local.json` の名前で照合）。
4. **一覧を作り直す**：`aco lessons render` で `knowledge/approved-lessons/LESSONS.md` を更新する。

## 2. 入れてよいもの・入れないもの

| 入れてよい | 入れない |
|---|---|
| どの会社の記事でも成り立つ編集判断（例：直した場所を章の見出しで示す） | 特定の会社の表記・呼称・好み（例：ある会社では「WEB」と書く）→ その案件の台帳へ |
| 制作責任者が明示に指示・承認した進め方 | エージェントが「よさそう」と判断しただけのもの |
| 承認された、記事の種類ごとの決まり（scope を付ける） | 社名・人名・社内の数字・未公開の情報を含む文 |
| 失敗から得た、再発を防ぐ手順 | 一度だけの事情（特定の締め切り・特定の担当者の都合） |

## 3. scope の意味

| scope | 当てはめる範囲 |
|---|---|
| `global` | 全案件 |
| `official-article` | 企業の公式記事（採用広報・経営者／社員インタビュー・カルチャー記事・会社紹介） |
| `interview` | インタビュー記事 |
| `revision` | 修正の進め方 |
| `delivery` | 納品・報告の出し方 |

## 4. 使われ方

- 制作の最初に `python3 scripts/aco ledger <slug> brief` を読むと、その案件の台帳と、ここの承認済みルールだけが出る。ほかの案件の台帳は出ない。
- ルールと案件の台帳がぶつかったら、案件の台帳（先方の決まり）を優先する。ぶつかったことは台帳の `decisions` に書く。
- ルールと `philosophy/` の原則がぶつかったら、原則を優先し、ルールの見直しを候補に挙げる。

## 5. ルールをやめるとき

- 制作責任者の指示があったときだけ、`knowledge/approved-lessons/lessons.json` から外して `render` を走らせる。外した理由は、その時点で関わっていた案件の `projects/<slug>/history.md` か、このリポジトリのコミットメッセージに残す。
- 番号は使い回さない（外した番号は欠番にする）。
