"""structure・revtable・new/status・validate。"""
from __future__ import annotations

import hashlib
import json
import unittest

from aco_test_helpers import TempRepo
from aco_lib import revtable, structure

ART = """# 判断を現場に置く

リード。現場の判断はどう動いているのか。

## 第1章 入社まで

── 入社のきっかけは何でしょうか。

佐伯：設計をしていました。

── 決め手は何でしょうか。

佐伯：現場に近いことです。

## 第2章 現場の判断

── 現場ではどう決めていますか。

佐伯：班長が決めます。

## 第3章 これから

佐伯：もっと現場で決められるようにしたいです。現場の判断を大事にしています。
"""


class StructureTest(unittest.TestCase):
    def test_chapters_and_questions(self):
        res = structure.analyze(ART)
        self.assertEqual([c["questions"] for c in res["chapters"]], [2, 1, 0])
        self.assertEqual(res["chapters"][0]["speakers"], ["佐伯"])
        self.assertFalse([f for f in res["findings"] if f["level"] == "error"])

    def test_duplicate_question(self):
        dup = ART.replace("── 現場ではどう決めていますか。", "── 入社のきっかけは何でしょうか。")
        res = structure.analyze(dup)
        self.assertTrue([f for f in res["findings"] if f["code"] == "G4" and f["level"] == "error"])

    def test_long_chapter(self):
        long = ART.replace("佐伯：班長が決めます。", "佐伯：" + "班長が決めます。" * 40)
        res = structure.analyze(long)
        self.assertTrue([f for f in res["findings"] if f["code"] == "F7"])

    def test_closing_not_matching_lead(self):
        txt = ART.replace("佐伯：もっと現場で決められるようにしたいです。現場の判断を大事にしています。", "佐伯：ありがとうございました。")
        res = structure.analyze(txt)
        self.assertTrue([f for f in res["findings"] if f["code"] == "F5"])


class RevtableTest(unittest.TestCase):
    def test_context(self):
        after = ART.replace("佐伯：班長が決めます。", "佐伯：ラインを止めるかは班長が決めます。")
        rows = revtable.build(ART, after)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["chapter"], "第2章 現場の判断")
        self.assertEqual(rows[0]["question"], "現場ではどう決めていますか。")
        md = revtable.to_markdown(rows)
        self.assertIn("| 1 | 章「第2章 現場の判断」／問い「現場ではどう決めていますか。」 |", md)


class ProjectTest(TempRepo):
    def test_new_and_status(self):
        code, out = self.aco("new", "sample-a", "--client", "株式会社ミズハ測器（架空）", "--type", "employee-interview", "--title", "仮題")
        self.assertEqual(code, 0, out)
        pj = self.read_json("projects/sample-a/project.json")
        self.assertEqual(pj["slug"], "sample-a")
        self.assertEqual(pj["client"]["name"], "株式会社ミズハ測器（架空）")
        self.assertEqual(pj["visibility"], "confidential")
        self.assertEqual(self.read_json("projects/sample-a/ledger.json")["rules"], [])
        self.assertEqual(self.aco("new", "sample-a")[0], 1)
        self.assertEqual(self.aco("new", "Bad_Slug")[0], 1)
        code, out = self.aco("status", "sample-a", "--json")
        st = json.loads(out)
        self.assertIn("目的設計", st["next"])
        for rel in ("work/01_brief.md", "work/02_source-audit.md", "work/03_insight.md", "work/04_structure.md", "drafts/v1.md"):
            self.write("projects/sample-a/" + rel, "x\n")
        st = json.loads(self.aco("status", "sample-a", "--json")[1])
        self.assertIn("v1 の編集レビュー", st["next"])
        self.write("projects/sample-a/work/reviews/v1_brand.md", "x\n")
        st = json.loads(self.aco("status", "sample-a", "--json")[1])
        self.assertIn("事実確認", st["next"])


AGENT = """---
name: fact-checker
description: 事実を確かめる
tools: Read, Grep, Bash
model: inherit
skills:
  - article-fact-check
---

参照：`knowledge/failure-patterns/official-article.md` の C1 と AI-06。
"""
SKILL = """---
name: article-fact-check
description: 事実と発言を照合する
argument-hint: "[案件スラッグ]"
---

手順は `templates/fact-check-table.md` を使う。詳しくは [基準](criteria.md)。
"""


class ValidateTest(TempRepo):
    def make_valid(self):
        self.write("agents/fact-checker.md", AGENT)
        self.write("skills/article-fact-check/SKILL.md", SKILL)
        self.write("skills/article-fact-check/criteria.md", "基準\n")
        self.write("templates/fact-check-table.md", "表\n")
        self.write("knowledge/failure-patterns/official-article.md", "### C1. 話していないことをセリフにする\n")
        self.write("knowledge/failure-patterns/ai-writing-signs.md", "## AI-06 否定の並列\n")
        self.write("references/original/A.md", "原文\n")
        h = hashlib.sha256("原文\n".encode("utf-8")).hexdigest()
        self.write_json("references/original/MANIFEST.json", {"version": 1, "files": [{"id": "A", "file": "A.md", "sha256": h, "visibility": "internal"}]})

    def test_valid_repo(self):
        self.make_valid()
        code, out = self.aco("validate")
        self.assertEqual(code, 0, out)

    def test_errors(self):
        self.make_valid()
        self.write("agents/wrong-name.md", AGENT.replace("article-fact-check", "no-such-skill"))
        self.write("CLAUDE.md", "`workflows/nothing.md` を読む。A7 と AI-18 と D2 を見る。\n")
        self.write("skills/bad/SKILL.md", "---\nname: bad\ndescription: " + "あ" * 1100 + "\ndisable-model-invocation: true\n---\n")
        self.write("references/original/A.md", "書き換えた\n")
        code, out = self.aco("validate", "--json")
        self.assertEqual(code, 2)
        errs = "\n".join(json.loads(out)["errors"])
        for needle in ("ファイル名", "no-such-skill", "workflows/nothing.md", "A7", "AI-18", "D2", "1,024", "disable-model-invocation", "sha256"):
            self.assertIn(needle, errs)


if __name__ == "__main__":
    unittest.main()
