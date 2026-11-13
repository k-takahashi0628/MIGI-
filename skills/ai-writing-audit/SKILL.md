---
name: ai-writing-audit
description: AI 的な文章の癖の監査。aco audit で兆候（重要性の誇張・文末の価値づけ・曖昧な関係・根拠のない一般化・抽象語の過剰・否定の並列・三項列挙・形式的な締め・文末の均質・整いすぎた発言など AI-01〜AI-17）を拾い、一つずつ文脈で判断する。語の置き換えで隠さず、具体の不足という本当の問題を素材で直し、素材がなければ【要取材】にする。「AIっぽさを消して」「AIが書いたみたい」「ありきたり」「抽象的」「AIチェックして」と言われたとき、STEP 6 のレビューで使う。
argument-hint: "[案件スラッグ] [対象ファイル]"
---

# AI 的な文章の監査

対象：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグと原稿を使う）

## 目的
AI 的に見える文章の根にある問題（具体的な事実がない所を言葉で埋めている、何にでも当てはまる、予定調和）を見つけて直す。兆候の数を減らすことは目的にしない。

## 使う場面
- STEP 6 のレビュー（literary-editor）。抽象的・ありきたりと言われた原稿。

## 使わない場面
- 「AI が書いたかどうか」を判定するため（この監査は判定をしない）。

## 入力
- 原稿（`projects/<slug>/drafts/v<N>.md`）
- `projects/<slug>/work/02_source-audit.md`（具体の素材）
- `projects/<slug>/sources/` の書き起こし（発言の確認用）

## 手順
1. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" audit <draft> --project <slug>` を回す（件数が多ければ `--json` で整理）。
2. 結果は兆候であって判定ではない。一件ずつ次を確かめる：その表現は情報を運んでいるか／根拠はあるか／取り除くと何が失われるか。
3. 直すべきものは、根にある問題を名指して直す。多くは「具体的な事実がない所を言葉で埋めている」ことから出る。素材分析にある具体（発言・行動・数字・出来事）に差し替える。素材にないときは【要取材：何が足りないか】にして、事実を作らない（`${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/specificity.md`）。
4. 単語や構文だけを理由に消さない。文脈に要る対比・列挙・まとめは残す。語を言い換えて兆候を隠すだけの修正はしない（検出から外れても文章は良くならない）。
5. 発言の中の兆候（AI-14）は書き起こしと照らす（`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" quotes <draft> --transcript <書き起こし>`）。書き起こしどおりなら本人の言葉として残す。整文で書き手が足した決め台詞なら書き起こしに戻す。
6. 機械では拾えない兆候も読む：何にでも当てはまる企業紹介、予定調和の結論、具体から飛躍した因果、途中に挟まる総括、読者の感情の説明。
7. AI 判定ツールの点数を品質の根拠にしない。報告にも書かない。

## 出力
- `projects/<slug>/work/reviews/v<N>_ai-audit.md`（`${CLAUDE_PLUGIN_ROOT}/templates/review.md` の形）
  - 冒頭：結論と件数のまとめ（直す／残す／要取材）
  - 各指摘：ID（AI-xx・負け筋の番号）・箇所（章の見出し／問いの文／該当文）・判断（直す／残す）と理由・修正案・副作用

## 失敗条件（出さずに止めて報告する）
- 修正案に、素材にない事実・数字・発言が入った。
- 語の置き換えだけで兆候の数を減らした。
- 「残す」と判断した指摘に理由がない。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/ai-writing-signs.md`
- `${CLAUDE_PLUGIN_ROOT}/references/derived/B_ai-writing-signs.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/specificity.md`
- `${CLAUDE_PLUGIN_ROOT}/philosophy/human-writing.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/review.md`
