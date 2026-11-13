"""修正表のひな形：差分ごとに、章の見出し・直前の問い・今・直しを並べる。"""
from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any, Dict, List

from . import paths
from .textutil import HEADING_RE, is_question_line, md_cell, question_text


def _context(lines: List[str], idx: int) -> Dict[str, str]:
    chapter = "リード"
    question = ""
    for k in range(min(idx, len(lines) - 1), -1, -1):
        ln = lines[k].rstrip("\n")
        m = HEADING_RE.match(ln)
        if m:
            if len(m.group(1)) == 1:
                chapter = "タイトル" if k == idx else "リード"
            else:
                chapter = m.group(2).strip()
            break
        if not question and is_question_line(ln):
            question = question_text(ln)
    return {"chapter": chapter, "question": question}


def build(before: str, after: str) -> List[Dict[str, Any]]:
    a = before.splitlines(keepends=True)
    b = after.splitlines(keepends=True)
    rows: List[Dict[str, Any]] = []
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        ctx = _context(a, i1 if i1 < len(a) else len(a) - 1) if a else {"chapter": "リード", "question": ""}
        old = "".join(a[i1:i2]).strip("\n")
        new = "".join(b[j1:j2]).strip("\n")
        kind = {"replace": "変更", "delete": "削除", "insert": "追加"}[tag]
        if not old.strip() and not new.strip():
            kind = "空行・改行"
        rows.append({"no": len(rows) + 1, "chapter": ctx["chapter"], "question": ctx["question"], "before": old, "after": new, "kind": kind, "line": i1 + 1})
    return rows


def to_markdown(rows: List[Dict[str, Any]]) -> str:
    out = ["| No. | 場所（章「…」／問い「…」） | 今 | 直し | どうしたか | 当たった負け筋 | 理由 |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        place = "章「%s」" % r["chapter"] + ("／問い「%s」" % r["question"] if r["question"] else "")
        mark = {"変更": "🟥 変更", "追加": "🟦 追加"}.get(r["kind"], r["kind"])
        out.append("| %d | %s | %s | %s | %s |  |  |" % (
            r["no"], md_cell(place),
            md_cell(r["before"] or "（なし）"), md_cell(r["after"] or "（削除）"), mark))
    return "\n".join(out) + "\n"


def cmd_revtable(args) -> int:
    bp, ap = Path(args.before), Path(args.after)
    for p in (bp, ap):
        if not p.exists():
            print("ファイルがない：%s" % p)
            return 1
    rows = build(paths.read_text(bp), paths.read_text(ap))
    md = to_markdown(rows)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md, encoding="utf-8")
        print("修正表のひな形を書いた：%s（%d 件）" % (args.out, len(rows)))
    else:
        print(md, end="")
    return 0
