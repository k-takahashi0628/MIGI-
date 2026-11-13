---
name: editorial-critique
description: 編集長視点の批評と 10 軸評価、または不採用の理由を探す敵対的レビュー。chief モードでは全レビュー票を統合し、採る指摘・採らない指摘を決め、10 軸（独自性・発見・固有性・具体性・構成・自然さ・表現・正確性・ブランド適合・目的への貢献）を根拠と改善案つきで採点し、aco score で公開不可・頭打ちを判定する。adversarial モードでは「この企業でなければ成立しないか」など 7 つの問いで記事が落ちる理由を探す。「批評して」「編集長として見て」「点数をつけて」「公開できる？」「厳しく見て」「ダメな所を探して」と言われたとき、STEP 6 と修正後の再評価で使う。
argument-hint: "[案件スラッグ] [chief|adversarial]"
---

# 編集長の批評・敵対的レビュー

案件とモード：$ARGUMENTS（モードの指定がなければ、呼び出したのが chief-editor なら chief、adversarial-reviewer なら adversarial）

## 目的
- chief：レビューを一本の修正方針にまとめ、公開してよいかを判断する材料を出す。
- adversarial：記事が不採用になる理由を、公開前に見つける。

## 使う場面
- STEP 6（レビューの統合と採点）。修正後の再評価。

## 使わない場面
- 個別の文の推敲だけ（natural-japanese）。

## 入力
- 原稿全文、`projects/<slug>/work/01_brief.md`・`projects/<slug>/work/03_insight.md`・`projects/<slug>/work/04_structure.md`
- chief：その版のレビュー票すべて（ai-audit・literary・brand・fact・adversarial）と機械検査の結果
- adversarial：原稿・目的設計・素材分析だけ（ほかのレビュー票は読まない）
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力

## 手順（chief モード）
1. 上の入力を読む。
2. 指摘を統合する。重複はまとめる。ぶつかる指摘は、決裁者の意向と目的設計で決める。採る／採らないを一行ずつ、理由つきで書く。
3. 10 軸を採点し、`${CLAUDE_PLUGIN_ROOT}/templates/scores.json` の形で書く。基準は `${CLAUDE_PLUGIN_ROOT}/philosophy/quality-standards.md`。各軸に理由（原稿のどこで）と改善案。点数は判断の補助であって、品質の保証ではない。
4. ブロッカーを scores.json に挙げる：根拠のない発言の創作／重要な事実の矛盾／未承認の機密／変更禁止事項への違反／未解決の重大なブランドリスク。
5. 集計する：`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" score <scores.json> --history <前の版の scores.json>`。公開不可・要改善・公開候補と、頭打ちかどうかを確かめる。
6. 修正指示を作る。採った指摘を、場所（章の見出し／問いの文）・修正案・副作用つきで並べ、feature-writer に渡す形にする。
7. 修正後の版は、全文を読み直して再評価する（直した所だけを見ない）。
8. 頭打ちなら、残った問題を追加取材・情報不足・判断待ちに分け、誰に何を聞くかを書いて止める。

## 手順（adversarial モード）
1. 原稿・目的設計・素材分析だけを読む。
2. 7 つの問いで、記事が落ちる理由を探す。
   - この企業でなければ成立しないか（社名を替えても通じる段落を挙げる）
   - 取材対象者の発言として自然か（整いすぎ・本人の語彙にない言葉）
   - 経営者や広報担当者が読んで違和感はないか
   - 社員や取引先を意図せず傷つけないか
   - 読者にとって新しい発見があるか
   - 目的を達成する構成になっているか
   - 説明だけで終わっていないか
3. 各問いに：結論（通る／落ちる）・根拠（該当文を必ず引く）・どう直せば通るか・直したときの副作用。
4. 遠慮はしない。根拠のない難癖は書かない。

## 出力
- chief：`projects/<slug>/work/reviews/v<N>_chief.md`（統合の結論・採否・修正指示）と `projects/<slug>/work/reviews/v<N>_scores.json`
- adversarial：`projects/<slug>/work/reviews/v<N>_adversarial.md`（`${CLAUDE_PLUGIN_ROOT}/templates/review.md` の形）

## 失敗条件（出さずに止めて報告する）
- 点数だけを根拠に「公開してよい」と言うこと。
- ブロッカーが残っているのに「公開候補」とすること。
- 指摘に修正案か副作用がない。
- adversarial で、該当文を引かずに結論を書いた。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/philosophy/quality-standards.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/scores.json`
- `${CLAUDE_PLUGIN_ROOT}/templates/review.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/official-article.md`
