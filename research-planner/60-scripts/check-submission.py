#!/usr/bin/env python3
"""제출본 검사 — 계획서를 내기 전에 결정론적으로 잡히는 결함만 본다.

  python3 60-scripts/check-submission.py 50-grants/<공고>/proposal-제출본.md
  python3 60-scripts/check-submission.py <파일> --json

검사 항목 (전부 2026-08-03 실측 결함에서 나옴):
  1. 제작 메타언어      요건ID(N##)·게이트ID(G#/D#)·Phase 참조·근거유형 태그·작업파일명
  2. 자백 문구          "확인하지 못했다"·"확인 불가" — 제출본에 있어선 안 된다
  3. 표 정합            열 수 불일치·구분선 어긋남
  4. 인건비 단가        참여율 합계 × 기간으로 1인월 단가를 역산해 통상 구간과 대조
  5. 예산 합계          비목 합계가 총액과 맞는가

이 검사는 **형식**만 본다. 사실의 정확성·방법의 타당성은 잡지 못한다
(2026-08-03 데모에서 법령 오독은 모든 형식 게이트를 통과했다).
"""
import argparse, json, re, sys
from pathlib import Path

# 한글 Windows(cp949)에서도 출력이 깨지거나 멈추지 않게 UTF-8로 고정한다
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# 직급별 통상 계상 단가 (천원/월, 출연연 기준·4대보험 포함)
RATE_MIN, RATE_MAX = 4_500, 10_000
PCT_PAT = r"\|\s*(?:각|평균|약)?\s*(\d{1,3})\s*%"


def _num(s):
    """'43,200' → 43200. 실패하면 None."""
    try:
        return int(re.sub(r"[^\d]", "", s))
    except ValueError:
        return None


def check_meta(t):
    """제작 메타언어 — 내부 추적용 표기가 제출본에 남았는가."""
    pats = [
        ("요건ID", r"\bN\d{1,2}\b(?!\s*[)\]])"),
        ("게이트ID", r"\b[GD]\d\b"),
        ("Phase참조", r"Phase\s*[ABC]\b"),
        ("근거유형태그", r"\[[①②③④⑤][^\]]*\]"),
        ("작업파일명", r"proposal-[ABC]\.md"),
        ("자체검증문구", r"누락 0|7/7|불일치 0건|게이트 자체 판정"),
    ]
    out = []
    for name, p in pats:
        for m in re.finditer(p, t):
            line = t[:m.start()].count("\n") + 1
            out.append({"kind": name, "line": line, "text": m.group(0)})
    return out


def check_confession(t):
    """제출본에 있어선 안 되는 자백 문구.

    ⚠️ **인용된 제3자의 미확인은 자백이 아니다.**
    "소관 부처가 원인을 파악하지 못했다"는 근거로 인용한 사실이지 우리 고백이 아니다.
    출처 표기(`출처:`)가 붙은 문단은 인용으로 간주해 제외한다. (2026-08-04 오탐 사례)
    """
    lines = t.split("\n")
    out = []
    for m in re.finditer(r"확인하지 못했|확인 불가|확보하지 못했|파악하지 못했", t):
        ln = t[:m.start()].count("\n")
        # 같은 줄 + 뒤 2줄에 출처 표기가 있으면 인용 → 제외
        ctx = "\n".join(lines[ln:ln + 3])
        if "출처:" in ctx or "출처 :" in ctx:
            continue
        out.append({"kind": "자백문구", "line": ln + 1,
                    "text": t[max(0, m.start() - 25):m.end() + 15].replace("\n", " ")})
    return out


def check_tables(t):
    """표 열 수 불일치 — 정규식 일괄치환 후 흔히 깨진다."""
    out, cols, start = [], None, 0
    for i, ln in enumerate(t.split("\n"), 1):
        if ln.strip().startswith("|"):
            n = ln.count("|")
            if cols is None:
                cols, start = n, i
            elif n != cols:
                out.append({"kind": "표열불일치", "line": i,
                            "text": f"{n}열 (표 시작 {start}행은 {cols}열)"})
        else:
            cols = None
    return out


def check_personnel(t):
    """인건비 단가 역산 — 총액이 맞아도 1인월 단가가 비현실적일 수 있다."""
    out = []
    months = None
    m = re.search(r"연구기간[^\n]{0,20}?(\d{1,2})\s*개월|(\d{1,2})\s*개월[^\n]{0,10}?(?:과제|연구)", t)
    if m:
        months = int(m.group(1) or m.group(2))
    if not months:
        m = re.search(r"기간\**\s*[:：|]?\s*\**(\d{1,2})\s*개월", t)
        months = int(m.group(1)) if m else None

    # 참여율 표 탐지 — 헤딩에 의존하지 않고 "참여율 %가 있는 표"를 찾는다.
    # (헤딩 문구는 계획서마다 달라 놓치기 쉽다 — 2026-08-04 실측)
    fte = None
    rows = None
    for blk in re.findall(r"((?:\|[^\n]*\n){2,})", t):
        head = blk.split("\n")[0]
        if not re.search(r"참여율|참여 ?비율", head):
            continue
        if re.search(PCT_PAT, blk):
            rows = blk
            break
    if rows:
        # 소계·합계 행은 참여율을 이미 합산한 값이라 이중계상된다 → 제외
        keep = [ln for ln in rows.split("\n")
                if not re.search(r"소계|합계|계\s*\|", ln)]
        rates = [int(x) for x in re.findall(PCT_PAT, "\n".join(keep))]
        if rates:
            # '각 40%' 처럼 인원수 열이 있으면 곱한다
            fte = 0.0
            for ln in keep:
                r_ = re.search(PCT_PAT, ln)
                if not r_:
                    continue
                n_ = re.search(r"\|\s*(\d{1,2})\s*\|", ln)
                cnt = int(n_.group(1)) if n_ else 1
                fte += cnt * int(r_.group(1)) / 100.0

    # 인건비 계상액
    pay = None
    m = re.search(r"\|\s*인건비\s*\|\s*([\d,]+)", t)
    if m:
        pay = _num(m.group(1))

    if fte and months and pay:
        manmonths = fte * months
        rate = pay / manmonths if manmonths else 0
        ok = RATE_MIN <= rate <= RATE_MAX
        out.append({"kind": "인건비단가", "line": 0, "ok": ok,
                    "text": f"{fte:.2f} FTE × {months}개월 = {manmonths:.1f}인월 · "
                            f"{pay:,}천원 ÷ {manmonths:.1f} = 1인월 {rate:,.0f}천원 "
                            f"({'정합' if ok else f'통상 {RATE_MIN:,}~{RATE_MAX:,} 벗어남'})"})
    else:
        miss = [n for n, v in [("참여율", fte), ("연구기간", months), ("인건비", pay)] if not v]
        out.append({"kind": "인건비단가", "line": 0, "ok": None,
                    "text": f"검산 불가 — {'·'.join(miss)} 추출 실패"})
    return out


def check_budget(t):
    """비목 합계 == 총액."""
    out = []
    m = re.search(r"\|\s*비목\s*\|[^\n]*\n\|[-:| ]+\|\n((?:\|[^\n]*\n)+)", t)
    if not m:
        return out
    items, total = [], None
    for ln in m.group(1).strip().split("\n"):
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) < 2:
            continue
        name, val = cells[0].replace("*", "").strip(), _num(cells[1])
        if val is None:
            continue
        if "합계" in name or name.startswith("총"):
            total = val
        else:
            items.append(val)
    if total is not None:
        s = sum(items)
        out.append({"kind": "예산합계", "line": 0, "ok": s == total,
                    "text": f"비목 합 {s:,} vs 총액 {total:,}" + ("" if s == total else "  ← 불일치")})
    return out


def run(path):
    t = Path(path).read_text(encoding="utf-8")
    r = {"file": str(path), "size": len(t.encode())}
    r["meta"] = check_meta(t)
    r["confession"] = check_confession(t)
    r["tables"] = check_tables(t)
    r["personnel"] = check_personnel(t)
    r["budget"] = check_budget(t)
    fails = (len(r["meta"]) + len(r["confession"]) + len(r["tables"])
             + sum(1 for x in r["personnel"] + r["budget"] if x.get("ok") is False))
    # 검산 불가는 통과가 아니다 — 게이트가 조용히 넘어가면 잡을 수 있는 결함을 놓친다
    warns = sum(1 for x in r["personnel"] + r["budget"] if x.get("ok") is None)
    r["fail_count"] = fails
    r["warn_count"] = warns
    r["verdict"] = "ISSUES" if fails else ("WARN" if warns else "PASS")
    return r


def main():
    ap = argparse.ArgumentParser(description="제출본 결정론 검사")
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not Path(a.path).exists():
        print(f"파일 없음: {a.path}", file=sys.stderr)
        return 2
    r = run(a.path)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["verdict"] == "PASS" else 1

    print(f"{r['file']}  ({r['size']:,}B)\n")
    for key, label in [("meta", "제작 메타언어"), ("confession", "자백 문구"), ("tables", "표 정합")]:
        v = r[key]
        print(f"  {label:12s} {'PASS' if not v else f'ISSUE {len(v)}건'}")
        for x in v[:6]:
            print(f"      L{x['line']}  {x['kind']}: {x['text']}")
        if len(v) > 6:
            print(f"      … 외 {len(v)-6}건")
    for key, label in [("personnel", "인건비 단가"), ("budget", "예산 합계")]:
        for x in r[key]:
            mark = {True: "PASS", False: "ISSUE", None: "미검산"}[x.get("ok")]
            print(f"  {label:12s} {mark}\n      {x['text']}")
    tail = ""
    if r["fail_count"]:
        tail = f" (결함 {r['fail_count']}건)"
    elif r.get("warn_count"):
        tail = f" (검산 불가 {r['warn_count']}건 — 표 형식을 확인하세요)"
    print(f"\n  판정: {r['verdict']}{tail}")
    return 0 if r["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
