# TEST F：知識の継承

承認済みの表現・却下案・案件固有のルール・変更禁止の文を保存し、次の記事に正しく反映できるか。別の案件のルールや、未承認の候補が混ざらないかを確かめる。

## 入力（すべて架空）
`input/` は、そのまま `ACO_ROOT` に使える小さなリポジトリの形になっている。
- `input/projects/nagisa-logistics/`（案件 1）：台帳に locked・approved・rejected・rules（仲間→メンバー、Web→WEB、お客さま→お客様）・confidential・未承認の候補（PR-1：倉庫→センター）。`sources/` に前編と後編の取材メモ
- `input/projects/hamanasu-shobo/`（案件 2）：逆向きのルール（メンバー→スタッフ、WEB→ウェブ）
- `input/knowledge/approved-lessons/`：承認済みの全体ルール GL-001 と、未承認の候補 PL-001（見出しの頭に【】）
- `input/instruction.md`：依頼

## 実行手順（Claude Code で頼む）
1. 台帳を読む：
   ```bash
   ACO_ROOT=tests/scenarios/F_knowledge-carryover/input python3 scripts/aco ledger nagisa-logistics brief
   ```
2. `/article-desk` で依頼を渡し、feature-writer エージェントに `article-writing` スキルで後編の初稿を書いてもらい、`output/article.md` に置く。台帳の中身を依頼文に書き写して渡さない（台帳から読めるかを見るため）。

頼み方の例：
```text
/article-desk nagisa-logistics 後編の初稿。案件フォルダは tests/scenarios/F_knowledge-carryover/input/projects/nagisa-logistics
（ACO_ROOT=tests/scenarios/F_knowledge-carryover/input）。依頼は input/instruction.md。出力は tests/scenarios/F_knowledge-carryover/output/article.md に。
```

## 合格条件
- 一時フォルダに複製した案件 1 の台帳で `aco ledger nagisa-logistics check` に通る
- locked の文がそのまま残り、rejected の表現と confidential の語がなく、rules に従っている
- 案件 2 のルール（スタッフ・ウェブ）が混ざっていない
- 未承認の候補（PL-001・PR-1）を使っていない
- 一時フォルダの中で、社名（ナギサ物流）を含む全体ルール候補は `aco lessons approve` で拒否され、社名を含まない候補は承認される。リポジトリ本体の `knowledge/approved-lessons/` は変わらない

## 検査
```bash
python3 tests/scenarios/F_knowledge-carryover/verify.py
python3 tests/scenarios/F_knowledge-carryover/verify.py --target tests/scenarios/F_knowledge-carryover/controls/bad   # 不合格になるはず
```
