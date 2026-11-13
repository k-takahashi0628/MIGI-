"""audit：否定の並列・分断・近接反復を拾い、普通の文で warn を出しすぎない。"""
from __future__ import annotations

import unittest

from aco_test_helpers import TempRepo
from aco_lib.audit import audit_text
from aco_lib.textutil import split_sentences


def codes(items, level=None):
    return [i["code"] for i in items if level is None or i["level"] == level]


NATURAL = """# 手順書を作り直した夜

佐伯は入社3年目の昨年、検査工程の手順書を作り直した。きっかけは、夜勤明けの班長から届いた一通のメモだった。

## 冷えた部品

「この順番だと、測る前に部品が冷えてしまう」。佐伯は翌週、温度計を持って夜勤に入った。測ってみると、手順書どおりに進めた場合、部品は規定より2度低い状態で検査台に載っていた。

手順を入れ替えた新しい版は、今年の4月から使われている。
"""


class AuditTest(unittest.TestCase):
    def test_negative_parallel(self):
        items = audit_text("# t\n\n当社は単なるメーカーではなく、未来をつくるパートナーだ。\n")
        self.assertIn("AI-06", codes(items, "warn"))

    def test_division_a1(self):
        items = audit_text("# t\n\n## 章\n\n新しく加わったメンバーが変化の大きいプロジェクトをリードし、毎日の仕組みはこれまでのメンバーがつくってきた。\n")
        self.assertIn("A1", codes(items, "warn"))

    def test_repetition_d4(self):
        items = audit_text("# t\n\n経験を積むほど、経験の幅が広がる。経験が次の仕事を呼ぶ。\n")
        self.assertIn("D4", codes(items, "warn"))

    def test_hiragana_ima_inside_verbs_is_not_d4(self):
        items = audit_text("# t\n\n設計をしていました。現場にいました。話していました。\n")
        self.assertFalse([i for i in items if i["code"] == "D4" and "いま" in i["excerpt"]])

    def test_natural_text_has_few_warnings(self):
        items = audit_text(NATURAL)
        self.assertLessEqual(len(codes(items, "warn")), 1, items)

    def test_formal_ending_and_emotion(self):
        items = audit_text("# t\n\n## 章\n\n本文。\n\n胸が熱くなるのではないでしょうか。これからも、さらなる挑戦を続けていきます。\n")
        c = codes(items, "warn")
        self.assertIn("AI-08", c)
        self.assertIn("AI-11", c)

    def test_question_markers(self):
        items = audit_text("# t\n\n## 章\n\n──働き方にも表れていますか？\n\n佐伯：はい。\n")
        self.assertIn("G3", codes(items, "warn"))
        self.assertIn("E1", codes(items))

    def test_ledger_checks(self):
        ledger = {
            "rejected": [{"id": "RJ-1", "text": "業界の常識を変える", "reason": "言い過ぎ"}],
            "confidential": [{"id": "CF-1", "term": "第二工場計画", "reason": "未公表"}],
            "locked": [{"id": "LK-1", "text": "現場の判断を、現場に任せる。"}],
            "rules": [{"id": "RL-1", "avoid": "仲間", "use": "メンバー"}],
        }
        text = "# t\n\n業界の常識を変える。第二工場計画もある。仲間と働く。\n"
        items = audit_text(text, ledger=ledger)
        errs = [i for i in items if i["level"] == "error"]
        self.assertEqual(len(errs), 3, errs)
        self.assertTrue(any(i["refs"] == ["RL-1"] and i["level"] == "warn" for i in items))

    def test_rule_avoid_inside_use_is_not_flagged(self):
        ledger = {"rules": [{"id": "RL-1", "avoid": "加わった", "use": "新しく加わった"}]}
        items = audit_text("# t\n\n新しく加わったメンバー。\n", ledger=ledger)
        self.assertFalse([i for i in items if i["code"] == "LEDGER"])

    def test_final_placeholders(self):
        items = audit_text("# t\n\n〇〇年に入社【要確認】。\n", final=True)
        self.assertEqual(len([i for i in items if i["code"] == "FINAL"]), 2)

    def test_sentence_split_keeps_quotes(self):
        s = split_sentences("彼は「今日は休む。明日は来る」と言った。次の文。")
        self.assertEqual([x for x, _ in s], ["彼は「今日は休む。明日は来る」と言った。", "次の文。"])


class AuditCliTest(TempRepo):
    def test_cli_exit_codes(self):
        p = self.write("a.md", NATURAL)
        code, out = self.aco("audit", str(p))
        self.assertEqual(code, 0, out)
        self.assertIn("兆候の一覧で、品質の判定ではない", out)
        p2 = self.write("b.md", "# t\n\nTBD\n")
        code2, _ = self.aco("audit", str(p2), "--final")
        self.assertEqual(code2, 2)


if __name__ == "__main__":
    unittest.main()
