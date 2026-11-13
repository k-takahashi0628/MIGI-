"""リポジトリ自体の検査：フロントマター・参照パス・原文のハッシュ・知識 ID・JSON。"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import paths

KNOWN_TOOLS = {
    "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob", "Bash", "BashOutput", "KillShell", "WebFetch", "WebSearch",
    "Agent", "Task", "NotebookEdit", "NotebookRead", "Skill", "TodoWrite", "ToolSearch", "AskUserQuestion", "LS",
    "SlashCommand", "Monitor", "ExitPlanMode", "EnterPlanMode",
}
MODELS = {"inherit", "sonnet", "opus", "haiku", "fable"}
TOP_DIRS = {".claude", "philosophy", "references", "workflows", "knowledge", "templates", "scripts", "tests", "examples", "projects", "docs", "skills", "agents", "bin", "hooks"}
TOP_FILES = {"CLAUDE.md", "README.md", "aco.config.json", ".gitignore", "rules.md"}
LOSS_MAX = {"A": 6, "B": 7, "C": 8, "D": 13, "E": 7, "F": 7, "G": 4, "H": 5}
LOSS_RE = re.compile(r"(?<![A-Za-z0-9_\-])([A-H])([1-9][0-9]?)(?![0-9A-Za-z_])")
AI_RE = re.compile(r"(?<![A-Za-z0-9_\-])AI-(\d{2})(?![0-9])")
GL_RE = re.compile(r"(?<![A-Za-z0-9_\-])GL-(\d{3})(?![0-9])")
LOSS_DEF_RE = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\|\s*)?(?:\*\*)?([A-H][1-9][0-9]?)(?=[\s.．:：）)|*]|$)")
AI_DEF_RE = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\|\s*)?(?:\*\*)?(AI-\d{2})(?![0-9])")
TICK_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")


class Report:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def err(self, where: str, msg: str) -> None:
        self.errors.append("%s：%s" % (where, msg))

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append("%s：%s" % (where, msg))


def parse_frontmatter(text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, text
    fm: Dict[str, Any] = {}
    key = None
    for ln in lines[1:end]:
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*)$", ln)
        if m and not ln.startswith((" ", "\t")):
            key = m.group(1)
            val = m.group(2).strip()
            if val in ("|", ">", "|-", ">-", ""):
                fm[key] = [] if val == "" else ""
            else:
                fm[key] = _unquote(val)
            continue
        lm = re.match(r"^\s+-\s+(.*)$", ln)
        if lm and key is not None:
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(_unquote(lm.group(1).strip()))
            continue
        if key is not None and ln.startswith((" ", "\t")):
            cur = fm.get(key)
            if isinstance(cur, str):
                fm[key] = (cur + " " + ln.strip()).strip()
            elif cur == []:
                fm[key] = ln.strip()
    return fm, "\n".join(lines[end + 1 :])


def _unquote(v: str) -> str:
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def _as_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [x.strip().strip("\"'") for x in s.split(",") if x.strip()]


def check_agents(root: Path, r: Report) -> None:
    adir = root / "agents"
    sdir = root / "skills"
    if not adir.exists():
        r.warn("agents", "フォルダがない")
        return
    for p in sorted(adir.glob("*.md")):
        where = paths.rel(root, p)
        fm, _ = parse_frontmatter(paths.read_text(p))
        if fm is None:
            r.err(where, "フロントマターがない")
            continue
        if fm.get("name") != p.stem:
            r.err(where, "name（%s）がファイル名（%s）と違う" % (fm.get("name"), p.stem))
        if not str(fm.get("description") or "").strip():
            r.err(where, "description がない")
        for t in _as_list(fm.get("tools")):
            if t not in KNOWN_TOOLS and not t.startswith("mcp__") and not re.match(r"^\w+\(.*\)$", t):
                r.warn(where, "知らないツール名：%s" % t)
        for s in _as_list(fm.get("skills")):
            if not (sdir / s / "SKILL.md").exists():
                r.err(where, "skills に書いたスキルがない：%s" % s)
        model = fm.get("model")
        if model and model not in MODELS and not str(model).startswith("claude-"):
            r.warn(where, "model の値：%s" % model)


def check_skills(root: Path, r: Report) -> None:
    sdir = root / "skills"
    if not sdir.exists():
        r.warn("skills", "フォルダがない")
        return
    for d in sorted(x for x in sdir.iterdir() if x.is_dir()):
        sk = d / "SKILL.md"
        where = paths.rel(root, sk)
        if not sk.exists():
            r.warn(paths.rel(root, d), "SKILL.md がない")
            continue
        fm, _ = parse_frontmatter(paths.read_text(sk))
        if fm is None:
            r.err(where, "フロントマターがない")
            continue
        if fm.get("name") != d.name:
            r.err(where, "name（%s）がフォルダ名（%s）と違う" % (fm.get("name"), d.name))
        desc = str(fm.get("description") or "").strip()
        if not desc:
            r.err(where, "description がない")
        elif len(desc) > 1024:
            r.err(where, "description が 1,024 字を超える（%d 字）" % len(desc))
        if "disable-model-invocation" in fm:
            r.err(where, "disable-model-invocation がある（エージェントに読み込めなくなる）")


def scan_files(root: Path) -> List[Path]:
    out: List[Path] = []
    for f in ("CLAUDE.md", "README.md"):
        if (root / f).exists():
            out.append(root / f)
    for d in ("workflows", "philosophy", "knowledge", ".claude"):
        if (root / d).exists():
            out += sorted((root / d).rglob("*.md"))
    return out


def _clean_path(s: str) -> Optional[str]:
    s = s.strip()
    for pre in ("${CLAUDE_PLUGIN_ROOT}/", "$CLAUDE_PLUGIN_ROOT/"):
        if s.startswith(pre):
            s = s[len(pre):]
    if not s or any(c in s for c in "<>*{}$|") or "://" in s or re.search(r"\s", s):
        return None
    if s.startswith(("~", "/", "-")):
        return None
    if s.startswith("./"):
        s = s[2:]
    s = re.sub(r"#.*$", "", s)
    s = re.sub(r":\d+(?:-\d+)?$", "", s)
    s = s.rstrip("。、，,）)」")
    first = s.split("/")[0]
    if s in TOP_FILES or (first in TOP_DIRS and "/" in s):
        return s
    return None


def _internal_originals(root: Path) -> set:
    m = paths.read_json(root / "references" / "original" / "MANIFEST.json", {}) or {}
    return {f.get("file") for f in (m.get("files") or []) if f.get("file") and f.get("visibility") in ("internal", "confidential")}


def check_paths(root: Path, files: List[Path], r: Report) -> None:
    for p in files:
        where = paths.rel(root, p)
        text = paths.read_text(p)
        in_fence = False
        for i, ln in enumerate(text.split("\n"), start=1):
            if ln.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in TICK_RE.finditer(ln):
                cand = _clean_path(m.group(1))
                if cand and cand.startswith("projects/") and not cand.startswith(("projects/_template", "projects/_client_template", "projects/README.md")):
                    continue  # 実案件のパスの例（Git 管理外）
                if cand and cand.startswith("references/original/") and cand.split("/")[-1] in _internal_originals(root) and not (root / cand).exists():
                    continue  # 社内向けの原文（Git 管理外）。check_manifest が警告を出す
                if cand and not (root / cand).exists():
                    r.err("%s:%d" % (where, i), "参照先がない：%s" % cand)
            for m in LINK_RE.finditer(ln):
                tgt = m.group(1)
                if re.match(r"^[a-z]+:", tgt) or tgt.startswith("#"):
                    continue
                tgt = re.sub(r"#.*$", "", tgt)
                if not tgt:
                    continue
                if not ((p.parent / tgt).exists() or (root / tgt).exists()):
                    r.err("%s:%d" % (where, i), "リンク先がない：%s" % tgt)


def _defined(path: Path, rx: re.Pattern) -> Optional[set]:
    if not path.exists():
        return None
    ids = set()
    for ln in paths.read_text(path).split("\n"):
        m = rx.match(ln)
        if m:
            ids.add(m.group(1))
    return ids


def check_ids(root: Path, files: List[Path], r: Report) -> None:
    loss_def = _defined(root / "knowledge" / "failure-patterns" / "official-article.md", LOSS_DEF_RE)
    ai_def = _defined(root / "knowledge" / "failure-patterns" / "ai-writing-signs.md", AI_DEF_RE)
    lessons = paths.read_json(root / paths.LESSONS_DIR / "lessons.json", None)
    gl_def = None
    if isinstance(lessons, dict):
        gl_def = {l.get("id") for l in lessons.get("lessons") or []}
    if loss_def is None:
        r.warn("knowledge/failure-patterns/official-article.md", "まだないため負け筋 ID の定義を確かめられない")
    if ai_def is None:
        r.warn("knowledge/failure-patterns/ai-writing-signs.md", "まだないため AI-xx の定義を確かめられない")
    for p in files:
        where = paths.rel(root, p)
        for i, ln in enumerate(paths.read_text(p).split("\n"), start=1):
            for m in LOSS_RE.finditer(ln):
                letter, num = m.group(1), int(m.group(2))
                ident = "%s%d" % (letter, num)
                if num > LOSS_MAX[letter]:
                    r.err("%s:%d" % (where, i), "負け筋 ID が範囲外：%s" % ident)
                elif loss_def is not None and ident not in loss_def:
                    r.err("%s:%d" % (where, i), "負け筋 ID の定義が知識ファイルにない：%s" % ident)
            for m in AI_RE.finditer(ln):
                n = int(m.group(1))
                ident = "AI-%02d" % n
                if not (1 <= n <= 17):
                    r.err("%s:%d" % (where, i), "AI-xx が範囲外：%s" % ident)
                elif ai_def is not None and ident not in ai_def:
                    r.err("%s:%d" % (where, i), "AI-xx の定義が知識ファイルにない：%s" % ident)
            for m in GL_RE.finditer(ln):
                ident = "GL-%s" % m.group(1)
                if gl_def is not None and ident not in gl_def:
                    r.err("%s:%d" % (where, i), "全体ルール %s が lessons.json にない" % ident)


def check_manifest(root: Path, r: Report) -> None:
    mp = root / "references" / "original" / "MANIFEST.json"
    where = paths.rel(root, mp)
    if not mp.exists():
        r.warn(where, "ない")
        return
    try:
        m = json.loads(paths.read_text(mp))
    except json.JSONDecodeError as e:
        r.err(where, "JSON として読めない：%s" % e)
        return
    for f in m.get("files") or []:
        name = f.get("file")
        if not name:
            continue
        fp = mp.parent / name
        if not fp.exists():
            if f.get("visibility") in ("internal", "confidential"):
                # 社内向けの原文は Git に入れない（.gitignore）。ほかの人の手元にないのは正常
                r.warn(where, "社内向けの原文がこの手元にない（Git 管理外。持っている人に共有してもらう）：%s" % name)
            else:
                r.err(where, "原文がない：%s" % name)
            continue
        h = hashlib.sha256(fp.read_bytes()).hexdigest()
        want = (f.get("sha256") or "").strip()
        if not want:
            r.err(where, "sha256 が書かれていない：%s" % name)
        elif want != h:
            r.err(where, "原文が書き換えられている（sha256 不一致）：%s" % name)


def check_json(root: Path, r: Report) -> None:
    lp = root / paths.LESSONS_DIR / "lessons.json"
    pp = root / paths.LESSONS_DIR / "proposed.json"
    for p, key, prefix in ((lp, "lessons", "GL"), (pp, "proposals", "PL")):
        where = paths.rel(root, p)
        if not p.exists():
            r.warn(where, "ない")
            continue
        try:
            d = json.loads(paths.read_text(p))
        except json.JSONDecodeError as e:
            r.err(where, "JSON として読めない：%s" % e)
            continue
        if not isinstance(d, dict) or not isinstance(d.get(key), list):
            r.err(where, "\"%s\" のリストがない" % key)
            continue
        for e in d[key]:
            if not (e.get("rule") or "").strip():
                continue
            if not re.match(r"^%s-\d{3}$" % prefix, str(e.get("id", ""))):
                r.err(where, "ID の形が違う：%s" % e.get("id"))
            if key == "lessons" and not (e.get("approved_by") or "").strip():
                r.err(where, "%s に承認者（approved_by）がない" % e.get("id"))
    tdir = root / "projects" / "_template"
    if tdir.exists():
        for p in sorted(tdir.rglob("*.json")):
            try:
                json.loads(paths.read_text(p))
            except json.JSONDecodeError as e:
                r.err(paths.rel(root, p), "JSON として読めない：%s" % e)
        pj = paths.read_json(tdir / "project.json", None)
        if isinstance(pj, dict):
            for k in ("slug", "client", "people", "article_type", "visibility", "stage"):
                if k not in pj:
                    r.err("projects/_template/project.json", "項目がない：%s" % k)
        lj = paths.read_json(tdir / "ledger.json", None)
        if isinstance(lj, dict):
            for k in ("locked", "approved", "rejected", "pending", "rules", "facts", "confidential", "decisions", "proposals"):
                if k not in lj:
                    r.err("projects/_template/ledger.json", "欄がない：%s" % k)
    else:
        r.warn("projects/_template", "ない")


def run(root: Path) -> Report:
    r = Report()
    check_agents(root, r)
    check_skills(root, r)
    files = scan_files(root)
    check_paths(root, files, r)
    check_ids(root, files, r)
    check_manifest(root, r)
    check_json(root, r)
    return r


def cmd_validate(args) -> int:
    root = paths.engine_root()
    r = run(root)
    if args.json:
        print(json.dumps({"errors": r.errors, "warnings": r.warnings}, ensure_ascii=False, indent=2))
    else:
        print("validate：%s" % root)
        print("エラー %d 件／警告 %d 件" % (len(r.errors), len(r.warnings)))
        for e in r.errors:
            print("- [error] " + e)
        for w in r.warnings:
            print("- [warn] " + w)
        if not r.errors:
            print("エラーはない。")
    return 2 if r.errors else 0
