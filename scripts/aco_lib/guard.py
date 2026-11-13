"""Git に入れる前の公開範囲の検査（docs/architecture.md §7）。"""
from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import paths
from .lessons import EMAIL_RE, PHONE_RE, sensitive_names

TRANSCRIPT_NAME_RE = re.compile(r"書き起こし|文字起こし|transcript", re.I)
FRONT_VIS_RE = re.compile(r"^visibility\s*:\s*(confidential|internal)\s*$", re.M)
HOOK_MARK = "# ARTICLE CREATIVE OS: aco guard"


def _git(root: Path, *args: str) -> Optional[List[str]]:
    try:
        out = subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [l for l in out.stdout.splitlines() if l.strip()]


def list_files(root: Path, mode: str, given: List[str]) -> List[str]:
    if mode == "paths":
        out = []
        for g in given:
            p = Path(g)
            p = p if p.is_absolute() else (Path.cwd() / p)
            if p.is_dir():
                for q in p.rglob("*"):
                    if q.is_file() and ".git" not in q.parts:
                        out.append(paths.rel(root, q))
            else:
                out.append(paths.rel(root, p))
        return out
    if mode == "staged":
        files = _git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
        if files is None:
            raise SystemExit("Git のリポジトリではない（--all か --paths を使う）")
        return files
    files = _git(root, "ls-files", "-co", "--exclude-standard")
    if files is None:
        files = []
        for q in root.rglob("*"):
            if q.is_file() and ".git" not in q.parts and ".aco" not in q.parts and "__pycache__" not in q.parts:
                files.append(q.relative_to(root).as_posix())
    return files


def manifest_visibility(root: Path) -> Dict[str, str]:
    m = paths.read_json(root / "references" / "original" / "MANIFEST.json", None) or {}
    out = {}
    for f in m.get("files") or []:
        if f.get("file"):
            out["references/original/" + f["file"]] = f.get("visibility", "internal")
    return out


def _allowed_pii(value: str, allow: List[str]) -> bool:
    v = value.lower()
    for a in allow:
        a = a.lower()
        if v == a or v.endswith("@" + a) or v.endswith("." + a):
            return True
    return False


def check(root: Path, files: List[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    cfg = paths.load_config(root)
    public = cfg.get("repo_visibility") == "public"
    allow_pii = list(cfg.get("pii_allowlist") or [])
    vis = manifest_visibility(root)
    names = sensitive_names(root, include_public_samples=False)
    max_bytes = int(cfg.get("max_scan_kb", 2048)) * 1024
    blocks: List[Dict[str, str]] = []
    notes: List[Dict[str, str]] = []

    def block(f: str, why: str) -> None:
        blocks.append({"file": f, "reason": why})

    for f in files:
        parts = f.split("/")
        in_projects = parts[0] == "projects" and len(parts) >= 2
        in_scen = f.startswith("tests/scenarios/")
        if in_projects:
            if parts[1] in ("_template", "_client_template") or (len(parts) == 2 and parts[1] == "README.md"):
                pass
            else:
                slug = parts[1]
                proj = paths.read_json(root / "projects" / slug / "project.json", {}) or {}
                if not (cfg.get("allow_project_data_in_git") and proj.get("visibility") == "public-sample"):
                    block(f, "案件データ（projects/%s/）は Git に入れない" % slug)
                    continue
        v = vis.get(f)
        p = root / f
        text = ""
        if p.exists() and p.is_file():
            try:
                raw = p.read_bytes()
            except OSError:
                raw = b""
            if len(raw) > max_bytes:
                notes.append({"file": f, "reason": "大きいため中身は見ていない（%d KB）" % (len(raw) // 1024)})
            elif b"\x00" not in raw[:4096]:
                text = raw.decode("utf-8", errors="ignore")
        if v is None and text:
            m = FRONT_VIS_RE.search(text[:600]) if text.startswith("---") else None
            if m:
                v = m.group(1)
        if v == "confidential":
            block(f, "visibility: confidential のファイル")
            continue
        if v == "internal" and public:
            block(f, "visibility: internal のファイル（repo_visibility が public）")
            continue
        if TRANSCRIPT_NAME_RE.search(parts[-1]) and not in_projects and not in_scen:
            block(f, "書き起こしらしいファイル名（案件フォルダの外）")
            continue
        if not text:
            continue
        for m in EMAIL_RE.finditer(text):
            if not _allowed_pii(m.group(0), allow_pii):
                block(f, "メールアドレス：%s" % m.group(0))
                break
        for m in PHONE_RE.finditer(text):
            block(f, "電話番号らしい数字：%s" % m.group(0))
            break
        if not in_projects and v != "internal":
            hit = [n for n in names if n in text]
            if hit:
                block(f, "案件の社名・人名（blocklist を含む）が入っている：%s" % "・".join(hit[:5]))
        elif v == "internal":
            if any(n in text for n in names):
                notes.append({"file": f, "reason": "internal のファイルに実名がある（非公開リポジトリのため通す）"})
    return blocks, notes


def install_hook(root: Path, force: bool) -> int:
    gitdir = root / ".git"
    if not gitdir.is_dir():
        print("Git のリポジトリではない（先に git init）")
        return 1
    hook = gitdir / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    if hook.exists() and HOOK_MARK not in hook.read_text(encoding="utf-8", errors="ignore") and not force:
        print("別の pre-commit がある：%s（上書きするなら --force）" % hook)
        return 1
    hook.write_text(
        "#!/bin/sh\n%s\ncd \"$(git rev-parse --show-toplevel)\" || exit 1\n"
        "python3 scripts/aco guard --staged || { echo 'aco guard が止めました。上の理由を確認してください。'; exit 1; }\n" % HOOK_MARK,
        encoding="utf-8",
    )
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print("pre-commit に組み込んだ：%s" % hook)
    return 0


def cmd_guard(args) -> int:
    root = paths.engine_root()  # Git に入れるのはエンジン（このリポジトリ）
    if args.install_hook:
        return install_hook(root, args.force)
    mode = "paths" if args.paths else ("all" if args.all else "staged")
    files = list_files(root, mode, args.paths or [])
    blocks, notes = check(root, files)
    if args.json:
        print(json.dumps({"checked": len(files), "blocked": blocks, "notes": notes}, ensure_ascii=False, indent=2))
    else:
        cfg = paths.load_config(root)
        print("guard：%d ファイル（repo_visibility=%s）" % (len(files), cfg.get("repo_visibility")))
        for b in blocks:
            print("- [止める] %s：%s" % (b["file"], b["reason"]))
        for n in notes:
            print("- [info] %s：%s" % (n["file"], n["reason"]))
        if not blocks:
            print("止めるものはない。")
    return 2 if blocks else 0
