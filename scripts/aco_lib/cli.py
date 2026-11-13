"""コマンドの入口。`python3 scripts/aco --help`"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__

EPILOG = """終了コード：0＝問題なし／1＝使い方の誤り・実行エラー／2＝検査で止めるべきものが見つかった
詳しくは docs/architecture.md §6"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aco", description="ARTICLE CREATIVE OS の検査・管理コマンド", epilog=EPILOG,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version="aco " + __version__)
    sub = p.add_subparsers(dest="cmd", metavar="<サブコマンド>")

    s = sub.add_parser("new", help="案件フォルダを作る")
    s.add_argument("slug")
    s.add_argument("--client")
    s.add_argument("--type", help="ceo-business / ceo-organization / employee-interview / project-culture / company-intro / other")
    s.add_argument("--title")

    s = sub.add_parser("status", help="どの工程まで済んだか・次の一手")
    s.add_argument("slug")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("audit", help="AI 的な兆候と機械で拾える負け筋（品質の判定ではない）")
    s.add_argument("file")
    s.add_argument("--project", help="案件スラッグ（台帳と照合する）")
    s.add_argument("--final", action="store_true", help="仮置き文字・要確認の印を error にする")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("structure", help="章ごとの字数・問いの数・重複した問い・リードと締め")
    s.add_argument("file")
    s.add_argument("--compare", help="前の記事（字数の釣り合い）")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("quotes", help="記事の発言を書き起こしと照合（A〜E）")
    s.add_argument("article")
    s.add_argument("--transcript", action="append", help="書き起こし（複数可）")
    s.add_argument("--speaker", help="ラベルのない答えの話し手（既定は project.json の people[0]）")
    s.add_argument("--project", help="案件スラッグ（話し手の既定値と、台帳の表記ルールの言い換えに使う）")
    s.add_argument("--interviewer", action="append", help="聞き手のラベルを足す")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("init", help="今のフォルダ（または指定のフォルダ）を作業フォルダにする（projects/・.aco/・aco.config.json）")
    s.add_argument("path", nargs="?")

    s = sub.add_parser("where", help="エンジンと作業フォルダの場所を出す")

    s = sub.add_parser("numbers", help="記事の全文の数値が素材にあるか（地の文も含む）")
    s.add_argument("file")
    s.add_argument("--source", action="append", help="素材（書き起こし・事実メモ・前の記事。複数可）")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("scope", help="指定範囲の外の差分を検査（必要なら元に戻す）")
    s.add_argument("before")
    s.add_argument("after")
    s.add_argument("--allow", action="append", help="heading:<語> / section:<語> / chapter-heading:<N> / chapter:<N> / lines:<a>-<b> / contains:<語>（複数可）")
    s.add_argument("--restore", help="範囲外を元に戻した本文の出力先")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("revtable", help="修正表のひな形（章・問い・今・直し）")
    s.add_argument("before")
    s.add_argument("after")
    s.add_argument("--out")

    s = sub.add_parser("ledger", help="案件台帳：add / list / close / approve / reject / check / brief")
    s.add_argument("slug")
    s.add_argument("op")
    s.add_argument("rest", nargs="*")
    for opt in ("text", "reason", "source", "context", "by", "item", "ask", "owner", "avoid", "use", "note", "claim",
                "status", "term", "decision", "target", "payload", "evidence", "date"):
        s.add_argument("--" + opt)
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("lessons", help="全体ルール：propose / approve / reject / list / render")
    s.add_argument("op")
    s.add_argument("rest", nargs="*")
    for opt in ("rule", "why", "how", "scope", "origin", "evidence", "by", "reason"):
        s.add_argument("--" + opt)
    s.add_argument("--all", action="store_true")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("score", help="10 軸の集計・公開不可・頭打ち")
    s.add_argument("file")
    s.add_argument("--history", nargs="*", help="前の scores.json（古い順）")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("guard", help="Git に入れる前の公開範囲の検査")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--staged", action="store_true", help="ステージ済みのファイル（既定）")
    g.add_argument("--all", action="store_true", help="Git が扱う全ファイル")
    g.add_argument("--paths", nargs="+", help="指定したファイル・フォルダ")
    g.add_argument("--install-hook", action="store_true", help=".git/hooks/pre-commit に組み込む")
    s.add_argument("--force", action="store_true")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("validate", help="リポジトリ自体の検査")
    s.add_argument("--json", action="store_true")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 1
    from . import audit, guard, ledger, lessons, numbers, project, quotes, revtable, scope, score, structure, validate

    table = {
        "new": project.cmd_new, "status": project.cmd_status, "init": project.cmd_init, "where": project.cmd_where, "audit": audit.cmd_audit, "structure": structure.cmd_structure,
        "quotes": quotes.cmd_quotes, "numbers": numbers.cmd_numbers, "scope": scope.cmd_scope, "revtable": revtable.cmd_revtable, "ledger": ledger.cmd_ledger,
        "lessons": lessons.cmd_lessons, "score": score.cmd_score, "guard": guard.cmd_guard, "validate": validate.cmd_validate,
    }
    try:
        return int(table[args.cmd](args) or 0)
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code)
            return 1
        raise
    except KeyboardInterrupt:
        return 1
