"""承認済みの全体ルール（knowledge/approved-lessons/lessons.json）と候補（proposed.json）。

全体ルールには、案件の社名・人名・blocklist の名前・メールアドレス・電話番号を入れない。
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import paths

SCOPES = ["global", "official-article", "interview", "revision", "delivery"]
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<![\d-])0\d{1,4}-\d{1,4}-\d{3,4}(?![\d-])|(?<![0-9A-Za-z])0[789]0\d{8}(?![0-9A-Za-z])")
CORP_RE = re.compile(r"^(株式会社|有限会社|合同会社|一般社団法人|一般財団法人)|(株式会社|有限会社|合同会社)$")


def lessons_path(root: Path) -> Path:
    return root / paths.LESSONS_DIR / "lessons.json"


def proposed_path(root: Path) -> Path:
    return root / paths.LESSONS_DIR / "proposed.json"


def load_lessons(root: Path) -> Dict[str, Any]:
    d = paths.read_json(lessons_path(root), None) or {"version": 1, "lessons": []}
    d.setdefault("lessons", [])
    d["lessons"] = [l for l in d["lessons"] if (l.get("rule") or "").strip()]
    return d


def load_proposed(root: Path) -> Dict[str, Any]:
    d = paths.read_json(proposed_path(root), None) or {"version": 1, "proposals": []}
    d.setdefault("proposals", [])
    d["proposals"] = [p for p in d["proposals"] if (p.get("rule") or "").strip()]
    return d


def _name_variants(name: str) -> List[str]:
    out = {name.strip()}
    base = re.sub(r"[（(][^）)]*[）)]", "", name).strip()
    out.add(base)
    out.add(CORP_RE.sub("", base).strip())
    return [n for n in out if len(n) >= 2]


def sensitive_names(root: Path, include_public_samples: bool = True) -> List[str]:
    """projects/*/project.json（_template を除く）と .aco/blocklist.local.json の名前。

    include_public_samples=False のときは、visibility が public-sample（架空のサンプル）の案件の名前を除く。
    """
    names: List[str] = []
    roots = [root]
    ws = paths.workspace_root()
    if ws.resolve() != root.resolve():
        roots.append(ws)
    for base in roots:
        names += _names_in(base, include_public_samples)
    return sorted(set(n for n in names if n), key=len, reverse=True)


def _names_in(root: Path, include_public_samples: bool) -> List[str]:
    names: List[str] = []
    pdir = root / "projects"
    if pdir.exists():
        for pj in sorted(list(pdir.glob("*/project.json")) + list(pdir.glob("*/*/project.json")) + list(pdir.glob("*/client.json"))):
            if any(part.startswith("_") for part in pj.relative_to(pdir).parts[:-1]):
                continue
            try:
                proj = json.loads(pj.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not include_public_samples and proj.get("visibility") == "public-sample":
                continue
            client = proj.get("client") or {}
            if client.get("name"):
                names += _name_variants(client["name"])
            for a in client.get("aliases") or []:
                if a:
                    names += _name_variants(a)
            for p in proj.get("people") or []:
                if p.get("name"):
                    names += _name_variants(p["name"])
    bl = paths.read_json(root / ".aco" / "blocklist.local.json", None)
    if isinstance(bl, dict):
        for n in bl.get("names") or []:
            if n:
                names += _name_variants(str(n))
    seen = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return seen


def leak_reasons(root: Path, texts: List[str]) -> List[str]:
    joined = "\n".join(t for t in texts if t)
    reasons = []
    for n in sensitive_names(root):
        if n in joined:
            reasons.append("案件の社名・人名（または blocklist の名前）が入っている：%s" % n)
    for m in EMAIL_RE.finditer(joined):
        reasons.append("メールアドレスが入っている：%s" % m.group(0))
    for m in PHONE_RE.finditer(joined):
        reasons.append("電話番号が入っている：%s" % m.group(0))
    return reasons


def _next(entries: List[Dict[str, Any]], prefix: str) -> str:
    n = 0
    for e in entries:
        m = re.match(r"^%s-(\d+)$" % prefix, str(e.get("id", "")))
        if m:
            n = max(n, int(m.group(1)))
    return "%s-%03d" % (prefix, n + 1)


def render(root: Path) -> str:
    d = load_lessons(root)
    out = [
        "# 承認済みの全体ルール",
        "",
        "このファイルは `python3 scripts/aco lessons render` で lessons.json から作る。直接編集しない。",
    ]
    for l in d["lessons"]:
        out.append("")
        out.append("## %s ［%s］ %s" % (l.get("id", ""), l.get("scope", ""), l.get("rule", "")))
        out.append("- なぜ：%s" % l.get("why", ""))
        out.append("- どうする：%s" % l.get("how", ""))
        out.append("- 出どころ：%s（承認：%s／%s）" % (l.get("origin", ""), l.get("approved_by", ""), l.get("approved_date", "")))
    text = "\n".join(out) + "\n"
    p = root / paths.LESSONS_DIR / "LESSONS.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return text


def _lessons_root():
    """全体ルールを書く場所。エンジンが Git のリポジトリ（または ACO_ROOT 指定）ならエンジン、プラグインとして入れた環境なら作業フォルダの .aco/。"""
    eng = paths.engine_root()
    if os.environ.get("ACO_ROOT") or (eng / ".git").exists():
        return eng, True
    return paths.workspace_root() / ".aco", False


def cmd_lessons(args) -> int:
    root, is_repo = _lessons_root()
    op = args.op
    if op in ("approve", "reject", "render") and not is_repo:
        print("全体ルールの承認・却下は、リポジトリ（miginanameue/article-creative-os）を手元に取ってきた管理者が行う。"
              "プラグインとして入れた環境では候補を出すまで（%s）。" % (root / paths.LESSONS_DIR / "proposed.json"))
        return 1
    if op == "list" and not is_repo:
        root = paths.engine_root()
    rest = args.rest or []
    if op == "propose":
        if not (args.rule or "").strip():
            print("--rule が必要")
            return 1
        scope = args.scope or "global"
        if scope not in SCOPES:
            print("--scope が違う：%s（%s）" % (scope, " / ".join(SCOPES)))
            return 1
        reasons = leak_reasons(root, [args.rule, args.why, args.how, args.origin, args.evidence])
        if reasons:
            print("全体の候補にしない（案件固有の情報が入っている）。案件固有なら `aco ledger <slug> add proposals` に入れる：")
            for r in reasons:
                print("- " + r)
            return 2
        d = load_proposed(root)
        pid = _next(d["proposals"] + [{"id": d.get("last_id", "")}], "PL")
        d["last_id"] = pid
        entry = {"id": pid, "rule": args.rule, "why": args.why or "", "how": args.how or "", "scope": scope,
                 "origin": args.origin or "", "evidence": args.evidence or "", "status": "proposed", "date": paths.today(), "reason": ""}
        d["proposals"].append(entry)
        paths.write_json(proposed_path(root), d)
        print("候補にした：%s（承認されるまで規則として使わない）" % pid)
        return 0
    if op in ("approve", "reject"):
        if not rest:
            print("候補の ID を指定する（例：%s PL-001）" % op)
            return 1
        pid = rest[0]
        d = load_proposed(root)
        e = next((p for p in d["proposals"] if p.get("id") == pid), None)
        if e is None:
            print("候補が見つからない：%s" % pid)
            return 1
        if op == "reject":
            e["status"] = "rejected"
            e["reason"] = args.reason or ""
            paths.write_json(proposed_path(root), d)
            print("却下した：%s" % pid)
            return 0
        if not (args.by or "").strip():
            print("承認者（--by）がないため承認しない。本人の明示の OK を確かめてから --by に名前を書く")
            return 1
        if e.get("status") != "proposed":
            print("%s は %s のため承認しない" % (pid, e.get("status")))
            return 1
        reasons = leak_reasons(root, [e.get("rule", ""), e.get("why", ""), e.get("how", ""), e.get("origin", "")])
        if reasons:
            print("全体ルールにしない（%s）：" % pid)
            for r in reasons:
                print("- " + r)
            print("固有名を役割（代表・人事担当など）に置き換えた候補を出し直すか、案件の台帳に入れる。")
            return 2
        L = load_lessons(root)
        gid = _next(L["lessons"], "GL")
        L["lessons"].append({"id": gid, "rule": e["rule"], "why": e.get("why", ""), "how": e.get("how", ""), "scope": e.get("scope", "global"),
                             "origin": e.get("origin", ""), "approved_by": args.by, "approved_date": paths.today()})
        paths.write_json(lessons_path(root), L)
        d["proposals"] = [p for p in d["proposals"] if p.get("id") != pid]
        paths.write_json(proposed_path(root), d)
        render(root)
        print("承認した：%s → %s（LESSONS.md も更新）" % (pid, gid))
        return 0
    if op == "list":
        L = load_lessons(root)
        if args.json:
            out: Dict[str, Any] = {"lessons": L["lessons"]}
            if args.all:
                out["proposals"] = load_proposed(root)["proposals"]
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0
        print("## 承認済み（%d）" % len(L["lessons"]))
        for l in L["lessons"]:
            print("- %s［%s］%s" % (l.get("id"), l.get("scope"), l.get("rule")))
        if args.all:
            P = load_proposed(root)
            print("## 候補（%d）" % len(P["proposals"]))
            for p in P["proposals"]:
                print("- %s［%s・%s］%s" % (p.get("id"), p.get("scope"), p.get("status"), p.get("rule")))
        return 0
    if op == "render":
        render(root)
        print("LESSONS.md を作り直した（%d 件）" % len(load_lessons(root)["lessons"]))
        return 0
    print("操作が違う：%s（propose / approve / reject / list / render）" % op)
    return 1
