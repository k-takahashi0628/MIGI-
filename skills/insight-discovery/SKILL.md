---
name: insight-discovery
description: 価値の発見（STEP 3）。素材の中から、この会社・この人・この出来事でしか成立しない中心の発見と、読者に示す新しい視点を探す。候補を複数出し、社名を替えても通じるかを試して一般論を落とし、根拠と山場にできるエピソードを決める。「この記事の核は？」「切り口を考えて」「何が面白い？」「独自の視点を見つけて」と言われたとき、構成の前に使う。
argument-hint: "[案件スラッグ]"
---

# 価値の発見（STEP 3）

案件：$ARGUMENTS（引数がなければ、呼び出し元から渡された案件スラッグを使う）

## 目的
記事の中心になる発見を一つ決める。素材で支えられる発見だけを採る。

## 使う場面
- 構成を作る前。既存原稿が「きれいだが何も残らない」と言われたとき。

## 使わない場面
- 範囲の決まった修正。

## 入力
- `projects/<slug>/work/01_brief.md`
- `projects/<slug>/work/02_source-audit.md`
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aco" ledger <slug> brief` の出力

## 手順
1. 目的設計・素材分析・台帳の brief を読む。
2. 発見の候補を 3〜5 出す。各候補に `${CLAUDE_PLUGIN_ROOT}/templates/insight.md` の欄を埋める。
   - 一文の言い切り
   - 根拠（素材分析の行と、発言の短い原文）
   - この会社でなければ成立しないか
   - 読者にとって新しいか（読者がもう思っていることの確認になっていないか）
   - 一番の印象につながるか
   - 公開可否の懸念
3. 置き換えの試し：候補の文の社名・人名を別の会社に替えて読む。そのまま通るものは一般論として下げる。
4. 一つ選ぶ。選んだ理由と、捨てた候補の理由を書く。
5. 選んだ発見を支える具体（出来事・数字・本人の言葉）を挙げる。山場にできるエピソードを一つ決める。
6. 素材で支えられない発見は採らない。どうしても要るなら、追加取材で聞くことに回す（interview-design）。

## 出力
- `projects/<slug>/work/03_insight.md`（`${CLAUDE_PLUGIN_ROOT}/templates/insight.md` の形）

## 失敗条件（出さずに止めて報告する）
- どの候補も置き換えの試しを通らない。「素材不足」として、追加取材で聞くことを挙げて止める。
- 選んだ発見の根拠が、書き手の解釈か推測だけ。
- 山場にできる具体のエピソードがない（構成へ進む前に報告する）。

## 参照
- `${CLAUDE_PLUGIN_ROOT}/templates/insight.md`
- `${CLAUDE_PLUGIN_ROOT}/philosophy/editorial-principles.md`
- `${CLAUDE_PLUGIN_ROOT}/philosophy/human-writing.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/editorial-patterns/specificity.md`
