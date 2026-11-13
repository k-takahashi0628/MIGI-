# ARTICLE CREATIVE OS

企業の記事（採用広報・経営者インタビュー・社員インタビュー・カルチャー記事・会社紹介）を作る制作システム。
目的は量産ではなく、編集者が時間をかけて行う観察・発見・構成・執筆・推敲・校閲の質を安定して出すこと。
記事の価値は、どれだけ流暢に書けたかではなく、何が書かれているかで決まる。

## 最上位のルール（全工程・全エージェント共通）

1. **作らない。** 話していない発言、確かめていない事実・数値・固有名を書かない。素材が足りなければ、もっともらしい文で埋めずに【要取材】として残し、追加取材か構成の変更を提案する。
2. **情報の種類を分ける。** 発言・事実・解釈・推測・提案を混ぜない。印の付け方は `philosophy/editorial-principles.md`。
3. **指定された範囲の外を変えない。** 「ここだけ修正」「他は変更禁止」「原文を維持」「前回の指示を継承」は最優先で守る。修正のたびに `python3 scripts/aco scope` で差分を確かめ、範囲外の変更は元に戻す。
4. **承認されていない判断を規則にしない。** 学習は候補として出し、本人の明示の OK があってから台帳や全体ルールに入れる。ある案件のルールを別の案件に持ち込まない。
5. **兆候は問題そのものではない。** `aco audit` が拾う AI 文章の兆候は、語を消すためではなく、具体性の不足・根拠のない価値づけなど本当の問題を見つけるために使う。AI 判定ツールの点数を品質の根拠にしない。
6. **話し手の個性を残す。** 全員を同じ優等生の文にしない。誤字や口語をわざと混ぜることを人間らしさと取り違えない。
7. **案件データを外に出さない。** `projects/<slug>/` は Git に入れない。顧客名・人名・書き起こし・未公開の原稿を `knowledge/` `examples/` `tests/` などに書かない（サンプルは架空の会社だけ）。
8. **点数で合格にしない。** 作った発言・重要な事実の矛盾・未承認の機密・変更禁止違反・未解決の重大なブランドリスクのどれかがあれば、点数にかかわらず公開可の完成稿としない（`philosophy/quality-standards.md`）。

## 入口

- 記事の仕事はまず `/article-desk <案件スラッグ> <依頼>` で始める。依頼の種類を見て必要な工程だけを選ぶ。
- 依頼の種類ごとの工程：`workflows/README.md`
- 工程の中身：`workflows/planning.md`（STEP 1〜4）・`workflows/interview.md`・`workflows/writing.md`（STEP 5）・`workflows/reviewing.md`（STEP 6〜8）・`workflows/delivery.md`（STEP 9〜10）
- このリポジトリは RPO チームの Claude Code プラグイン（`.claude-plugin/`）。スキルは `skills/`、専門エージェント 10 体は `agents/`。プラグインでは CLAUDE.md が読まれないので、最上位のルールは `rules.md` にも置いてある（この CLAUDE.md の「最上位のルール」を直したら `rules.md` も直す）。進行はメインの会話が持ち、エージェントはサブエージェントとして呼ぶ（サブエージェントは別のサブエージェントを呼べない）。
- 全体の設計（名前・パス・ファイルの形）：`docs/architecture.md`

## 読み込みの方針（コンテキストを無駄にしない）

- 全部を読まない。今の工程のスキルが指している知識ファイルだけを読む。
- 制作を始めるとき、再開するときは、まず `python3 scripts/aco ledger <slug> brief` を読む（その案件の台帳と承認済みの全体ルールだけが出る）。
- 別の案件フォルダは読まない。同じ会社の決まりは会社の台帳（`projects/<会社>/client-ledger.json`）から brief に出てくるので、それ以外のほかの案件は開かない。
- 案件フォルダを作らない単発の作業では、出力先に `history.md` と `*_notes.md` を置き、台帳の代わりに `python3 scripts/aco lessons list` を読む。
- 長い素材（書き起こしなど）は、必要な箇所を探してから読む。

## よく使うコマンド

```bash
python3 scripts/aco new <会社>/<案件> --client "社名" --type employee-interview   # 案件を作る（会社フォルダも作る）
python3 scripts/aco ledger <会社> add rules --avoid "…" --use "…"           # 会社全体の決まりを足す
python3 scripts/aco status <slug>                                          # どこまで進んだか
python3 scripts/aco ledger <slug> brief                                    # 制作前に読む一枚
python3 scripts/aco audit projects/<slug>/drafts/v2.md --project <slug>    # 兆候と台帳の照合
python3 scripts/aco quotes projects/<slug>/drafts/v2.md --transcript projects/<slug>/sources/transcript.md
python3 scripts/aco scope <前の版> <新しい版> --allow chapter-heading:3       # 範囲外の差分の検査（第3章の見出しだけ）
python3 scripts/aco score projects/<slug>/work/reviews/v2_scores.json      # 10 軸の集計と公開可否
python3 scripts/aco validate                                               # リポジトリ自体の検査
```

## 報告のしかた

- 日本語で、結果を先に短く。直した場所は「章の見出し」と「問いの文」で示す。
- 修正は、まず修正前→修正後のテキストを出す。見た目の作り込みはそのあと。
- 作業中の原稿には【要確認：…】【要取材：…】の印を残してよい。清書（読者に見せるもの）では外し、確認事項は別のファイルに出す。`aco audit --final` が残りを止める。

## このリポジトリを直すとき

- 名前・パス・ファイルの形を変えるときは、先に `docs/architecture.md` を直す。
- `references/original/` の原文は書き換えない（`aco validate` が sha256 で確かめる）。
- 直したら `python3 scripts/aco validate` と `python3 -m unittest discover -s tests/unit` を通す。
- Git に入れる前に `python3 scripts/aco guard` が走る（`aco guard --install-hook` で設定）。GitHub への push は、公開範囲（非公開リポジトリか）を本人に確かめてから。
