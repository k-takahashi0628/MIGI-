"""ledger・lessons：台帳の照合、承認者なしの承認を拒む、全体ルールに案件名を入れない、案件を混ぜない。"""
from __future__ import annotations

import json
import unittest

from aco_test_helpers import TempRepo


class LedgerTest(TempRepo):
    def setUp(self) -> None:
        super().setUp()
        code, out = self.aco("new", "proj-a", "--client", "株式会社テスト商事（架空）", "--type", "employee-interview")
        self.assertEqual(code, 0, out)
        code, out = self.aco("new", "proj-b", "--client", "株式会社サンプル精工（架空）")
        self.assertEqual(code, 0, out)

    def test_add_and_check(self):
        self.assertEqual(self.aco("ledger", "proj-a", "add", "rules", "--avoid", "仲間", "--use", "メンバー", "--note", "社内の呼称")[0], 0)
        self.assertEqual(self.aco("ledger", "proj-a", "add", "rejected", "--text", "業界の常識を変える", "--reason", "言い過ぎ")[0], 0)
        self.assertEqual(self.aco("ledger", "proj-a", "add", "locked", "--text", "現場の判断を、現場に任せる。")[0], 0)
        self.assertEqual(self.aco("ledger", "proj-a", "add", "confidential", "--term", "第二工場計画")[0], 0)
        led = self.read_json("projects/proj-a/ledger.json")
        self.assertEqual(led["rules"][0]["id"], "RL-1")
        self.assertEqual(led["rejected"][0]["id"], "RJ-1")

        bad = self.write("bad.md", "# t\n\n仲間と業界の常識を変える。第二工場計画。\n")
        code, out = self.aco("ledger", "proj-a", "check", str(bad))
        self.assertEqual(code, 2, out)
        self.assertIn("RJ-1", out)
        self.assertIn("LK-1", out)
        self.assertIn("CF-1", out)
        self.assertIn("RL-1", out)

        good = self.write("good.md", "# t\n\n現場の判断を、現場に任せる。メンバーと進める。\n")
        code, out = self.aco("ledger", "proj-a", "check", str(good))
        self.assertEqual(code, 0, out)

    def test_approve_requires_by(self):
        payload = json.dumps({"avoid": "Web", "use": "WEB", "note": "前の記事に合わせる"}, ensure_ascii=False)
        code, out = self.aco("ledger", "proj-a", "add", "proposals", "--target", "rules", "--payload", payload, "--evidence", "前編の表記")
        self.assertEqual(code, 0, out)
        code, out = self.aco("ledger", "proj-a", "approve", "PR-1")
        self.assertEqual(code, 1, out)
        led = self.read_json("projects/proj-a/ledger.json")
        self.assertEqual(led["proposals"][0]["status"], "proposed")
        self.assertEqual(led["rules"], [])
        # 承認前の候補は brief で「規則として使わない」と出る
        code, out = self.aco("ledger", "proj-a", "brief")
        self.assertIn("承認待ち", out)
        self.assertNotIn("### 表記ルール", out)

        code, out = self.aco("ledger", "proj-a", "approve", "PR-1", "--by", "本人")
        self.assertEqual(code, 0, out)
        led = self.read_json("projects/proj-a/ledger.json")
        self.assertEqual(led["rules"][0]["avoid"], "Web")
        self.assertEqual(led["rules"][0]["approved_by"], "本人")
        self.assertEqual(led["proposals"][0]["status"], "approved")

    def test_brief_does_not_mix_projects(self):
        self.aco("ledger", "proj-a", "add", "rules", "--avoid", "仲間", "--use", "メンバー")
        self.aco("ledger", "proj-b", "add", "rules", "--avoid", "社員", "--use", "スタッフ")
        code, out = self.aco("ledger", "proj-a", "brief")
        self.assertEqual(code, 0)
        self.assertIn("仲間", out)
        self.assertNotIn("スタッフ", out)
        self.assertNotIn("サンプル精工", out)

    def test_close_pending(self):
        self.aco("ledger", "proj-a", "add", "pending", "--item", "数値の掲載可否", "--ask", "広報担当に確認")
        code, out = self.aco("ledger", "proj-a", "close", "PD-1", "--note", "掲載可")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read_json("projects/proj-a/ledger.json")["pending"][0]["status"], "closed")


EXPECTED_LESSONS_MD = """# 承認済みの全体ルール

このファイルは `python3 scripts/aco lessons render` で lessons.json から作る。直接編集しない。

## GL-001 ［official-article］ 直した場所は章の見出しと問いの文で示す
- なぜ：どこを直したか分からないと確認が止まる
- どうする：修正表に章・問い・今・直しを並べる
- 出どころ：制作者のフィードバック（承認：本人／%s）
"""


class LessonsTest(TempRepo):
    def setUp(self) -> None:
        super().setUp()
        self.aco("new", "proj-a", "--client", "株式会社テスト商事（架空）")
        proj = self.read_json("projects/proj-a/project.json")
        proj["people"] = [{"name": "山田", "role": "代表", "kind": "interviewee"}]
        self.write_json("projects/proj-a/project.json", proj)

    def test_propose_with_client_name_is_refused(self):
        code, out = self.aco("lessons", "propose", "--rule", "テスト商事では呼称をメンバーにする", "--scope", "global")
        self.assertEqual(code, 2, out)
        self.assertIn("テスト商事", out)
        code, out = self.aco("lessons", "propose", "--rule", "代表の言葉は山田さんの口調で", "--scope", "global")
        self.assertEqual(code, 2, out)

    def test_approve_flow_and_render(self):
        code, out = self.aco("lessons", "propose", "--rule", "直した場所は章の見出しと問いの文で示す", "--why", "どこを直したか分からないと確認が止まる",
                             "--how", "修正表に章・問い・今・直しを並べる", "--scope", "official-article", "--origin", "制作者のフィードバック")
        self.assertEqual(code, 0, out)
        self.assertIn("PL-001", out)
        code, out = self.aco("lessons", "approve", "PL-001")
        self.assertEqual(code, 1, out)
        code, out = self.aco("lessons", "approve", "PL-001", "--by", "本人")
        self.assertEqual(code, 0, out)
        L = self.read_json("knowledge/approved-lessons/lessons.json")
        self.assertEqual(L["lessons"][0]["id"], "GL-001")
        P = self.read_json("knowledge/approved-lessons/proposed.json")
        self.assertEqual(P["proposals"], [])
        md = (self.root / "knowledge/approved-lessons/LESSONS.md").read_text(encoding="utf-8")
        self.assertEqual(md, EXPECTED_LESSONS_MD % L["lessons"][0]["approved_date"])
        # 次の候補の番号は再利用しない
        code, out = self.aco("lessons", "propose", "--rule", "見出しは章の答えを言い切る", "--scope", "official-article")
        self.assertIn("PL-002", out)

    def test_approve_refuses_names_added_by_hand(self):
        self.write_json("knowledge/approved-lessons/proposed.json", {"version": 1, "proposals": [
            {"id": "PL-001", "rule": "テスト商事の表記に合わせる", "why": "", "how": "", "scope": "global", "origin": "", "evidence": "",
             "status": "proposed", "date": "", "reason": ""}]})
        code, out = self.aco("lessons", "approve", "PL-001", "--by", "本人")
        self.assertEqual(code, 2, out)
        self.assertEqual(self.read_json("knowledge/approved-lessons/lessons.json")["lessons"], [])

    def test_blocklist_names(self):
        self.write_json(".aco/blocklist.local.json", {"names": ["秘密食堂"]})
        code, out = self.aco("lessons", "propose", "--rule", "秘密食堂の記事では口語を使わない")
        self.assertEqual(code, 2, out)


if __name__ == "__main__":
    unittest.main()
