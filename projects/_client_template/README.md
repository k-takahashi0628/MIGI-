# 会社フォルダ（ひな形）

同じ会社の案件をまとめるフォルダ。`python3 scripts/aco new <会社>/<案件> --client "社名"` で、会社フォルダがなければこのひな形から作られる。

- `client.json`：社名・別名・会社の資料の場所（`knowledge`）
- `client-ledger.json`：会社の台帳。表記ルール・書かないこと・公開禁止・決まったことなど、**この会社のすべての案件に効く**決まり。ほかの会社には効かない
  - 足す：`python3 scripts/aco ledger <会社> add rules --avoid "…" --use "…"`
  - 案件の `aco ledger <会社>/<案件> brief`・`check`・`aco audit --project`・`aco quotes --project` は、会社の台帳もあわせて読む
- `knowledge/`：会社理解のメモ・過去の記事など（案件をまたいで使う資料）
- `<案件>/`：案件フォルダ（`projects/_template` と同じ形）

実在の会社のフォルダは Git に入らない（.gitignore）。
