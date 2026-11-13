"""案件台帳（projects/<slug>/ledger.json）の操作。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import paths
from .audit import format_findings, ledger_findings

KINDS = ["locked", "approved", "rejected", "pending", "rules", "facts", "confidential", "decisions", "proposals"]
PREFIX = {"locked": "LK", "approved": "AP", "rejected": "RJ", "pending": "PD", "rules": "RL", "facts": "FC",
          "confidential": "CF", "decisions": "DC", "proposals": "PR"}
ALIASES = {"lock": "locked", "approve": "approved", "reject": "rejected", "rule": "rules", "fact": "facts",
           "decision": "decisions", "proposal": "proposals", "secret": "confidential"}
LABEL = {"locked": "変更禁止", "approved": "承認済みの表現", "rejected": "却下された表現・案", "pending": "保留・要確認",
         "rules": "表記ルール", "facts": "確定した事実", "confidential": "公開禁止", "decisions": "確定事項", "proposals": "学習候補（承認待ち）"}
REQUIRED = {"locked": ["text"], "approved": ["text"], "rejected": ["text"], "pending": ["item"], "rules": ["avoid", "use"],
            "facts": ["claim"], "confidential": ["term"], "decisions": ["decision"], "proposals": ["target", "payload"]}


def empty_ledger() -> Dict[str, Any]:
    d: Dict[str, Any] = {"version": 1}
    for k in KINDS:
        d[k] = []
    return d


def ledger_path(root: Path, slug: str) -> Path:
    return paths.ledger_file(root, slug)


def load(root: Path, slug: str, create: bool = False) -> Dict[str, Any]:
    pdir = paths.project_dir(root, slug)
    if not pdir.exists():
        raise SystemExit("案件フォルダがない：%s（先に `python3 scripts/aco new %s`）" % (paths.rel(root, pdir), slug))
    p = ledger_path(root, slug)
    data = paths.read_json(p, None)
    if data is None:
        if not create:
            raise SystemExit("ledger.json がない：%s" % paths.rel(root, p))
        data = empty_ledger()
    for k in KINDS:
        data.setdefault(k, [])
    # ひな形の空の行（中身がすべて空）は数えない
    for k in KINDS:
        data[k] = [e for e in data[k] if _has_content(e)]
    return data


def _has_content(e: Dict[str, Any]) -> bool:
    if e.get("payload"):
        return True
    for key, v in e.items():
        if key in ("id", "status", "date", "kind"):
            continue
        if isinstance(v, str) and v.strip():
            return True
    return False


def save(root: Path, slug: str, data: Dict[str, Any]) -> None:
    paths.write_json(ledger_path(root, slug), data)


def next_id(entries: List[Dict[str, Any]], prefix: str) -> str:
    n = 0
    for e in entries:
        m = re.match(r"^%s-(\d+)$" % prefix, str(e.get("id", "")))
        if m:
            n = max(n, int(m.group(1)))
    return "%s-%d" % (prefix, n + 1)


def find(data: Dict[str, Any], eid: str):
    for k in KINDS:
        for e in data[k]:
            if e.get("id") == eid:
                return k, e
    return None, None


def build_entry(kind: str, a) -> Dict[str, Any]:
    d = paths.today()
    if kind == "locked":
        return {"text": a.text, "reason": a.reason or "", "source": a.source or "", "date": a.date or d}
    if kind == "approved":
        return {"text": a.text, "context": a.context or "", "approved_by": a.by or "", "date": a.date or d}
    if kind == "rejected":
        return {"text": a.text, "reason": a.reason or "", "rejected_by": a.by or "", "date": a.date or d}
    if kind == "pending":
        return {"item": a.item, "ask": a.ask or "", "owner": a.owner or "", "status": "open", "date": a.date or d}
    if kind == "rules":
        return {"avoid": a.avoid, "use": a.use, "note": a.note or "", "source": a.source or "", "date": a.date or d}
    if kind == "facts":
        return {"claim": a.claim, "source": a.source or "", "status": a.status or "approved"}
    if kind == "confidential":
        return {"term": a.term, "reason": a.reason or ""}
    if kind == "decisions":
        return {"decision": a.decision, "by": a.by or "", "date": a.date or d}
    if kind == "proposals":
        try:
            payload = json.loads(a.payload)
        except json.JSONDecodeError as e:
            raise SystemExit("--payload が JSON として読めない：%s" % e)
        target = ALIASES.get(a.target, a.target)
        if target not in ("rules", "approved", "rejected", "locked", "decisions", "facts", "confidential"):
            raise SystemExit("--target が違う：%s" % a.target)
        return {"kind": target, "payload": payload, "evidence": a.evidence or "", "status": "proposed", "date": a.date or d}
    raise SystemExit("種類が違う：%s" % kind)


def describe(kind: str, e: Dict[str, Any]) -> str:
    if kind == "rules":
        return "「%s」→「%s」%s" % (e.get("avoid"), e.get("use"), ("（%s）" % e["note"]) if e.get("note") else "")
    if kind == "pending":
        return "%s%s［%s］" % (e.get("item"), ("（%s）" % e["ask"]) if e.get("ask") else "", e.get("status", "open"))
    if kind == "facts":
        return "%s［%s］%s" % (e.get("claim"), e.get("status", ""), ("出典：" + e["source"]) if e.get("source") else "")
    if kind == "confidential":
        return "%s%s" % (e.get("term"), ("（%s）" % e["reason"]) if e.get("reason") else "")
    if kind == "decisions":
        return "%s%s" % (e.get("decision"), ("（%s）" % e["by"]) if e.get("by") else "")
    if kind == "proposals":
        return "→%s %s［%s］%s" % (e.get("kind"), json.dumps(e.get("payload"), ensure_ascii=False), e.get("status"), ("根拠：" + e["evidence"]) if e.get("evidence") else "")
    t = e.get("text", "")
    extra = e.get("reason") or e.get("context") or ""
    return "%s%s" % (t, ("（%s）" % extra) if extra else "")


def check_draft(root: Path, slug: str, draft: Path) -> List[Dict[str, Any]]:
    load(root, slug)  # 案件の台帳があるかを確かめる
    return ledger_findings(paths.read_text(draft), paths.effective_ledger(root, slug))


def _section(out: List[str], data: Dict[str, Any]) -> bool:
    any_entry = False
    for k in ["locked", "rules", "approved", "rejected", "confidential", "decisions", "facts", "pending"]:
        entries = data.get(k) or []
        if k == "pending":
            entries = [e for e in entries if e.get("status", "open") != "closed"]
        entries = [e for e in entries if _has_content(e)]
        if not entries:
            continue
        any_entry = True
        out.append("### %s" % LABEL[k])
        for e in entries:
            out.append("- %s %s" % (e.get("id", ""), describe(k, e)))
    props = [p for p in (data.get("proposals") or []) if p.get("status") == "proposed"]
    if props:
        any_entry = True
        out.append("### 学習候補（%d 件・承認待ち。規則として使わない）" % len(props))
        for p in props:
            out.append("- %s %s" % (p.get("id"), describe("proposals", p)))
    return any_entry


def brief_text(root: Path, slug: str) -> str:
    data = load(root, slug)
    proj = paths.load_project(root, slug) or {}
    lessons = paths.read_json(paths.engine_root() / paths.LESSONS_DIR / "lessons.json", {"lessons": []}) or {"lessons": []}
    out = ["# 制作前に読む一枚：%s" % slug, ""]
    client = (proj.get("client") or {}).get("name", "")
    if paths.is_client_dir(root, slug):
        cj = paths.read_json(paths.project_dir(root, slug) / "client.json", {}) or {}
        cases = sorted(p.parent.name for p in paths.project_dir(root, slug).glob("*/project.json"))
        out.append("- 会社：%s（この台帳は %s のすべての案件に効く）" % ((cj.get("client") or {}).get("name", slug), slug))
        out.append("- 案件：%s" % ("・".join(cases) or "（まだない）"))
        if cj.get("knowledge"):
            out.append("- 会社の資料：%s" % "・".join(cj["knowledge"]))
    else:
        out.append("- 案件：%s／%s／種類 %s／媒体 %s" % (proj.get("title", ""), client, proj.get("article_type", ""), proj.get("medium", "")))
        out.append("- 決裁者：%s／進行担当：%s／工程：%s／期日：%s" % (proj.get("decision_maker", ""), proj.get("coordinator", ""), proj.get("stage", ""), proj.get("deadline", "") or "-"))
    series = proj.get("series") or {}
    if series.get("name"):
        out.append("- シリーズ：%s %s（前の記事：%s）" % (series.get("name"), series.get("part", ""), "・".join(series.get("previous") or []) or "-"))
    out.append("")
    c = paths.client_slug(slug)
    if c and not paths.is_client_dir(root, slug):
        cinfo = paths.load_client(root, slug) or {}
        cl = paths.read_json(paths.project_dir(root, c) / "client-ledger.json", None)
        out.append("## 会社の台帳：%s（%s のすべての案件に効く。ほかの会社には使わない）" % (c, (cinfo.get("client") or {}).get("name", c)))
        if cinfo.get("knowledge"):
            out.append("- 会社の資料：%s" % "・".join(cinfo.get("knowledge")))
        if not (cl and _section(out, cl)):
            out.append("（まだ記録がない）")
        out.append("")
    out.append("## この案件の台帳（ほかの案件には使わない）" if not paths.is_client_dir(root, slug) else "## 会社の台帳（この会社のすべての案件に効く）")
    any_entry = False
    for k in ["locked", "rules", "approved", "rejected", "confidential", "decisions", "facts", "pending"]:
        entries = data[k]
        if k == "pending":
            entries = [e for e in entries if e.get("status", "open") != "closed"]
        if not entries:
            continue
        any_entry = True
        out.append("### %s" % LABEL[k])
        for e in entries:
            out.append("- %s %s" % (e.get("id", ""), describe(k, e)))
    props = [p for p in data["proposals"] if p.get("status") == "proposed"]
    if props:
        any_entry = True
        out.append("### 学習候補（%d 件・承認待ち。規則として使わない）" % len(props))
        for p in props:
            out.append("- %s %s" % (p.get("id"), describe("proposals", p)))
    if not any_entry:
        out.append("（まだ記録がない）")
    out.append("")
    out.append("## 承認済みの全体ルール（knowledge/approved-lessons/lessons.json）")
    ls = lessons.get("lessons") or []
    ls = [l for l in ls if l.get("rule")]
    if not ls:
        out.append("（まだない）")
    for l in ls:
        out.append("- %s［%s］%s" % (l.get("id"), l.get("scope"), l.get("rule")))
    return "\n".join(out) + "\n"


def cmd_ledger(args) -> int:
    root = paths.repo_root()
    slug = args.slug
    op = args.op
    rest = args.rest or []
    if op == "brief" and not paths.project_dir(root, slug).exists():
        lessons = paths.read_json(paths.engine_root() / paths.LESSONS_DIR / "lessons.json", {"lessons": []}) or {"lessons": []}
        print("案件フォルダがない：%s（単発の作業として、承認済みの全体ルールだけを出す。案件にするなら `python3 scripts/aco new %s`）" % (slug, slug))
        print("")
        print("## 承認済みの全体ルール")
        for l in lessons.get("lessons", []):
            print("- %s ［%s］ %s" % (l.get("id"), l.get("scope"), l.get("rule")))
        return 0
    if op == "add":
        if not rest:
            print("種類を指定する：" + " / ".join(KINDS))
            return 1
        kind = ALIASES.get(rest[0], rest[0])
        if kind not in KINDS:
            print("種類が違う：%s（%s）" % (rest[0], " / ".join(KINDS)))
            return 1
        missing = [f for f in REQUIRED[kind] if not getattr(args, f, None)]
        if missing:
            print("%s には %s が必要" % (kind, "、".join("--" + m for m in missing)))
            return 1
        data = load(root, slug, create=True)
        entry = build_entry(kind, args)
        entry = {"id": next_id(data[kind], PREFIX[kind]), **entry}
        data[kind].append(entry)
        save(root, slug, data)
        print("追加した：%s %s %s" % (entry["id"], LABEL[kind], describe(kind, entry)))
        return 0
    if op == "list":
        data = load(root, slug)
        kinds = [ALIASES.get(rest[0], rest[0])] if rest else KINDS
        if args.json:
            print(json.dumps({k: data[k] for k in kinds if k in data}, ensure_ascii=False, indent=2))
            return 0
        for k in kinds:
            if k not in KINDS:
                print("種類が違う：%s" % k)
                return 1
            if not data[k]:
                continue
            print("## %s" % LABEL[k])
            for e in data[k]:
                print("- %s %s" % (e.get("id"), describe(k, e)))
        return 0
    if op in ("close", "approve", "reject"):
        if not rest:
            print("ID を指定する（例：%s PD-1）" % op)
            return 1
        eid = rest[0]
        data = load(root, slug)
        kind, e = find(data, eid)
        if e is None:
            print("ID が見つからない：%s" % eid)
            return 1
        if op == "close":
            if kind != "pending":
                print("close は保留・要確認（PD-）だけ")
                return 1
            e["status"] = "closed"
            if args.note:
                e["closed_note"] = args.note
            e["closed_date"] = paths.today()
            save(root, slug, data)
            print("閉じた：%s %s" % (eid, e.get("item")))
            return 0
        if kind != "proposals":
            print("%s は学習候補（PR-）だけ" % op)
            return 1
        if e.get("status") != "proposed":
            print("%s はすでに %s" % (eid, e.get("status")))
            return 1
        if op == "approve":
            if not (args.by or "").strip():
                print("承認者（--by）がないため承認しない。本人か先方の明示の OK を確かめてから --by に名前を書く")
                return 1
            target = e.get("kind")
            if target not in KINDS or target == "proposals":
                print("候補の移し先が違う：%s" % target)
                return 1
            payload = dict(e.get("payload") or {})
            payload.setdefault("date", paths.today())
            payload["approved_by"] = args.by
            payload["from_proposal"] = eid
            new_id = next_id(data[target], PREFIX[target])
            data[target].append({"id": new_id, **payload})
            e["status"] = "approved"
            e["moved_to"] = new_id
            e["approved_by"] = args.by
            e["approved_date"] = paths.today()
            save(root, slug, data)
            print("承認した：%s → %s（%s）" % (eid, new_id, LABEL[target]))
            return 0
        e["status"] = "rejected"
        e["reason"] = args.reason or ""
        e["rejected_date"] = paths.today()
        save(root, slug, data)
        print("却下した：%s" % eid)
        return 0
    if op == "check":
        if not rest:
            print("原稿のパスを指定する")
            return 1
        draft = Path(rest[0])
        if not draft.exists():
            print("ファイルがない：%s" % draft)
            return 1
        items = check_draft(root, slug, draft)
        if args.json:
            print(json.dumps({"findings": items}, ensure_ascii=False, indent=2))
        else:
            if items:
                print(format_findings(items, "ledger check：%s × %s" % (slug, draft)))
            else:
                print("ledger check：%s × %s：台帳との食い違いはない。" % (slug, draft))
        return 2 if items else 0
    if op == "brief":
        if args.json:
            data = load(root, slug)
            lessons = paths.read_json(paths.engine_root() / paths.LESSONS_DIR / "lessons.json", {"lessons": []})
            print(json.dumps({"project": paths.load_project(root, slug), "ledger": data, "lessons": lessons.get("lessons", [])}, ensure_ascii=False, indent=2))
        else:
            print(brief_text(root, slug), end="")
        return 0
    print("操作が違う：%s（add / list / close / approve / reject / check / brief）" % op)
    return 1
