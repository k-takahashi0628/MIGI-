---
name: revision-control
description: 指定範囲だけの修正と版の管理。「ここだけ修正」「他は変更禁止」「原文を維持」「前回の指示を継承」を厳格に扱う。指示の原文を履歴に残し、指示を範囲（見出しの行・章・行番号・段落）に直し、新しい版を作り、aco scope で範囲外の差分が 0 かを確かめ、出たら元に戻す。変更禁止の文・却下案・承認済み表現は台帳で照合する。「ここだけ直して」「見出しだけ変えて」「他はいじらないで」「FBを反映して」「この段落だけ」と言われたとき、原稿ファイルを書き換えるときは必ず使う。
argument-hint: "[案件スラッグ] [修正指示]"
---

# 修正管理

案件と指示：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグと指示を使う）

## 目的
指示された範囲の外を一文字も変えない。誰の、どの指示で、どこを変えたかを後から追えるようにする。

## 使う場面
- 原稿ファイルを書き換えるときすべて。先方の FB の反映。範囲を限った修正。

## 使わない場面
- 初稿を書くとき（article-writing）。レビューで修正案を出すだけのとき（原稿は書き換えない）。

## 入力
- 指示の原文（言い換えない）と、指示した人・日付
- 最新版 `projects/<slug>/drafts/v<N>.md`
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力
- 「前回の指示を継承」のときは `projects/<slug>/history.md` の過去の指示

## 手順
1. 指示の原文を `projects/<slug>/history.md` に書く（`${CLAUDE_PLUGIN_ROOT}/templates/history-entry.md` の形）。指示した人・日付・どの版への指示か。
2. 台帳の brief を読む（変更禁止・却下案・承認済みの表現・表記ルール）。継承の指示なら、history の過去の指示も読む。
3. 先方の FB なら、直す前に意図の読みを 3〜5 行で書く：何が気になったのか（誰が読んでどう感じるのが嫌なのか）、案の項目どうしのつながり、書き手側の思い込みだった所。
4. 指示を範囲に直す。
   - `heading:<語>`：その語を含む見出しの行だけ
   - `section:<語>`：その見出しの章全体
   - `lines:<a>-<b>`：前の版の行番号
   - `contains:<語>`：その語を含む段落
   範囲が曖昧なら狭いほうに取り、広げる必要があれば確認事項に挙げる。範囲の決め方と理由を history に書く。
5. 最新版を複製して `projects/<slug>/drafts/v<N+1>.md` を作り、範囲の中だけを直す。前の版は上書きしない。版情報は原稿に書かず history.md に書く（原稿に足すと範囲外の差分になる）。
6. 差分を検査する：`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" scope <前の版> <新しい版> --allow <範囲>`。範囲外の差分が出たら `--restore <出力先>` で範囲外を元に戻し、もう一度検査して 0 を確かめる。1 文字・改行 1 つも差分として扱う。
7. 台帳を検査する：`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> check <新しい版>`。変更禁止の文が変わった・却下案が入った・公開禁止語がある、のどれかが出たら直す。
8. 直した範囲に発言があれば `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" quotes <新しい版> --transcript <書き起こし>` を回す。範囲の外で問題に気づいても直さず、確認事項として報告する。
9. history に結果を書く：新しい版、範囲、scope の結果（範囲外 0）、ledger check の結果、気づいたが直さなかった所。
10. 修正表のひな形が要るときは `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" revtable <前の版> <新しい版> --out <file>`。
11. 承認されていない判断を台帳の規則にしない。台帳に書くのは、先方・本人が明示した変更禁止・承認・却下だけ（`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> add …`。引数は `--help` で確かめる）。それ以外の気づきは feedback-learning の候補に回す。

## 出力
- `projects/<slug>/drafts/v<N+1>.md`
- `projects/<slug>/history.md` の記録
- 修正表（必要なとき）と、範囲外で気づいた点の一覧

## 失敗条件（出さずに止めて報告する）
- `aco scope` の範囲外の差分が 0 にならない。
- 変更禁止の文が変わった（`aco ledger check` が error）。
- 範囲を勝手に広げた。前の版を上書きした。
- 指示の原文が history に残っていない。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/templates/history-entry.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/revision-table.md`
- `${CLAUDE_PLUGIN_ROOT}/docs/architecture.md`（§4 案件フォルダ・§6 スクリプト）
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/official-article.md`（H4・A5・F3）
