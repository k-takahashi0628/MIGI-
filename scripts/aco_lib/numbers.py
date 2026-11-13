"""記事の全文（タイトル・リード・見出し・地の文・発言）に出てくる数値が、素材のどこかにあるかを確かめる。

発言の照合（quotes）は話し手ごとに見るが、こちらは地の文も含めて「素材にない数値」を拾う。
意味（何の数か）までは見ないので、見つかった数値も文脈は人が確かめる。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from . import paths
from .textutil import blank_html_comments, extract_numbers, numbers_supported

MARKER_RE = re.compile(r"【(?:要確認|要取材|提案)[^】]*】")


def check(article_text: str, source_texts: List[str]) -> Dict[str, Any]:
    src_nums = []
    for t in source_texts:
        src_nums += extract_numbers(t)
    text = MARKER_RE.sub(lambda m: " " * len(m.group(0)), blank_html_comments(article_text))
    rows = []
    total = 0
    for i, line in enumerate(text.split("\n")):
        nums = extract_numbers(line)
        total += len(nums)
        for v, unit in numbers_supported(nums, src_nums):
            rows.append({"line": i + 1, "value": v, "unit": unit, "text": line.strip()[:60]})
    return {"total": total, "missing": rows}


def cmd_numbers(args) -> int:
    art = Path(args.file)
    if not art.exists():
        print("ファイルがない：%s" % art)
        return 1
    if not args.source:
        print("--source で素材（書き起こし・事実メモ・前の記事など）を 1 つ以上渡す")
        return 1
    texts = []
    for s in args.source:
        p = Path(s)
        if not p.exists():
            print("素材がない：%s" % p)
            return 1
        texts.append(paths.read_text(p))
    res = check(paths.read_text(art), texts)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("numbers：%s（数値 %d 個／素材にないもの %d 個）" % (art, res["total"], len(res["missing"])))
        if res["missing"]:
            print("素材に見つからない数値（根拠を確かめるまで公開しない）：")
            for r in res["missing"]:
                print("- L%d %s%s「%s」" % (r["line"], r["value"], r["unit"], r["text"]))
        else:
            print("素材にない数値はない（何の数かは人が確かめる）。")
    return 2 if res["missing"] else 0
