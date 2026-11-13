"""プラグインとして入れた環境：エンジン（知識・テンプレート）と作業フォルダ（案件データ）が別の場所にある。"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ACO = Path(__file__).resolve().parents[2] / "scripts" / "aco"


class PluginModeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aco-plugin-"))
        self.engine = self.tmp / "engine"   # Git のリポジトリではない（プラグインのキャッシュに相当）
        self.ws = self.tmp / "ws"
        (self.engine / "knowledge" / "approved-lessons").mkdir(parents=True)
        (self.engine / "knowledge" / "approved-lessons" / "lessons.json").write_text(json.dumps(
            {"version": 1, "lessons": [{"id": "GL-001", "rule": "テストの全体ルール", "scope": "global"}]}, ensure_ascii=False), encoding="utf-8")
        for t in ("_template", "_client_template"):
            (self.engine / "projects" / t).mkdir(parents=True)
        (self.engine / "projects" / "_template" / "project.json").write_text(json.dumps({"slug": "", "client": {"name": "", "aliases": []}}), encoding="utf-8")
        (self.engine / "projects" / "_client_template" / "client.json").write_text(json.dumps({"slug": "", "client": {"name": "", "aliases": []}}), encoding="utf-8")
        self.ws.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def aco(self, *args: str):
        env = {k: v for k, v in os.environ.items() if k not in ("ACO_ROOT", "ACO_WORKSPACE", "ACO_ENGINE")}
        env.update({"ACO_ENGINE": str(self.engine), "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
        p = subprocess.run([sys.executable, str(ACO)] + list(args), cwd=str(self.ws), env=env, capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    def test_new_creates_workspace_and_uses_engine_templates(self):
        code, out = self.aco("new", "acme/no1", "--client", "株式会社アクメ（架空）")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.ws / "aco.config.json").exists())
        self.assertTrue((self.ws / "projects" / "acme" / "no1" / "project.json").exists())
        self.assertFalse((self.engine / "projects" / "acme").exists())  # エンジンには書かない

    def test_brief_reads_engine_lessons_and_workspace_ledger(self):
        self.aco("new", "acme/no1", "--client", "株式会社アクメ（架空）")
        self.aco("ledger", "acme", "add", "rules", "--avoid", "仲間", "--use", "メンバー")
        code, out = self.aco("ledger", "acme/no1", "brief")
        self.assertEqual(code, 0, out)
        self.assertIn("テストの全体ルール", out)
        self.assertIn("「仲間」→「メンバー」", out)

    def test_lessons_propose_goes_to_workspace_and_approve_is_refused(self):
        self.aco("init")
        code, out = self.aco("lessons", "propose", "--rule", "見出しは章の答えを言い切る", "--why", "x", "--how", "y", "--scope", "official-article")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.ws / ".aco" / "knowledge" / "approved-lessons" / "proposed.json").exists())
        self.assertFalse((self.engine / "knowledge" / "approved-lessons" / "proposed.json").exists())
        code, out = self.aco("lessons", "approve", "PL-001", "--by", "テスト")
        self.assertEqual(code, 1, out)
        self.assertIn("管理者", out)


if __name__ == "__main__":
    unittest.main()
