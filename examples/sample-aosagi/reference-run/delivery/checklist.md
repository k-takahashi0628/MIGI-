# 納品前チェック

<!-- 案件：sample-aosagi ／ 版：v2 ／ 実行日：2026-11-11 -->
<!-- 一つでも通らなければ清書を作らずに止めて報告する（delivery-package の手順 1）。 -->

**結果：通らない。清書（final_v2.md）は作っていない。** 了承待ちの情報と【要取材】が残っているため、今回は「確認のお願い」（`delivery/reply.md`・`delivery/open-questions.md`）だけを出す。

## 機械検査
- [ ] `python3 scripts/aco audit projects/sample-aosagi/drafts/v2.md --final --project sample-aosagi` で error が 0（結果：**error 9**。【要確認】7・【要取材】2 の印と、先頭のサンプル注記のコメント 1。終了コード 2）
- [x] `python3 scripts/aco ledger sample-aosagi check projects/sample-aosagi/drafts/v2.md` が通る（結果：台帳との食い違いはない。終了コード 0）
- [x] `python3 scripts/aco quotes projects/sample-aosagi/drafts/v2.md --transcript projects/sample-aosagi/sources/interview-record.md --project sample-aosagi` で D・E が 0（結果：A 30／B 0／C 0／D 0／E 0。終了コード 0）
- [ ] `python3 scripts/aco score projects/sample-aosagi/work/reviews/v2_scores.json` が「公開不可」でない（結果：**公開不可（ブロッカーあり）**。合計 60／100。ブロッカー 4：未承認の機密 3〔氏名・2019 年の作り直しと 300 食分・冷凍麺のラインと時期〕、重要な事実の矛盾 1〔ノートの時期〕。終了コード 2）
- [x] 直前の修正（v1→v2）の `aco scope` の結果が history.md にある（範囲外の差分 0 件）

## 清書
- [ ] 【要確認】【要取材】の印・社内メモ・出典名・版情報コメントが残っていない（清書を作っていないため対象外。v2 には印が残っている）
- [ ] 章のタイトルから、その章の最後の一文まで、そのまま貼れる（同上）
- [ ] ファイル名に版が入っている。返信に「最終版は〜」と書いた（返信では「v2 は確認用の初稿で、清書ではない」と明記した）

## 修正表・要確認
- [x] 場所を章の見出しと問いの文で示した（`delivery/open-questions.md`）
- [x] 修正前→修正後のテキストが説明より先にある（`delivery/revision-table.md`。先方に渡した前の版がないため、先方向けの修正はない）
- [x] 当たった負け筋の番号を書いた（社内の `work/v2_revtable.md` と `history.md`。先方向けの返信には書かない）
- [x] 要確認を、ドキュメントの該当の文にもコメントで付けた（付ける場所を一覧に書いた。コメントそのものは先方のドキュメントに貼る段階で付ける）

## 返信
- [x] 決裁者あてと進行担当あてに分けた
- [ ] 直した要点を、先方の案・指摘の項目どおりに並べた（初回のため、先方の指摘はまだない）
- [x] 案から変えた所・担当者の案を消した所に理由を書いた（依頼メモから変えた所＝字数。理由を書いた）
- [x] 期日と、前日のリマインドの予定を書いた（期日は【仮】2026-11-18。`project.json` の deadline が空のため、進行担当に確かめる）

## 候補者・社外に見せるもの
- [x] 社内向けの注記が候補者の目に触れる所に出ていない（候補者に見せる清書は、まだ作っていない）
