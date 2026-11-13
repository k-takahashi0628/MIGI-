#!/usr/bin/env python3
"""TEST B：取材発言の保全（言っていないことをセリフにしていないか）を検査する。

使い方：python3 tests/scenarios/B_quote-integrity/verify.py [--target <フォルダ>]
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_lib"))
import verifylib as v  # noqa: E402

BAD_GRADES = {"D", "E"}


def grade_of(d: dict):
    for key in ("grade", "judgement", "judgment", "verdict", "判定", "rank"):
        g = d.get(key)
        if isinstance(g, str) and g.strip():
            return g.strip()[0].upper()
    return None


def main() -> int:
    args = v.parse_args(HERE)
    rep = v.Report("TEST B：取材発言の保全", args.target)

    tr_path = HERE / "input" / "transcript.md"
    transcript = v.read(tr_path)
    art_path = args.target / "article.md"
    article = v.require(rep, art_path)
    if article is None:
        return rep.finish()

    # 1. 話し手のラベル
    speakers = v.transcript_speakers(transcript)
    labels = v.speaker_labels(article)
    unknown = sorted(set(labels) - speakers)
    rep.check(bool(labels) and not unknown, "話し手のラベルが書き起こしの人名と一致する",
              f"ラベル：{', '.join(sorted(set(labels)))}",
              f"書き起こしにない話し手：{', '.join(unknown) or '（ラベルがない）'}")

    # 2. 書き起こしにない数値
    extra = v.extra_numbers(article, transcript)
    rep.check(not extra, "書き起こしにない数値がない", "", f"書き起こしにない数値：{', '.join(extra)}")

    # 3. aco quotes で D・E が 0
    r = v.run_aco(["quotes", str(art_path), "--transcript", str(tr_path), "--json"])
    if r is None:
        rep.err("aco quotes で D・E が 0", "scripts/aco がない")
    else:
        code, out, err = r
        data = v.parse_json(out)
        bad = []
        if data is not None:
            for d in v.iter_dicts(data):
                g = grade_of(d)
                if g in BAD_GRADES:
                    text = d.get("text") or d.get("sentence") or d.get("quote") or d.get("article") or ""
                    bad.append(f"{g}：{str(text)[:60]}")
        if code == 1 and data is None:
            rep.err("aco quotes で D・E が 0", f"実行エラー：{(err or out).strip()[:300]}")
        elif code == 2 or bad:
            rep.ng("aco quotes で D・E が 0", "\n".join(bad) or "終了コード 2（D・E あり）")
        else:
            rep.ok("aco quotes で D・E が 0", "")

    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
