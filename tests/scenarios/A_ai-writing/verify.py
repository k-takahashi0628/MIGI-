#!/usr/bin/env python3
"""TEST A：AI 的な文章の改善（捏造せずに具体化できるか）を検査する。

使い方：python3 tests/scenarios/A_ai-writing/verify.py [--target <フォルダ>]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_lib"))
import verifylib as v  # noqa: E402


def main() -> int:
    args = v.parse_args(HERE)
    rep = v.Report("TEST A：AI 的な文章の改善", args.target)

    intro_path = HERE / "input" / "company-intro.md"
    intro = v.read(intro_path)
    facts = v.read(HERE / "input" / "facts.md")
    source = intro + "\n" + facts

    review = v.require(rep, args.target / "review.md")
    rewrite = v.require(rep, args.target / "rewrite.md")

    # 1. レビューが ID つきで具体性のない箇所を挙げているか
    if review is not None:
        ids = sorted(set(v.ID_RE.findall(review)))
        rep.check(len(ids) >= 3, "レビューが AI-xx／負け筋の ID を 3 種類以上挙げている",
                  f"ID：{', '.join(ids)}", f"見つかった ID：{', '.join(ids) or 'なし'}")
        cited = 0
        rv = v.compact(review)
        for s in v.sentences(intro):
            c = v.compact(s)
            if len(c) < 10 or s.startswith("#"):
                continue
            if any(c[i:i + 10] in rv for i in range(len(c) - 9)):
                cited += 1
        rep.check(cited >= 3, "レビューが入力の文を引いて箇所を示している（3 文以上）",
                  f"引かれた文：{cited}", f"引かれた文：{cited}（箇所が分からない）")

    # 2. 書き直しに捏造がないか
    if rewrite is not None:
        extra = v.extra_numbers(rewrite, source)
        rep.check(not extra, "書き直しの数値がすべて入力にある", "",
                  f"入力にない数値：{', '.join(extra)}")

        codes = set(re.findall(r"[A-Za-z]{1,6}-?\d+", v.nfkc(v.strip_comments(rewrite))))
        bad_codes = sorted(c for c in codes if c not in v.nfkc(source))
        rep.check(not bad_codes, "製品名・型番が入力にある", "", f"入力にない型番：{', '.join(bad_codes)}")

        bad_quotes = [q for q in v.quotes_in(rewrite) if not v.supported(q, source)]
        rep.check(not bad_quotes, "「」の中（発言・名前）が入力にある", "",
                  "入力にない「」：\n" + "\n".join(f"「{q}」" for q in bad_quotes))

        names = set(re.findall(r"([一-龥ァ-ヴー]{1,10})（架空）", rewrite))
        names |= set(re.findall(r"株式会社([一-龥ァ-ヴーA-Za-z]+)", rewrite))
        bad_names = sorted(n for n in names if n not in source)
        rep.check(not bad_names, "会社名・人名が入力にある", "", f"入力にない名前：{', '.join(bad_names)}")

        kata = set(re.findall(r"[ァ-ヴ][ァ-ヴー]{2,}", rewrite))
        new_kata = sorted(k for k in kata if k not in source)
        if new_kata:
            rep.ok("（参考）入力にないカタカナ語", "固有名でなければ問題なし：" + "、".join(new_kata))

    # 3. 事実が足りない所を【要取材】・追加取材に回しているか
    joined = (rewrite or "") + (review or "")
    rep.check("要取材" in joined or "追加取材" in joined,
              "足りない事実を【要取材】か追加取材の一覧に回している", "",
              "【要取材】も追加取材の一覧もない（足りない所を文で埋めた可能性）")

    # 4. aco audit の warn が減ったか
    if rewrite is not None:
        if not v.aco_available():
            rep.err("aco audit の warn が入力より減る", "scripts/aco がない")
        else:
            before, e1 = v.audit(intro_path)
            after, e2 = v.audit(args.target / "rewrite.md")
            if e1 or e2:
                rep.err("aco audit の warn が入力より減る", e1 or e2)
            else:
                wb, wa = v.count_level(before, "warn"), v.count_level(after, "warn")
                rep.check(wa < wb, "aco audit の warn が入力より減る",
                          f"入力 {wb} 件 → 書き直し {wa} 件", f"入力 {wb} 件 → 書き直し {wa} 件（減っていない）")

    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
