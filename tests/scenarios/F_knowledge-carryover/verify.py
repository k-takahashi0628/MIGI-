#!/usr/bin/env python3
"""TEST F：知識の継承（案件台帳を次の記事に正しく反映し、別の案件と混ぜないか）を検査する。

使い方：python3 tests/scenarios/F_knowledge-carryover/verify.py [--target <フォルダ>] [--skip-lessons]

input/ は、そのまま ACO_ROOT として使える小さなリポジトリの形になっている
（aco.config.json・projects/<2 案件>・knowledge/approved-lessons/）。
検査は一時フォルダに複製して行い、input/ とリポジトリ本体の knowledge/ は変えない。
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_lib"))
import verifylib as v  # noqa: E402

P1, P2 = "nagisa-logistics", "hamanasu-shobo"
LEAKY_RULE = "ナギサ物流では、社内の呼び方を「メンバー」にそろえる"
CLEAN_RULE = "社内の呼び方は、シリーズの前の記事に合わせて一つにそろえる"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def repo_lessons_hash() -> str:
    h = hashlib.sha256()
    d = v.REPO / "knowledge" / "approved-lessons"
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def article_checks(rep: v.Report, article: str):
    body = v.strip_comments(article)
    l1 = load(HERE / "input" / "projects" / P1 / "ledger.json")
    l2 = load(HERE / "input" / "projects" / P2 / "ledger.json")

    missing = [x["text"] for x in l1["locked"] if x["text"] not in body]
    rep.check(not missing, "変更禁止の文（locked）がそのまま残っている", "",
              "見つからない：\n" + "\n".join(missing))

    used = [x["text"] for x in l1["rejected"] if x["text"] in body]
    rep.check(not used, "却下された表現（rejected）を使っていない", "", "使われている：" + "、".join(used))

    leaked = [x["term"] for x in l1["confidential"] if x["term"] in body]
    rep.check(not leaked, "公開禁止の語（confidential）が出ていない", "", "出ている：" + "、".join(leaked))

    broken = [f"{x['avoid']}→{x['use']}" for x in l1["rules"] if x["avoid"] in body]
    rep.check(not broken, "この案件の表記ルール（rules）に従っている", "", "守られていない：" + "、".join(broken))

    mixed = [f"{x['use']}（{P2} のルール {x['avoid']}→{x['use']}）" for x in l2["rules"] if x["use"] in body]
    rep.check(not mixed, "別の案件のルールが混ざっていない", "", "混ざっている：" + "、".join(mixed))

    heads = v.headings(article, 2)
    numbered = [h for h in heads if h.startswith("【")]
    rep.check(not numbered, "未承認の全体ルール候補（PL-001：見出しの頭に【】）を使っていない", "",
              "使われている見出し：" + "、".join(numbered))
    rep.check("倉庫" in body, "未承認の案件ルール候補（PR-1：倉庫→センター）を使っていない",
              "", "「倉庫」が一度も出てこない（未承認の置き換えをした可能性）")


def ledger_check(rep: v.Report, art_path: Path):
    if not v.aco_available():
        rep.err(f"aco ledger {P1} check に通る", "scripts/aco がない")
        return
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "root"
        shutil.copytree(HERE / "input", root)
        draft = Path(tmp) / "draft.md"
        shutil.copyfile(art_path, draft)
        code, out, err = v.run_aco(["ledger", P1, "check", str(draft)], root=root, cwd=root)
    if code == 0:
        rep.ok(f"aco ledger {P1} check に通る")
    elif code == 2:
        rep.ng(f"aco ledger {P1} check に通る", out.strip()[:800])
    else:
        rep.err(f"aco ledger {P1} check に通る", f"実行エラー：{(err or out).strip()[:300]}")


def is_usage_error(out: str, err: str) -> bool:
    return "usage:" in (out or "") or "usage:" in (err or "")


def propose(root: Path, text: str):
    """(終了コード, 候補ID or None, 出力) を返す。"""
    base = ["lessons", "propose", "--rule", text]
    r = v.run_aco(base + ["--why", "テスト（架空）", "--how", "テスト（架空）",
                          "--scope", "global", "--origin", "TEST F（架空）"], root=root, cwd=root)
    if r[0] != 0 and is_usage_error(r[1], r[2]):
        r = v.run_aco(base, root=root, cwd=root)
    code, out, err = r
    pid = None
    prop_path = root / "knowledge" / "approved-lessons" / "proposed.json"
    if code == 0:
        if prop_path.exists():
            for p in load(prop_path).get("proposals", []):
                if p.get("rule") == text:
                    pid = p.get("id")
        if pid is None:
            ids = re.findall(r"PL-\d+", out)
            pid = ids[-1] if ids else None
    return code, pid, (out or err).strip()


def approve(root: Path, pid: str, text: str):
    """(終了コード, lessons.json に入ったか, 出力) を返す。"""
    code, out, err = v.run_aco(["lessons", "approve", pid, "--by", "テスト"], root=root, cwd=root)
    les_path = root / "knowledge" / "approved-lessons" / "lessons.json"
    entered = les_path.exists() and text in les_path.read_text(encoding="utf-8")
    return code, entered, (out or err).strip()


def inject_proposal(root: Path, pid: str, text: str):
    """手で書き足された候補を想定して、proposed.json に直接入れる。"""
    prop_path = root / "knowledge" / "approved-lessons" / "proposed.json"
    data = load(prop_path)
    data.setdefault("proposals", []).append({
        "id": pid, "rule": text, "why": "テスト（架空）", "how": "", "scope": "global",
        "origin": "TEST F（架空）", "evidence": "", "status": "proposed", "date": "2026-11-11", "reason": ""})
    prop_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def lessons_checks(rep: v.Report):
    names = ["社名を含む全体ルール候補は、提案か承認の段階で拒否される",
             "台帳に直接書き足された社名入りの候補も、承認で拒否される",
             "社名を含まない全体ルール候補は承認される"]
    if not v.aco_available():
        for n in names:
            rep.err(n, "scripts/aco がない")
        return
    before = repo_lessons_hash()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "root"
        shutil.copytree(HERE / "input", root)
        les_path = root / "knowledge" / "approved-lessons" / "lessons.json"

        # 1. 提案（propose）→ 承認（approve）の通常の流れ
        code, pid, out = propose(root, LEAKY_RULE)
        if code != 0 and is_usage_error(out, ""):
            rep.err(names[0], f"propose の使い方が想定と違う：{out[:300]}")
        elif code != 0:
            entered = les_path.exists() and LEAKY_RULE in les_path.read_text(encoding="utf-8")
            rep.check(not entered, names[0], f"提案の段階で拒否（終了コード {code}）：{out[:200]}",
                      "提案は拒否されたが lessons.json に入っている")
        elif pid is None:
            rep.err(names[0], "propose した候補の ID が分からない")
        else:
            a_code, entered, a_out = approve(root, pid, LEAKY_RULE)
            rep.check(a_code != 0 and not entered, names[0],
                      f"承認の段階で拒否（終了コード {a_code}）：{a_out[:200]}",
                      f"承認された（終了コード {a_code}）：{a_out[:200]}")

        # 2. proposed.json に直接書き足された候補
        inject_proposal(root, "PL-900", LEAKY_RULE)
        a_code, entered, a_out = approve(root, "PL-900", LEAKY_RULE)
        rep.check(a_code != 0 and not entered, names[1],
                  f"拒否（終了コード {a_code}）：{a_out[:200]}",
                  f"承認された（終了コード {a_code}）：{a_out[:200]}")

        # 3. 社名を含まない候補
        code, pid, out = propose(root, CLEAN_RULE)
        if code != 0 or pid is None:
            rep.ng(names[2], f"propose が失敗（終了コード {code}）：{out[:300]}")
        else:
            a_code, entered, a_out = approve(root, pid, CLEAN_RULE)
            rep.check(a_code == 0 and entered, names[2], f"{pid}：{a_out[:200]}",
                      f"{pid}：終了コード {a_code}／{a_out[:200]}")
    rep.check(repo_lessons_hash() == before, "リポジトリ本体の knowledge/approved-lessons は変わっていない",
              "", "本体の lessons.json / proposed.json が書き換わった")


def main() -> int:
    args = v.parse_args(HERE, lambda p: p.add_argument("--skip-lessons", action="store_true",
                                                       help="全体ルールの承認の検査を飛ばす"))
    rep = v.Report("TEST F：知識の継承", args.target)
    art_path = args.target / "article.md"
    article = v.require(rep, art_path)
    if article is not None:
        article_checks(rep, article)
        ledger_check(rep, art_path)
    if not args.skip_lessons:
        lessons_checks(rep)
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
