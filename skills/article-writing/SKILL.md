---
name: article-writing
description: 本文執筆（STEP 5）。構成と素材に忠実に、事実と話し手の個性を保ったまま原稿を書く。発言は書き起こしから整文し、話していないことをセリフにしない。取材後の出来事は地の文にする。具体が足りない所は【要取材】、根拠が弱い所は【要確認】で残し、もっともらしい文で埋めない。書いたら aco で機械検査を回す。「本文を書いて」「初稿を作って」「記事にして」「インタビューを記事に起こして」と言われたときに使う。
argument-hint: "[案件スラッグ]"
---

# 本文執筆（STEP 5）

案件：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグを使う）

## 目的
素材にあることだけで、密度の高い自然な原稿を書く。話し手が読んで「自分の言葉だ」と思える発言にする。

## 使う場面
- STEP 5（初稿）。構成からやり直した全面改稿。STEP 7 で chief-editor が採った指摘を反映するとき。

## 使わない場面
- 範囲の決まった修正（revision-control）。

## 入力
- `projects/<slug>/work/01_brief.md`〜`projects/<slug>/work/05_headlines.md`
- `projects/<slug>/sources/` の書き起こし
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力（表記ルール・承認済みの表現・却下案・公開禁止）

## 手順
1. 上の入力を読む。構成がなければ書かずに止める。
2. 書式は `${CLAUDE_PLUGIN_ROOT}/docs/architecture.md` §9（問いは `── `、話し手は段落の頭に `名前：`）。版情報は原稿に書かず `projects/<slug>/drafts/v<N>_notes.md` に書く。最後の答えのあとに地の文を置くときは区切りの行（`---`）を入れる。
3. 発言の扱い（`${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/quote-editing.md`）
   - 発言は書き起こしの該当箇所から整文する。言い淀み・重複は削ってよい。意味・範囲・強さは変えない。
   - 本人が言っていない内容をセリフにしない。話をつなぐ必要がある所は地の文にするか、【要確認：書き起こしにない】と書く。
   - 取材の後の出来事はセリフにせず、地の文で事実だけ書く。
   - 話し手の言葉の癖・語彙を残す。全員を同じ文体にしない（`${CLAUDE_PLUGIN_ROOT}/philosophy/human-writing.md`）。
4. 地の文は見出しのすぐ下に置き、答えの段落と混ぜない。
5. 抽象語で埋めない。具体の素材がなければ【要取材：何が足りないか】と書く（`${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/specificity.md`）。数字・固有名・年月は素材分析にあるものだけ使う。
6. 台帳の表記ルールと承認済みの表現を使い、却下案は使わない。
7. 書き終えたら機械検査を回し、はっきりしたものから直す。
   - `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" audit <draft> --project <slug>`
   - `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" structure <draft>`（シリーズなら `--compare <前の記事>`）
   - `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" quotes <draft> --transcript <書き起こし>`（インタビュー記事）
   quotes で D・E になった発言は、書き起こしに戻って直すか【要確認】にする。
8. 書き手の迷い（どちらにも書けた所・削って惜しい素材）を執筆メモに残す。

## 出力
- `projects/<slug>/drafts/v<N>.md`（初稿は v1。前の版は上書きしない）
- `projects/<slug>/drafts/v<N>_notes.md`（執筆メモ：使った素材、【要取材】【要確認】の一覧、迷った所、機械検査の結果）

## 字数と素材
- 字数より、根拠のある素材の範囲を優先する。届かないときは埋めずに、足りない字数と追加取材の質問を報告する（`${CLAUDE_PLUGIN_ROOT}/workflows/writing.md` の「字数と素材がぶつかるとき」）。
- 構成（`projects/<slug>/work/04_structure.md`）がない短い仕事では、最小限の構成（章・山場・各章の根拠）を `v<N>_notes.md` に書いてから書く。長い記事なら story-architect に戻す。

## 失敗条件（出さずに止めて報告する）
- 構成がない。先に story-architecture。
- インタビュー記事なのに書き起こしがない。セリフを書かずに止める。
- `aco quotes` の D・E が残ったまま「完成」と言うこと。
- 素材にない数字・固有名・出来事が入った。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/quote-editing.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/specificity.md`
- `${CLAUDE_PLUGIN_ROOT}/philosophy/human-writing.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/official-article.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/ai-writing-signs.md`
