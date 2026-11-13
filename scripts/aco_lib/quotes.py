"""記事の発言を書き起こしと照合し、A〜E で判定する。

A：書き起こしにほぼ同じ文がある
B：書き起こしから言える（整文・要約で要素が一致）
C：言い換えで意味・範囲が変わった可能性がある（要確認）
D：書き起こしに根拠が見つからない（作ったセリフの疑い）
E：数値・固有名（カタカナ語）が書き起こしと合わない
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import paths
from .textutil import (
    Utterance,
    bigrams,
    content_tokens,
    extract_numbers,
    katakana_words,
    md_cell,
    nfkc,
    normalize,
    numbers_supported,
    parse_document,
    parse_transcript,
    quoted_segments,
    same_person,
    short,
    split_sentences,
)

MIN_CHARS = 5
GRADE_NOTE = {
    "A": "ほぼ原文",
    "B": "整文の範囲（要素一致）",
    "C": "言い換え・要約。意味と範囲を本人の言葉と並べて確認",
    "D": "書き起こしに根拠なし。作ったセリフでないか確認するまで公開しない",
    "E": "数値・固有名が書き起こしと合わない",
}


class Candidate:
    __slots__ = ("raw", "norm", "line", "bg", "parts")

    def __init__(self, parts: List[Tuple[int, str]]) -> None:
        self.parts = parts
        self.raw = "".join(t for _, t in parts)
        self.norm = normalize(self.raw)
        self.line = parts[0][0]
        self.bg = bigrams(self.norm)


def build_candidates(utts: Sequence[Utterance]) -> Dict[str, List[Candidate]]:
    """話し手ごとに、1 発言と連続 2〜3 発言のつなぎを候補にする。"""
    by_spk: Dict[str, List[Utterance]] = {}
    for u in utts:
        if u.is_interviewer:
            continue
        by_spk.setdefault(u.speaker, []).append(u)
    cands: Dict[str, List[Candidate]] = {}
    for spk, us in by_spk.items():
        lst: List[Candidate] = []
        for i in range(len(us)):
            for k in (1, 2, 3):
                if i + k <= len(us):
                    lst.append(Candidate([(u.line, u.text) for u in us[i : i + k]]))
        cands[spk] = lst
    return cands


def article_units(text: str, default_speaker: Optional[str], known: Sequence[str]) -> List[Dict[str, Any]]:
    blocks = parse_document(text, default_speaker=default_speaker)
    units: List[Dict[str, Any]] = []
    for b in blocks:
        if b.kind != "para":
            continue
        if b.is_answer:
            for s, off in split_sentences(b.text):
                units.append({"speaker": b.speaker, "text": s, "line": b.line_of(b.label_len + off), "kind": "answer"})
        else:
            for seg, off in quoted_segments(b.raw, 10):
                spk = None
                before = b.raw[max(0, off - 40) : off]
                for name in known:
                    if name and name in before:
                        spk = name
                for s, soff in split_sentences(seg):
                    units.append({"speaker": spk, "text": s, "line": b.line_of(off + soff), "kind": "quote"})
    return units


CONTENT_CHAR = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff々〆ヵヶ\u30a1-\u30faー0-9A-Za-z]")


def content_bigrams(norm: str) -> set:
    """2 文字とも漢字・カタカナ・数字・英字の 2-gram（助詞・語尾をまたぐものを除く）。"""
    return {g for g in bigrams(norm) if len(g) == 2 and CONTENT_CHAR.match(g[0]) and CONTENT_CHAR.match(g[1])}


def grade_sentence(sent: str, cands: List[Candidate], speaker_text_norm: str, speaker_nums) -> Dict[str, Any]:
    ns = normalize(sent)
    sbg = bigrams(ns)
    cbg = content_bigrams(ns)
    use_c = len(cbg) >= 3
    best: Optional[Candidate] = None
    best_key = (-1.0, -1.0, 0)
    best_all = 0.0
    best_c = 0.0
    for c in cands:
        v_all = len(sbg & c.bg) / len(sbg) if sbg else 0.0
        v_c = (len(cbg & c.bg) / len(cbg)) if use_c else v_all
        key = (v_c, v_all, -len(c.norm))
        if key > best_key:
            best_key = key
            best = c
            best_all = v_all
            best_c = v_c
    shown_line, shown_text = (None, "")
    if best is not None:
        shown_line, shown_text = max(best.parts, key=lambda pt: len((cbg or sbg) & bigrams(normalize(pt[1]))))
    aligned = 0.0
    if best is not None and ns:
        sm = difflib.SequenceMatcher(None, ns, best.norm, autojunk=False)
        aligned = sum(m.size for m in sm.get_matching_blocks()) / len(ns)
    toks = content_tokens(sent)
    if toks and best is not None:
        bn = best.norm
        cov = sum(1 for t in toks if normalize(t) in bn) / len(toks)
    else:
        cov = best_c
    missing_nums = numbers_supported(extract_numbers(sent), speaker_nums)
    missing_kata = [w for w in katakana_words(sent) if normalize(w) not in speaker_text_norm]
    if best_c >= 0.75 and best_all >= 0.75:
        grade = "A"
    elif best_c >= 0.5 and cov >= 0.7:
        grade = "B"
    elif best_c >= 0.3 or cov >= 0.5:
        grade = "C"
    else:
        grade = "D"
    if (missing_nums or missing_kata) and grade != "D":
        grade = "E"
    reason = ""
    if missing_nums:
        reason += "書き起こしにない数値：" + "・".join(v + c for v, c in missing_nums) + "。"
    if missing_kata:
        reason += "書き起こしにない語：" + "・".join(missing_kata) + "。"
    return {
        "grade": grade,
        "similarity": round(best_c, 2),
        "similarity_all": round(best_all, 2),
        "aligned": round(aligned, 2),
        "coverage": round(cov, 2),
        "source_line": shown_line,
        "source": short(shown_text, 40) if best else "",
        "reason": reason,
    }


def check(article_text: str, transcript_texts: Sequence[str], default_speaker: Optional[str] = None, interviewers: Sequence[str] = (), equivalents: Sequence[Tuple[str, str]] = ()) -> Dict[str, Any]:
    """equivalents：台帳の表記ルール（avoid, use）。記事の use は書き起こしの avoid と同じ語として照合する。"""
    utts: List[Utterance] = []
    for t in transcript_texts:
        utts += parse_transcript(t, interviewers)
    cands = build_candidates(utts)
    speakers = list(cands.keys())
    all_cands = [c for lst in cands.values() for c in lst]
    spk_text: Dict[str, str] = {}
    spk_nums: Dict[str, list] = {}
    for u in utts:
        if u.is_interviewer:
            continue
        spk_text[u.speaker] = spk_text.get(u.speaker, "") + u.text
    for spk, t in spk_text.items():
        spk_nums[spk] = extract_numbers(t)
    all_text = "".join(spk_text.values())
    all_nums = extract_numbers(all_text)

    # 【要確認：…】【要取材：…】【提案：…】は書き手の印なので、発言として照合しない
    article_text = re.sub(r"【(?:要確認|要取材|提案)[^】]*】", lambda m: " " * len(m.group(0)), article_text)
    units = article_units(article_text, default_speaker, speakers)
    rows: List[Dict[str, Any]] = []
    skipped = 0
    for u in units:
        if len(normalize(u["text"])) < MIN_CHARS:
            skipped += 1
            continue
        matched = [s for s in speakers if same_person(u["speaker"], s)]
        if matched:
            spk = matched[0]
            pool = cands[spk]
            text_norm = normalize(spk_text[spk])
            nums = spk_nums[spk]
            note = ""
        else:
            pool = all_cands
            text_norm = normalize(all_text)
            nums = all_nums
            note = "話し手が書き起こしで特定できないため全員の発言と照合。" if u["speaker"] not in (None, "不明") else "話し手不明。全員の発言と照合。"
        g = grade_sentence(u["text"], pool, text_norm, nums)
        alt = u["text"]
        for avoid, use in equivalents:
            if avoid and use and use in alt:
                alt = alt.replace(use, avoid)
        if alt != u["text"]:
            g2 = grade_sentence(alt, pool, text_norm, nums)
            if "ABCDE".index(g2["grade"]) < "ABCDE".index(g["grade"]):
                g2["reason"] = "表記ルールの置き換えを戻して照合。" + g2.get("reason", "")
                g = g2
        g["reason"] = note + g["reason"]
        rows.append({"no": len(rows) + 1, "line": u["line"], "speaker": u["speaker"] or "不明", "text": u["text"], "kind": u["kind"], **g})
    summary = {k: sum(1 for r in rows if r["grade"] == k) for k in "ABCDE"}
    return {"rows": rows, "summary": summary, "skipped_short": skipped, "transcript_speakers": speakers}


def format_report(res: Dict[str, Any], article: str) -> str:
    s = res["summary"]
    out = [
        "quotes：%s" % article,
        "判定：A %d／B %d／C %d／D %d／E %d（%d 字未満の短い文 %d 件は対象外）" % (s["A"], s["B"], s["C"], s["D"], s["E"], MIN_CHARS, res["skipped_short"]),
        "書き起こしの話し手：%s" % ("・".join(res["transcript_speakers"]) or "（なし）"),
        "A〜C が整文の範囲かは人が確かめる。D・E は根拠を確認するまで公開しない。",
        "",
        "| No. | 行 | 話し手 | 記事の発言 | 近い書き起こし | 一致度 | 判定 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in res["rows"]:
        src = ("L%s %s" % (r["source_line"], r["source"])) if r["source"] else "-"
        grade = r["grade"] + ((" " + r["reason"]) if r["reason"] else "")
        out.append("| %d | %d | %s | %s | %s | %.2f | %s |" % (r["no"], r["line"], md_cell(r["speaker"]), md_cell(short(r["text"], 50)), md_cell(src), r["similarity"], md_cell(grade)))
    bad = [r for r in res["rows"] if r["grade"] in ("D", "E")]
    if bad:
        out.append("")
        out.append("要確認（D・E）：")
        for r in bad:
            out.append("- L%d %s「%s」→ %s %s" % (r["line"], r["speaker"], short(r["text"], 60), r["grade"], GRADE_NOTE[r["grade"]] + ("。" + r["reason"] if r["reason"] else "")))
    return "\n".join(out)


def cmd_quotes(args) -> int:
    article = Path(args.article)
    if not article.exists():
        print("ファイルがない：%s" % article)
        return 1
    if not args.transcript:
        print("--transcript で書き起こしを 1 つ以上渡す")
        return 1
    texts = []
    for t in args.transcript:
        p = Path(t)
        if not p.exists():
            print("書き起こしがない：%s" % p)
            return 1
        texts.append(paths.read_text(p))
    default_speaker = args.speaker
    if not default_speaker and args.project:
        proj = paths.load_project(paths.repo_root(), args.project) or {}
        people = proj.get("people") or []
        if people and people[0].get("name"):
            default_speaker = people[0]["name"]
    equivalents = []
    if args.project:
        led = paths.effective_ledger(paths.repo_root(), args.project)
        for r in led.get("rules") or []:
            if r.get("avoid") and r.get("use"):
                equivalents.append((r["avoid"], r["use"]))
    res = check(paths.read_text(article), texts, default_speaker, args.interviewer or [], equivalents)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(format_report(res, str(article)))
    return 2 if (res["summary"]["D"] or res["summary"]["E"]) else 0
