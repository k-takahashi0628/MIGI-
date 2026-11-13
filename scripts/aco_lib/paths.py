"""リポジトリ直下・設定・JSON の読み書き。"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CONFIG: Dict[str, Any] = {
    "repo_visibility": "private",
    "allow_project_data_in_git": False,
    "pii_allowlist": ["noreply@anthropic.com", "example.com", "example.jp"],
    "max_scan_kb": 2048,
}

LESSONS_DIR = Path("knowledge") / "approved-lessons"


def engine_root() -> Path:
    """エンジン（知識・テンプレート・スクリプト）の場所。ACO_ROOT があればそれ、なければこのスクリプトのリポジトリ（プラグイン）。"""
    env = os.environ.get("ACO_ENGINE") or os.environ.get("ACO_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent.parent


def find_workspace() -> Optional[Path]:
    """作業フォルダ（案件データ projects/ と .aco/ を置く所）。ACO_WORKSPACE・ACO_ROOT → 今のフォルダから上へ aco.config.json。"""
    env = os.environ.get("ACO_WORKSPACE") or os.environ.get("ACO_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    cur = Path.cwd().resolve()
    for p in [cur] + list(cur.parents):
        if (p / "aco.config.json").exists():
            return p
    return None


def workspace_root() -> Path:
    """見つからなければ今のフォルダ（`aco init` / `aco new` で作業フォルダにする）。"""
    return find_workspace() or Path.cwd().resolve()


def init_workspace(path: Path) -> bool:
    """作業フォルダの印（aco.config.json）と .aco/・projects/ を作る。作ったら True。"""
    created = False
    if not (path / "aco.config.json").exists():
        write_json(path / "aco.config.json", {"repo_visibility": "private", "allow_project_data_in_git": False,
                                              "pii_allowlist": DEFAULT_CONFIG["pii_allowlist"]})
        created = True
    (path / ".aco").mkdir(exist_ok=True)
    bl = path / ".aco" / "blocklist.local.json"
    if not bl.exists():
        write_json(bl, {"note": "Git や共有の知識に入れない。実在の顧客名・人名を登録すると、全体ルールへの混入を止める。", "names": []})
    (path / "projects").mkdir(exist_ok=True)
    return created


def repo_root() -> Path:
    """案件データを扱うコマンドの基準（＝作業フォルダ）。リポジトリで作業するときはエンジンと同じ場所になる。"""
    return workspace_root()


def load_config(root: Path) -> Dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    p = root / "aco.config.json"
    if p.exists():
        try:
            cfg.update(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            raise SystemExit("aco.config.json が JSON として読めない：%s" % e)
    return cfg


def read_text(path: Path) -> str:
    data = Path(path).read_bytes()
    text = data.decode("utf-8-sig")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_json(path: Path, default: Any = None) -> Any:
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def today() -> str:
    return datetime.date.today().isoformat()


def project_dir(root: Path, slug: str) -> Path:
    return root / "projects" / slug


# 会社フォルダ：projects/<会社>/ に client.json と client-ledger.json を置き、案件は projects/<会社>/<案件>/。
# スラッグは「会社/案件」（例 japan-relief/no3-taidan）。会社の台帳はその会社の全案件に効き、ほかの会社には効かない。
def client_slug(slug: str) -> Optional[str]:
    return slug.split("/", 1)[0] if "/" in slug else None


def is_client_dir(root: Path, slug: str) -> bool:
    d = project_dir(root, slug)
    return (d / "client.json").exists() and not (d / "project.json").exists()


def ledger_file(root: Path, slug: str) -> Path:
    d = project_dir(root, slug)
    return d / ("client-ledger.json" if is_client_dir(root, slug) else "ledger.json")


def load_client(root: Path, slug: str) -> Optional[Dict[str, Any]]:
    c = client_slug(slug)
    if not c:
        return None
    return read_json(project_dir(root, c) / "client.json", None)


def effective_ledger(root: Path, slug: str) -> Dict[str, Any]:
    """会社の台帳（あれば）＋案件の台帳。会社の項目には "_from": "client" を付ける。"""
    own = read_json(ledger_file(root, slug), None)
    if own is None:
        raise SystemExit("台帳がない：%s" % rel(root, ledger_file(root, slug)))
    c = client_slug(slug)
    if not c:
        return own
    cl = read_json(project_dir(root, c) / "client-ledger.json", None) or {}
    merged: Dict[str, Any] = {"version": own.get("version", 1)}
    for k in set(list(own.keys()) + list(cl.keys())):
        if isinstance(own.get(k, []), list) or isinstance(cl.get(k, []), list):
            merged[k] = [dict(e, _from="client") for e in (cl.get(k) or []) if isinstance(e, dict)] + list(own.get(k) or [])
    return merged


def load_project(root: Path, slug: str) -> Optional[Dict[str, Any]]:
    return read_json(project_dir(root, slug) / "project.json", None)


def rel(root: Path, path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)
