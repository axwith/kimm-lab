#!/usr/bin/env python3
"""인용 실재 확인기 — DOI/arXiv 인용이 실재하는지, 철회되지 않았는지 결정론적으로 판정한다.

왜 스크립트인가: `/lit` Step 4(실재 확인)와 연구 수행 파이프라인 게이트 R③은 매 연구마다 돌아야 하는데,
손으로 하면 "확인했다고 생각하는" 인용이 남는다. 인용 조작 발생률은 2023→2026년 사이 10배 늘었다
(논문 2,828편당 1편 → 277편당 1편, research-lab 리서치 기록).

사용법:
    python3 60-scripts/cite_check.py --selftest
    python3 60-scripts/cite_check.py doi 10.1002/jrsm.70018 --title "..." --year 2025
    python3 60-scripts/cite_check.py file 10-literature/some-review.md
    python3 60-scripts/cite_check.py file 10-literature/sources/my-sources.jsonl --json

종료 코드 (fetch 실패와 결과 0을 구별한다 — 60-scripts/README.md 무결성 규약):
    0  전부 통과 (OK / OK_PREPRINT)
    1  위반 있음 (NOT_FOUND / RETRACTED / TITLE_MISMATCH / YEAR_MISMATCH)
    2  판정 불가 있음 (FETCH_FAIL) — 위반은 없으나 확인을 못 했다
    3  검사 대상 0건 (입력에 DOI/arXiv 식별자가 없다)

third_party:
    - Crossref  https://www.crossref.org/documentation/retrieve-metadata/
                privacy: https://www.crossref.org/operations-and-sustainability/privacy/
    - OpenAlex  terms: https://openalex.org/OpenAlex_termsofservice.pdf
                privacy: https://openalex.org/OpenAlex_privacy_policy.pdf
    - arXiv API http://export.arxiv.org/api/query  (terms: https://arxiv.org/help/api/tou)
    확인일 2026-08-04. 모두 인증 없이 읽기 전용 조회.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# 한글 Windows(cp949)에서도 출력이 깨지거나 멈추지 않게 UTF-8로 고정한다
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TIMEOUT = 20
UA = "research-lab-cite-check/1.0 (+local research workspace; stdlib urllib)"


def _ssl_context():
    """macOS framework Python은 CA 번들 경로가 비어 있어 HTTPS가 전부 실패한다(실측 2026-08-04).
    certifi → 시스템 번들 → 기본값 순으로 신뢰 저장소를 찾는다. 검증을 끄지는 않는다."""
    import ssl
    try:
        import certifi  # 있으면 쓴다. 없어도 동작해야 한다
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    for bundle in ("/etc/ssl/cert.pem", "/usr/local/etc/openssl/cert.pem"):
        try:
            return ssl.create_default_context(cafile=bundle)
        except Exception:
            continue
    return ssl.create_default_context()


_SSL = _ssl_context()

# 판정값
OK = "OK"
OK_PREPRINT = "OK_PREPRINT"
NOT_FOUND = "NOT_FOUND"
RETRACTED = "RETRACTED"
TITLE_MISMATCH = "TITLE_MISMATCH"
YEAR_MISMATCH = "YEAR_MISMATCH"
FETCH_FAIL = "FETCH_FAIL"

PASS_VERDICTS = {OK, OK_PREPRINT}
VIOLATION_VERDICTS = {NOT_FOUND, RETRACTED, TITLE_MISMATCH, YEAR_MISMATCH}

TITLE_MIN_RATIO = 0.72   # 제목 유사도 하한
YEAR_TOLERANCE = 1       # online-first/게재 연도 차이 허용폭

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9<>+\[\]]+", re.IGNORECASE)
ARXIV_RE = re.compile(r"arxiv[:/\s]*(\d{4}\.\d{4,5})(v\d+)?", re.IGNORECASE)
DOI_TRAILING = ".,;:)]}>'\"”’"


# --------------------------------------------------------------------------- #
# HTTP — 셀프테스트에서 이 함수만 갈아끼운다
# --------------------------------------------------------------------------- #
def _http_get_json(url: str) -> tuple[str, Any]:
    """(status, payload) 반환. status는 'ok' | 'not_found' | 'fetch_fail'."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_SSL) as resp:
            return "ok", json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return "not_found", None
        return "fetch_fail", f"HTTP {e.code}"
    except Exception as e:  # 네트워크·타임아웃·JSON 파싱
        return "fetch_fail", f"{type(e).__name__}: {e}"


def _http_get_text(url: str) -> tuple[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_SSL) as resp:
            return "ok", resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return "not_found", None
        return "fetch_fail", f"HTTP {e.code}"
    except Exception as e:
        return "fetch_fail", f"{type(e).__name__}: {e}"


# --------------------------------------------------------------------------- #
# 정규화·추출
# --------------------------------------------------------------------------- #
def normalize_title(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"<[^>]+>", " ", s)              # crossref 제목의 태그
    s = re.sub(r"[^0-9a-z가-힣\s]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def title_ratio(a: str, b: str) -> float:
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def clean_doi(raw: str) -> str:
    d = raw.strip()
    while d and d[-1] in DOI_TRAILING:
        d = d[:-1]
    return d.lower()


def extract_identifiers(text: str) -> list[dict]:
    """본문에서 DOI·arXiv 식별자를 중복 없이 뽑는다. 등장 순서를 보존한다."""
    found: list[dict] = []
    seen: set[str] = set()
    for m in DOI_RE.finditer(text):
        doi = clean_doi(m.group(0))
        key = f"doi:{doi}"
        if key not in seen:
            seen.add(key)
            found.append({"kind": "doi", "id": doi})
    for m in ARXIV_RE.finditer(text):
        arx = m.group(1)
        key = f"arxiv:{arx}"
        if key not in seen:
            seen.add(key)
            found.append({"kind": "arxiv", "id": arx})
    return found


# --------------------------------------------------------------------------- #
# 소스별 조회
# --------------------------------------------------------------------------- #
def fetch_crossref(doi: str) -> dict:
    status, payload = _http_get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    if status != "ok":
        return {"status": status, "detail": payload}
    msg = (payload or {}).get("message") or {}
    titles = msg.get("title") or []
    year = None
    for field in ("issued", "published-print", "published-online", "created"):
        parts = ((msg.get(field) or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            year = parts[0]
            break
    updates = msg.get("update-to") or []
    retracted = any((u.get("type") or "").lower() in ("retraction", "withdrawal") for u in updates)
    ctype = (msg.get("type") or "").lower()
    return {
        "status": "ok",
        "title": titles[0] if titles else "",
        "year": year,
        "journal": (msg.get("container-title") or [""])[0],
        "type": ctype,
        "is_preprint": ctype == "posted-content",
        "retracted": retracted,
        "authors": [
            " ".join(x for x in (a.get("given"), a.get("family")) if x)
            for a in (msg.get("author") or [])
        ],
    }


def fetch_openalex(doi: str) -> dict:
    status, payload = _http_get_json("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi))
    if status != "ok":
        return {"status": status, "detail": payload}
    p = payload or {}
    src = ((p.get("primary_location") or {}).get("source") or {})
    return {
        "status": "ok",
        "title": p.get("display_name") or p.get("title") or "",
        "year": p.get("publication_year"),
        "journal": src.get("display_name") or "",
        "type": (p.get("type") or "").lower(),
        "is_preprint": (p.get("type") or "").lower() == "preprint",
        "retracted": bool(p.get("is_retracted")),
        "authors": [
            (a.get("author") or {}).get("display_name", "")
            for a in (p.get("authorships") or [])
        ],
    }


def fetch_arxiv(arxiv_id: str) -> dict:
    url = ("http://export.arxiv.org/api/query?id_list=" + urllib.parse.quote(arxiv_id)
           + "&max_results=1")
    status, payload = _http_get_text(url)
    if status != "ok":
        return {"status": status, "detail": payload}
    text = payload or ""
    entry_m = re.search(r"<entry>(.*?)</entry>", text, re.S)
    if not entry_m:
        return {"status": "not_found", "detail": None}
    # ⚠️ Atom 피드는 <entry> 앞에 feed-level <title>("arXiv Query: ...")을 둔다.
    # 문서 전체에서 첫 <title>을 잡으면 그 쿼리 문자열을 논문 제목으로 오인한다 (실측 버그, 2026-08-04).
    entry = entry_m.group(1)

    def tag(name: str) -> str:
        m = re.search(rf"<{name}>(.*?)</{name}>", entry, re.S)
        return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    published = tag("published")
    year = int(published[:4]) if published[:4].isdigit() else None
    doi_m = re.search(r"<arxiv:doi[^>]*>(.*?)</arxiv:doi>", entry, re.S)
    return {
        "status": "ok",
        "title": tag("title"),
        "year": year,
        "journal": "arXiv",
        "type": "preprint",
        "is_preprint": True,
        "retracted": False,          # arXiv에는 철회 플래그가 없다 — withdrawn은 판별 불가
        "authors": re.findall(r"<name>(.*?)</name>", entry, re.S),
        "published_doi": doi_m.group(1).strip() if doi_m else None,
    }


# --------------------------------------------------------------------------- #
# 판정
# --------------------------------------------------------------------------- #
def judge(claim: dict, sources: dict) -> dict:
    """claim: {kind,id,title?,year?} · sources: {소스명: fetch 결과}"""
    live = {k: v for k, v in sources.items() if v.get("status") == "ok"}
    failed = {k: v for k, v in sources.items() if v.get("status") == "fetch_fail"}
    missing = {k: v for k, v in sources.items() if v.get("status") == "not_found"}

    notes: list[str] = []
    for k, v in failed.items():
        notes.append(f"{k} 조회 실패: {v.get('detail')}")

    if not live:
        # 조회가 전부 실패했으면 '없다'가 아니라 '확인 불가'다 — 이 구별이 규약이다
        if failed and not missing:
            return {"verdict": FETCH_FAIL, "notes": notes, "meta": None}
        if failed and missing:
            notes.append("일부 소스는 미등재, 일부는 조회 실패 — 확인 불가")
            return {"verdict": FETCH_FAIL, "notes": notes, "meta": None}
        return {"verdict": NOT_FOUND, "notes": notes + ["조회한 모든 소스에 미등재"], "meta": None}

    # 대표 메타데이터: 철회 플래그를 가진 소스를 우선, 없으면 첫 소스
    meta = next((v for v in live.values() if v.get("retracted")), next(iter(live.values())))
    src_names = ", ".join(live.keys())
    notes.append(f"실재 확인: {src_names}")

    if any(v.get("retracted") for v in live.values()):
        who = [k for k, v in live.items() if v.get("retracted")]
        return {"verdict": RETRACTED, "notes": notes + [f"철회 표시: {', '.join(who)}"], "meta": meta}

    if claim.get("title"):
        ratios = {k: title_ratio(claim["title"], v.get("title", "")) for k, v in live.items()}
        best = max(ratios.values()) if ratios else 0.0
        if best < TITLE_MIN_RATIO:
            notes.append(f"제목 유사도 {best:.2f} < {TITLE_MIN_RATIO} · 실제 제목: {meta.get('title')!r}")
            return {"verdict": TITLE_MISMATCH, "notes": notes, "meta": meta}
        notes.append(f"제목 유사도 {best:.2f}")

    if claim.get("year"):
        years = [v.get("year") for v in live.values() if v.get("year")]
        if years and all(abs(int(claim["year"]) - y) > YEAR_TOLERANCE for y in years):
            notes.append(f"주장 연도 {claim['year']} vs 메타데이터 {years}")
            return {"verdict": YEAR_MISMATCH, "notes": notes, "meta": meta}

    if any(v.get("is_preprint") for v in live.values()):
        notes.append("preprint — 기본 D급. 저널 게재본을 찾아 등급을 올린다")
        return {"verdict": OK_PREPRINT, "notes": notes, "meta": meta}

    return {"verdict": OK, "notes": notes, "meta": meta}


def check_one(claim: dict) -> dict:
    if claim["kind"] == "doi":
        sources = {"crossref": fetch_crossref(claim["id"]), "openalex": fetch_openalex(claim["id"])}
    else:
        sources = {"arxiv": fetch_arxiv(claim["id"])}
    result = judge(claim, sources)
    result.update({"kind": claim["kind"], "id": claim["id"]})
    if claim.get("title"):
        result["claimed_title"] = claim["title"]
    if claim.get("year"):
        result["claimed_year"] = claim["year"]
    return result


# --------------------------------------------------------------------------- #
# 출력·종료 코드
# --------------------------------------------------------------------------- #
def exit_code(results: list[dict]) -> int:
    if not results:
        return 3
    if any(r["verdict"] in VIOLATION_VERDICTS for r in results):
        return 1
    if any(r["verdict"] == FETCH_FAIL for r in results):
        return 2
    return 0


def report(results: list[dict], as_json: bool) -> None:
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    if not results:
        print("검사 대상 0건 — 입력에 DOI/arXiv 식별자가 없다")
        return
    mark = {OK: "✅", OK_PREPRINT: "🟡", FETCH_FAIL: "⚠️ ",
            NOT_FOUND: "❌", RETRACTED: "🚫", TITLE_MISMATCH: "❌", YEAR_MISMATCH: "❌"}
    for r in results:
        print(f"{mark.get(r['verdict'], '  ')} {r['verdict']:<15} {r['kind']}:{r['id']}")
        meta = r.get("meta") or {}
        if meta.get("title"):
            print(f"      → {meta.get('title')} ({meta.get('year')}) {meta.get('journal') or ''}".rstrip())
        for n in r.get("notes", []):
            print(f"      · {n}")
    counts: dict[str, int] = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print("\n요약: " + " · ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    viol = sum(v for k, v in counts.items() if k in VIOLATION_VERDICTS)
    fail = counts.get(FETCH_FAIL, 0)
    if viol:
        print(f"❌ 위반 {viol}건 — 해당 인용은 본문에서 뺀다 (게이트 R③ 미통과)")
    elif fail:
        print(f"⚠️  판정 불가 {fail}건 — '확인 불가'로 남긴다. 통과로 처리하지 않는다")
    else:
        print("✅ 게이트 R③ 통과")


# --------------------------------------------------------------------------- #
# 셀프테스트 — 네트워크 없이 판정 로직을 검증한다
# --------------------------------------------------------------------------- #
def selftest() -> int:
    global _http_get_json, _http_get_text
    real_json, real_text = _http_get_json, _http_get_text
    failures: list[str] = []

    def check(name: str, got, want) -> None:
        if got != want:
            failures.append(f"{name}: got {got!r}, want {want!r}")

    # 1) 식별자 추출 — 문장 끝 마침표·괄호를 DOI에 포함하지 않는다
    ids = extract_identifiers(
        "보고서 [Clark et al., 2025, doi 10.1002/jrsm.70018]. 그리고 arXiv:2509.21403 와 "
        "https://doi.org/10.1002/jrsm.70018 (중복), arXiv:2402.05015v2."
    )
    check("extract:개수", len(ids), 3)
    check("extract:doi정리", ids[0], {"kind": "doi", "id": "10.1002/jrsm.70018"})
    check("extract:arxiv", ids[1], {"kind": "arxiv", "id": "2509.21403"})
    check("extract:없음", extract_identifiers("DOI 없는 본문"), [])

    # 2) 제목 정규화·유사도
    check("title:동일", title_ratio("A Sober Look at LLMs", "a sober look at llms") > 0.99, True)
    check("title:태그제거", normalize_title("Deep <i>NMR</i> methods"), "deep nmr methods")
    check("title:무관", title_ratio("완전히 다른 제목", "A Sober Look at LLMs") < TITLE_MIN_RATIO, True)

    # 3) 판정 로직 — 합성 payload
    ok_meta = {"status": "ok", "title": "Real Paper", "year": 2025, "journal": "J",
               "type": "journal-article", "is_preprint": False, "retracted": False}
    cases = [
        ("정상", {"kind": "doi", "id": "x"}, {"crossref": dict(ok_meta)}, OK),
        ("제목일치", {"kind": "doi", "id": "x", "title": "Real Paper"},
         {"crossref": dict(ok_meta)}, OK),
        ("제목불일치", {"kind": "doi", "id": "x", "title": "완전히 없는 논문 제목"},
         {"crossref": dict(ok_meta)}, TITLE_MISMATCH),
        ("연도허용", {"kind": "doi", "id": "x", "year": 2026}, {"crossref": dict(ok_meta)}, OK),
        ("연도불일치", {"kind": "doi", "id": "x", "year": 2019},
         {"crossref": dict(ok_meta)}, YEAR_MISMATCH),
        ("철회", {"kind": "doi", "id": "x"},
         {"crossref": {**ok_meta, "retracted": True}}, RETRACTED),
        ("철회우선", {"kind": "doi", "id": "x", "title": "Real Paper"},
         {"crossref": dict(ok_meta), "openalex": {**ok_meta, "retracted": True}}, RETRACTED),
        ("preprint", {"kind": "arxiv", "id": "x"},
         {"arxiv": {**ok_meta, "is_preprint": True, "type": "preprint"}}, OK_PREPRINT),
        ("미등재", {"kind": "doi", "id": "x"},
         {"crossref": {"status": "not_found"}, "openalex": {"status": "not_found"}}, NOT_FOUND),
        ("조회실패", {"kind": "doi", "id": "x"},
         {"crossref": {"status": "fetch_fail", "detail": "HTTP 503"}}, FETCH_FAIL),
        ("실패+미등재는_확인불가", {"kind": "doi", "id": "x"},
         {"crossref": {"status": "fetch_fail", "detail": "timeout"},
          "openalex": {"status": "not_found"}}, FETCH_FAIL),
        ("한쪽만_살아도_판정", {"kind": "doi", "id": "x"},
         {"crossref": {"status": "fetch_fail", "detail": "timeout"},
          "openalex": dict(ok_meta)}, OK),
    ]
    for name, claim, sources, want in cases:
        check(f"judge:{name}", judge(claim, sources)["verdict"], want)

    # 4) 종료 코드 — fetch 실패와 결과 0을 구별하는지
    check("exit:빈입력", exit_code([]), 3)
    check("exit:정상", exit_code([{"verdict": OK}, {"verdict": OK_PREPRINT}]), 0)
    check("exit:위반", exit_code([{"verdict": OK}, {"verdict": NOT_FOUND}]), 1)
    check("exit:판정불가", exit_code([{"verdict": OK}, {"verdict": FETCH_FAIL}]), 2)
    check("exit:위반우선", exit_code([{"verdict": FETCH_FAIL}, {"verdict": RETRACTED}]), 1)

    # 5) fetch 파서 — HTTP 계층을 갈아끼워 Crossref/OpenAlex 파싱을 검증
    crossref_payload = {"message": {
        "title": ["Generative AI for evidence synthesis"],
        "author": [{"given": "J", "family": "Clark"}],
        "issued": {"date-parts": [[2025, 4, 24]]},
        "container-title": ["Research Synthesis Methods"],
        "type": "journal-article",
        "update-to": [{"type": "retraction"}],
    }}
    openalex_payload = {"display_name": "Some Preprint", "publication_year": 2024,
                        "type": "preprint", "is_retracted": False,
                        "primary_location": {"source": {"display_name": "arXiv"}},
                        "authorships": [{"author": {"display_name": "A B"}}]}

    def fake_json(url: str):
        if "crossref" in url:
            return "ok", crossref_payload
        if "openalex" in url:
            return "ok", openalex_payload
        return "not_found", None

    _http_get_json = fake_json  # noqa: F811
    cr = fetch_crossref("10.1/x")
    check("parse:crossref제목", cr["title"], "Generative AI for evidence synthesis")
    check("parse:crossref연도", cr["year"], 2025)
    check("parse:crossref철회", cr["retracted"], True)
    check("parse:crossref저자", cr["authors"], ["J Clark"])
    oa = fetch_openalex("10.1/x")
    check("parse:openalex제목", oa["title"], "Some Preprint")
    check("parse:openalex preprint", oa["is_preprint"], True)
    check("parse:openalex철회", oa["retracted"], False)

    # 실제 arXiv Atom 응답은 <entry> 앞에 feed-level <title>과 <name>을 둔다.
    # 이 케이스가 없어서 feed 제목을 논문 제목으로 읽는 버그를 selftest가 놓쳤다 (2026-08-04 회귀 추가).
    arxiv_xml = ("<feed><title>arXiv Query: search_query=&amp;id_list=2402.05015</title>"
                 "<author><name>arXiv api core</name></author>"
                 "<entry><title>A Sober Look at LLMs</title>"
                 "<published>2024-02-07T00:00:00Z</published>"
                 "<author><name>Kristian Gupta</name></author></entry></feed>")
    def fake_text_ok(url: str):
        del url
        return "ok", arxiv_xml

    _http_get_text = fake_text_ok  # noqa: F811
    ax = fetch_arxiv("2402.05015")
    check("parse:arxiv제목", ax["title"], "A Sober Look at LLMs")
    check("parse:arxiv연도", ax["year"], 2024)
    check("parse:arxiv preprint", ax["is_preprint"], True)
    check("parse:arxiv저자_entry스코프", ax["authors"], ["Kristian Gupta"])
    def fake_text_empty(url: str):
        del url
        return "ok", "<feed></feed>"

    _http_get_text = fake_text_empty
    check("parse:arxiv미등재", fetch_arxiv("9999.99999")["status"], "not_found")

    _http_get_json, _http_get_text = real_json, real_text

    if failures:
        print("❌ selftest 실패 %d건" % len(failures))
        for f in failures:
            print("   -", f)
        return 1
    print("✅ selftest 통과 — 추출 4 · 정규화 3 · 판정 12 · 종료코드 5 · 파서 10")
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="인용 실재 확인 (게이트 R③)")
    ap.add_argument("--selftest", action="store_true", help="네트워크 없이 자기 검증")
    ap.add_argument("--json", action="store_true", help="JSON 출력")
    sub = ap.add_subparsers(dest="cmd")

    p_doi = sub.add_parser("doi", help="DOI 1건 확인")
    p_doi.add_argument("value")
    p_doi.add_argument("--title", help="주장한 제목 (대조용)")
    p_doi.add_argument("--year", type=int, help="주장한 연도 (대조용)")

    p_arx = sub.add_parser("arxiv", help="arXiv ID 1건 확인")
    p_arx.add_argument("value")
    p_arx.add_argument("--title")
    p_arx.add_argument("--year", type=int)

    p_file = sub.add_parser("file", help="파일에서 DOI·arXiv를 전부 뽑아 확인")
    p_file.add_argument("path")
    p_file.add_argument("--limit", type=int, default=0, help="검사 건수 상한 (0=전부)")

    args = ap.parse_args()
    if args.selftest:
        return selftest()

    if args.cmd in ("doi", "arxiv"):
        claim = {"kind": args.cmd,
                 "id": clean_doi(args.value) if args.cmd == "doi" else args.value}
        if args.title:
            claim["title"] = args.title
        if args.year:
            claim["year"] = args.year
        results = [check_one(claim)]
    elif args.cmd == "file":
        try:
            with open(args.path, encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            print(f"입력 파일을 읽을 수 없다: {e}", file=sys.stderr)
            return 2
        claims = extract_identifiers(text)
        total = len(claims)
        if args.limit and total > args.limit:
            claims = claims[: args.limit]
            print(f"⚠️  식별자 {total}건 중 {args.limit}건만 검사한다 (--limit) — 나머지는 미확인이다\n")
        results = [check_one(c) for c in claims]
    else:
        ap.print_help()
        return 3

    report(results, args.json)
    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
