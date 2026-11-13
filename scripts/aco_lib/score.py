"""10 軸の評価の集計・公開不可の判定・頭打ちの判定（philosophy/quality-standards.md）。

点数は編集上の判断を助けるもので、品質を保証するものではない。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import paths

AXES = [
    ("originality", "企画の独自性"),
    ("discovery", "読者にとっての発見"),
    ("distinctiveness", "企業・人物の固有性"),
    ("concreteness", "情報の具体性"),
    ("structure", "構成の必然性"),
    ("naturalness", "日本語の自然さ"),
    ("expression", "表現の完成度"),
    ("accuracy", "事実の正確性"),
    ("brand_fit", "ブランドへの適合性"),
    ("purpose", "記事目的への貢献"),
]
BLOCKER_TYPES = {
    "fabricated-quote": "根拠のない発言の創作",
    "fact-contradiction": "重要な事実の矛盾",
    "confidential": "未承認の機密",
    "locked-violation": "変更禁止事項への違反",
    "brand-risk": "未解決の重大なブランドリスク",
}
PLATEAU_POINTS = 3


def evaluate(data: Dict[str, Any]) -> Dict[str, Any]:
    axes = data.get("axes") or {}
    rows = []
    missing = []
    warnings = []
    total = 0.0
    for key, label in AXES:
        a = axes.get(key) or {}
        sc = a.get("score")
        if sc is None or sc == "":
            missing.append(label)
            rows.append({"key": key, "label": label, "score": None, "reason": a.get("reason", ""), "improve": a.get("improve", "")})
            continue
        try:
            v = float(sc)
        except (TypeError, ValueError):
            warnings.append("%s の点数が数字でない：%r" % (label, sc))
            missing.append(label)
            rows.append({"key": key, "label": label, "score": None, "reason": a.get("reason", ""), "improve": a.get("improve", "")})
            continue
        if not (0 <= v <= 10):
            warnings.append("%s の点数が 0〜10 の外：%s" % (label, sc))
        if not (a.get("reason") or "").strip():
            warnings.append("%s の評価理由がない" % label)
        total += v
        rows.append({"key": key, "label": label, "score": v, "reason": a.get("reason", ""), "improve": a.get("improve", "")})
    unknown = [k for k in axes if k not in dict(AXES)]
    if unknown:
        warnings.append("知らない軸：%s" % "、".join(unknown))
    blockers = []
    for b in data.get("blockers") or []:
        if b.get("resolved"):
            continue
        if not ((b.get("detail") or "").strip() or (b.get("location") or "").strip()):
            continue  # ひな形の空の行
        blockers.append({"type": b.get("type"), "label": BLOCKER_TYPES.get(b.get("type"), b.get("type")), "detail": b.get("detail", ""), "location": b.get("location", "")})
    filled = [r for r in rows if r["score"] is not None]
    low = min(filled, key=lambda r: r["score"]) if filled else None
    if missing:
        warnings.append("未記入の軸：%s" % "、".join(missing))
    if blockers:
        verdict = "公開不可（ブロッカーあり）"
    elif missing:
        verdict = "評価未完了（未記入の軸あり）"
    elif any(r["score"] <= 5 for r in filled) or total < 70:
        verdict = "要改善"
    else:
        verdict = "公開候補（最終判断は人）"
    return {"version": data.get("version", ""), "reviewer": data.get("reviewer", ""), "rows": rows, "total": round(total, 1),
            "lowest": low, "blockers": blockers, "verdict": verdict, "warnings": warnings}


def plateau(totals: List[float]) -> Optional[Dict[str, Any]]:
    if len(totals) < 3:
        return None
    gain = (totals[-1] - totals[-2]) + (totals[-2] - totals[-3])
    return {"gain_last_two": round(gain, 1), "plateau": gain < PLATEAU_POINTS}


def cmd_score(args) -> int:
    p = Path(args.file)
    if not p.exists():
        print("ファイルがない：%s" % p)
        return 1
    try:
        data = json.loads(paths.read_text(p))
    except json.JSONDecodeError as e:
        print("JSON として読めない：%s" % e)
        return 1
    res = evaluate(data)
    hist_totals: List[float] = []
    for h in args.history or []:
        hd = json.loads(paths.read_text(Path(h)))
        hist_totals.append(evaluate(hd)["total"])
    totals = hist_totals + [res["total"]]
    pl = plateau(totals)
    res["history_totals"] = totals
    res["plateau"] = pl
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        out = ["score：%s（%s %s）" % (p, res["version"], res["reviewer"]),
               "点数は判断を助けるもので、品質の保証ではない。", "",
               "| 軸 | 点 | 理由 | 改善案 |", "|---|---|---|---|"]
        for r in res["rows"]:
            sc = "-" if r["score"] is None else ("%g" % r["score"])
            out.append("| %s | %s | %s | %s |" % (r["label"], sc, (r["reason"] or "").replace("|", "｜"), (r["improve"] or "").replace("|", "｜")))
        out.append("")
        out.append("合計 %g／100" % res["total"] + ("　最低：%s %g" % (res["lowest"]["label"], res["lowest"]["score"]) if res["lowest"] else ""))
        for b in res["blockers"]:
            out.append("[ブロッカー] %s：%s %s" % (b["label"], b["detail"], ("（%s）" % b["location"]) if b["location"] else ""))
        out.append("判定：%s" % res["verdict"])
        if len(totals) >= 2:
            out.append("推移：" + " → ".join("%g" % t for t in totals))
        if pl and pl["plateau"]:
            out.append("頭打ち：直近 2 回の改善が合計 %g 点（%d 点未満）。文章の手直しを続けず、追加取材・情報不足・判断待ちとして報告する。" % (pl["gain_last_two"], PLATEAU_POINTS))
        for w in res["warnings"]:
            out.append("[warn] " + w)
        print("\n".join(out))
    if res["blockers"] or (pl and pl["plateau"]):
        return 2
    return 0
