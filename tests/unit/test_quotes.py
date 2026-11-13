"""quotes：作ったセリフは D、数値違いは E、整文は A/B、聞き手の発言は根拠にしない。"""
from __future__ import annotations

import unittest

from aco_test_helpers import TempRepo
from aco_lib import quotes

TRANSCRIPT = """[00:00:03] 聞き手：入社のきっかけは何でしょうか。
[00:00:10] 佐伯：えー、前職では、まあ、10年間ずっと設計をしていました。
で、やっぱり現場に近い仕事がしたかったんです。
聞き手：現場ではチームで改善を進めているそうですね。
佐伯：あの、ラインを止めるかどうかは班長が決めます。去年は3回止めました。
佐伯：止めた日は、その日のうちに全員で原因を話し合います。
"""


def article(body: str) -> str:
    return "# 見出し\n\n## 章\n\n── 問いでしょうか。\n\n" + body + "\n"


class QuotesTest(unittest.TestCase):
    def grade(self, body: str):
        res = quotes.check(article(body), [TRANSCRIPT])
        return [r["grade"] for r in res["rows"]], res

    def test_verbatim_and_cleaned_are_a_or_b(self):
        g, _ = self.grade("佐伯：前職では10年間、ずっと設計をしていました。現場に近い仕事がしたかったんです。")
        self.assertTrue(all(x in ("A", "B") for x in g), g)

    def test_fabricated_quote_is_d(self):
        g, _ = self.grade("佐伯：私たちの挑戦は、地域の未来を照らす灯台のような存在だと信じています。")
        self.assertEqual(g, ["D"])

    def test_number_mismatch_is_e(self):
        g, res = self.grade("佐伯：ラインを止めるかどうかは班長が決めます。去年は5回止めました。")
        self.assertIn("E", g)
        self.assertIn("5回", res["rows"][-1]["reason"])

    def test_kanji_number_matches_arabic(self):
        g, _ = self.grade("佐伯：前職では十年間、ずっと設計をしていました。")
        self.assertNotIn("E", g)

    def test_interviewer_words_are_not_support(self):
        g, _ = self.grade("佐伯：現場ではチームで改善を進めています。")
        self.assertIn(g[0], ("D", "E", "C"))
        self.assertNotIn(g[0], ("A", "B"))

    def test_label_is_inherited_within_answer(self):
        res = quotes.check(article("佐伯：ラインを止めるかどうかは班長が決めます。\n\n止めた日は、その日のうちに全員で原因を話し合います。"), [TRANSCRIPT])
        self.assertEqual([r["speaker"] for r in res["rows"]], ["佐伯", "佐伯"])
        self.assertEqual([r["grade"] for r in res["rows"]], ["A", "A"])

    def test_narration_quote_is_checked(self):
        text = "# 見出し\n\n## 章\n\n佐伯さんは「ラインを止めるかどうかは班長が決めます」と話す。そして「毎朝五時に全員で体操をしています」とも言う。\n"
        res = quotes.check(text, [TRANSCRIPT])
        grades = [r["grade"] for r in res["rows"]]
        self.assertEqual(grades[0], "A")
        self.assertIn(grades[1], ("D", "E"))


class QuotesCliTest(TempRepo):
    def test_exit_code_2_on_d(self):
        a = self.write("a.md", article("佐伯：私たちの挑戦は、地域の未来を照らす灯台のような存在だと信じています。"))
        t = self.write("t.md", TRANSCRIPT)
        code, out = self.aco("quotes", str(a), "--transcript", str(t))
        self.assertEqual(code, 2, out)
        self.assertIn("要確認", out)

    def test_exit_code_0_when_supported(self):
        a = self.write("a.md", article("佐伯：ラインを止めるかどうかは班長が決めます。去年は3回止めました。"))
        t = self.write("t.md", TRANSCRIPT)
        code, out = self.aco("quotes", str(a), "--transcript", str(t))
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()


class QuotesExtraTest(unittest.TestCase):
    def test_separator_returns_to_narration(self):
        body = ("佐伯：ラインを止めるかどうかは班長が決めます。\n\n---\n\n"
                "この工場では、止めた日のうちに原因を話し合うことが決まりになっている。")
        res = quotes.check(article(body), [TRANSCRIPT])
        speakers = [r["speaker"] for r in res["rows"]]
        # 区切りの後ろの地の文は発言として照合しない
        self.assertEqual(len(res["rows"]), 1, speakers)

    def test_ledger_rule_equivalent_is_not_e(self):
        tr = "佐伯：チームの仲間と、毎朝ミーティングをしています。\n"
        art = article("佐伯：チームのメンバーと、毎朝ミーティングをしています。")
        g0 = [r["grade"] for r in quotes.check(art, [tr])["rows"]]
        g1 = [r["grade"] for r in quotes.check(art, [tr], equivalents=[("仲間", "メンバー")])["rows"]]
        self.assertIn("E", g0)
        self.assertTrue(all(x in ("A", "B") for x in g1), g1)

    def test_bullet_quote_style_transcript(self):
        tr = "- 佐伯「ラインを止めるかどうかは班長が決めます」\n"
        g = [r["grade"] for r in quotes.check(article("佐伯：ラインを止めるかどうかは班長が決めます。"), [tr])["rows"]]
        self.assertEqual(g, ["A"])


class NumbersTest(unittest.TestCase):
    def test_narration_number_not_in_source_is_caught(self):
        from aco_lib import numbers
        art = "# 題\n\nリード。創業は1987年、社員は84人。\n\n## 章\n\n年に3回、ラインを止めた。\n"
        res = numbers.check(art, ["設立：1987年。社員数：84名。\n佐伯：去年は3回止めました。"])
        self.assertEqual(res["missing"], [])
        res2 = numbers.check(art.replace("84人", "120人"), ["設立：1987年。社員数：84名。\n佐伯：去年は3回止めました。"])
        self.assertEqual([m["value"] for m in res2["missing"]], ["120"])


class QuotesMarkerTest(unittest.TestCase):
    def test_markers_in_answer_are_not_quotes(self):
        body = "佐伯：ラインを止めるかどうかは班長が決めます。【要確認：去年止めた回数を本人に確かめる（3回か5回か）】"
        res = quotes.check(article(body), [TRANSCRIPT])
        self.assertEqual([r["grade"] for r in res["rows"]], ["A"])
