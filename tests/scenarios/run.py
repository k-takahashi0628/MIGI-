#!/usr/bin/env python3
"""シナリオテストをまとめて回す。

  python3 tests/scenarios/run.py controls   # 検査そのものの確認：good は合格、bad* は不合格になるか
  python3 tests/scenarios/run.py outputs    # 実際の出力（各 output/）の検査
  python3 tests/scenarios/run.py outputs A D # 一部だけ

終了コード：期待どおりなら 0、そうでなければ 2、検査できないものがあれば 1。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = {0: "合格", 1: "検査できず", 2: "不合格"}


def scenarios(only):
    for d in sorted(HERE.iterdir()):
        if d.is_dir() and (d / "verify.py").exists():
            if not only or d.name.split("_")[0] in only:
                yield d


def run(verify: Path, target: Path, quiet: bool) -> int:
    p = subprocess.run([sys.executable, str(verify), "--target", str(target)],
                       capture_output=True, text=True)
    if not quiet or p.returncode not in (0, 2):
        print(p.stdout.rstrip())
        if p.stderr.strip():
            print(p.stderr.rstrip())
    return p.returncode


def main(argv) -> int:
    mode = argv[0] if argv else "controls"
    only = set(a.upper() for a in argv[1:])
    rows, worst = [], 0
    for d in scenarios(only):
        if mode == "controls":
            for c in sorted((d / "controls").iterdir()):
                if not c.is_dir():
                    continue
                expect = 0 if c.name == "good" else 2
                got = run(d / "verify.py", c, quiet=True)
                ok = got == expect
                rows.append((d.name, c.name, NAMES.get(expect), NAMES.get(got, str(got)), "○" if ok else "×"))
                if got == 1:
                    worst = max(worst, 1)
                elif not ok:
                    worst = 2
        else:
            got = run(d / "verify.py", d / "output", quiet=False)
            rows.append((d.name, "output", "合格", NAMES.get(got, str(got)), "○" if got == 0 else "×"))
            worst = max(worst, got if got in (1, 2) else 2)
            print()
    print("| テスト | 対象 | 期待 | 結果 | 一致 |")
    print("|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(r) + " |")
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
