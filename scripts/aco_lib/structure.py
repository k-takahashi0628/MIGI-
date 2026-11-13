"""章ごとの字数・問いの数・重複した問い・リードと締めの対応。"""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List

from . import paths
from .textutil import Block, char_len, content_tokens, md_cell, normalize, parse_document


def analyze(text: str) -> Dict[str, Any]:
    blocks = parse_document(text)
    title = next((b.text for b in blocks if b.kind == "title"), "")
    lead = [b for b in blocks if b.kind == "para" and b.chapter == 0]
    chapters: List[Dict[str, Any]] = []
    for b in blocks:
        if b.kind == "heading" and b.level <= 2:
            chapters.append({"no": len(chapters) + 1, "title": b.text, "line": b.line, "chars": 0, "questions": 0, "speakers": [], "paragraphs": 0})
    by_no = {c["no"]: c for c in chapters}
    for b in blocks:
        if b.chapter == 0 or b.chapter not in by_no:
            continue
        c = by_no[b.chapter]
        if b.kind == "para":
            c["chars"] += char_len(b.text)
            c["paragraphs"] += 1
            if b.speaker and b.speaker not in c["speakers"]:
                c["speakers"].append(b.speaker)
        elif b.kind == "question":
            c["chars"] += char_len(b.text)
            c["questions"] += 1
        elif b.kind == "heading" and b.level > 2:
            c["chars"] += char_len(b.text)
    lead_chars = sum(char_len(b.text) for b in lead)
    total = lead_chars + sum(c["chars"] for c in chapters)
    findings: List[Dict[str, Any]] = []

    if len(chapters) >= 3:
        med = statistics.median([c["chars"] for c in chapters]) or 1
        for c in chapters:
            if c["chars"] > med * 1.8:
                findings.append({"level": "info", "code": "F7", "line": c["line"],
                                 "message": "章「%s」が %d 字（中央値 %d 字の %.1f 倍）。山場でなければ削るか分ける" % (c["title"], c["chars"], med, c["chars"] / med)})
    for c in chapters:
        if c["questions"] > 3:
            findings.append({"level": "info", "code": "第1部7", "line": c["line"],
                             "message": "章「%s」の問いが %d（目安は 2〜3。記事の性質による）" % (c["title"], c["questions"])})

    seen: Dict[str, Block] = {}
    for b in blocks:
        if b.kind != "question":
            continue
        key = normalize(b.text)
        if not key:
            continue
        if key in seen:
            findings.append({"level": "error", "code": "G4", "line": b.line,
                             "message": "同じ問いが二度入っている（%d 行目と %d 行目）：%s" % (seen[key].line, b.line, b.text[:40])})
        else:
            seen[key] = b

    paras = [b for b in blocks if b.kind == "para"]
    if lead and paras and paras[-1] not in lead:
        lead_tok = set(content_tokens(" ".join(b.text for b in lead)))
        last_tok = set(content_tokens(paras[-1].text))
        if lead_tok:
            inter = lead_tok & last_tok
            ratio = len(inter) / max(1, min(len(lead_tok), len(last_tok) or 1))
            if not inter or ratio < 0.1:
                findings.append({"level": "info", "code": "F5", "line": paras[-1].line,
                                 "message": "最後の段落とリードに共通の言葉がほとんどない。締めがリードの問いを本文の言葉で回収しているか確認する"})
    return {"title": title, "lead_chars": lead_chars, "total_chars": total, "chapters": chapters, "findings": findings}


def cmd_structure(args) -> int:
    path = Path(args.file)
    if not path.exists():
        print("ファイルがない：%s" % path)
        return 1
    res = analyze(paths.read_text(path))
    if args.compare:
        prev = analyze(paths.read_text(Path(args.compare)))
        ratio = res["total_chars"] / prev["total_chars"] if prev["total_chars"] else 0
        res["compare"] = {"file": args.compare, "total_chars": prev["total_chars"], "ratio": round(ratio, 2)}
        if ratio and not (0.8 <= ratio <= 1.2):
            res["findings"].append({"level": "info", "code": "F7", "line": 0,
                                    "message": "全体の字数が前の記事の %.2f 倍（%d 字／%d 字）。シリーズの釣り合いを確認" % (ratio, res["total_chars"], prev["total_chars"])})
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        out = ["structure：%s" % path, "タイトル：%s" % (res["title"] or "（なし）"), "リード %d 字／全体 %d 字（空白を除く）" % (res["lead_chars"], res["total_chars"])]
        if "compare" in res:
            out.append("前の記事：%d 字（比 %.2f）" % (res["compare"]["total_chars"], res["compare"]["ratio"]))
        out.append("")
        out.append("| No. | 見出し | 字数 | 問い | 話し手 |")
        out.append("|---|---|---|---|---|")
        for c in res["chapters"]:
            out.append("| %d | %s | %d | %d | %s |" % (c["no"], md_cell(c["title"]), c["chars"], c["questions"], "・".join(c["speakers"]) or "-"))
        if res["findings"]:
            out.append("")
            for f in res["findings"]:
                out.append("L%s [%s] %s %s" % (f["line"] or "-", f["level"], f["code"], f["message"]))
        print("\n".join(out))
    return 2 if any(f["level"] == "error" for f in res["findings"]) else 0
