# TEST A：AI 的な文章の改善

抽象的でありきたりな会社紹介文から、具体性のない箇所を見つけ、事実を作らずに書き直せるかを確かめる。

## 入力（すべて架空）
- `input/company-intro.md`：わざと AI 文章の兆候（AI-01・AI-04〜AI-12・AI-17 など）を多く入れた会社紹介文
- `input/facts.md`：分かっている事実と、分かっていないこと

## 実行手順（Claude Code で頼む）
1. literary-editor エージェントに、`ai-writing-audit` スキルで `input/company-intro.md` を見てもらう。根拠は `input/facts.md` だけ。結果を `output/review.md` に、レビュー票の形（`docs/architecture.md` §10）で書く。
2. feature-writer エージェントに、レビュー票と `input/facts.md` だけを根拠に、`natural-japanese` スキルと `knowledge/editorial-patterns/specificity.md` に沿って書き直してもらい、`output/rewrite.md` に書く（literary-editor は原稿を書き換えない）。事実が足りない所は【要取材】と追加取材の一覧に回す。

頼み方の例：
```text
literary-editor で tests/scenarios/A_ai-writing/input/company-intro.md を ai-writing-audit → natural-japanese の順に見て、review.md に書いて。
そのあと feature-writer で、レビューと facts.md だけを根拠に書き直して rewrite.md に。
事実は input/facts.md だけを使う。レビューは output/review.md、書き直しは output/rewrite.md に。
```

## 合格条件
- `output/review.md` が AI-xx か負け筋の ID を 3 種類以上挙げ、入力の文を引いて箇所を示している
- `output/rewrite.md` の数値・型番・「」の中・会社名と人名が、すべて入力にある（捏造なし）
- `aco audit` の warn の数が、入力より書き直しのほうが少ない
- 事実が足りない所を【要取材】か追加取材の一覧に回している

## 検査
```bash
python3 tests/scenarios/A_ai-writing/verify.py
python3 tests/scenarios/A_ai-writing/verify.py --target tests/scenarios/A_ai-writing/controls/bad   # 不合格になるはず
```
