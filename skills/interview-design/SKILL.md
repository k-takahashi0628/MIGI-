---
name: interview-design
description: 取材設計。一般的な質問集を作らず、記事の中心となる発見を引き出す質問を、発言の背景・具体的な出来事・判断の理由・矛盾・転機・固有の経験の観点で組み、各質問に「この答えで記事の何が書けるか」と優先度を付ける。「取材の質問を作って」「インタビュー設計」「何を聞けばいい？」「追加取材で聞くことを出して」と言われたとき、取材前と、素材不足で追加取材が要るときに使う。
argument-hint: "[案件スラッグ]"
---

# 取材設計

案件：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグを使う）

## 目的
記事の中心になる発見を、取材の場で引き出す。答えを聞いたあとに「記事の何が書けるか」が決まっている質問だけを残す。

## 使う場面
- 取材の前。素材不足で追加取材が要るとき（insight-discovery・story-architecture から戻ってきたとき）。

## 使わない場面
- 取材が終わり、素材が足りている案件。

## 入力
- `projects/<slug>/work/01_brief.md`
- `projects/<slug>/work/02_source-audit.md`（あれば）
- `projects/<slug>/work/03_insight.md`（仮説があれば）
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力

## 手順
1. 目的設計と、あれば素材分析・発見の仮説を読む。
2. 記事の中心の仮説を一文で置く（取材で崩れてよい）。置けないなら「確かめたいこと」を 3 つまで書く。
3. 仮説ごとに質問を束ね、この順に並べる。
   - 入口：答えやすい事実（いつ・何を担当しているか）
   - 具体：一つの出来事（いつ・どこで・誰と・何をしたか・何が起きたか）
   - 理由：なぜその判断をしたか、ほかの選択肢は何だったか
   - 揺さぶり：迷い・失敗・反対意見・前と言っていることの違い
   - 固有：その人・その会社でしか起きないこと、本人の言い方
4. 各質問に「この答えで記事の何が書けるか」を一言付ける。書けない質問は削る。
5. 避ける質問：はい／いいえで終わる、感想だけを聞く、答えを誘導する（「大変でしたよね？」）、どの会社にも聞ける（「御社の強みは？」）。
6. 配慮の要る話題（資本・人事・取引先・数字）は、聞き方と、出してよいかの確かめ方を分けて書く。
7. 取材の後に起きる予定の出来事を記事に入れたい場合は、取材の場で本人の言葉として確かめる質問を入れる（取材後の出来事を取材のセリフにしないため）。
8. 優先度（必ず聞く／時間があれば）と時間配分を付ける。

## 出力
- `projects/<slug>/work/03_interview-plan.md`（`${CLAUDE_PLUGIN_ROOT}/templates/interview-plan.md` の形）

## 失敗条件（出さずに止めて報告する）
- 目的設計がない。先に article-brief を行う。
- 質問がどの会社にも聞ける一般論だけになった。仮説を立て直す。
- 「記事で何が書けるか」が空の質問が残っている。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/interview-craft.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/structure-types.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/interview-plan.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/failure-patterns/official-article.md`（C2・E1）
