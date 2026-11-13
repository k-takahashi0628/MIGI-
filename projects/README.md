# projects（案件フォルダ）

記事の案件ごとのデータを置く場所。共通の制作エンジン（このリポジトリのほかの部分）とは分けて扱う。

## 作り方
```bash
python3 scripts/aco new <会社>/<案件> --client "社名" --type employee-interview --title "仮題"
```
`projects/<会社>/<案件>/` ができる（会社フォルダがなければ `projects/_client_template/` から作る）。会社に属さない単独の案件は `aco new <slug>`。中の決まりは `docs/architecture.md` §4。

- 会社全体の決まり（表記・書かないこと・人名の扱いなど）は、会社の台帳 `projects/<会社>/client-ledger.json` に一度だけ書く。その会社のすべての案件に効き、ほかの会社には効かない。

## 決まり
- 実案件のフォルダは Git に入らない（`.gitignore` で `projects/*` を除外。Git に入るのは `_template/`・`_client_template/` とこの README だけ）
- 書き起こし・先方資料・未公開の原稿・顧客名・人名は、このフォルダの外（`knowledge/` `examples/` `tests/` など）に書かない
- ある案件の台帳（`ledger.json`）やルールを、別の案件にコピーしない。全案件に使える判断は、承認を得てから `knowledge/approved-lessons/` に一般化して入れる
- 原稿の版（`drafts/v<N>.md`）は上書きしない
- 外に共有するとき（クラウドに上げる・人に送る）は、公開範囲を本人に確かめてから
- 案件を終えたら `project.json` の `stage` を `09_delivered` か `10_learned` にしておく
