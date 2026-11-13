"""シナリオテストの verify.py が共通で使う道具。

- scripts/aco を subprocess で呼ぶ（ACO_ROOT を渡せば案件データの置き場を差し替えられる）
- aco の JSON 出力を、項目名の細かな違いに左右されずに読む
- 数値・固有名を取り出して「入力にないものが出力に増えていないか」を確かめる
- 結果を日本語で表示し、終了コードを決める（合格 0／不合格 2／検査できず 1）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ACO = REPO / "scripts" / "aco"

ID_RE = re.compile(r"(?<![A-Za-z0-9-])(AI-\d{2}|[A-H]\d{1,2})(?!\d)")


# ---------------------------------------------------------------- 引数・結果

def parse_args(scenario_dir: Path, extra=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="シナリオテストの検査")
    p.add_argument("--target", default=str(scenario_dir / "output"),
                   help="検査する出力フォルダ（既定は output/。controls/good などを渡せる）")
    if extra:
        extra(p)
    a = p.parse_args()
    a.target = Path(a.target).resolve()
    return a


class Report:
    def __init__(self, title: str, target: Path):
        self.title = title
        self.target = target
        self.rows = []  # (state, name, detail)

    def ok(self, name, detail=""):
        self.rows.append(("合格", name, detail))

    def ng(self, name, detail=""):
        self.rows.append(("不合格", name, detail))

    def err(self, name, detail=""):
        self.rows.append(("検査できず", name, detail))

    def check(self, cond: bool, name: str, ok_detail="", ng_detail=""):
        if cond:
            self.ok(name, ok_detail)
        else:
            self.ng(name, ng_detail)
        return cond

    def finish(self) -> int:
        print(f"■ {self.title}")
        print(f"  対象：{self.target}")
        for state, name, detail in self.rows:
            mark = {"合格": "○", "不合格": "×", "検査できず": "－"}[state]
            print(f"  {mark} {name}")
            if detail:
                for line in str(detail).splitlines():
                    print(f"      {line}")
        states = [r[0] for r in self.rows]
        if "不合格" in states:
            code, verdict = 2, "不合格"
        elif "検査できず" in states:
            code, verdict = 1, "検査できず（必要なファイルか scripts/aco が足りない）"
        else:
            code, verdict = 0, "合格"
        print(f"  判定：{verdict}")
        return code


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def require(rep: Report, path: Path) -> str | None:
    text = read(path)
    if text is None:
        rep.ng(f"{path.name} がある", f"見つからない：{path}")
    return text


# ---------------------------------------------------------------- aco の呼び出し

def aco_available() -> bool:
    return ACO.exists()


def run_aco(args, root: Path | None = None, cwd: Path | None = None, timeout=120):
    """(終了コード, 標準出力, 標準エラー) を返す。aco がなければ None。"""
    if not aco_available():
        return None
    env = dict(os.environ)
    if root is not None:
        env["ACO_ROOT"] = str(root)
    cmd = [sys.executable, str(ACO)] + [str(a) for a in args]
    p = subprocess.run(cmd, cwd=str(cwd or (root or REPO)), env=env,
                       capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def parse_json(text: str):
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        pass
    for opener in ("{", "["):
        i = text.find(opener)
        if i >= 0:
            try:
                return json.loads(text[i:])
            except ValueError:
                continue
    return None


def iter_dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from iter_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_dicts(v)


def finding_level(d: dict) -> str | None:
    lv = d.get("level", d.get("severity"))
    if not isinstance(lv, str):
        return None
    lv = lv.lower()
    return {"warning": "warn", "err": "error"}.get(lv, lv)


def finding_ids(d: dict) -> set:
    ids = set()
    for key in ("code", "id", "ids", "ref", "refs", "rule", "pattern", "tags", "codes"):
        v = d.get(key)
        vals = v if isinstance(v, list) else [v]
        for x in vals:
            if isinstance(x, str):
                ids.update(ID_RE.findall(x))
    return ids


def audit(path: Path, root: Path | None = None, extra_args=()):
    """aco audit の結果を [(level, {ID...}), ...] で返す。失敗したら (None, 理由)。"""
    r = run_aco(["audit", str(path), "--json", *extra_args], root=root)
    if r is None:
        return None, "scripts/aco がない"
    code, out, err = r
    data = parse_json(out)
    findings = []
    if data is not None:
        for d in iter_dicts(data):
            lv = finding_level(d)
            if lv in ("info", "warn", "error"):
                findings.append((lv, finding_ids(d)))
        return findings, None
    if code == 1:
        return None, f"aco audit が実行エラー：{(err or out).strip()[:300]}"
    # JSON が読めないときは、行ごとの文字で数える
    for line in out.splitlines():
        low = line.lower()
        lv = "error" if "error" in low else "warn" if "warn" in low else "info" if "info" in low else None
        if lv:
            findings.append((lv, set(ID_RE.findall(line))))
    return findings, None


def count_level(findings, level: str) -> int:
    return sum(1 for lv, _ in findings if lv == level)


def count_id(findings, fid: str, levels=("info", "warn", "error")) -> int:
    return sum(1 for lv, ids in findings if fid in ids and lv in levels)


# ---------------------------------------------------------------- 文字の扱い

def nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def strip_comments(s: str) -> str:
    return re.sub(r"<!--.*?-->", "", s, flags=re.S)


def compact(s: str) -> str:
    """空白・句読点・記号を除いて比べやすくする。"""
    s = nfkc(strip_comments(s))
    return re.sub(r"[\s、。，．,.・「」『』（）()【】\[\]！!？?：:；;…─―ー\-〜~]", "", s)


_KANJI_DIGIT = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_KANJI_UNIT = {"十": 10, "百": 100, "千": 1000}
_COUNTER = r"(?:年|人|名|食|回|日|か月|ヶ月|カ月|週|時間|時|分|秒|歳|割|倍|件|社|台|度|色|班|個|枚|本|%|％|パーセント)"


def kanji_to_int(s: str) -> int | None:
    total, cur = 0, 0
    for ch in s:
        if ch in _KANJI_DIGIT:
            cur = _KANJI_DIGIT[ch]
        elif ch in _KANJI_UNIT:
            total += (cur or 1) * _KANJI_UNIT[ch]
            cur = 0
        else:
            return None
    return total + cur


def numbers(text: str) -> set:
    """文章の中の数値を集める。章番号・箇条書きの番号・時刻表示は除く。

    漢数字は「数＋助数詞」の形だけ数える（「一つ」「一番」など一文字の「一」は数えない）。
    """
    t = nfkc(strip_comments(text))
    t = re.sub(r"\[\d{1,2}:\d{2}(?::\d{2})?\]", " ", t)                    # 書き起こしの時刻
    t = re.sub(r"(?m)^(\s*#+\s*)\d+[.．、]\s*", r"\1", t)                   # 見出しの番号
    t = re.sub(r"(?m)^\s*\d+[.)．]\s+", " ", t)                             # 箇条書きの番号
    found = set()
    for m in re.findall(r"\d+(?:[.,]\d+)*", t):
        found.add(m.replace(",", ""))
    for m in re.finditer(r"([〇一二三四五六七八九十百千]+)(?=" + _COUNTER + ")", t):
        s = m.group(1)
        if s == "一":
            continue
        v = kanji_to_int(s)
        if v is not None:
            found.add(str(v))
    return found


def extra_numbers(output: str, *sources: str) -> list:
    base = set()
    for s in sources:
        base |= numbers(s)
    return sorted(numbers(output) - base, key=lambda x: (len(x), x))


def quotes_in(text: str) -> list:
    return re.findall(r"「([^「」]{1,200})」", strip_comments(text))


def bigrams(s: str) -> set:
    return {s[i:i + 2] for i in range(len(s) - 1)}


def supported(fragment: str, source: str, threshold=0.8) -> bool:
    """fragment が source にほぼそのままあるか（部分一致か、2文字組の重なり）。"""
    f, src = compact(fragment), compact(source)
    if not f:
        return True
    if f in src:
        return True
    bf = bigrams(f)
    if not bf:
        return False
    # source を文ごとに見て、いちばん重なる文と比べる
    best = 0.0
    for sent in re.split(r"[。\n]", nfkc(strip_comments(source))):
        bs = bigrams(compact(sent))
        if bs:
            best = max(best, len(bf & bs) / len(bf))
    return best >= threshold


def sentences(text: str) -> list:
    t = strip_comments(text)
    parts = re.split(r"(?<=[。！？!?])|\n", t)
    return [p.strip() for p in parts if p.strip()]


def headings(text: str, level: int = 2) -> list:
    pat = re.compile(r"^" + "#" * level + r"\s+(.+?)\s*$")
    return [m.group(1) for line in strip_comments(text).splitlines() if (m := pat.match(line))]


def chapters(text: str) -> list:
    """[(見出し, 本文)] を返す。見出しより前（リード）は含めない。"""
    out, cur, buf = [], None, []
    for line in strip_comments(text).splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if cur is not None:
                out.append((cur, "\n".join(buf)))
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out.append((cur, "\n".join(buf)))
    return out


QUESTION_RE = re.compile(r"^\s*(──\s|――|Q[.．:：])")
LABEL_RE = re.compile(r"^\s*([^\s：:「」#─―*>\-]{1,12})[：:]")


def speaker_labels(article: str) -> list:
    labels = []
    for para in re.split(r"\n\s*\n", strip_comments(article)):
        line = para.strip()
        if not line or line.startswith("#") or QUESTION_RE.match(line):
            continue
        m = LABEL_RE.match(line)
        if m:
            labels.append(m.group(1))
    return labels


def transcript_speakers(transcript: str) -> set:
    names = set()
    for line in transcript.splitlines():
        line = re.sub(r"^\s*\[\d{1,2}:\d{2}(?::\d{2})?\]\s*", "", line)
        m = re.match(r"^([^\s：:#\-*]{1,12})[：:]", line)
        if m:
            names.add(m.group(1))
    return names - {"聞き手", "インタビュアー", "Q", "会社", "話し手", "取材日"}
