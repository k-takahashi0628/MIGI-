# ARTICLE CREATIVE OS

企業の記事（採用広報・経営者インタビュー・社員インタビュー・カルチャー記事・会社紹介）を、Claude Code で作るための制作システム。
10 の専門エージェント、16 のスキル、検査スクリプト `aco`、会社・案件ごとの台帳でできている。RPO チームの Claude Code プラグインとして配る。

ねらいは量産ではない。作った発言や確かめていない事実なしで、読者が「この会社の記事だから読みたい」と思える記事を、毎回同じ質で出すこと。

---

## 1. 使い始める（RPO チームのみんな）

Claude Code の**プラグイン**として入れる。入れると、どのフォルダで Claude Code を開いても `/article-desk` などのスキルと専門エージェントが使える。リポジトリを取ってくる必要はない。

### 最初に一回だけ

1. GitHub の **rpo チーム**（`miginanameue/rpo`）に入れてもらい、GitHub にログインできることを確かめる。
2. ターミナルで、GitHub の認証を Git に渡す（非公開のリポジトリから取り込むため）。`gh` がなければ `brew install gh` で入れる。
   ```bash
   gh auth login
   ```
   ```bash
   gh auth setup-git
   ```
3. プラグインの配布元を足して、入れる。`claude` コマンドがなくても、デスクトップアプリに入っている Claude Code を探して使う一行にしてある。
   ```bash
   CLAUDE_BIN="$(command -v claude || ls -d "$HOME/Library/Application Support/Claude/claude-code/"*/*/claude.app/Contents/MacOS/claude | tail -1)"; "$CLAUDE_BIN" plugin marketplace add miginanameue/article-creative-os && "$CLAUDE_BIN" plugin install article-creative-os@migi-rpo
   ```
   Claude Code の画面（CLI）で入れる場合は `/plugin marketplace add miginanameue/article-creative-os` → `/plugin install article-creative-os@migi-rpo`。
4. Claude Code（デスクトップアプリの Code タブ）を開き直す。

### 案件を始める

1. 記事の仕事用のフォルダを一つ作る（例：`~/RPO記事`）。Claude Code でそのフォルダを開く。ここが**作業フォルダ**になり、案件のデータは `projects/<会社>/<案件>/` に入る（GitHub には上がらない）。
2. 頼む：`/article-desk japan-relief/no3-taidan 企画と下書きを見て記事にしたい`（`/article-desk` が出なければ `/article-creative-os:article-desk`）。
3. 初めての作業フォルダでは、作業フォルダにしてよいか聞かれる。顧客名・人名は `.aco/blocklist.local.json` に足しておく（全体の知識への混入を止める）。

### 更新を受け取る

プラグインの自動更新は最初は止まっている。新しい版が出たら次を回す（または `/plugin` の画面で配布元の自動更新を有効にする）。

```bash
CLAUDE_BIN="$(command -v claude || ls -d "$HOME/Library/Application Support/Claude/claude-code/"*/*/claude.app/Contents/MacOS/claude | tail -1)"; "$CLAUDE_BIN" plugin marketplace update migi-rpo && "$CLAUDE_BIN" plugin update article-creative-os@migi-rpo
```

### 知っておくこと

- 案件のデータ（作業フォルダの `projects/`）はメンバーごとの手元にあり、GitHub では共有されない。同じ案件を引き継ぐときは、案件フォルダを社内のドライブなどで渡す。
- 全体ルール（`knowledge/approved-lessons/`）の承認は管理者がリポジトリで行う。プラグインの中では候補を出すまで（作業フォルダの `.aco/` に残る）。候補は管理者に共有する。
- 資料 A の原文は顧客名を含むため GitHub に上げていない。分類・匿名化したもの（`knowledge/`）だけが配られる。

## 1-2. このリポジトリを直す人（管理者）

1. 取ってくる：`gh repo clone miginanameue/article-creative-os`。スキルは `skills/`、エージェントは `agents/`、プラグインの設定は `.claude-plugin/`（`plugin.json`・`marketplace.json`）。
2. 直したら回す（必要なのは Python 3.9 以上だけ）。
   ```bash
   python3 scripts/aco validate
   ```
   ```bash
   python3 -m unittest discover -s tests/unit
   ```
3. Git に入れる前の検査を有効にする：`python3 scripts/aco guard --install-hook`。実在の顧客名は `.aco/blocklist.local.json` に入れておく。
4. スキル・エージェントの中で、知識やスクリプトは `${CLAUDE_PLUGIN_ROOT}/…` で指す（プラグインとして入れたときの場所に置き換わる）。最上位のルールは `rules.md`（プラグインでは CLAUDE.md が読まれないため）。
5. main に push すると、メンバーは「更新を受け取る」の手順で新しい版を受け取れる。
6. 全体ルールの候補をメンバーから受け取ったら、リポジトリで `python3 scripts/aco lessons propose …` → 本人の OK のあと `approve --by` → push。

---

## 2. 依頼のしかた

入口は `/article-desk`。依頼の種類を見て、必要な工程だけを回す。工程ごとのスキルを直接呼んでもよい。

| したいこと | 頼み方の例 |
|---|---|
| 案件を始める | `python3 scripts/aco new maruyama/no1-interview --client "株式会社〇〇" --type employee-interview --title "仮題"` のあと、資料を `projects/maruyama/no1-interview/sources/` に置く（会社ごとのフォルダ `projects/maruyama/` も作られる） |
| 会社全体の決まりを足す | `python3 scripts/aco ledger maruyama add rules --avoid "仲間" --use "メンバー"`（その会社の全案件に効く） |
| 取材済みの素材から記事を作る | `/article-desk kitamura-2026 書き起こしから社員インタビュー記事を作りたい` |
| 取材の前に質問を作る | `/interview-design kitamura-2026` |
| 目的・読み手を決める | `/article-brief kitamura-2026` |
| 構成だけ考える | `/story-architecture kitamura-2026` |
| 先方の修正指示を反映する | `/article-desk kitamura-2026 先方のFB（sources/fb_1110.md）を反映して` |
| ここだけ直す | `/revision-control kitamura-2026 第3章の見出しだけ変更。他は一文字も変えない` |
| AI っぽさ・不自然さを見る | `/ai-writing-audit kitamura-2026` → `/natural-japanese kitamura-2026` |
| 広報上のリスクを見る | `/brand-risk-review kitamura-2026` |
| 事実と発言を確かめる | `/article-fact-check kitamura-2026` |
| 編集長の批評と 10 軸の採点 | `/editorial-critique kitamura-2026 chief` （不採用の理由探しは `adversarial`） |
| 納品物を作る | `/delivery-package kitamura-2026` |
| 修正から学ぶ | `/feedback-learning kitamura-2026`（候補を出すだけ。承認は本人） |
| どこまで進んだか | `python3 scripts/aco status kitamura-2026` |

機械の検査だけを使うこともできる。

```bash
python3 scripts/aco audit projects/kitamura-2026/drafts/v2.md --project kitamura-2026          # AI 文章の兆候と負け筋・台帳の照合
python3 scripts/aco audit projects/kitamura-2026/delivery/final_v3.md --final --project kitamura-2026   # 清書に印・社内メモが残っていないか
python3 scripts/aco quotes projects/kitamura-2026/drafts/v2.md --transcript projects/kitamura-2026/sources/interview.md --project kitamura-2026
python3 scripts/aco numbers projects/kitamura-2026/drafts/v2.md --source projects/kitamura-2026/sources/interview.md --source projects/kitamura-2026/sources/facts.md
python3 scripts/aco structure projects/kitamura-2026/drafts/v2.md --compare projects/kitamura-2026/sources/previous.md
python3 scripts/aco scope projects/kitamura-2026/drafts/v2.md projects/kitamura-2026/drafts/v3.md --allow chapter-heading:3
python3 scripts/aco revtable projects/kitamura-2026/drafts/v2.md projects/kitamura-2026/drafts/v3.md --out projects/kitamura-2026/delivery/revision-table.md
python3 scripts/aco score projects/kitamura-2026/work/reviews/v3_scores.json --history projects/kitamura-2026/work/reviews/v2_scores.json
```

---

## 3. 仕組み

### 工程（STEP 1〜10）

| STEP | 工程 | 担当エージェント | スキル | 成果物（`projects/<slug>/`） |
|---|---|---|---|---|
| 1 | 目的設計 | chief-editor | article-brief | `work/01_brief.md` |
| 2 | 素材分析 | research-editor | source-audit | `work/02_source-audit.md` |
| （取材前） | 取材設計 | interview-director | interview-design | `work/03_interview-plan.md` |
| 3 | 価値の発見 | chief-editor | insight-discovery | `work/03_insight.md` |
| 4 | 構成設計 | story-architect | story-architecture・headline-craft | `work/04_structure.md` `work/05_headlines.md` |
| 5 | 初稿 | feature-writer | article-writing | `drafts/v1.md` |
| 6 | 編集レビュー（4 体が独立に → 編集長が統合） | literary-editor・brand-reputation-editor・fact-checker・adversarial-reviewer → chief-editor | ai-writing-audit・natural-japanese・brand-risk-review・article-fact-check・editorial-critique | `work/reviews/v<N>_*.md` `v<N>_scores.json` |
| 7 | 品質改善 | feature-writer | article-writing・natural-japanese | `drafts/v<N+1>.md`（直したら全文を再評価） |
| 8 | 事実確認 | fact-checker | article-fact-check | `work/reviews/v<N>_fact.md` |
| 9 | 納品 | production-manager | delivery-package | `delivery/`（清書・修正表・要確認・返信文・チェック表） |
| 10 | 学習 | production-manager | feedback-learning | 台帳の候補・全体ルールの候補（承認待ち） |

- 進行はメインの会話（`/article-desk`）が持ち、エージェントはサブエージェントとして呼ぶ（サブエージェントは別のサブエージェントを呼べないため）。
- 修正の依頼（指定箇所だけ・先方の指摘の反映）は production-manager が `revision-control` で受ける。毎回 `aco scope` で範囲外の差分が 0 であることを確かめ、出たら元に戻す。
- 工程ごとに中間成果物を残すので、`aco status` で途中から再開できる。軽い依頼では全工程を回さない（`workflows/README.md`）。

### 品質の評価（10 軸）

企画の独自性・読者にとっての発見・企業と人物の固有性・情報の具体性・構成の必然性・日本語の自然さ・表現の完成度・事実の正確性・ブランドへの適合性・記事目的への貢献を、各 10 点で採点する（`philosophy/quality-standards.md`）。

- 点数は判断の補助で、品質の保証ではない。
- 作った発言・重要な事実の矛盾・未承認の機密・変更禁止違反・未解決の重大なブランドリスクのどれかがあれば、点数にかかわらず「公開不可」（`aco score`）。
- 直近 2 回の改善が合計 3 点未満なら「頭打ち」。直し続けずに、追加取材・情報不足・判断待ちとして報告する。

### AI 的な文章の監査

`aco audit` は、AI 文章の兆候 17 種（AI-01〜AI-17：重要性の誇張、表層的な価値づけ、否定の並列、三項列挙、形式的な締め、抽象語の過剰 など）と、機械で拾える負け筋（社員の分断、言い過ぎ、口語、同じ語の近接反復 など）を行番号つきで出す。

- 結果は「兆候の一覧」で、判定ではない。点数（AI らしさの点）は出さない。
- 語を消すことが目的ではない。具体的な事実が足りない・根拠のない価値づけ、という本当の問題を直す。事実が足りなければ作らずに【要取材】にする。
- 基準：`knowledge/failure-patterns/ai-writing-signs.md`（資料 B から抽出し、日本語の企業記事に当てはめたもの）

### 事実確認

- 主張ごとに A（直接確認）〜E（矛盾あり）で判定する（`article-fact-check`）。
- 発言は `aco quotes` で書き起こしと照合し、作ったセリフ（D）や数値違い（E）を止める。地の文の数値は `aco numbers` で素材と照合する。
- 未確認のものを勝手に確定させず、要確認として残す。

### 案件ごとの台帳と学習

- 案件は会社ごとのフォルダにまとめる（`projects/<会社>/<案件>/`）。会社全体の決まりは会社の台帳 `projects/<会社>/client-ledger.json` に一度だけ書き、その会社のすべての案件に効かせる。ほかの会社には効かない。
- 各案件の `ledger.json` に、変更禁止の文・承認済みの表現・却下された案・保留・表記ルール・確定した事実・公開禁止の語・確定事項・学習候補を持つ。`aco ledger <slug> check` で原稿を照合する。
- 学習は候補として出すだけ。本人の明示の OK のあとに `approve --by` で規則になる。
- 全体ルール（`knowledge/approved-lessons/lessons.json`）に上げるとき、案件の社名・人名・除外リストの名前・メールアドレス・電話番号が入っていたら拒否する。ある案件のルールが別の案件に混ざらない。

### 参照資料

- 資料 A「オフィシャル記事の負け筋と構成設計」：原文は `references/original/`（顧客名を含むため Git には入れず手元だけ。sha256 は `MANIFEST.json`）。57 の負け筋を「基本原則／公式記事原則／案件固有／推奨／条件付き判断」に分けたものが `references/derived/A_classification.md`、匿名化した本文が `knowledge/failure-patterns/official-article.md`。
- 資料 B（Wikipedia「Signs of AI writing」）：原文は保存せず、URL と版を `MANIFEST.json` に記録。抽出は `references/derived/B_ai-writing-signs.md`。

---

## 4. フォルダ

```text
CLAUDE.md                 毎回読まれる共通ルール（最上位のルール・入口・読み込み方針）
docs/architecture.md      設計書（名前・パス・ファイルの形・スクリプト）
agents/           専門エージェント 10 体
skills/           スキル 16 個
philosophy/               制作哲学・人間らしさ・品質基準
references/               提供資料の原文と、その分類・抽出
workflows/                工程の進め方と、依頼の種類ごとの工程選び
knowledge/                負け筋・AI 文章の兆候・構成や見出しの型・承認済みの全体ルール
templates/                中間成果物と納品物のひな形 15 種
scripts/aco               検査スクリプト（Python 標準ライブラリだけ）
tests/                    単体テスト・シナリオテスト A〜F・実行結果
examples/                 架空のサンプル案件
projects/                 実案件（_template 以外は Git に入らない）
```

---

## 5. 機密と公開範囲

- 実案件のフォルダ（`projects/<slug>/`）は `.gitignore` で Git に入らない。
- `aco guard` が、Git に入れる前に次を止める：案件フォルダの中身、internal の原文、メールアドレス・電話番号、案件の社名・人名や除外リストの名前が `knowledge/` などに出てくること、書き起こしらしいファイル名。
- `aco.config.json` の `repo_visibility` を `public` にすると、internal の資料も止める。リポジトリを公開する前に切り替える。

---

## 6. テスト

```bash
python3 -m unittest discover -s tests/unit        # 単体テスト（63 件）
python3 tests/scenarios/run.py controls           # 採点の検査が良い出力と悪い出力を見分けるか（17 件）
python3 tests/scenarios/run.py outputs            # シナリオ A〜F の実際の出力を採点
```

2026-11-11 の結果は `tests/results/2026-11-11_report.md`（すべて合格。テストで見つかった 15 点の食い違いを直した記録つき）。

---

## 7. 個人スキルとの関係

- 個人スキル `~/skills/fact-check` は、同じ名前のプロジェクトスキルより優先される。そのため、このリポジトリの事実確認スキルは `article-fact-check` という名前にしている。判定（A〜E）は個人スキルと同じ。
- 個人スキル `official-article` と資料 A は同じ中身。このリポジトリでは、資料 A を分類・匿名化して `knowledge/` に分けて持っている。

---

## 8. まだできていないこと

- Claude Code 本体で、スキルの自動選択とエージェントの個別呼び出しを通しで確かめていない（テストは、分身がエージェント定義とスキルを読んで役を順に演じる形で行った）。
- 実案件での利用。出力の質を編集者の目で評価すること。
- Google ドキュメント・note への貼り付け、コメントの書き込みなど、外部ツールとのつなぎ込み。
- `aco audit` の語の一覧は手作り。案件を重ねて、誤検出の多い語を外していく必要がある。

## 9. 今後の改善候補

- 実案件 2〜3 本で使い、差し戻しの指摘を feedback-learning で台帳・全体ルールに積む。
- 先方の修正指示（Google ドキュメントのコメント）を取り込み、`revision-control` に渡す手順。
- 前の記事との表記の照合（呼称・時期の言葉・数値）を `aco` に足す。
- シナリオテストを、Claude Code の非対話モードで自動実行できるようにする。
