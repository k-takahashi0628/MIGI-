# ARTICLE CREATIVE OS 設計書

この文書は、リポジトリの全体構成・命名・ファイルの形・スクリプトの使い方を一か所で決めるもの。
エージェント・スキル・スクリプトは、ここに書いた名前とパスに従う。変えるときは先にこの文書を直す。

---

## 0. 設計の前提

- 配り方：このリポジトリが Claude Code のプラグイン（article-creative-os）兼 配布元（migi-rpo）になっている。メンバーは GitHub から入れ、どのフォルダでも使う。**エンジン**（プラグイン本体：知識・テンプレート・スクリプト）と**作業フォルダ**（各メンバーの案件データ `projects/`・`.aco/`）を分ける。スキル・エージェントの中ではエンジンの場所を `${CLAUDE_PLUGIN_ROOT}/…` で書く。`aco` はエンジンの場所を自分の位置から、作業フォルダを今のフォルダから上へ `aco.config.json` を探して決める（`aco where` で確認、`aco init` で作る）。

- 呼び出しの流れ：**メインの会話（入口スキル `/article-desk`）が工程を進め、専門エージェントをサブエージェントとして呼ぶ。** サブエージェントは別のサブエージェントを呼べないため、編集長エージェントも「判断」を担い、工程の進行はメインが持つ。
- 共通知識は `philosophy/`・`knowledge/`・`workflows/` に一度だけ書き、エージェントとスキルはパスで参照する（同じ規則を何度も書かない）。
- 必要なときに必要な分だけ読む。スキルの本文は手順だけにし、長い基準は参照ファイルに置く。
- 機械で確かめられることはスクリプト（`scripts/aco`）で確かめる。判断が要ることは人とエージェントが決める。スクリプトの結果は「兆候」であり、品質の保証ではない。
- 共通の制作エンジン（このリポジトリ）と案件データ（`projects/<slug>/`、Git 管理外）を分ける。
- Python 3.9 標準ライブラリだけで動かす（追加インストール不要）。

---

## 1. ディレクトリ

```text
article-creative-os/
├── README.md                 日本語の運用 README（初回手順・コマンド例）
├── CLAUDE.md                 Claude Code が毎回読む共通設定（最上位ルール・入口・読み込み方針）
├── aco.config.json           公開範囲の設定（repo_visibility など）
├── rules.md                  最上位のルールと場所の決まり（プラグインでは CLAUDE.md が読まれないため、スキル・エージェントが最初に読む）
├── .claude-plugin/
│   ├── plugin.json           プラグインの設定（名前 article-creative-os）
│   └── marketplace.json      配布元の設定（名前 migi-rpo、source は "./"）
├── .claude/settings.json     リポジトリを開いたときの共有設定
├── agents/                   専門エージェント 10 体（プラグインの標準の場所）
├── skills/                   スキル 16 個（入口 article-desk ＋ 15 工程）
├── bin/aco                   プラグインを入れると PATH に入る検査スクリプトの入口
├── docs/architecture.md      この文書
├── philosophy/               制作哲学・人間らしさ・品質基準（10 軸）
├── references/
│   ├── original/             提供資料の原文（改変禁止）＋ MANIFEST.json
│   └── derived/              原文の分類・抽出（適用範囲つき、匿名化済み）
├── workflows/                STEP 1〜10 の進め方と、依頼の種類ごとの工程選び
├── knowledge/
│   ├── editorial-patterns/   構成の型・見出し・問い・リードと締め
│   ├── failure-patterns/     負け筋（A1〜H5）と AI 文章の兆候（AI-01〜AI-17）
│   └── approved-lessons/     承認済みの全体ルール（lessons.json）と候補（proposed.json）
├── templates/                中間成果物・納品物のひな形
├── scripts/                  aco（CLI）と aco_lib/
├── tests/
│   ├── unit/                 スクリプトの単体テスト（python3 -m unittest）
│   ├── scenarios/            TEST A〜F の入力・手順・合格条件・検証スクリプト
│   └── results/              実行結果の記録
├── examples/                 架空企業のサンプル案件（実在の顧客情報は入れない）
└── projects/
    ├── _template/            案件フォルダのひな形（Git 管理する唯一の案件フォルダ）
    └── <slug>/               実案件（.gitignore で除外）
```

---

## 2. 専門エージェント（`agents/<name>.md`）

| name | 役割 | 主に使うスキル | 書いてよい場所 |
|---|---|---|---|
| chief-editor | 編集長。目的・中心の発見・企画価値・最終判定 | article-brief, insight-discovery, editorial-critique | `work/01_brief.md` `work/03_insight.md` `work/reviews/v<N>_chief.md` |
| research-editor | 資料分析。事実・発言・推測・未確認を分ける | source-audit | `work/02_source-audit.md` |
| interview-director | 取材設計。中心の発見を引き出す質問 | interview-design | `work/03_interview-plan.md` |
| story-architect | 構成。背骨・章立て・順序・山場・結末 | story-architecture, headline-craft | `work/04_structure.md` `work/05_headlines.md` |
| feature-writer | 執筆。素材に忠実で密度の高い日本語 | article-writing, headline-craft, natural-japanese | `drafts/v<N>.md` |
| literary-editor | 文章表現。語感・リズム・必然性 | natural-japanese, ai-writing-audit | `work/reviews/v<N>_literary.md` |
| brand-reputation-editor | 広報・レピュテーション | brand-risk-review | `work/reviews/v<N>_brand.md` |
| fact-checker | 校閲・事実確認 | article-fact-check | `work/reviews/v<N>_fact.md` |
| adversarial-reviewer | 不採用の理由を探す批判的レビュー | editorial-critique（adversarial） | `work/reviews/v<N>_adversarial.md` |
| production-manager | 版・指示・禁止事項・要確認・納品の管理 | revision-control, delivery-package, feedback-learning | `history.md` `ledger.json` `delivery/` |

各エージェントのファイルの中身（見出しの順番）：
1. 役割（1〜2 文）
2. 担当範囲／担当しないこと
3. 入力（読むファイル）
4. 出力（書くファイルとその形）
5. 判断基準
6. 参照スキル・参照知識
7. 禁止事項
8. 終わったら返すもの（メインの会話への短い報告の形）

フロントマターの形（公式仕様 https://code.claude.com/docs/en/sub-agents.md）：

```yaml
---
name: fact-checker
description: （日本語。いつ呼ぶかが分かるように）
tools: Read, Grep, Glob, Bash, Write
model: inherit
skills:
  - article-fact-check
---
```
- `skills:` に書いたスキルは、呼び出し時に全文がエージェントに読み込まれる（YAML のリストで書く）。
- サブエージェントは CLAUDE.md も読む。共通ルールを本文に書き写さない。
レビュー担当は原稿（`drafts/`）を書き換えない。原稿を書くのは feature-writer と、修正指示の反映時の production-manager（revision-control）だけ。

---

## 3. スキル（`skills/<name>/SKILL.md`）

| name | 工程 | 主な担当 | 中間成果物 |
|---|---|---|---|
| article-desk | 入口。依頼を見て工程を選び、エージェントを呼ぶ | メイン会話 | `project.json` の stage を更新 |
| article-brief | STEP 1 目的設計 | chief-editor | `work/01_brief.md` |
| source-audit | STEP 2 素材分析 | research-editor | `work/02_source-audit.md` |
| interview-design | 取材設計（取材前の案件） | interview-director | `work/03_interview-plan.md` |
| insight-discovery | STEP 3 価値の発見 | chief-editor | `work/03_insight.md` |
| story-architecture | STEP 4 構成設計 | story-architect | `work/04_structure.md` |
| headline-craft | タイトル・見出し・リード | story-architect / feature-writer | `work/05_headlines.md` |
| article-writing | STEP 5 初稿 | feature-writer | `drafts/v1.md` |
| natural-japanese | 不自然な日本語の修正 | literary-editor / feature-writer | レビュー票 or 原稿 |
| ai-writing-audit | AI 的な癖の検出（機械＋判断） | literary-editor | `work/reviews/v<N>_ai-audit.md` |
| brand-risk-review | 広報リスク | brand-reputation-editor | `work/reviews/v<N>_brand.md` |
| article-fact-check | 事実・発言の照合（A〜E） | fact-checker | `work/reviews/v<N>_fact.md` |
| editorial-critique | 編集長の批評・10 軸評価・敵対的レビュー | chief-editor / adversarial-reviewer | `work/reviews/v<N>_chief.md` `v<N>_adversarial.md` `v<N>_scores.json` |
| revision-control | 指定箇所だけの修正と差分検査 | production-manager | `drafts/v<N+1>.md` `history.md` |
| delivery-package | 清書・修正表・要確認・返信文 | production-manager | `delivery/` |
| feedback-learning | 修正履歴から知見を抽出（承認待ちとして） | production-manager | `ledger.json` の proposals / `knowledge/approved-lessons/proposed.json` |

**名前の衝突について**：個人スキル（`~/skills/`）は同名のプロジェクトスキルより優先される。事実確認スキルを `fact-check` にすると、個人版がある環境ではこのリポジトリ版が使われない。そのため `article-fact-check` とする。

フロントマターの形（公式仕様 https://code.claude.com/docs/en/skills.md）：

```yaml
---
name: article-brief
description: （日本語・1,024 字以内。何をするか＋どんな依頼で使うか）
argument-hint: "[案件スラッグ]"
---
```
- `disable-model-invocation` は付けない（付けるとエージェントに読み込めない）。
- `/article-brief sample-mizuha` のように呼ぶと、本文の `$ARGUMENTS` が引数に置き換わる。
- リポジトリのファイルは、リポジトリ直下からの相対パスをバッククォートで書く（`aco validate` が存在を確かめる）。

SKILL.md の中身（見出しの順番）：目的／使う場面（使わない場面）／入力／手順／出力／失敗条件（この状態なら出さずに止めて報告する）／参照。本文は 150 行以内を目安にし、長い基準は参照ファイルへ。

---

## 4. 案件フォルダ（`projects/<slug>/`）

```text
projects/<slug>/
├── project.json        案件の基本情報（下の形）
├── ledger.json         案件台帳：変更禁止・承認済み・却下・保留・表記ルール・確定事実・公開禁止・確定事項・学習候補
├── history.md          修正履歴（版・指示した人・指示の原文・直した範囲・差分検査の結果）
├── sources/            取材資料・書き起こし・先方資料・前の記事（原本。書き換えない）
├── work/
│   ├── 01_brief.md
│   ├── 02_source-audit.md
│   ├── 03_insight.md
│   ├── 03_interview-plan.md   取材前の案件だけ
│   ├── 04_structure.md
│   ├── 05_headlines.md
│   └── reviews/
│       ├── v<N>_ai-audit.md / v<N>_literary.md / v<N>_brand.md / v<N>_fact.md / v<N>_adversarial.md / v<N>_chief.md
│       └── v<N>_scores.json
├── drafts/             v1.md, v2.md …（版は上書きしない）＋ v<N>_notes.md（執筆メモ：使った素材・【要取材】【要確認】の一覧・迷った所）
└── delivery/           final_v<N>.md, revision-table.md, open-questions.md, reply.md, checklist.md
```

### 会社フォルダ（同じ会社の案件をまとめる）

```text
projects/<会社>/
├── client.json          社名・別名・会社の資料の場所（knowledge）
├── client-ledger.json   会社の台帳（ledger.json と同じ形）。この会社のすべての案件に効く
├── knowledge/           会社理解のメモ・表記の決まり・過去の記事
└── <案件>/              案件フォルダ（上と同じ形）
```
- スラッグは「会社/案件」（例 `japan-relief/no3-taidan`）。`aco new <会社>/<案件> --client 社名` で、会社フォルダがなければ `projects/_client_template/` から作る。
- 表記ルール・書かないこと・公開禁止・人名の扱いなど、会社全体の決まりは会社の台帳に一度だけ書く（`aco ledger <会社> add …`）。案件の `brief`・`check`・`audit --project`・`quotes --project` は会社の台帳もあわせて読む。
- 会社の台帳は、ほかの会社の案件には効かない。会社をまたいで使う判断は、承認を得て一般化してから `knowledge/approved-lessons/` に入れる。
- 会社に属さない単独の案件（`projects/<slug>/`）もこれまでどおり使える。

### project.json
```json
{
  "slug": "sample-mizuha",
  "title": "仮題",
  "client": {"name": "株式会社ミズハ測器（架空）", "aliases": ["ミズハ測器"]},
  "people": [{"name": "佐伯", "role": "製造部 主任", "kind": "interviewee"}],
  "article_type": "employee-interview",
  "medium": "note",
  "visibility": "confidential",
  "decision_maker": "代表",
  "coordinator": "人事",
  "series": {"name": "", "part": "", "previous": []},
  "interview_dates": [],
  "stage": "00_new",
  "deadline": "",
  "created": "YYYY-MM-DD"
}
```
- `article_type`：`ceo-business` `ceo-organization` `employee-interview` `project-culture` `company-intro` `other`
- `visibility`：`confidential`（既定。Git に入れない）／`internal`／`public-sample`（架空のサンプルだけ）
- `stage`：`00_new` `01_brief` `02_source-audit` `03_insight` `04_structure` `05_draft` `06_review` `07_revise` `08_fact-check` `09_delivered` `10_learned`、止まっているときは `blocked`（理由と誰の判断待ちかを `history.md` に書く）

### ledger.json
```json
{
  "version": 1,
  "locked":       [{"id": "LK-1", "text": "変更禁止の文（完全一致）", "reason": "", "source": "", "date": ""}],
  "approved":     [{"id": "AP-1", "text": "承認済みの表現", "context": "", "approved_by": "", "date": ""}],
  "rejected":     [{"id": "RJ-1", "text": "却下された表現・案", "reason": "", "rejected_by": "", "date": ""}],
  "pending":      [{"id": "PD-1", "item": "要確認事項", "ask": "誰に何を聞くか", "owner": "", "status": "open", "date": ""}],
  "rules":        [{"id": "RL-1", "avoid": "仲間", "use": "メンバー", "note": "社内の呼称", "source": "", "date": ""}],
  "facts":        [{"id": "FC-1", "claim": "", "source": "", "status": "approved"}],
  "confidential": [{"id": "CF-1", "term": "公開禁止の語・情報", "reason": ""}],
  "decisions":    [{"id": "DC-1", "decision": "", "by": "", "date": ""}],
  "proposals":    [{"id": "PR-1", "kind": "rules|approved|rejected|locked|decisions", "payload": {}, "evidence": "", "status": "proposed", "date": ""}]
}
```
- `proposals` は feedback-learning が出した学習候補。本人（または先方）の承認があるまで規則として使わない。`aco ledger <slug> approve PR-1 --by <名前>` で該当の欄へ移る。

---

## 5. 知識の ID

- 負け筋：資料 A の番号をそのまま使う（`A1`〜`A6` `B1`〜`B7` `C1`〜`C8` `D1`〜`D13` `E1`〜`E7` `F1`〜`F7` `G1`〜`G4` `H1`〜`H5`、計 57）。本文は `knowledge/failure-patterns/official-article.md`。
- AI 文章の兆候：`AI-01`〜`AI-17`。本文は `knowledge/failure-patterns/ai-writing-signs.md`。

| ID | 名前 | 機械検出 |
|---|---|---|
| AI-01 | 重要性・意義の誇張（「重要な役割」「欠かせない」「象徴」「〜といっても過言ではない」） | 語の一覧 |
| AI-02 | 表層的な分析・文末の価値づけ（「〜を体現」「〜を物語る」「〜につながっている」） | 文末の型 |
| AI-03 | 曖昧な関係の表現（「深く結びつく」「密接に関わる」） | 語の一覧 |
| AI-04 | 根拠のない一般化・曖昧な権威（「多くの人が」「〜と言われています」「業界では」） | 語の一覧 |
| AI-05 | 抽象語の過剰（挑戦・成長・価値・可能性・想い・未来…） | 密度と回数 |
| AI-06 | 否定の並列（「単なるAではなくB」「AだけでなくB」「AというよりB」） | 型 |
| AI-07 | 三項列挙の多用（「A、B、そしてC」「〜も、〜も、〜も」） | 型と回数 |
| AI-08 | 形式的な締め（「これからも」「さらなる」「期待が高まります」） | 最終段落の語 |
| AI-09 | 文末・文長の均質（同じ文末の連続、長さが揃いすぎ） | 統計 |
| AI-10 | 途中の総括・言い換え（「つまり」「このように」「まさに」） | 語の一覧 |
| AI-11 | 読者の感情の説明（「〜ではないでしょうか」「心に響く」） | 語の一覧 |
| AI-12 | 意味の薄い比喩（「架け橋」「羅針盤」「原動力」「扉を開く」） | 語の一覧 |
| AI-13 | ダッシュの多用（問いの記号「── 」は除く） | 回数 |
| AI-14 | 整いすぎた発言（発言の中の決め台詞・三項・否定の並列） | 発言内の兆候 |
| AI-15 | 根拠を確かめるべき因果（「そこで」「だからこそ」「その結果」）＝C7 | 語の一覧 |
| AI-16 | 装飾の不自然（太字の多用・見出しの絵文字・「AとB」型見出しの連続） | 記号 |
| AI-17 | AI 調の定型句（「〜を通じて」「〜において」「〜に寄り添い」「〜の一環として」） | 密度 |

- 承認済みの全体ルール：`GL-001`〜（`knowledge/approved-lessons/lessons.json`）。候補：`PL-001`〜（`proposed.json`）。

---

## 6. スクリプト `scripts/aco`

すべてリポジトリの直下から `python3 scripts/aco <サブコマンド>` で動かす。終了コードは 0＝問題なし、1＝使い方の誤り・実行エラー、2＝検査で止めるべきものが見つかった。

| サブコマンド | 何をするか | 主な引数 |
|---|---|---|
| `new <slug>` | `projects/_template` から案件フォルダを作る | `--client 名` `--type 種類` `--title 仮題` |
| `status <slug>` | どの工程まで済んだか・最新版・未解決の要確認・次の一手 | |
| `audit <file>` | AI 的な兆候（AI-xx）と機械で拾える負け筋（A1・B1・B5・C4・C7・D1〜D6・D9・D10・D13・E1・G3）を行番号つきで出す | `--project <slug>`（台帳の照合も行う）`--final`（仮置き文字を止める）`--json` |
| `structure <file>` | 章ごとの字数・問いの数・極端に長い章・重複した問い・リードと締めの言葉の重なり | `--compare <前の記事>` `--json` |
| `quotes <article>` | 記事の発言を書き起こしと照合し A〜E で判定 | `--transcript <file>`（複数可）`--project <slug>`（表記ルールの言い換えを戻して照合）`--json` |
| `numbers <article>` | 記事の全文（地の文・見出しを含む）の数値が素材にあるか | `--source <file>`（複数可）`--json` |
| `scope <before> <after>` | 指定範囲の外に差分がないか検査し、必要なら範囲外を元に戻す | `--allow chapter-heading:<N>`（N 番目の章の見出しだけ）/ `chapter:<N>` / `heading:<語>` / `section:<語>` / `lines:<a>-<b>` / `contains:<語>`（複数可）`--restore <出力先>` |
| `revtable <before> <after>` | 修正表のひな形（章の見出し・直前の問い・今・直し）を作る | `--out <file>` |
| `ledger <slug> <操作>` | 案件台帳の `add` `list` `close` `approve` `reject` `check <draft>` `brief` | |
| `lessons <操作>` | 全体ルールの `propose` `approve <PL-id> --by 名` `reject` `list` `render` | |
| `score <scores.json>` | 10 軸の集計・公開不可の判定・頭打ちの判定 | `--history <前の scores.json>…` |
| `guard` | Git に入れる前の公開範囲の検査 | `--staged`（既定）`--all` `--paths …` `--install-hook` |
| `validate` | リポジトリ自体の検査（フロントマター・参照パス・原文のハッシュ・知識 ID） | |

### 判定・閾値の考え方
- `audit` の結果は `info`（気づき）／`warn`（直す候補）／`error`（台帳違反・公開禁止語・仮置き文字）に分ける。`info` と `warn` は文脈で判断する。点数（AI らしさの点）は出さない。
- `quotes` の判定（fact-check の A〜E にそろえる）
  - A：書き起こしにほぼ同じ文がある
  - B：書き起こしから言える（整文・要約で要素が一致）
  - C：言い換えで意味・範囲が変わった可能性がある（要確認）
  - D：書き起こしに根拠が見つからない（作ったセリフの疑い）
  - E：数値・固有名が書き起こしと合わない
  - D・E が 1 件でもあれば終了コード 2。
- `scope` は 1 文字・改行 1 つの違いも差分として扱う。
- `score` は未解決のブロッカー（作った発言・重要な事実の矛盾・未承認の機密・変更禁止違反・未解決の重大なブランドリスク）が 1 つでもあれば点数にかかわらず「公開不可」。直近 2 回の改善が合計 3 点未満なら「頭打ち」として、追加取材・情報不足・判断待ちを報告する。

---

## 7. 公開範囲の仕組み

- `aco.config.json`：`{"repo_visibility": "private", "allow_project_data_in_git": false, "pii_allowlist": [...]}`
- `.gitignore`：`projects/*`（`_template` と `README.md` を除く）、`.aco/`、`*.local.json`。
- `references/original/MANIFEST.json` に原文ごとの `visibility`（`internal` など）と sha256 を書く。`internal` のファイルは `repo_visibility` が `public` のとき Git に入れられない。
- `.aco/blocklist.local.json`（Git 管理外）に、実在の顧客名・人名を登録する。`guard` は `projects/*/project.json` の社名・人名と合わせて、案件フォルダ以外（`knowledge/` など）に出てきたら止める。
- `guard --install-hook` で Git の pre-commit に組み込む。

---

## 8. 学習の仕組み（案件間で混ぜない）

1. feedback-learning は、修正履歴と先方の指摘から「次も使える判断」を**候補**として出す。
2. 案件固有の候補 → その案件の `ledger.json` の `proposals`。全体の候補 → `knowledge/approved-lessons/proposed.json`。
3. 承認（本人の明示の OK）があるまで、候補は規則として使わない。
4. 全体ルールへの昇格（`aco lessons approve`）は、案件の社名・人名・未公開の語が入っていたら拒否する。
5. 制作の最初に `aco ledger <slug> brief` を読む。出てくるのは「その会社の台帳（会社フォルダの案件なら）」「その案件の台帳」「承認済みの全体ルール」だけ。他の会社・他の案件の台帳は読まない。
6. 同じ会社の案件どうしで使う判断は、承認を得て会社の台帳（`client-ledger.json`）に入れる。会社をまたぐものだけを全体ルールにする。

---

## 9. 原稿の書式（スクリプトが読む形）

```markdown
# タイトル

リード（地の文）。

## 章の見出し

地の文（あれば見出しのすぐ下）。

── 問いの文でしょうか。

佐伯：答えの1段落目。

答えの2段落目（直前の話し手が続く）。

── 次の問い。

答え。
```
- 問いの行は `── `（罫線 U+2500 を 2 つ＋半角空白 1 つ）で始める。`――` `Q.` `Q：` も問いとして読む。
- 話し手は段落の頭の `名前：` で示す。書かれていなければ直前の話し手、章の中で一度も書かれていなければ `project.json` の `people[0]`、それもなければ「不明」。
- 書き起こしの形：`名前：発言`（`[00:01:23] 名前：…` も可）。ラベルのない行は直前の話し手の続き。`聞き手` `インタビュアー` `Q` は聞き手として扱う。
- 原稿の中の印：【要確認：…】【要取材：…】【提案：…】と `<!-- 根拠：… -->`。清書（delivery/final_v<N>.md）では外し、`delivery/open-questions.md` に移す（`philosophy/editorial-principles.md`）。
- 版情報（版・もとにした版・指示）は原稿に書かず、`history.md` と `drafts/v<N>_notes.md` に書く。原稿に入れると、局所修正のときに範囲外の差分になるため。
- 最後の答えのあとに地の文を置くときは、間に区切りの行（`---` `＊` `◆` など）を一行入れる。区切りのあとは地の文として読む（`aco quotes` は発言として照合しない）。
- 案件フォルダを作らない単発の作業（テスト・一回きりの添削）では、出力先のフォルダに `history.md` と `*_notes.md` を置き、`aco ledger <slug> brief` の代わりに `aco lessons list` を読む。

## 10. レビュー票の形（`work/reviews/v<N>_<担当>.md`）

```markdown
# v2 ブランド・広報レビュー（brand-reputation-editor）

結論：（1〜2 文。公開を止める問題があるか）

### R-1 ［重大度：高］ A1 社員を分断する
- 箇所：章「…」／問い「…」／該当文「…」（問いのない記事は、段落の書き出し「…」）
- 指摘：
- 根拠：（原稿・資料・負け筋のどこに基づくか）
- 修正案：（そのまま差し替えられる文）
- 副作用：（直すと何が失われるか・別の問題が出ないか）
- 判断が要る人：（なし／決裁者／進行担当／本人）
```
- 重大度：高＝公開を止める／中＝直すべき／低＝好みや磨き。
- 点数は `v<N>_scores.json`（`templates/scores.json` の形）に分けて書く。

## 11. テンプレート（`templates/`）

| ファイル | 使う工程 |
|---|---|
| `templates/brief.md` | STEP 1 |
| `templates/source-audit.md` | STEP 2 |
| `templates/insight.md` | STEP 3 |
| `templates/interview-plan.md` | 取材設計 |
| `templates/structure.md` | STEP 4 |
| `templates/headlines.md` | 見出し |
| `templates/review.md` | STEP 6（レビュー票） |
| `templates/scores.json` | STEP 6（10 軸） |
| `templates/fact-check-table.md` | STEP 8 |
| `templates/revision-table.md` | 修正・納品 |
| `templates/open-questions.md` | 納品 |
| `templates/reply.md` | 納品（決裁者あて・進行担当あて） |
| `templates/delivery-checklist.md` | 納品 |
| `templates/history-entry.md` | 修正履歴 |
| `templates/lesson-proposal.md` | 学習 |

## 12. テスト（`tests/`）

- `tests/unit/`：スクリプトの単体テスト。`python3 -m unittest discover -s tests/unit -v`
- `tests/scenarios/<A〜F>_<名前>/`：
  - `README.md`：目的・実行手順（どのエージェント・スキルで何をするか）・合格条件
  - `input/`：架空の入力（実在の会社・人は使わない）
  - `verify.py`：`output/` に置かれた結果を機械で検査（合格 0／不合格 2）
  - `controls/`：わざと不合格にした出力。`verify.py` がそれを落とせることを確かめる
  - `output/`：実行結果
- `tests/results/<日付>_report.md`：実行の記録（合否・不合格の原因・直したこと・未実施）

## 13. 共有するファイルの形（スクリプトと知識で同じものを使う）

### 知識ファイルの一覧（エージェント・スキルはこのパスで参照する）
- `philosophy/editorial-principles.md`（最上位の制作哲学・情報の区別）
- `philosophy/human-writing.md`（人間らしさの定義・話し手の個性）
- `philosophy/quality-standards.md`（10 軸の評価基準・公開不可の条件・頭打ちの扱い）
- `references/original/MANIFEST.json`（原文の台帳）
- `references/derived/A_classification.md`（資料 A の 57 項目を 5 区分と適用範囲・例外に分類）
- `references/derived/B_ai-writing-signs.md`（資料 B の観察を 10 の観点で抽出し、日本語の企業記事に当てはめたもの）
- `knowledge/failure-patterns/README.md`（索引）
- `knowledge/failure-patterns/official-article.md`（負け筋 A1〜H5。匿名化・適用範囲つき）
- `knowledge/failure-patterns/ai-writing-signs.md`（AI-01〜AI-17）
- `knowledge/editorial-patterns/README.md`（索引）
- `knowledge/editorial-patterns/structure-types.md`（記事の種類ごとの章立ての型と、型を使わない判断）
- `knowledge/editorial-patterns/headlines-and-questions.md`（タイトル・見出し・問い）
- `knowledge/editorial-patterns/lead-and-ending.md`（リードと締め）
- `knowledge/editorial-patterns/interview-craft.md`（取材で掘る観点）
- `knowledge/editorial-patterns/quote-editing.md`（発言の整文で許すこと・許さないこと）
- `knowledge/editorial-patterns/specificity.md`（抽象を具体に置き換える手順・情報が足りないときの扱い）
- `knowledge/editorial-patterns/brand-voice-and-respect.md`（敬語・呼称・関係者への目配り・ネガティブな事実の扱い）
- `knowledge/approved-lessons/README.md` / `lessons.json` / `proposed.json` / `LESSONS.md`
- `workflows/README.md`（依頼の種類ごとの工程選び）/ `planning.md` / `interview.md` / `writing.md` / `reviewing.md` / `delivery.md`

### MANIFEST.json
```json
{"version": 1, "files": [
  {"id": "A", "file": "A_オフィシャル記事の負け筋と構成設計.md", "title": "", "provided_date": "2026-11-11",
   "source": "", "sha256": "", "visibility": "internal", "stored": "verbatim", "note": ""},
  {"id": "B", "file": null, "title": "Wikipedia:Signs of AI writing", "source": "https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing",
   "revision_note": "", "license": "CC BY-SA 4.0", "visibility": "public", "stored": "pointer-only", "note": ""}
]}
```

### lessons.json / proposed.json
```json
{"version": 1, "lessons": [
  {"id": "GL-001", "rule": "", "why": "", "how": "", "scope": "global", "origin": "", "approved_by": "", "approved_date": ""}
]}
```
```json
{"version": 1, "proposals": [
  {"id": "PL-001", "rule": "", "why": "", "how": "", "scope": "global", "origin": "", "evidence": "", "status": "proposed", "date": "", "reason": ""}
]}
```
- `scope`：`global`（全案件）／`official-article`（企業の公式記事）／`interview`（インタビュー記事）／`revision`（修正の進め方）／`delivery`（納品の出し方）
- `status`：`proposed`／`rejected`（承認されたものは lessons.json へ移り、proposed.json からは消える）

### scores.json（`templates/scores.json`）
```json
{"version": "v1", "reviewer": "chief-editor", "date": "",
 "axes": {
  "originality":     {"label": "企画の独自性",       "score": null, "reason": "", "improve": ""},
  "discovery":       {"label": "読者にとっての発見", "score": null, "reason": "", "improve": ""},
  "distinctiveness": {"label": "企業・人物の固有性", "score": null, "reason": "", "improve": ""},
  "concreteness":    {"label": "情報の具体性",       "score": null, "reason": "", "improve": ""},
  "structure":       {"label": "構成の必然性",       "score": null, "reason": "", "improve": ""},
  "naturalness":     {"label": "日本語の自然さ",     "score": null, "reason": "", "improve": ""},
  "expression":      {"label": "表現の完成度",       "score": null, "reason": "", "improve": ""},
  "accuracy":        {"label": "事実の正確性",       "score": null, "reason": "", "improve": ""},
  "brand_fit":       {"label": "ブランドへの適合性", "score": null, "reason": "", "improve": ""},
  "purpose":         {"label": "記事目的への貢献",   "score": null, "reason": "", "improve": ""}
 },
 "blockers": [
  {"type": "fabricated-quote", "detail": "", "location": "", "resolved": false}
 ],
 "notes": ""}
```
- `blockers[].type`：`fabricated-quote`（根拠のない発言の創作）／`fact-contradiction`（重要な事実の矛盾）／`confidential`（未承認の機密）／`locked-violation`（変更禁止事項への違反）／`brand-risk`（未解決の重大なブランドリスク）

### 実在の名前を入れない
- `references/original/` 以外には、実在の顧客名・人名・媒体アカウントを書かない。資料 A の出典案件は「案件K」、話し手は「代表」「執行役員」「広報担当」「人事担当」などの役割で書く。
- サンプルとテストは架空の会社だけを使い、名前に「（架空）」を付ける（例：株式会社ミズハ測器（架空））。
- 自分たちの説明文も、AI 文章の兆候（`knowledge/failure-patterns/ai-writing-signs.md`）を避けた平易な日本語で書く。
