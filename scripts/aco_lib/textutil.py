"""原稿・書き起こしの読み取り（見出し・段落・問い・話し手・文・数値・内容語）。

書式は docs/architecture.md §9 に従う。
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

# ---------------------------------------------------------------------------
# 原稿の構造

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
QUESTION_RE = re.compile(r"^\s*(──|――|——|[QＱ][\.．:：])")
SPEAKER_RE = re.compile(
    r"^(?:\*\*)?([^\s：:「」『』（）()、。，．,.*#\[\]【】]{1,12})(?:\*\*)?\s*[：:]\s*(.*)$", re.S
)
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+・]|\d+[.)．）])\s+")
# 答えのまとまりを閉じて、地の文に戻す区切りの行（--- / ＊＊＊ / ◆ など）
SEPARATOR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|＊{1,3}|◆|◇|※{3})\s*$")
NOT_SPEAKER = {"http", "https", "mailto", "ftp", "例", "注", "※", "参考", "出典", "備考", "結論", "ポイント", "要点", "NG", "OK"}
INTERVIEWER_LABELS = {"聞き手", "インタビュアー", "Q", "Ｑ", "質問者", "司会", "ライター", "編集", "編集部", "取材者"}


@dataclass
class Block:
    kind: str  # title / heading / question / para
    raw: str  # 原稿のままの文字列（複数行は \n でつなぐ）
    text: str  # 話し手のラベルを除いた本文（問いは記号を除いた文）
    line: int  # 1 始まりの開始行
    end_line: int
    level: int = 0
    speaker: Optional[str] = None
    explicit_speaker: bool = False
    is_answer: bool = False
    chapter: int = 0  # 0 = リード（最初の ## より前）
    chapter_title: str = ""
    label_len: int = 0  # raw の先頭から取り除いたラベルの文字数

    def line_of(self, raw_offset: int) -> int:
        return self.line + self.raw[: max(0, raw_offset)].count("\n")


def blank_html_comments(text: str) -> str:
    """HTML コメントを空白に置き換える（行番号は保つ）。"""
    return re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)


def is_question_line(line: str) -> bool:
    return bool(QUESTION_RE.match(line))


def question_text(line: str) -> str:
    s = line.strip()
    s = re.sub(r"^(──|――|——)\s*", "", s)
    s = re.sub(r"^[QＱ][\.．:：]\s*", "", s)
    return s.strip()


def split_speaker(text: str) -> Tuple[Optional[str], str, int]:
    """段落の頭の `名前：` を取り出す。(名前, 本文, 取り除いた文字数)"""
    m = SPEAKER_RE.match(text)
    if not m:
        return None, text, 0
    name = m.group(1).strip()
    rest = m.group(2)
    if name.lower() in NOT_SPEAKER or name in NOT_SPEAKER or rest.startswith("//"):
        return None, text, 0
    if re.fullmatch(r"[0-9０-９]+", name):
        return None, text, 0
    return name, rest, len(text) - len(rest)


def parse_document(text: str, default_speaker: Optional[str] = None) -> List[Block]:
    text = blank_html_comments(text)
    lines = text.split("\n")
    blocks: List[Block] = []
    chapter = 0
    chapter_title = ""
    in_answer = False
    last_speaker: Optional[str] = None
    buf: List[str] = []
    buf_start = 0
    seen_title = False
    in_fence = False

    def flush() -> None:
        nonlocal buf, last_speaker
        if not buf:
            return
        raw = "\n".join(buf)
        name, rest, label_len = split_speaker(raw)
        is_answer = in_answer or name is not None
        speaker = None
        if is_answer:
            if name:
                speaker = name
                last_speaker = name
            else:
                speaker = last_speaker or default_speaker or "不明"
        blocks.append(
            Block(
                kind="para",
                raw=raw,
                text=rest if name else raw,
                line=buf_start + 1,
                end_line=buf_start + len(buf),
                speaker=speaker,
                explicit_speaker=name is not None,
                is_answer=is_answer,
                chapter=chapter,
                chapter_title=chapter_title,
                label_len=label_len if name else 0,
            )
        )
        buf = []

    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip():
            flush()
            continue
        hm = HEADING_RE.match(line)
        if hm:
            flush()
            level = len(hm.group(1))
            title = hm.group(2).strip()
            if level == 1 and not seen_title:
                seen_title = True
                blocks.append(Block("title", line, title, i + 1, i + 1, level=1, chapter=0))
                continue
            if level <= 2:
                chapter += 1
                chapter_title = title
                last_speaker = None
            in_answer = False
            blocks.append(Block("heading", line, title, i + 1, i + 1, level=level, chapter=chapter, chapter_title=chapter_title))
            continue
        if SEPARATOR_RE.match(line):
            flush()
            in_answer = False
            last_speaker = None
            continue
        if is_question_line(line):
            flush()
            blocks.append(Block("question", line, question_text(line), i + 1, i + 1, chapter=chapter, chapter_title=chapter_title))
            in_answer = True
            continue
        if LIST_ITEM_RE.match(line) or line.lstrip().startswith("|"):
            flush()  # 箇条書きの項目・表の行は、それぞれを一つのまとまりとして扱う
        if not buf:
            buf_start = i
        buf.append(line)
    flush()
    return blocks


# ---------------------------------------------------------------------------
# 文の分割

OPENERS = "「『（(【〈《“"
CLOSERS = "」』）)】〉》”"
ENDERS = "。！？!?"


def split_sentences(text: str) -> List[Tuple[str, int]]:
    """文に分ける。「」などの中の句点では切らない。改行も区切りとして扱う。(文, 開始位置)"""
    res: List[Tuple[str, int]] = []
    depth = 0
    start = 0
    i = 0
    n = len(text)

    def push(a: int, b: int) -> None:
        seg = text[a:b]
        stripped = seg.strip()
        if stripped:
            res.append((stripped, a + (len(seg) - len(seg.lstrip()))))

    while i < n:
        ch = text[i]
        if ch in OPENERS:
            depth += 1
        elif ch in CLOSERS:
            depth = max(0, depth - 1)
        elif ch == "\n":
            push(start, i)
            start = i + 1
            depth = 0
        elif ch in ENDERS and depth == 0:
            j = i + 1
            while j < n and text[j] in ENDERS + "」』）)":
                j += 1
            push(start, j)
            start = j
            i = j
            continue
        i += 1
    push(start, n)
    return res


def quoted_segments(text: str, min_len: int = 10) -> List[Tuple[str, int]]:
    """「…」の中身（入れ子を考える）。(中身, 開始位置)"""
    res: List[Tuple[str, int]] = []
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "「":
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == "」" and depth > 0:
            depth -= 1
            if depth == 0 and start >= 0:
                seg = text[start:i]
                if len(seg.strip()) >= min_len:
                    res.append((seg, start))
                start = -1
    return res


# ---------------------------------------------------------------------------
# 正規化と比較

FILLER_RE = re.compile(
    r"(えー+|ええと|ええっと|えっと|あのー+|あの(?=[、,，\s…])|まあ(?=[、,，\s…])|なんか(?=[、,，\s…])|こう(?=[、,，\s…]))"
)
PUNCT_RE = re.compile(r"[\s、。，．,.・！？!?「」『』（）()\[\]【】〈〉《》“”\"'…‥─―—\-~〜～:：;；/／*＊#＃]")
HIRA_NUM = {"ひとり": "一人", "ふたり": "二人", "ひとつ": "一つ", "ふたつ": "二つ", "みっつ": "三つ", "よっつ": "四つ"}


def nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def normalize(s: str) -> str:
    s = nfkc(s)
    s = FILLER_RE.sub("", s)
    for k, v in HIRA_NUM.items():
        s = s.replace(k, v)
    s = PUNCT_RE.sub("", s)
    return s


def char_len(s: str) -> int:
    """空白を除いた文字数。"""
    return len(re.sub(r"\s", "", s))


def bigrams(s: str) -> Set[str]:
    if len(s) < 2:
        return {s} if s else set()
    return {s[i : i + 2] for i in range(len(s) - 1)}


def containment(sentence_norm: str, candidate_norm: str) -> float:
    a = bigrams(sentence_norm)
    if not a:
        return 0.0
    b = bigrams(candidate_norm)
    return len(a & b) / len(a)


KANJI_RUN = re.compile(r"[㐀-䶿一-鿿々〆ヵヶ]{2,}")
KATA_RUN = re.compile(r"[ァ-ヺー]{3,}")
ALNUM_RUN = re.compile(r"[A-Za-z][A-Za-z0-9]+")


def katakana_words(s: str) -> List[str]:
    return [w for w in KATA_RUN.findall(nfkc(s)) if w.strip("ー") and len(w.strip("ー")) >= 3]


def content_tokens(s: str) -> List[str]:
    s = nfkc(s)
    toks = KANJI_RUN.findall(s) + katakana_words(s) + ALNUM_RUN.findall(s)
    return toks


# ---------------------------------------------------------------------------
# 数値

KANJI_DIGITS = {"〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "壱": 1, "弐": 2}
KANJI_SMALL = {"十": 10, "百": 100, "千": 1000}
KANJI_BIG = {"万": 10 ** 4, "億": 10 ** 8, "兆": 10 ** 12}
COUNTERS = [
    "パーセント", "か月", "ヶ月", "カ月", "ケ月", "箇月", "週間", "時間", "年間", "年目", "年度", "種類", "店舗", "拠点", "部署",
    "職種", "チーム", "カ国", "か国", "ヶ国", "か所", "カ所", "箇所", "ヶ所", "ページ", "工場", "万円", "億円",
    "年", "月", "日", "人", "名", "社", "件", "割", "倍", "回", "度", "分", "秒", "%", "円", "店", "台", "個", "本", "期",
    "代", "歳", "才", "位", "校", "つ", "点", "坪", "階", "号", "巻", "km", "kg", "トン",
]
COUNTER_RE = "|".join(re.escape(c) for c in sorted(COUNTERS, key=len, reverse=True))
ARABIC_NUM_RE = re.compile(r"(?<![0-9.])(\d+(?:[.,]\d+)*)(万|億|兆)?(" + COUNTER_RE + r")?")
KANJI_NUM_RE = re.compile(r"([〇零一二三四五六七八九十百千壱弐][〇零一二三四五六七八九十百千万億兆壱弐]*)(" + COUNTER_RE + r")")


def kanji_to_int(s: str) -> Optional[int]:
    total = 0
    section = 0
    digit = None
    for ch in s:
        if ch in KANJI_DIGITS:
            if digit is not None:  # 「二〇二六」のような並び
                digit = digit * 10 + KANJI_DIGITS[ch]
            else:
                digit = KANJI_DIGITS[ch]
        elif ch in KANJI_SMALL:
            section += (digit if digit is not None else 1) * KANJI_SMALL[ch]
            digit = None
        elif ch in KANJI_BIG:
            section += digit if digit is not None else 0
            total += (section if section else 1) * KANJI_BIG[ch]
            section = 0
            digit = None
        else:
            return None
    section += digit if digit is not None else 0
    return total + section


def _fmt(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return ("%f" % v).rstrip("0").rstrip(".")


def extract_numbers(s: str) -> List[Tuple[str, str]]:
    """数量表現を (値, 単位) で取り出す。算用数字は単位なしでも拾う。漢数字は単位つきだけ。"""
    s = nfkc(s)
    for k, v in HIRA_NUM.items():
        s = s.replace(k, v)
    out: List[Tuple[str, str]] = []
    for m in ARABIC_NUM_RE.finditer(s):
        num = m.group(1).replace(",", "")
        try:
            v = float(num)
        except ValueError:
            continue
        if m.group(2):
            v *= KANJI_BIG[m.group(2)]
        out.append((_fmt(v), m.group(3) or ""))
    for m in KANJI_NUM_RE.finditer(s):
        word = m.group(1)
        if word + m.group(2) in ("十分",) and not re.search(r"十分(間|後|前|ほど|くらい|程度)", s[m.start():m.end() + 2]):
            continue
        v = kanji_to_int(word)
        if v is None:
            continue
        out.append((str(v), m.group(2)))
    return out


# 同じ数え方とみなす単位（記事で「人」、素材で「名」など）
UNIT_SAME = {"名": "人", "人": "人", "ヶ月": "か月", "カ月": "か月", "ケ月": "か月", "箇所": "か所", "ヵ所": "か所", "ヶ所": "か所", "年間": "年"}


def numbers_supported(article_nums: Sequence[Tuple[str, str]], source_nums: Sequence[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """記事の数値のうち、出典側に見当たらないものを返す。"""
    missing = []
    for v, c in article_nums:
        ok = False
        c = UNIT_SAME.get(c, c)
        for sv, sc in source_nums:
            sc = UNIT_SAME.get(sc, sc)
            if sv == v and (c == "" or sc == "" or sc == c or sc.startswith(c) or c.startswith(sc)):
                ok = True
                break
        if not ok:
            missing.append((v, c))
    return missing


# ---------------------------------------------------------------------------
# 書き起こし

TRANSCRIPT_LINE_RE = re.compile(r"^\s*(?:[-*・]\s*)?(?:\[?\(?\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\)?\]?\s*)?([^\s：:\[\]（）()「」]{1,15})\s*[：:]\s*(.*)$")
# 書き起こしの冒頭に書かれるメタ情報（発言としては読まない）
TRANSCRIPT_META_KEYS = {"会社", "社名", "話し手", "話者", "聞き手", "取材日", "日時", "日付", "場所", "媒体", "出席者", "参加者", "時間", "形式", "備考"}
# 「- 名前「発言」」の形（取材メモの抜粋など）
TRANSCRIPT_QUOTE_RE = re.compile(r"^\s*(?:[-*・]\s*)?([^\s：:\[\]（）()「」]{1,15})\s*「(.+)」\s*$")
TIMESTAMP_ONLY_RE = re.compile(r"^\s*\[?\(?\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\)?\]?\s*$")


@dataclass
class Utterance:
    speaker: str
    text: str
    line: int
    is_interviewer: bool


def parse_transcript(text: str, extra_interviewers: Iterable[str] = ()) -> List[Utterance]:
    interviewers = set(INTERVIEWER_LABELS) | set(extra_interviewers)
    utts: List[Utterance] = []
    for i, line in enumerate(text.replace("\r\n", "\n").split("\n")):
        if not line.strip() or TIMESTAMP_ONLY_RE.match(line):
            continue
        if line.lstrip().startswith("#") or line.lstrip().startswith("<!--"):
            continue
        m = TRANSCRIPT_LINE_RE.match(line)
        if m and m.group(1).strip() in TRANSCRIPT_META_KEYS:
            continue
        if not m:
            mq = TRANSCRIPT_QUOTE_RE.match(line)
            if mq:
                spk = mq.group(1).strip()
                utts.append(Utterance(spk, mq.group(2).strip(), i + 1, spk in interviewers))
                continue
        if m and not m.group(2).startswith("//"):
            spk = m.group(1).strip()
            utts.append(Utterance(spk, m.group(2).strip(), i + 1, spk in interviewers))
        elif utts:
            utts[-1].text += line.strip()
        else:
            utts.append(Utterance("不明", line.strip(), i + 1, False))
    return utts


def same_person(a: Optional[str], b: Optional[str]) -> bool:
    if not a or not b:
        return False
    a2 = re.sub(r"(さん|氏|様|（.*?）|\(.*?\))$", "", a)
    b2 = re.sub(r"(さん|氏|様|（.*?）|\(.*?\))$", "", b)
    return a2 == b2 or (len(a2) >= 2 and a2 in b2) or (len(b2) >= 2 and b2 in a2)


def offsets_to_lines(text: str) -> List[int]:
    """各文字位置の行番号（1 始まり）を返すための累積表。"""
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def line_at(starts: List[int], offset: int) -> int:
    import bisect

    return bisect.bisect_right(starts, offset)


def short(s: str, n: int = 40) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def excerpt_around(s: str, pos: int, width: int = 30) -> str:
    a = max(0, pos - width)
    b = min(len(s), pos + width)
    out = s[a:b].replace("\n", " ")
    return ("…" if a > 0 else "") + out + ("…" if b < len(s) else "")


def md_cell(s: str) -> str:
    return s.replace("|", "｜").replace("\n", "<br>")


def names_from_doc(blocks: Sequence[Block]) -> Set[str]:
    return {b.speaker for b in blocks if b.explicit_speaker and b.speaker}


def body_blocks(blocks: Sequence[Block]) -> List[Block]:
    return [b for b in blocks if b.kind in ("para", "question")]


def count_dict(items: Iterable[str]) -> Dict[str, int]:
    d: Dict[str, int] = {}
    for it in items:
        d[it] = d.get(it, 0) + 1
    return d
