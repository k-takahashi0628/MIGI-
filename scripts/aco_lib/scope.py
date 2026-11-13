"""指定範囲の外に差分がないかを行単位（改行を含む）で検査し、必要なら範囲外を元に戻す。

--allow の種類
  heading:<語>   その語を含む見出しの 1 行だけ
  section:<語>   その語を含む見出しから、次の同じか上の階層の見出しの前まで（末尾への追加可）
  lines:<a>-<b>  変更前の a〜b 行目（1 始まり・両端を含む。追加は範囲の内側だけ）
  contains:<語>  その語を含む段落（空行で区切られたまとまり。末尾への追加可）
  chapter-heading:<N>  N 番目の章（`## ` 見出し）の見出しの 1 行だけ。「第3章の見出しだけ」に使う
  chapter:<N>          N 番目の章の全体（見出しから次の `## ` の前まで。末尾への追加可）
"""
from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import paths

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


@dataclass
class Range:
    start: int  # 0 始まり・含む
    end: int  # 0 始まり・含む
    kind: str
    spec: str
    allow_append: bool

    def contains(self, i: int) -> bool:
        return self.start <= i <= self.end


class ScopeError(Exception):
    pass


def _strip_nl(s: str) -> str:
    return s.rstrip("\n")


def parse_allow(spec: str, lines: List[str]) -> List[Range]:
    if ":" not in spec:
        raise ScopeError("--allow の形が違う：%s（heading: / section: / chapter-heading: / chapter: / lines: / contains: のどれか）" % spec)
    kind, arg = spec.split(":", 1)
    kind = kind.strip()
    out: List[Range] = []
    if kind == "heading" or kind == "section":
        for i, ln in enumerate(lines):
            m = HEADING_RE.match(_strip_nl(ln))
            if m and arg in m.group(2):
                if kind == "heading":
                    out.append(Range(i, i, kind, spec, False))
                else:
                    level = len(m.group(1))
                    end = len(lines) - 1
                    for j in range(i + 1, len(lines)):
                        m2 = HEADING_RE.match(_strip_nl(lines[j]))
                        if m2 and len(m2.group(1)) <= level:
                            end = j - 1
                            break
                    out.append(Range(i, end, kind, spec, True))
        if not out:
            raise ScopeError("見出しが見つからない：%s" % spec)
    elif kind in ("chapter-heading", "chapter"):
        if not arg.strip().isdigit() or int(arg) < 1:
            raise ScopeError("%s: には章の番号（1 始まり）を書く：%s（例 chapter-heading:3）" % (kind, spec))
        n = int(arg)
        idx = [i for i, ln in enumerate(lines)
               if (lambda m: m is not None and len(m.group(1)) == 2)(HEADING_RE.match(_strip_nl(ln)))]
        if n > len(idx):
            raise ScopeError("章が %d 個しかない：%s" % (len(idx), spec))
        i = idx[n - 1]
        if kind == "chapter-heading":
            out.append(Range(i, i, kind, spec, False))
        else:
            end = len(lines) - 1
            for j in range(i + 1, len(lines)):
                m2 = HEADING_RE.match(_strip_nl(lines[j]))
                if m2 and len(m2.group(1)) <= 2:
                    end = j - 1
                    break
            out.append(Range(i, end, kind, spec, True))
    elif kind == "lines":
        m = re.fullmatch(r"\s*(\d+)\s*(?:-\s*(\d+))?\s*", arg)
        if not m:
            raise ScopeError("lines: の形が違う：%s（例 lines:10-20）" % spec)
        a = int(m.group(1))
        b = int(m.group(2) or a)
        if a < 1 or b < a or a > len(lines):
            raise ScopeError("行番号が範囲外：%s（変更前は %d 行）" % (spec, len(lines)))
        out.append(Range(a - 1, min(b, len(lines)) - 1, kind, spec, False))
    elif kind == "contains":
        for i, ln in enumerate(lines):
            if arg and arg in ln:
                s = i
                while s - 1 >= 0 and _strip_nl(lines[s - 1]).strip() and not HEADING_RE.match(_strip_nl(lines[s - 1])):
                    s -= 1
                e = i
                while e + 1 < len(lines) and _strip_nl(lines[e + 1]).strip() and not HEADING_RE.match(_strip_nl(lines[e + 1])):
                    e += 1
                if HEADING_RE.match(_strip_nl(ln)):
                    s = e = i
                out.append(Range(s, e, kind, spec, True))
        if not out:
            raise ScopeError("その語を含む段落が見つからない：%s" % spec)
    else:
        raise ScopeError("--allow の種類が違う：%s" % kind)
    return out


def _in_scope(i: int, ranges: List[Range]) -> bool:
    return any(r.contains(i) for r in ranges)


def _insert_ok(i1: int, ranges: List[Range]) -> bool:
    """変更前の位置 i1 の手前への追加が許されるか。"""
    for r in ranges:
        if r.contains(i1 - 1) and (r.contains(i1) or (i1 == r.end + 1 and r.allow_append)):
            return True
    return False


def _pieces(a: List[str], b: List[str]):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                yield "replace", i1 + k, i1 + k + 1, j1 + k, j1 + k + 1
        else:
            yield tag, i1, i2, j1, j2


def check_scope(before: str, after: str, specs: List[str]) -> Dict[str, Any]:
    a = before.splitlines(keepends=True)
    b = after.splitlines(keepends=True)
    ranges: List[Range] = []
    for sp in specs:
        ranges += parse_allow(sp, a)
    in_scope: List[Dict[str, Any]] = []
    violations: List[Dict[str, Any]] = []
    merged: List[str] = []
    for tag, i1, i2, j1, j2 in _pieces(a, b):
        if tag == "equal":
            merged += a[i1:i2]
            continue
        if tag == "insert":
            ok = _insert_ok(i1, ranges)
        else:
            ok = all(_in_scope(i, ranges) for i in range(i1, i2))
        kind = {"replace": "置き換え", "delete": "削除", "insert": "追加"}[tag]
        rec = {
            "kind": kind,
            "before_lines": [i1 + 1, i2] if i2 > i1 else [i1, i1],
            "after_lines": [j1 + 1, j2] if j2 > j1 else [j1, j1],
            "before": "".join(a[i1:i2]),
            "after": "".join(b[j1:j2]),
        }
        if ok:
            in_scope.append(rec)
            merged += b[j1:j2]
        else:
            violations.append(rec)
            merged += a[i1:i2]
    return {
        "ranges": [{"spec": r.spec, "lines": [r.start + 1, r.end + 1]} for r in ranges],
        "in_scope": in_scope,
        "violations": violations,
        "restored_text": "".join(merged),
    }


def _show(s: str, n: int = 60) -> str:
    if s == "":
        return "（なし）"
    r = repr(s)
    return r if len(r) <= n else r[: n - 1] + "…"


def cmd_scope(args) -> int:
    bp, ap = Path(args.before), Path(args.after)
    for p in (bp, ap):
        if not p.exists():
            print("ファイルがない：%s" % p)
            return 1
    if not args.allow:
        print("--allow で直してよい範囲を 1 つ以上指定する（例 --allow \"heading:第3章\"）")
        return 1
    before = bp.read_bytes().decode("utf-8")
    after = ap.read_bytes().decode("utf-8")
    try:
        res = check_scope(before, after, args.allow)
    except ScopeError as e:
        print(str(e))
        return 1
    restored_ok: Optional[bool] = None
    if args.restore:
        Path(args.restore).write_bytes(res["restored_text"].encode("utf-8"))
        res2 = check_scope(before, res["restored_text"], args.allow)
        restored_ok = not res2["violations"]
    warn = None
    if not res["in_scope"]:
        warn = "指示の箇所が変わっていない（範囲内の変更 0 件）"
    if args.json:
        out = {k: v for k, v in res.items() if k != "restored_text"}
        out.update({"restored": args.restore, "restored_ok": restored_ok, "warning": warn})
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        lines = ["scope：%s → %s" % (bp, ap)]
        lines.append("直してよい範囲：" + "、".join("%s（%d〜%d 行）" % (r["spec"], r["lines"][0], r["lines"][1]) for r in res["ranges"]))
        lines.append("範囲内の変更：%d 件／範囲外の変更：%d 件" % (len(res["in_scope"]), len(res["violations"])))
        if warn:
            lines.append("[warn] " + warn)
        for v in res["violations"]:
            lines.append("- [範囲外] %s 変更前 %d〜%d 行：%s → %s" % (v["kind"], v["before_lines"][0], v["before_lines"][1], _show(v["before"]), _show(v["after"])))
        if args.restore:
            lines.append("範囲外を元に戻した本文：%s（再検査：%s）" % (args.restore, "範囲外 0 件" if restored_ok else "まだ範囲外がある"))
        if not res["violations"]:
            lines.append("範囲外の差分はない。")
        print("\n".join(lines))
    if res["violations"]:
        return 2
    return 0
