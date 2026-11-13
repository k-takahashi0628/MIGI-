"""会社フォルダ：projects/<会社>/<案件>。会社の台帳はその会社の全案件に効き、ほかの会社には効かない。"""
from __future__ import annotations

import json
import unittest

from aco_test_helpers import TempRepo


class ClientFolderTest(TempRepo):
    def setUp(self) -> None:
        super().setUp()
        self.write_json("projects/_client_template/client.json", {"slug": "", "client": {"name": "", "aliases": []}, "knowledge": [], "notes": "", "created": ""})
        code, out = self.aco("new", "acme/no1", "--client", "株式会社アクメ（架空）", "--type", "employee-interview")
        self.assertEqual(code, 0, out)
        self.assertIn("会社フォルダを作った", out)
        code, out = self.aco("new", "acme/no2")
        self.assertEqual(code, 0, out)
        code, out = self.aco("new", "other/no1", "--client", "株式会社アザー（架空）")
        self.assertEqual(code, 0, out)

    def test_client_folder_and_inherited_name(self):
        cj = self.read_json("projects/acme/client.json")
        self.assertEqual(cj["client"]["name"], "株式会社アクメ（架空）")
        pj = self.read_json("projects/acme/no2/project.json")
        self.assertEqual(pj["client"]["name"], "株式会社アクメ（架空）")
        self.assertTrue((self.root / "projects/acme/client-ledger.json").exists())

    def test_client_rules_apply_to_all_cases_of_that_client_only(self):
        self.assertEqual(self.aco("ledger", "acme", "add", "rules", "--avoid", "仲間", "--use", "メンバー")[0], 0)
        self.assertEqual(self.aco("ledger", "acme", "add", "confidential", "--term", "新工場計画")[0], 0)
        self.assertEqual(self.read_json("projects/acme/client-ledger.json")["rules"][0]["avoid"], "仲間")
        bad = self.write("bad.md", "# t\n\n仲間と新工場計画を進める。\n")
        for case in ("acme/no1", "acme/no2"):
            code, out = self.aco("ledger", case, "check", str(bad))
            self.assertEqual(code, 2, out)
            code, out = self.aco("audit", str(bad), "--project", case)
            self.assertIn("新工場計画", out)
        # ほかの会社の案件には効かない
        code, out = self.aco("ledger", "other/no1", "check", str(bad))
        self.assertEqual(code, 0, out)

    def test_brief_shows_client_ledger_and_not_other_client(self):
        self.aco("ledger", "acme", "add", "rules", "--avoid", "仲間", "--use", "メンバー")
        self.aco("ledger", "other", "add", "rules", "--avoid", "メンバー", "--use", "スタッフ")
        code, out = self.aco("ledger", "acme/no1", "brief")
        self.assertEqual(code, 0, out)
        self.assertIn("会社の台帳：acme", out)
        self.assertIn("「仲間」→「メンバー」", out)
        self.assertNotIn("スタッフ", out)

    def test_quotes_uses_client_rules(self):
        self.aco("ledger", "acme", "add", "rules", "--avoid", "仲間", "--use", "メンバー")
        tr = self.write("tr.md", "佐伯：チームの仲間と、毎朝ミーティングをしています。\n")
        art = self.write("a.md", "# t\n\n## 章\n\n── 問い。\n\n佐伯：チームのメンバーと、毎朝ミーティングをしています。\n")
        code, out = self.aco("quotes", str(art), "--transcript", str(tr), "--project", "acme/no1")
        self.assertEqual(code, 0, out)

    def test_client_names_are_sensitive(self):
        code, out = self.aco("lessons", "propose", "--rule", "株式会社アクメ（架空）では見出しを短くする", "--why", "x", "--how", "y", "--scope", "global")
        self.assertEqual(code, 2, out)

    def test_bad_slug(self):
        code, out = self.aco("new", "acme/no1/extra")
        self.assertEqual(code, 1, out)


if __name__ == "__main__":
    unittest.main()
