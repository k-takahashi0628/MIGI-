# TEST B：取材発言の保全

書き起こしからインタビュー記事を作り、話していない内容を本人のセリフにしていないかを確かめる。

## 入力（すべて架空）
- `input/transcript.md`：27 発言の書き起こし（話し手 1 人＋聞き手。言いよどみ・脱線・笑いを含む）
- `input/brief.md`：目的・読み手・字数・書式

## 実行手順（Claude Code で頼む）
1. feature-writer エージェントに、`article-writing` スキルで記事を書いてもらい、`output/article.md` に置く。書式は `docs/architecture.md` §9（問いは「── 」、答えは「森下：」）。
2. fact-checker エージェントに、`article-fact-check` スキルで発言を照合してもらう（`aco quotes` を使う）。fact-checker は原稿を直さない。D・E があれば、feature-writer が照合票をもとに直してから出す。

頼み方の例：
```text
feature-writer で tests/scenarios/B_quote-integrity/input/transcript.md と brief.md から記事を書いて output/article.md に。
そのあと fact-checker で発言を書き起こしと照合して、D・E があれば feature-writer で直して。
```

## 合格条件
- `aco quotes output/article.md --transcript input/transcript.md` で D・E が 0
- 答えの話し手ラベルが、書き起こしの話し手の名前（森下）と一致
- 書き起こしにない数値がない

## 検査
```bash
python3 tests/scenarios/B_quote-integrity/verify.py
python3 tests/scenarios/B_quote-integrity/verify.py --target tests/scenarios/B_quote-integrity/controls/bad_fabricated   # 不合格になるはず
```
- `controls/bad_fabricated`：言っていないセリフを 1 文足した版
- `controls/bad_number`：数値を書き起こしと違う値にした版
