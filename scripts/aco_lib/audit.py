"""AI 的な文章の兆候（AI-01〜AI-17）と、機械で拾える負け筋の検出。

結果は「兆候の一覧」であって品質の判定ではない。点数は出さない。
"""
from __future__ import annotations

import json
import re
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

from . import paths
from .textutil import (
    Block,
    KANJI_RUN,
    char_len,
    excerpt_around,
    katakana_words,
    nfkc,
    offsets_to_lines,
    line_at,
    parse_document,
    split_sentences,
)

NOTE = "これは兆候の一覧で、品質の判定ではない。info／warn は文脈で判断する（語を消すことが目的ではない）。"

NAMES = {
    "AI-01": "重要性・意義の誇張",
    "AI-02": "表層的な分析・文末の価値づけ",
    "AI-03": "曖昧な関係の表現",
    "AI-04": "根拠のない一般化・曖昧な権威",
    "AI-05": "抽象語の過剰",
    "AI-06": "否定の並列",
    "AI-07": "三項列挙の多用",
    "AI-08": "形式的な締め",
    "AI-09": "文末・文長の均質",
    "AI-10": "途中の総括・言い換え",
    "AI-11": "読者の感情の説明",
    "AI-12": "意味の薄い比喩",
    "AI-13": "ダッシュの多用",
    "AI-14": "整いすぎた発言",
    "AI-15": "根拠を確かめるべき因果",
    "AI-16": "装飾の不自然",
    "AI-17": "AI 調の定型句",
    "A1": "社員を分断する",
    "A2": "新しい挑戦を特定の人たちの手柄にする",
    "A4": "社員への過剰な敬語",
    "B1": "何も考えていなかったように見える",
    "B5": "言い切れない大きな宣言",
    "C4": "言い過ぎ",
    "D1": "口語",
    "D2": "カタカナの口語",
    "D3": "弱い文末・二重のぼかし",
    "D4": "同じ語を近くで繰り返す",
    "D5": "類語を順番に使い回す",
    "D6": "作った感じのする型",
    "D9": "頭でっかち・つなぎすぎ",
    "D10": "「たとえば」なのに例がない",
    "D13": "「そのまま」「すぐに」の言い過ぎ",
    "E1": "問いが感想・はい／いいえ",
    "G1": "呼び方の揺れ",
    "G3": "記号・空白",
    "LEDGER": "案件台帳との照合",
    "FINAL": "仮置き文字の残り",
}

# (code, refs, level, pattern, hint)
WORD_RULES = [
    ("AI-01", [], "warn",
     r"重要な役割|大きな役割|欠かせない|不可欠|極めて重要|大きな意味を持|象徴(?:する|して|的)|の証(?:だ|です|である|と言え)|礎|鍵を握|過言ではな|画期的|革新的|唯一無二|新たな地平|大きな一歩",
     "何がどう重要かを、出来事・数字・発言で示す。示せないなら削る"),
    ("AI-03", [], "info",
     r"深く結びつ|密接に(?:関|結|つな)|と結びついて|に関わりを持|と深く関わ|と深い関わり",
     "何と何が、どういう関係か（誰が何をしたか）を直接書く"),
    ("AI-04", [], "warn",
     r"多くの(?:人|方|企業|社員)が|誰もが|一般的に|と(?:言|い)われて(?:い|お)|専門家(?:は|の間|によ)|業界では|よく知られ|さまざまな声|多くの声|多方面から",
     "誰が言ったのか・何件なのかを出典どおりに書く。出典がなければ削る"),
    ("AI-10", [], "info",
     r"つまり|このように|言い換えれば|すなわち|要するに|総じて|以上のように|まさに",
     "途中のまとめが本当に要るか。前の文で言えていれば削る"),
    ("AI-11", [], "warn",
     r"ではないでしょうか|心に響|胸が熱く|感動を覚え|共感を呼|と感じる方も多い|心を動かされ|心を打|胸を打",
     "読者の感情は説明せず、感情が動く事実を置く"),
    ("AI-12", [], "info",
     r"まるで|のような存在|羅針盤|架け橋|原動力|DNA|種をま|花開|扉を開|道しるべ|旅路|航海|彩り|物語を紡",
     "比喩で言い換えた中身（具体的な事実）が書けるならそちらを書く"),
    ("B1", [], "info",
     r"迷うことは(?:ほとんど)?(?:な|あり)|手をつけられて(?:い)?な|手が回らな|できていなかった|やりきれな|考えていなかった|後回しにして",
     "過去を無策に見せない。意図した選択として書けるか（例：限られた体制では最も確実な方法だった）"),
    ("B5", ["C4"], "warn",
     r"必ず|絶対|一番|No\.?\s?1|ナンバーワン|日本一|業界初|業界一|唯一|ゼロ|格段に|最も|圧倒的|完璧|100\s?%",
     "根拠の言葉どおりの数と範囲にする。言い切れなければ基準・節目として書く"),
    ("C4", ["B5"], "info",
     r"全員|すべての|全ての|あらゆる",
     "実際の範囲（例：グループ長全員）と合っているか"),
    ("D1", [], "warn",
     r"なんです|っていう|めっちゃ|やっぱり|すごく|みたいな|ちゃんと|たくさん|いちばん",
     "公式記事なら書き言葉に（媒体と話し手の語り口による）"),
    ("D1", [], "info",
     r"そこは|しそう|走り出|いい変化|してくれ|ですね|とか(?=[、。]|$)",
     "公式記事なら書き言葉に（話し手の個性として残すかは判断）"),
    ("D13", [], "info",
     r"そのまま(?:生き|活き|使え|通用|役立)|すぐに",
     "データや仕組みが何をどれだけ縮めるのかを正確に書く"),
]

D2_WORDS = {
    "チャンス": "機会", "タイミング": "時期・局面", "スムーズ": "円滑", "アップデート": "見直す・手を入れる",
    "カルチャー": "文化", "チャレンジ": "挑戦", "マインド": "姿勢・考え方", "コミット": "責任を持つ・約束する",
    "スピード感": "速さ", "ワクワク": "（感情が動いた具体的な出来事を書く）",
}

AI05_WORDS = [
    "挑戦", "成長", "価値", "可能性", "想い", "未来", "新たな", "さまざまな", "様々な", "多様な", "大切", "魅力", "やりがい",
    "変革", "実現", "貢献", "寄り添", "一人ひとり", "前向き", "真摯", "最適", "共創", "ワクワク", "わくわく", "情熱", "誇り",
    "本質", "革新", "進化", "飛躍",
]
AI05_RE = re.compile("|".join(re.escape(w) for w in AI05_WORDS) + r"|思い(?!ま|出|切|つ|込)")

AI17_RE = re.compile(r"を通じて|を通して|において|における|に寄り添|の一環として|を軸に|を胸に|を武器に|に向き合い|といった|とともに")

AI06_STRONG = re.compile(
    r"単なる[^。]{0,30}?(?:ではな|でもな|に(?:とど|留)まら)|ただの[^。]{0,20}?ではな|だけでなく|だけではなく|だけじゃなく|のみならず|というより(?:も)?|よりもむしろ|からではなく"
)
AI06_WEAK = re.compile(r"ではなく")

AI02_STRONG = re.compile(r"(?:を体現|を物語|を象徴|に寄与|を育ん|を育む|を後押し)[^。]{0,8}$")
AI02_WEAK = re.compile(r"(?:を示し|を示す|につなが)[^。]{0,8}$")

AI07_RES = [
    re.compile(r"[^、。]{1,15}、[^、。]{1,15}、そして[^、。]{1,20}"),
    re.compile(r"[^。]{1,20}も、[^。]{1,20}も、[^。]{1,20}も"),
    re.compile(r"(?:[^\s・、。「」]{1,8}・){2,}[^\s・、。「」]{1,8}"),
    re.compile(r"[^、。]{2,15}し、[^、。]{2,15}し、"),
]

AI08_RE = re.compile(r"これからも|今後も|さらなる|未来へ|未来に向け|期待が高まり|目が離せ|楽しみです|挑戦は続|歩みは止ま|していきたいと思います|に違いありません|ことでしょう|続けていきます")
AI14_RE = re.compile(r"こそが|にほかなりません|と確信しています|に尽きます")
AI15_RE = re.compile(r"^\s*(そこで|だからこそ|その結果|それによって|そのため|だから)")
AI01_RE = re.compile(WORD_RULES[0][3])

A1_NEW = re.compile(r"新しく(?:加わ|入っ|入社)|新たに(?:加わ|入っ|入社)|中途(?:入社|採用|で)|経験者|新メンバー|新しいメンバー|新加入")
A1_OLD = re.compile(
    r"これまでの(?:メンバー|社員|人|方)|既存(?:の)?(?:メンバー|社員|組織|の方)|生え抜き|古参|以前からの(?:メンバー|社員)|もともといた|これまでいた|プロパー|昔からの(?:メンバー|社員)"
)
A2_RE = re.compile(
    r"(?:推進役|中心|リード|主役|けん引|牽引)[^。]{0,25}(?:新しく|新たに)(?:加わ|入)|(?:新しく|新たに)(?:加わ|入)[^。]{0,25}(?:推進役|中心|リード|主役|けん引|牽引)"
)
A4_RE = re.compile(r"いただ(?:き|い|け|く)|くださ(?:っ|い|る)")
D3_RE = re.compile(r"のだと思います|と思います|と思っています|と考えています|と感じています|かもしれません")
D10_RE = re.compile(r"たとえば|例えば")
E1_YESNO = re.compile(r"(ますか|ですか|ませんか|でしたか|ましたか)[？?]?\s*$")
E1_WH = re.compile(r"何|なに|なぜ|どう|どの|どこ|いつ|誰|だれ|どれ|どんな|いかが|どれくらい|どのくらい|理由|きっかけ|どちら")
PLACEHOLDER_RE = re.compile(r"（仮）|〇〇|○○|●●|XX|ＸＸ|TBD|【要確認[^】]*】|【要取材[^】]*】|【提案[^】]*】|\[要確認[^\]]*\]|（要確認[^）]*）|\(要確認[^)]*\)")
# 原稿の中の印（中身つきも含む）。兆候の検査では中身を数えない
MARKER_RE = re.compile(r"【(?:要確認|要取材|提案)[^】]*】")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF]")
D5_GROUPS = [
    ["挑戦", "取り組み", "打ち手", "施策", "チャレンジ"],
    ["メンバー", "社員", "仲間", "スタッフ", "人材"],
    ["お客様", "顧客", "クライアント"],
]
D4_STOP = {"当社", "弊社", "自分", "私達", "私たち"}


class Finder:
    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []
        self._seen: Set[tuple] = set()

    def add(self, code: str, level: str, line: int, excerpt: str, hint: str, refs: Optional[List[str]] = None, col: Optional[int] = None) -> None:
        key = (code, level, line, excerpt, col)
        if key in self._seen:
            return
        self._seen.add(key)
        self.items.append(
            {"code": code, "name": NAMES.get(code, code), "refs": refs or [], "level": level, "line": line, "excerpt": excerpt, "hint": hint}
        )


def _sentence_units(blocks: Sequence[Block]):
    """(block, sentence, raw_offset) を返す。"""
    for b in blocks:
        if b.kind not in ("para", "question"):
            continue
        base = b.label_len if b.kind == "para" else 0
        src = b.text if b.kind == "para" else b.raw
        for s, off in split_sentences(src):
            yield b, s, base + off if b.kind == "para" else off


def audit_text(text: str, ledger: Optional[Dict[str, Any]] = None, final: bool = False, extra_names: Sequence[str] = ()) -> List[Dict[str, Any]]:
    original_text = text
    # 【要取材：…】などの印の中身は兆候として数えない（行と位置は変えない）
    text = MARKER_RE.sub(lambda m: " " * len(m.group(0)), text)
    blocks = parse_document(text)
    f = Finder()
    content_blocks = [b for b in blocks if b.kind in ("para", "question", "heading", "title")]
    paras = [b for b in blocks if b.kind == "para"]
    body_chars = sum(char_len(b.text) for b in paras) or 1

    # 語の一覧
    for code, refs, level, pat, hint in WORD_RULES:
        rx = re.compile(pat)
        for b in content_blocks:
            for m in rx.finditer(b.raw):
                f.add(code, level, b.line_of(m.start()), excerpt_around(b.raw, m.start()), hint, refs, col=m.start())

    # D2 カタカナの口語
    d2 = re.compile("|".join(D2_WORDS))
    for b in content_blocks:
        for m in d2.finditer(b.raw):
            f.add("D2", "info", b.line_of(m.start()), excerpt_around(b.raw, m.start()), "言い換えの例：%s → %s" % (m.group(0), D2_WORDS[m.group(0)]))

    sentences = list(_sentence_units(blocks))

    # AI-02 文末の価値づけ / AI-15 因果 / D9 長い文 / D10 たとえば / D6
    for idx, (b, s, off) in enumerate(sentences):
        core = re.sub(r"[。！？!?」』）)\s]+$", "", s)
        if AI02_STRONG.search(core):
            f.add("AI-02", "warn", b.line_of(off), s[:60], "文末で価値づけをしていないか。何が起きたかの事実で終える")
        elif AI02_WEAK.search(core):
            f.add("AI-02", "info", b.line_of(off), s[:60], "何に・どうつながったのかが本文の事実で言えているか")
        if AI15_RE.match(s):
            f.add("AI-15", "info", b.line_of(off), s[:60], "この因果は本人の発言・資料にあるか。書き手の推測なら外す", ["C7"])
        n = char_len(s)
        commas = s.count("、")
        if n > 90 or commas >= 4:
            f.add("D9", "info", b.line_of(off), s[:60], "長い文（%d 字・読点 %d）。文を分けられないか" % (n, commas))
        if D10_RE.search(s):
            nxt = sentences[idx + 1][1] if idx + 1 < len(sentences) and sentences[idx + 1][0] is b else ""
            both = s + nxt
            concrete = re.search(r"\d", nfkc(both)) or "「" in both or katakana_words(both) or re.search(r"[一二三四五六七八九十百千]+(人|社|件|年|回|か月|日)", both)
            if not concrete:
                f.add("D10", "info", b.line_of(off), s[:60], "「たとえば」の後に具体的な場面（根拠のあるもの）があるか")

    # D6 「〜こと。」の連続・「〜のか。」の連続（段落ごと）
    for b in paras:
        sents = split_sentences(b.text)
        run_koto = 0
        run_noka = 0
        for s, off in sents:
            core = s.rstrip("」』）) ")
            run_koto = run_koto + 1 if re.search(r"こと[。]?$", core) else 0
            run_noka = run_noka + 1 if re.search(r"のか[。？?]?$", core) else 0
            if run_koto == 2:
                f.add("D6", "warn", b.line_of(b.label_len + off), s[:60], "「〜こと。〜こと。」の型は一つの記事で一度まで")
            if run_noka == 2:
                f.add("D6", "warn", b.line_of(b.label_len + off), s[:60], "「〜のか。〜のか。」と問いを重ねる型は一つの記事で一度まで")

    # AI-06 否定の並列
    strong_count = 0
    for b in content_blocks:
        strong_spans = []
        for m in AI06_STRONG.finditer(b.raw):
            strong_spans.append((m.start(), m.end()))
            strong_count += 1
            refs = ["B4"] if "からではなく" in m.group(0) else []
            f.add("AI-06", "warn", b.line_of(m.start()), excerpt_around(b.raw, m.start()), "否定した側の言葉が印象に残らないか。対比を外して言いたいことだけを書けるか", refs)
        for m in AI06_WEAK.finditer(b.raw):
            if any(a <= m.start() < z for a, z in strong_spans):
                continue
            f.add("AI-06", "info", b.line_of(m.start()), excerpt_around(b.raw, m.start()), "「AではなくB」が必要な対比か（否定した言葉が残らないか）", ["B4"])
    for i in range(len(sentences) - 1):
        b1, s1, o1 = sentences[i]
        b2, s2, _ = sentences[i + 1]
        if b1 is b2 and re.search(r"(ではありません|ではない|じゃない)[。]$", s1) and re.search(r"(です|だ|のです)[。]$", s2):
            f.add("AI-06", "info", b1.line_of(o1), s1[:60], "「〜ではありません。〜です。」の型。言いたい方だけで書けるか")

    # AI-07 三項列挙
    ai07 = 0
    first07 = None
    for b, s, off in sentences:
        for rx in AI07_RES:
            m = rx.search(s)
            if m:
                ai07 += 1
                ln = b.line_of(off)
                first07 = first07 or ln
                f.add("AI-07", "info", ln, s[:60], "三つ並べる必要があるか。一番大事な一つを具体的に書けないか")
                break
    if ai07 >= 3:
        f.add("AI-07", "warn", first07 or 1, "三項列挙が %d か所" % ai07, "列挙が多いと網羅を装った表層的な文に見える")

    # AI-08 形式的な締め（最後の 2 段落）
    for b in paras[-2:]:
        for m in AI08_RE.finditer(b.raw):
            f.add("AI-08", "warn", b.line_of(m.start()), excerpt_around(b.raw, m.start()), "締めはリードの問いを本文の言葉で回収する。抽象的な未来への期待で終えない")

    # AI-09 文末・文長の均質
    para_sents = [(b, s, off) for b, s, off in sentences if b.kind == "para"]
    run = 1
    prev = None
    for b, s, off in para_sents:
        core = re.sub(r"[。！？!?」』）)\s]+$", "", s)
        key = core[-3:]
        if prev is not None and key == prev:
            run += 1
            if run == 4:
                f.add("AI-09", "info", b.line_of(off), "「…%s」で終わる文が 4 つ続く" % key, "文末をそろえすぎていないか（体言止め・問い・短い文で変化をつけられるか）")
            if run == 5:
                f.add("AI-09", "warn", b.line_of(off), "「…%s」で終わる文が 5 つ以上続く" % key, "同じ文型・文末が続いている")
        else:
            run = 1
        prev = key
    lens = [char_len(s) for _, s, _ in para_sents if char_len(s) >= 5]
    if len(lens) >= 10:
        mean = statistics.mean(lens)
        cv = statistics.pstdev(lens) / mean if mean else 0
        if cv < 0.25:
            f.add("AI-09", "info", para_sents[0][0].line, "文の長さが均一（変動係数 %.2f）" % cv, "長い文と短い文の緩急がない")

    # AI-05 抽象語
    counts: Dict[str, List[int]] = {}
    total05 = 0
    for b in paras:
        for m in AI05_RE.finditer(b.raw):
            counts.setdefault(m.group(0), []).append(b.line_of(m.start()))
            total05 += 1
    for w, lines in sorted(counts.items(), key=lambda kv: -len(kv[1])):
        if len(lines) >= 3:
            f.add("AI-05", "info", lines[0], "「%s」が %d 回" % (w, len(lines)), "この語が指す中身（誰が何をしたか）を書けるか")
    dens05 = total05 / (body_chars / 1000.0)
    if total05 >= 5 and dens05 >= 10:
        f.add("AI-05", "warn", paras[0].line if paras else 1, "抽象語が 1,000 字あたり %.1f 個（計 %d）" % (dens05, total05), "抽象語が多い。具体的な出来事・数字・発言に置き換える（`knowledge/editorial-patterns/specificity.md`）")

    # AI-17 定型句
    c17: Dict[str, List[int]] = {}
    for b in paras:
        for m in AI17_RE.finditer(b.raw):
            c17.setdefault(m.group(0), []).append(b.line_of(m.start()))
    total17 = sum(len(v) for v in c17.values())
    for w, lines in c17.items():
        if len(lines) >= 3:
            f.add("AI-17", "info", lines[0], "「%s」が %d 回" % (w, len(lines)), "定型句を普通の言い方にできるか（〜を通じて→〜で）")
    if total17 >= 5 and total17 / (body_chars / 1000.0) >= 3:
        f.add("AI-17", "warn", paras[0].line if paras else 1, "定型句が計 %d 回" % total17, "AI 調の定型句が多い")

    # AI-13 ダッシュ
    dash_lines = []
    for b in paras:
        for m in re.finditer(r"──|——|―{2}|—", b.raw):
            dash_lines.append(b.line_of(m.start()))
    if len(dash_lines) > 3:
        f.add("AI-13", "info", dash_lines[0], "本文のダッシュが %d 個" % len(dash_lines), "読点・括弧・文の区切りで足りないか")

    # AI-14 整いすぎた発言 / A4 敬語
    for b in paras:
        if not b.is_answer:
            continue
        sig = len(AI06_STRONG.findall(b.raw)) + len(AI01_RE.findall(b.raw)) + len(AI14_RE.findall(b.raw))
        sig += sum(1 for rx in AI07_RES[:2] if rx.search(b.raw))
        if sig >= 2:
            f.add("AI-14", "info", b.line, b.text[:50], "発言が決め台詞に整いすぎていないか。書き起こしの言い方に戻せるか", ["C1"])
        for m in A4_RE.finditer(b.raw):
            f.add("A4", "info", b.line_of(m.start()), excerpt_around(b.raw, m.start()), "社内の人への敬語なら外す（顧客・パートナーへは残す。「方」は候補者にだけ）")

    # AI-16 装飾
    bolds = []
    for b in content_blocks:
        for m in re.finditer(r"\*\*[^*\n]+\*\*", b.raw):
            bolds.append(b.line_of(m.start()))
    if len(bolds) > 5:
        f.add("AI-16", "info", bolds[0], "太字が %d か所" % len(bolds), "太字を絞る")
    heads = [b for b in blocks if b.kind == "heading"]
    for h in heads:
        if EMOJI_RE.search(h.text):
            f.add("AI-16", "info", h.line, h.text[:40], "見出しの絵文字")
    to_heads = [h for h in heads if re.fullmatch(r"[^、。]{1,12}と[^、。]{1,12}", h.text)]
    if len(to_heads) >= 3:
        f.add("AI-16", "info", to_heads[0].line, "「AとB」型の見出しが %d 本" % len(to_heads), "見出しは章の答えを言い切る（F4）")

    # A1 分断 / A2 手柄
    for i, b in enumerate(paras):
        mnew = A1_NEW.search(b.raw)
        if not mnew:
            continue
        hit = A1_OLD.search(b.raw)
        if not hit:
            for j in (i - 1, i + 1):
                if 0 <= j < len(paras):
                    near = paras[j]
                    if abs(near.line - b.line) <= 6 and A1_OLD.search(near.raw):
                        hit = A1_OLD.search(near.raw)
                        break
        if hit:
            f.add("A1", "warn", b.line_of(mnew.start()), excerpt_around(b.raw, mnew.start()),
                  "新しく加わった人とこれまでの人を対で書いていないか。主語を会社・組織・全員にし、加わったことは「補強」として一度だけ書く")
    for b in paras:
        for m in A2_RE.finditer(b.raw):
            f.add("A2", "warn", b.line_of(m.start()), excerpt_around(b.raw, m.start()), "挑戦の主語は会社。「事業がその局面に入った」「組織が補強された」と書く")

    # D3 弱い文末
    total3 = 0
    first3 = None
    for b in paras:
        ms = list(D3_RE.finditer(b.raw))
        total3 += len(ms)
        if ms and first3 is None:
            first3 = b.line_of(ms[0].start())
        if len(ms) >= 2:
            f.add("D3", "warn", b.line_of(ms[0].start()), "一つの段落に弱い文末が %d 回" % len(ms), "言い切れる所は言い切る")
    if total3 >= 3:
        f.add("D3", "warn", first3 or 1, "弱い文末（と思います・と考えています等）が計 %d 回" % total3, "言い切れる所は言い切る")

    # D4 同じ語の近接反復
    stop = set(D4_STOP) | {n for n in extra_names if n}
    stop |= {b.speaker for b in blocks if b.explicit_speaker and b.speaker}
    body = [b for b in blocks if b.kind in ("para", "question")]
    joined = ""
    spans = []
    for b in body:
        spans.append((len(joined), b))
        joined += b.raw + "\n"
    tok_pos: Dict[str, List[int]] = {}
    for m in KANJI_RUN.finditer(joined):
        tok_pos.setdefault(m.group(0), []).append(m.start())
    for m in re.finditer(r"[ァ-ヺー]{3,}", joined):
        if m.group(0).strip("ー"):
            tok_pos.setdefault(m.group(0), []).append(m.start())
    for w, rx in (("いま", r"(?<![ぁ-ん])いま(?![すしせ])"), ("一つ", r"一つ")):
        for m in re.finditer(rx, joined):
            tok_pos.setdefault(w, []).append(m.start())

    start_of = {id(b): st for st, b in spans}

    def block_at(pos: int) -> Block:
        cur = spans[0][1]
        for start, b in spans:
            if start <= pos:
                cur = b
            else:
                break
        return cur

    for w, ps in tok_pos.items():
        if len(ps) < 3 or w in stop or any(w in n or n in w for n in stop if len(n) >= 2):
            continue
        reported_blocks = set()
        k = 0
        while k + 2 < len(ps):
            b0 = block_at(ps[k])
            same_para = block_at(ps[k + 2]) is b0
            if ps[k + 2] - ps[k] <= 200 or same_para:
                if id(b0) not in reported_blocks:
                    reported_blocks.add(id(b0))
                    f.add("D4", "warn", b0.line_of(ps[k] - start_of[id(b0)]), "「%s」が近くで 3 回以上" % w, "言い換えるか削る（同じものは同じ言葉で呼ぶ D5 との兼ね合いに注意）")
                k += 3
            else:
                k += 1

    # D5 類語の使い回し / G1 呼び方の揺れ
    for b in paras:
        for grp in D5_GROUPS:
            used = [w for w in grp if w in b.raw]
            if len(used) >= 3:
                f.add("D5", "info", b.line, "／".join(used), "同じものは同じ言葉で呼ぶ")
    allraw = "\n".join(b.raw for b in paras)
    members = [w for w in D5_GROUPS[1] if w in allraw]
    if len(members) >= 3:
        f.add("G1", "info", paras[0].line if paras else 1, "呼び方が %d 種類：%s" % (len(members), "／".join(members)), "社内の人の呼び方を一つにそろえる（案件の表記ルールに従う）")

    # E1 / G3 問い
    qs = [b for b in blocks if b.kind == "question"]
    markers = set()
    endings = set()
    for q in qs:
        s = q.raw.strip()
        if s.startswith("──"):
            markers.add("──")
            if not re.match(r"^── \S", s):
                f.add("G3", "warn", q.line, s[:40], "「── 」（罫線 2 つ＋半角空白 1 つ）にそろえる")
        elif s.startswith("――"):
            markers.add("――")
        elif s.startswith("——"):
            markers.add("——")
        else:
            markers.add("Q")
        last = q.text.rstrip()[-1:] if q.text.rstrip() else ""
        endings.add("？" if last == "？" else "?" if last == "?" else "なし")
        if E1_YESNO.search(q.text) and not E1_WH.search(q.text):
            f.add("E1", "info", q.line, q.text[:50], "はい／いいえで終わる問い。「どのように」「なぜ」で中身を聞けるか")
        if "気にな" in q.text:
            f.add("E1", "info", q.line, q.text[:50], "感想の問い。中身を聞く形にする")
    if len(markers) > 1:
        f.add("G3", "info", qs[0].line, "問いの記号が混在：%s" % "・".join(sorted(markers)), "問いの記号を一つにそろえる")
    if len(endings) > 1:
        f.add("G3", "info", qs[0].line, "問いの終わり方が混在：%s" % "・".join(sorted(endings)), "疑問符の有無と全角／半角をそろえる")

    # 台帳
    text = original_text
    if ledger:
        for item in ledger_findings(text, ledger):
            f.items.append(item)

    # 仮置き文字
    if final:
        lines = text.split("\n")
        for i, ln in enumerate(lines):
            for m in PLACEHOLDER_RE.finditer(ln):
                f.add("FINAL", "error", i + 1, excerpt_around(ln, m.start()), "納品稿に仮置き文字・要確認の印が残っている（%s）" % m.group(0), col=m.start())
        for m in HTML_COMMENT_RE.finditer(text):
            ln_no = text.count("\n", 0, m.start()) + 1
            f.add("FINAL", "error", ln_no, m.group(0)[:40], "納品稿に HTML コメント（根拠・版情報などの社内メモ）が残っている。清書では外し、delivery/open-questions.md などへ移す")

    order = {"error": 0, "warn": 1, "info": 2}
    f.items.sort(key=lambda d: (d["line"] or 0, order.get(d["level"], 3), d["code"]))
    return f.items


def _find_all(text: str, needle: str) -> List[int]:
    out = []
    if not needle:
        return out
    start = 0
    while True:
        i = text.find(needle, start)
        if i < 0:
            return out
        out.append(i)
        start = i + max(1, len(needle))


def ledger_findings(text: str, ledger: Dict[str, Any]) -> List[Dict[str, Any]]:
    """案件台帳（rejected・confidential・locked・rules）との照合。"""
    starts = offsets_to_lines(text)
    flat = text.replace("\n", "")
    res: List[Dict[str, Any]] = []

    def item(level: str, line: Optional[int], excerpt: str, hint: str, ref: str) -> Dict[str, Any]:
        return {"code": "LEDGER", "name": NAMES["LEDGER"], "refs": [ref], "level": level, "line": line or 0, "excerpt": excerpt, "hint": hint}

    for r in ledger.get("rejected", []) or []:
        t = (r.get("text") or "").strip()
        for pos in _find_all(text, t):
            res.append(item("error", line_at(starts, pos), t[:50], "却下された表現（%s）。理由：%s" % (r.get("id", ""), r.get("reason", "")), r.get("id", "")))
    for c in ledger.get("confidential", []) or []:
        t = (c.get("term") or "").strip()
        for pos in _find_all(text, t):
            res.append(item("error", line_at(starts, pos), t[:50], "公開禁止の情報（%s）。理由：%s" % (c.get("id", ""), c.get("reason", "")), c.get("id", "")))
    for lk in ledger.get("locked", []) or []:
        t = (lk.get("text") or "")
        if not t.strip():
            continue
        if t not in text and t.replace("\n", "") not in flat:
            res.append(item("error", 0, t[:50], "変更禁止の文（%s）が見つからない（変えられた・消えた）" % lk.get("id", ""), lk.get("id", "")))
    for rl in ledger.get("rules", []) or []:
        avoid = (rl.get("avoid") or "").strip()
        use = (rl.get("use") or "").strip()
        if not avoid:
            continue
        masked = text
        if use and avoid in use:
            masked = text.replace(use, "\u0000" * len(use))
        for pos in _find_all(masked, avoid):
            res.append(item("warn", line_at(starts, pos), avoid, "表記ルール（%s）：「%s」→「%s」%s" % (rl.get("id", ""), avoid, use, ("。" + rl["note"]) if rl.get("note") else ""), rl.get("id", "")))
    return res


def format_findings(items: List[Dict[str, Any]], title: str = "") -> str:
    out = []
    if title:
        out.append(title)
    out.append(NOTE)
    levels = {"error": 0, "warn": 0, "info": 0}
    for it in items:
        levels[it["level"]] = levels.get(it["level"], 0) + 1
    out.append("件数：error %d／warn %d／info %d" % (levels["error"], levels["warn"], levels["info"]))
    by_code: Dict[str, int] = {}
    for it in items:
        by_code[it["code"]] = by_code.get(it["code"], 0) + 1
    if by_code:
        out.append("内訳：" + "、".join("%s %s×%d" % (c, NAMES.get(c, ""), n) for c, n in sorted(by_code.items())))
    out.append("")
    for it in items:
        refs = ("（" + "・".join(it["refs"]) + "）") if it["refs"] else ""
        ln = ("L%d" % it["line"]) if it["line"] else "L-"
        out.append("%s [%s] %s %s%s「%s」→ %s" % (ln, it["level"], it["code"], it["name"], refs, it["excerpt"], it["hint"]))
    return "\n".join(out)


def load_ledger(root: Path, slug: str) -> Dict[str, Any]:
    """案件の台帳に、会社の台帳（projects/<会社>/client-ledger.json）を合わせたもの。"""
    return paths.effective_ledger(root, slug)


def project_names(project: Optional[Dict[str, Any]]) -> List[str]:
    if not project:
        return []
    names = []
    client = project.get("client") or {}
    if client.get("name"):
        names.append(client["name"])
    names += [a for a in client.get("aliases", []) or [] if a]
    names += [p.get("name") for p in project.get("people", []) or [] if p.get("name")]
    return names


def cmd_audit(args) -> int:
    root = paths.repo_root()
    path = Path(args.file)
    if not path.exists():
        print("ファイルがない：%s" % path)
        return 1
    text = paths.read_text(path)
    ledger = None
    names: List[str] = []
    if args.project:
        ledger = load_ledger(root, args.project)
        names = project_names(paths.load_project(root, args.project))
    items = audit_text(text, ledger=ledger, final=args.final, extra_names=names)
    if args.json:
        print(json.dumps({"note": NOTE, "file": str(path), "findings": items}, ensure_ascii=False, indent=2))
    else:
        print(format_findings(items, "audit：%s" % path))
    return 2 if any(it["level"] == "error" for it in items) else 0
