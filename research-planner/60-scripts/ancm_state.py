#!/usr/bin/env python3
"""공고 상태 추적 — 주간 실행에서 '이번에 새로 뜬 것'만 골라낸다.

  python3 60-scripts/ancm_state.py new              # 신규 공고만 (기본)
  python3 60-scripts/ancm_state.py new --keyword AI --json
  python3 60-scripts/ancm_state.py mark <uid> --verdict skip --note "자격미달"
  python3 60-scripts/ancm_state.py list             # 기록 전체
  python3 60-scripts/ancm_state.py stats

왜 필요한가: 매주 돌리면 같은 공고를 매번 다시 판정한다. 한 번 본 공고는
판정 결과와 함께 기록해두고, 다음 주에는 **신규분만** 파이프라인에 태운다.
마감일이 지난 기록은 자동으로 정리한다(closed).

상태 파일: 70-kb/outcomes/_seen.jsonl  (append-only, 한 줄 = 한 공고)
  {"uid","source","title","ministry","open","close","first_seen",
   "verdict","note","last_update"}

verdict 값
  new       아직 판정 안 함 (수집만 됨)
  skip      판정 후 제외 (자격미달·도메인불일치 등) — note에 사유 필수
  watch     이번엔 안 하지만 다음 회차 주시
  pursue    추진 — 계획서 작성 대상
  closed    마감 지남
"""
import argparse, json, re, subprocess, sys
from datetime import date, datetime
from pathlib import Path

# 한글 Windows(cp949)에서도 출력이 깨지거나 멈추지 않게 UTF-8로 고정한다
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "70-kb" / "outcomes" / "_seen.jsonl"
COLLECT = ROOT / "60-scripts" / "rnd_ancm.py"
VERDICTS = ("new", "skip", "watch", "pursue", "closed")


def _load():
    """uid → record. 같은 uid가 여러 줄이면 마지막이 이긴다(append-only 갱신)."""
    if not STATE.exists():
        return {}
    out = {}
    for line in STATE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue                      # 깨진 줄은 건너뛴다(전체를 못 읽는 것보다 낫다)
        if r.get("uid"):
            out[str(r["uid"])] = r
    return out


def _append(rec):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with STATE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _today():
    return date.today().isoformat()


def _parse_close(s):
    """'2026.08.27' | '2026-08-27' → date. 실패하면 None."""
    if not s:
        return None
    for fmt in ("%Y.%m.%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def collect(source="ntis", keyword=None, limit=50):
    """수집 스크립트를 호출해 현재 공고 목록을 가져온다."""
    cmd = [sys.executable, str(COLLECT), source, "--limit", str(limit), "--json"]
    if keyword:
        cmd += ["--keyword", keyword]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    if p.returncode != 0:
        raise RuntimeError(f"수집 실패 ({source}): {p.stderr.strip()[:200]}")
    body = "\n".join(l for l in p.stdout.splitlines() if not l.startswith("Using "))
    return json.loads(body).get("rows", [])


def _key(row):
    """uid가 없는 소스(IRIS)는 id, 그것도 없으면 제목으로 식별."""
    return str(row.get("uid") or row.get("id") or row.get("title") or "")


def _norm_title(t):
    """소스별 표기 차이(R&D vs RD, 공백·특수문자·후행공백)를 지워 같은 공고를 식별."""
    return re.sub(r"[^0-9a-z가-힣]", "", (t or "").lower())


def _dedupe(rows):
    """같은 공고가 NTIS·IRIS 양쪽 키로 들어온 기록을 하나로 접는다 (표시용 — 상태 파일은 불변).
    판정된 기록 > 마감일 있는 기록 순으로 남기고, 남는 쪽에 마감일이 없으면 상대에게서 보충한다."""
    def rank(x):
        return (x.get("verdict") not in (None, "", "new"), bool(x.get("close")))
    best = {}
    for r in rows:
        nt = _norm_title(r.get("title")) or str(r.get("uid"))
        cur = best.get(nt)
        if cur is None:
            best[nt] = r
            continue
        keep, drop = (r, cur) if rank(r) > rank(cur) else (cur, r)
        if not keep.get("close") and drop.get("close"):
            keep = {**keep, "close": drop["close"]}
        best[nt] = keep
    return list(best.values())


def cmd_new(a):
    seen = _load()
    rows, errs = [], []
    for src in (["ntis", "iris"] if a.source == "both" else [a.source]):
        try:
            rows += collect(src, a.keyword, a.limit)
        except Exception as e:
            errs.append(f"{src}: {e}")

    fresh = []
    seen_titles = {_norm_title(r.get("title")) for r in seen.values()}
    seen_titles.discard("")
    for r in rows:
        k = _key(r)
        if not k or k in seen:
            continue
        nt = _norm_title(r.get("title"))
        if nt and nt in seen_titles:      # 다른 소스에서 이미 들어온 같은 공고
            continue
        rec = {
            "uid": k, "source": r.get("source"), "title": r.get("title"),
            "ministry": r.get("ministry"), "open": r.get("open") or r.get("date"),
            "close": r.get("close"), "detail_url": r.get("detail_url") or r.get("url"),
            "first_seen": _today(), "verdict": "new", "note": "",
            "last_update": _today(),
        }
        _append(rec)
        fresh.append(rec)
        seen[k] = rec
        if nt:
            seen_titles.add(nt)

    closed = _sweep(seen)

    if a.json:
        print(json.dumps({"new": fresh, "closed": closed, "errors": errs},
                         ensure_ascii=False, indent=2))
        return 0

    if errs:
        print("⚠️ 일부 소스 실패: " + " / ".join(errs), file=sys.stderr)
    print(f"신규 {len(fresh)}건 · 마감처리 {len(closed)}건 · 누적 {len(seen)}건")
    for r in fresh:
        print(f"  [{r['source']}] {r.get('close') or '?'} | {r.get('ministry') or ''} | {r['title']}")
        if r.get("detail_url"):
            print(f"      {r['detail_url']}")
    if not fresh:
        print("  (이번 회차 신규 없음)")
    return 0


def _sweep(seen):
    """마감일이 지난 미종결 기록을 closed로."""
    today, out = date.today(), []
    for r in seen.values():
        if r.get("verdict") in ("closed",):
            continue
        d = _parse_close(r.get("close"))
        if d and d < today:
            nr = {**r, "verdict": "closed", "last_update": _today()}
            _append(nr)
            out.append(nr)
    return out


def cmd_mark(a):
    seen = _load()
    r = seen.get(str(a.uid))
    if not r:  # /grant search 로 찾은 공고 등 원장에 없는 공고는 새 행으로 남긴다(교육 배포본)
        r = {"uid": str(a.uid), "source": "manual", "title": a.title, "ministry": "",
             "open": None, "close": a.close, "first_seen": _today(), "verdict": "new",
             "note": "", "last_update": _today()}
    if a.verdict == "skip" and not a.note:
        print("skip은 --note에 사유가 필요합니다 (왜 제외했는지가 KB의 값어치)", file=sys.stderr)
        return 2
    nr = {**r, "verdict": a.verdict, "note": a.note or r.get("note", ""),
          "last_update": _today()}
    _append(nr)
    print(f"{a.uid} → {a.verdict}" + (f" ({a.note})" if a.note else ""))
    return 0


def cmd_list(a):
    seen = _load()
    rows = sorted(_dedupe(seen.values()),
                  key=lambda r: (r.get("verdict") or "", r.get("close") or ""))
    if a.verdict:
        rows = [r for r in rows if r.get("verdict") == a.verdict]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    if not rows:
        print("기록 없음")
        return 0
    for r in rows:
        note = f"  — {r['note']}" if r.get("note") else ""
        print(f"  {r.get('verdict','?'):8s} {r.get('close') or '?':12s} {(r.get('title') or '')[:52]}{note}")
    return 0


def cmd_stats(a):
    seen = _load()
    if not seen:
        print("기록 없음 — `new`로 시작하세요")
        return 0
    cnt = {}
    for r in seen.values():
        cnt[r.get("verdict", "?")] = cnt.get(r.get("verdict", "?"), 0) + 1
    print(f"누적 {len(seen)}건")
    for v in VERDICTS:
        if cnt.get(v):
            print(f"  {v:8s} {cnt[v]:4d}")
    unknown = {k: v for k, v in cnt.items() if k not in VERDICTS}
    for k, v in unknown.items():
        print(f"  {k:8s} {v:4d}  (알 수 없는 상태)")
    # 판정 대기
    pend = [r for r in _dedupe(seen.values()) if r.get("verdict") == "new"]
    if pend:
        print(f"\n판정 대기 {len(pend)}건:")
        for r in pend[:10]:
            print(f"  {r.get('close') or '?':12s} {(r.get('title') or '')[:56]}")
    return 0


def selftest():
    """상태 파일을 건드리지 않는 순수 함수 검사."""
    global STATE
    import tempfile
    assert _parse_close("2026.08.27") == date(2026, 8, 27)
    assert _parse_close("2026-08-27") == date(2026, 8, 27)
    assert _parse_close("") is None and _parse_close("없음") is None
    assert _key({"uid": "123"}) == "123"
    assert _key({"id": "A1"}) == "A1"
    assert _key({"title": "제목"}) == "제목"
    assert _norm_title("산업기술R&D연구기획사업 ") == _norm_title("산업기술RD연구기획사업")
    assert _norm_title("NCP활동지원사업 2차 공모 ") == _norm_title("NCP활동지원사업 2차 공모")
    d = _dedupe([
        {"uid": "n1", "title": "같은 공고 (R&D)", "close": "2026.08.27", "verdict": "new"},
        {"uid": "i1", "title": "같은 공고 (RD)", "close": None, "verdict": "watch"},
        {"uid": "n2", "title": "다른 공고", "close": None, "verdict": "new"},
    ])
    assert len(d) == 2, f"제목 dedupe 실패: {len(d)}"
    m = next(r for r in d if r["uid"] == "i1")
    assert m["verdict"] == "watch" and m["close"] == "2026.08.27", "판정 우선·마감 보충 실패"
    with tempfile.TemporaryDirectory() as d:
        orig = STATE
        STATE = Path(d) / "s.jsonl"
        _append({"uid": "1", "verdict": "new", "close": "2020.01.01"})
        _append({"uid": "1", "verdict": "skip"})          # 같은 uid → 마지막이 이긴다
        _append({"uid": "2", "verdict": "new", "close": "2099.01.01"})
        s = _load()
        assert len(s) == 2, f"uid 병합 실패: {len(s)}"
        assert s["1"]["verdict"] == "skip", "마지막 줄 우선 실패"
        STATE.write_text(STATE.read_text(encoding="utf-8") + "깨진줄\n", encoding="utf-8")   # 깨진 줄 내성
        assert len(_load()) == 2, "깨진 줄에서 전체 실패"
        closed = _sweep(_load())
        assert len(closed) == 0, "이미 skip인 건 sweep 대상 아님"
        _append({"uid": "3", "verdict": "new", "close": "2020.01.01"})
        assert len(_sweep(_load())) == 1, "마감 sweep 실패"
        STATE = orig
    print("selftest OK — 날짜파싱·식별키·uid병합·깨진줄내성·마감sweep 정상")
    return 0


def main():
    ap = argparse.ArgumentParser(description="공고 상태 추적 (주간 실행용)")
    sub = ap.add_subparsers(dest="cmd")

    n = sub.add_parser("new", help="신규 공고만 수집·기록")
    n.add_argument("--source", default="both", choices=["ntis", "iris", "both"])
    n.add_argument("--keyword")
    n.add_argument("--limit", type=int, default=50)
    n.add_argument("--json", action="store_true")
    n.set_defaults(fn=cmd_new)

    m = sub.add_parser("mark", help="판정 기록")
    m.add_argument("uid")
    m.add_argument("--verdict", required=True, choices=VERDICTS)
    m.add_argument("--note", default="")
    m.add_argument("--title", default="", help="원장에 없는 공고면 공고명")
    m.add_argument("--close", default=None, help="원장에 없는 공고면 마감일 YYYY-MM-DD")
    m.set_defaults(fn=cmd_mark)

    l = sub.add_parser("list", help="기록 조회")
    l.add_argument("--verdict", choices=VERDICTS)
    l.add_argument("--json", action="store_true")
    l.set_defaults(fn=cmd_list)

    s = sub.add_parser("stats", help="요약")
    s.set_defaults(fn=cmd_stats)

    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.cmd:
        ap.error("하위 명령(new|mark|list|stats) 또는 --selftest 필요")
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
