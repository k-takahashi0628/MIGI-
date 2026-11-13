"""score：ブロッカーは点数にかかわらず公開不可・頭打ちの判定。guard：案件データ・メール・案件名を止める。"""
from __future__ import annotations

import json
import os
import subprocess
import unittest

from aco_test_helpers import TempRepo

KEYS = ["originality", "discovery", "distinctiveness", "concreteness", "structure", "naturalness", "expression", "accuracy", "brand_fit", "purpose"]


def scores(val=8, blockers=None, **override):
    axes = {k: {"label": k, "score": override.get(k, val), "reason": "理由", "improve": ""} for k in KEYS}
    return {"version": "v1", "reviewer": "chief-editor", "axes": axes, "blockers": blockers or [], "notes": ""}


class ScoreTest(TempRepo):
    def run_score(self, data, history=()):
        p = self.write_json("s.json", data)
        args = ["score", str(p), "--json"]
        if history:
            hs = []
            for i, h in enumerate(history):
                hs.append(str(self.write_json("h%d.json" % i, h)))
            args += ["--history"] + hs
        code, out = self.aco(*args)
        return code, json.loads(out)

    def test_candidate(self):
        code, res = self.run_score(scores(8))
        self.assertEqual(code, 0)
        self.assertEqual(res["total"], 80)
        self.assertTrue(res["verdict"].startswith("公開候補"))

    def test_blocker_overrides_score(self):
        b = [{"type": "fabricated-quote", "detail": "第2章の発言が書き起こしにない", "location": "第2章", "resolved": False}]
        code, res = self.run_score(scores(10, blockers=b))
        self.assertEqual(code, 2)
        self.assertTrue(res["verdict"].startswith("公開不可"))

    def test_template_placeholder_blocker_is_ignored(self):
        b = [{"type": "fabricated-quote", "detail": "", "location": "", "resolved": False}]
        code, res = self.run_score(scores(8, blockers=b))
        self.assertEqual(code, 0)

    def test_low_axis(self):
        code, res = self.run_score(scores(9, accuracy=5))
        self.assertEqual(res["verdict"], "要改善")

    def test_missing_axis(self):
        d = scores(8)
        d["axes"]["purpose"]["score"] = None
        code, res = self.run_score(d)
        self.assertTrue(res["verdict"].startswith("評価未完了"))

    def test_plateau(self):
        code, res = self.run_score(scores(7, discovery=9), history=[scores(7), scores(7, discovery=8)])
        self.assertEqual(res["history_totals"], [70, 71, 72])
        self.assertTrue(res["plateau"]["plateau"])
        self.assertEqual(code, 2)
        code2, res2 = self.run_score(scores(8), history=[scores(6), scores(7)])
        self.assertFalse(res2["plateau"]["plateau"])


class GuardTest(TempRepo):
    def setUp(self) -> None:
        super().setUp()
        self.aco("new", "foo", "--client", "株式会社テスト商事（架空）")

    def guard(self, *paths):
        code, out = self.aco("guard", "--json", "--paths", *[str(self.root / p) for p in paths])
        return code, json.loads(out)

    def test_blocks_project_data(self):
        code, res = self.guard("projects/foo/project.json")
        self.assertEqual(code, 2)
        code, res = self.guard("projects/_template/project.json")
        self.assertEqual(code, 0, res)

    def test_blocks_email_and_names(self):
        self.write("notes/a.md", "連絡先 taro.yamada" + "@" + "gmail.com\n")  # リポジトリに実在風のアドレスを残さない
        self.write("notes/b.md", "noreply@anthropic.com と info@example.com はよい\n")
        self.write("knowledge/x.md", "テスト商事の例\n")
        code, res = self.guard("notes/a.md", "notes/b.md", "knowledge/x.md")
        self.assertEqual(code, 2)
        blocked = {b["file"] for b in res["blocked"]}
        self.assertEqual(blocked, {"notes/a.md", "knowledge/x.md"})

    def test_transcript_filename(self):
        self.write("docs/取材の書き起こし.md", "架空\n")
        self.write("tests/scenarios/B/input/transcript.md", "架空\n")
        code, res = self.guard("docs/取材の書き起こし.md", "tests/scenarios/B/input/transcript.md")
        self.assertEqual([b["file"] for b in res["blocked"]], ["docs/取材の書き起こし.md"])

    def test_internal_manifest_and_public_mode(self):
        self.write("references/original/A.md", "原文\n")
        self.write_json("references/original/MANIFEST.json", {"version": 1, "files": [{"id": "A", "file": "A.md", "visibility": "internal", "sha256": ""}]})
        code, res = self.guard("references/original/A.md")
        self.assertEqual(code, 0, res)
        cfg = self.read_json("aco.config.json")
        cfg["repo_visibility"] = "public"
        self.write_json("aco.config.json", cfg)
        code, res = self.guard("references/original/A.md")
        self.assertEqual(code, 2)

    def test_install_hook(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        code, out = self.aco("guard", "--install-hook")
        self.assertEqual(code, 0, out)
        hook = self.root / ".git" / "hooks" / "pre-commit"
        self.assertTrue(hook.exists())
        self.assertTrue(os.access(str(hook), os.X_OK))


if __name__ == "__main__":
    unittest.main()
