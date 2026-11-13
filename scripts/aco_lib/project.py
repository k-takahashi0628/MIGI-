"""案件フォルダの作成（new）と進み具合（status）。"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import paths
from .ledger import empty_ledger, load as load_ledger

TYPES = ["ceo-business", "ceo-organization", "employee-interview", "project-culture", "company-intro", "other"]
STEPS = [
    ("01_brief", "目的設計（/article-brief）", "work/01_brief.md"),
    ("02_source-audit", "素材分析（/source-audit）", "work/02_source-audit.md"),
    ("03_insight", "価値の発見（/insight-discovery）", "work/03_insight.md"),
    ("04_structure", "構成設計（/story-architecture）", "work/04_structure.md"),
    ("05_draft", "初稿（/article-writing）", "drafts/v1.md"),
]


def default_project(slug: str) -> Dict[str, Any]:
    return {
        "slug": slug, "title": "", "client": {"name": "", "aliases": []}, "people": [],
        "article_type": "other", "medium": "", "visibility": "confidential", "decision_maker": "", "coordinator": "",
        "series": {"name": "", "part": "", "previous": []}, "interview_dates": [], "stage": "00_new", "deadline": "", "created": "",
    }


def cmd_new(args) -> int:
    if paths.find_workspace() is None:
        paths.init_workspace(Path.cwd().resolve())
        print("作業フォルダにした：%s（aco.config.json・.aco/・projects/ を作った）" % Path.cwd().resolve())
    root = paths.repo_root()
    eng = paths.engine_root()
    slug = args.slug
    part = r"[a-z0-9][a-z0-9-]{1,60}"
    if not re.fullmatch(r"%s(?:/%s)?" % (part, part), slug):
        print("スラッグは英小文字・数字・ハイフン（2〜61 字）。会社ごとに分けるなら「会社/案件」（例 japan-relief/no3-taidan）：%s" % slug)
        return 1
    client = paths.client_slug(slug)
    if client and not paths.project_dir(root, client).exists():
        # 会社フォルダがなければ、ひな形から作る（会社の台帳はその会社の全案件に効く）
        ct = eng / "projects" / "_client_template"
        cdest = paths.project_dir(root, client)
        if ct.exists():
            shutil.copytree(ct, cdest)
        else:
            cdest.mkdir(parents=True)
        cj = paths.read_json(cdest / "client.json", None) or {"client": {"name": "", "aliases": []}, "knowledge": [], "notes": ""}
        cj.setdefault("client", {"name": "", "aliases": []})
        if args.client:
            cj["client"]["name"] = args.client
        cj["slug"] = client
        cj["created"] = paths.today()
        paths.write_json(cdest / "client.json", cj)
        if not (cdest / "client-ledger.json").exists():
            paths.write_json(cdest / "client-ledger.json", empty_ledger())
        print("会社フォルダを作った：%s（会社共通の決まりは client-ledger.json に。`aco ledger %s add rules …`）" % (paths.rel(root, cdest), client))
    elif client and paths.project_dir(root, client).exists() and not args.client:
        cj = paths.read_json(paths.project_dir(root, client) / "client.json", {}) or {}
        args.client = (cj.get("client") or {}).get("name") or None
    if args.type and args.type not in TYPES:
        print("--type が違う：%s（%s）" % (args.type, " / ".join(TYPES)))
        return 1
    tdir = eng / "projects" / "_template"
    dest = paths.project_dir(root, slug)
    if dest.exists():
        print("すでにある：%s（上書きしない）" % paths.rel(root, dest))
        return 1
    if tdir.exists():
        shutil.copytree(tdir, dest)
    else:
        dest.mkdir(parents=True)
    for d in ("sources", "work/reviews", "drafts", "delivery"):
        (dest / d).mkdir(parents=True, exist_ok=True)
    proj = paths.read_json(dest / "project.json", None) or default_project(slug)
    base = default_project(slug)
    for k, v in base.items():
        proj.setdefault(k, v)
    proj["slug"] = slug
    if args.title:
        proj["title"] = args.title
    client = proj.get("client") if isinstance(proj.get("client"), dict) else {"name": "", "aliases": []}
    if args.client:
        client["name"] = args.client
    elif client.get("name", "").startswith(("（", "(", "<")):
        client["name"] = ""
    proj["client"] = client
    if args.type:
        proj["article_type"] = args.type
    proj["visibility"] = "confidential"
    proj["stage"] = "00_new"
    proj["created"] = paths.today()
    paths.write_json(dest / "project.json", proj)
    paths.write_json(dest / "ledger.json", empty_ledger())
    print("案件フォルダを作った：%s" % paths.rel(root, dest))
    print("次：取材資料を %s/sources/ に置き、project.json の人・決裁者・媒体を埋めてから `/article-desk %s` で始める。" % (paths.rel(root, dest), slug))
    print("このフォルダは Git に入れない（.gitignore で除外）。")
    return 0


def _versions(ddir: Path) -> List[int]:
    vs = []
    if ddir.exists():
        for p in ddir.glob("v*.md"):
            m = re.fullmatch(r"v(\d+)\.md", p.name)
            if m:
                vs.append(int(m.group(1)))
    return sorted(vs)


def status(root: Path, slug: str) -> Dict[str, Any]:
    pdir = paths.project_dir(root, slug)
    if not pdir.exists():
        raise SystemExit("案件フォルダがない：projects/%s" % slug)
    proj = paths.read_json(pdir / "project.json", {}) or {}
    done = []
    nxt: Optional[str] = None
    for key, label, rel in STEPS:
        ok = (pdir / rel).exists()
        if key == "05_draft":
            ok = bool(_versions(pdir / "drafts"))
        done.append({"step": key, "label": label, "done": ok, "file": rel})
        if not ok and nxt is None:
            nxt = label
    vs = _versions(pdir / "drafts")
    latest = vs[-1] if vs else None
    reviews: List[str] = []
    if latest is not None:
        rdir = pdir / "work" / "reviews"
        if rdir.exists():
            for p in sorted(rdir.glob("v%d_*" % latest)):
                reviews.append(p.name)
        if nxt is None:
            if not any(not r.endswith("_scores.json") and not r.endswith("_fact.md") for r in reviews):
                nxt = "v%d の編集レビュー（STEP 6：/editorial-critique ほか）" % latest
            elif not any(r.endswith("_fact.md") for r in reviews):
                nxt = "v%d の事実確認（STEP 8：/article-fact-check）" % latest
    finals = sorted(p.name for p in (pdir / "delivery").glob("final_v*.md")) if (pdir / "delivery").exists() else []
    if nxt is None:
        if not finals:
            nxt = "納品物の作成（STEP 9：/delivery-package）"
        elif latest is not None and ("final_v%d.md" % latest) not in finals:
            nxt = "最新版 v%d の納品物（STEP 9）" % latest
        else:
            nxt = "学習（STEP 10：/feedback-learning）か、先方の返事待ち"
    pending = []
    try:
        led = load_ledger(root, slug)
        pending = [e for e in led.get("pending", []) if e.get("status", "open") != "closed"]
        proposals = [e for e in led.get("proposals", []) if e.get("status") == "proposed"]
    except SystemExit:
        proposals = []
    return {"slug": slug, "stage": proj.get("stage", ""), "steps": done, "latest_draft": ("v%d" % latest) if latest else None,
            "latest_reviews": reviews, "finals": finals, "open_pending": pending, "open_proposals": proposals, "next": nxt}


def cmd_status(args) -> int:
    root = paths.repo_root()
    st = status(root, args.slug)
    if args.json:
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0
    out = ["status：%s（project.json の工程：%s）" % (st["slug"], st["stage"] or "-")]
    for s in st["steps"]:
        out.append("- [%s] %s（%s）" % ("x" if s["done"] else " ", s["label"], s["file"]))
    out.append("最新版：%s／そのレビュー：%s" % (st["latest_draft"] or "なし", "・".join(st["latest_reviews"]) or "なし"))
    out.append("納品物：%s" % ("・".join(st["finals"]) or "なし"))
    if st["open_pending"]:
        out.append("未解決の要確認：%d 件" % len(st["open_pending"]))
        for e in st["open_pending"]:
            out.append("  - %s %s" % (e.get("id"), e.get("item")))
    if st["open_proposals"]:
        out.append("承認待ちの学習候補：%d 件" % len(st["open_proposals"]))
    out.append("次の一手：%s" % st["next"])
    print("\n".join(out))
    return 0


def cmd_init(args) -> int:
    path = Path(args.path).expanduser().resolve() if getattr(args, "path", None) else Path.cwd().resolve()
    path.mkdir(parents=True, exist_ok=True)
    made = paths.init_workspace(path)
    print(("作業フォルダにした：%s" if made else "すでに作業フォルダ：%s") % path)
    print("案件はここの projects/<会社>/<案件>/ に作られる（`aco new <会社>/<案件> --client 社名`）。顧客名は .aco/blocklist.local.json に足す。")
    return 0


def cmd_where(args) -> int:
    ws = paths.find_workspace()
    print("エンジン（知識・テンプレート・スクリプト）：%s" % paths.engine_root())
    print("作業フォルダ（案件データ）：%s" % (ws if ws else "（まだない。`aco init` で今のフォルダを作業フォルダにする）"))
    return 0
