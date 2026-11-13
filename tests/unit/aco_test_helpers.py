"""単体テストの共通部品：一時フォルダに小さなリポジトリを作り、aco を動かす。"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts"
ACO = SCRIPTS / "aco"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True

TEMPLATE_PROJECT = {
    "slug": "", "title": "", "client": {"name": "", "aliases": []}, "people": [], "article_type": "other", "medium": "",
    "visibility": "confidential", "decision_maker": "", "coordinator": "", "series": {"name": "", "part": "", "previous": []},
    "interview_dates": [], "stage": "00_new", "deadline": "", "created": "",
}
EMPTY_LEDGER = {"version": 1, "locked": [], "approved": [], "rejected": [], "pending": [], "rules": [], "facts": [],
                "confidential": [], "decisions": [], "proposals": []}


class TempRepo(unittest.TestCase):
    """setUp で一時リポジトリを作るテストの基底。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aco-test-"))
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self.write_json("aco.config.json", {"repo_visibility": "private", "allow_project_data_in_git": False,
                                            "pii_allowlist": ["noreply@anthropic.com", "example.com", "example.jp"]})
        self.write_json("projects/_template/project.json", TEMPLATE_PROJECT)
        self.write_json("projects/_template/ledger.json", EMPTY_LEDGER)
        self.write_json("knowledge/approved-lessons/lessons.json", {"version": 1, "lessons": []})
        self.write_json("knowledge/approved-lessons/proposed.json", {"version": 1, "proposals": []})

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel: str, text: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def write_json(self, rel: str, data) -> Path:
        return self.write(rel, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def read_json(self, rel: str):
        return json.loads((self.root / rel).read_text(encoding="utf-8"))

    def aco(self, *args: str):
        env = dict(os.environ)
        env["ACO_ROOT"] = str(self.root)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        r = subprocess.run([sys.executable, str(ACO)] + list(args), cwd=str(self.root), env=env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr
