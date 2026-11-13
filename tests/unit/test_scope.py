"""scope：指定範囲の外の差分を 1 文字・改行 1 つまで検出し、元に戻せるか。"""
from __future__ import annotations

import json
import unittest

from aco_test_helpers import TempRepo

BEFORE = """# タイトル

リード。

## 第1章 はじまり

本文1。

── 問い1でしょうか。

答え1。

## 第2章 なかみ

本文2。

## 第3章 これから

本文3。
"""


class ScopeTest(TempRepo):
    def run_scope(self, after: str, *allow: str, restore: bool = False):
        b = self.write("before.md", BEFORE)
        a = self.write("after.md", after)
        args = ["scope", str(b), str(a)]
        for x in allow:
            args += ["--allow", x]
        if restore:
            args += ["--restore", str(self.root / "restored.md")]
        args.append("--json")
        code, out = self.aco(*args)
        return code, json.loads(out) if out.strip().startswith("{") else out

    def test_heading_only_change_passes(self):
        after = BEFORE.replace("## 第3章 これから", "## 第3章 次の十年へ")
        code, res = self.run_scope(after, "heading:第3章")
        self.assertEqual(code, 0)
        self.assertEqual(len(res["in_scope"]), 1)
        self.assertEqual(res["violations"], [])

    def test_one_char_outside_is_caught_and_restored(self):
        after = BEFORE.replace("## 第3章 これから", "## 第3章 次の十年へ").replace("本文1。", "本文1、")
        code, res = self.run_scope(after, "heading:第3章", restore=True)
        self.assertEqual(code, 2)
        self.assertEqual(len(res["violations"]), 1)
        self.assertTrue(res["restored_ok"])
        restored = (self.root / "restored.md").read_text(encoding="utf-8")
        self.assertEqual(restored, BEFORE.replace("## 第3章 これから", "## 第3章 次の十年へ"))

    def test_trailing_newline_change_is_caught(self):
        after = BEFORE.replace("## 第3章 これから", "## 第3章 次の十年へ").rstrip("\n")
        code, res = self.run_scope(after, "heading:第3章")
        self.assertEqual(code, 2)
        self.assertEqual(res["violations"][0]["kind"], "置き換え")

    def test_insert_after_heading_is_out_of_scope_for_heading_only(self):
        after = BEFORE.replace("## 第3章 これから\n", "## 第3章 これから\n追加の一文。\n")
        code, res = self.run_scope(after, "heading:第3章")
        self.assertEqual(code, 2)
        self.assertEqual(res["violations"][0]["kind"], "追加")

    def test_section_scope_allows_inside_and_append(self):
        after = BEFORE.replace("本文2。\n", "本文2を直した。\n\n足した段落。\n")
        code, res = self.run_scope(after, "section:第2章")
        self.assertEqual(code, 0, res)
        after2 = after.replace("本文3。", "本文3を変えた。")
        code2, res2 = self.run_scope(after2, "section:第2章")
        self.assertEqual(code2, 2)

    def test_lines_scope(self):
        after = BEFORE.replace("本文1。", "本文1を変えた。")
        code, _ = self.run_scope(after, "lines:7-7")
        self.assertEqual(code, 0)
        after2 = BEFORE.replace("本文1。\n", "本文1。\n増えた行。\n")
        code2, _ = self.run_scope(after2, "lines:7-7")
        self.assertEqual(code2, 2)

    def test_contains_scope(self):
        after = BEFORE.replace("答え1。", "答え1を直した。")
        code, _ = self.run_scope(after, "contains:答え1")
        self.assertEqual(code, 0)

    def test_no_change_in_scope_warns(self):
        code, res = self.run_scope(BEFORE, "heading:第3章")
        self.assertEqual(code, 0)
        self.assertIn("変わっていない", res["warning"])

    def test_chapter_heading_by_number(self):
        after = BEFORE.replace("## 第3章 これから", "## 第3章 次の十年へ")
        code, res = self.run_scope(after, "chapter-heading:3")
        self.assertEqual(code, 0)
        self.assertEqual(len(res["in_scope"]), 1)
        # 本文の 1 文字は章の見出しの範囲外
        after2 = after.replace("本文3。", "本文3、")
        code2, res2 = self.run_scope(after2, "chapter-heading:3")
        self.assertEqual(code2, 2)
        self.assertEqual(len(res2["violations"]), 1)

    def test_chapter_whole_by_number(self):
        after = BEFORE.replace("本文2。", "本文2を直した。")
        code, res = self.run_scope(after, "chapter:2")
        self.assertEqual(code, 0)
        code2, _ = self.run_scope(after, "chapter:3")
        self.assertEqual(code2, 2)

    def test_unknown_heading_is_usage_error(self):
        code, out = self.run_scope(BEFORE, "heading:第9章")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
