#!/usr/bin/env python3
"""국가 R&D 공고 수집 — IRIS(범부처통합연구지원시스템) + NTIS(국가R&D통합공고).

실측 2026-08-03. 표준 라이브러리 + curl(전송)만 사용. 읽기 전용.
※ IRIS는 recordCountPerPage가 10 미만이어도 10건을 돌려준다(서버 최소치, 실측).

  python3 60-scripts/rnd_ancm.py iris --keyword 신약 --limit 20
  python3 60-scripts/rnd_ancm.py ntis --limit 20
  python3 60-scripts/rnd_ancm.py --selftest

접근 경로(실측):
  IRIS  POST https://www.iris.go.kr/contents/retrieveBsnsAncmList.do
        → JSON {listBsnsAncm:[...], paginationInfo:{totalRecordCount}}
        키워드 파라미터: ancmTl(공고명) / bsnsAncmTl(공고명+사업명)
  NTIS  POST https://www.ntis.go.kr/rndgate/eg/un/ra/mng.do
        → HTML 테이블 (순번/현황/공고명/부처명/접수일/마감일/D-day)
        ⚠️ 키워드 파라미터 미확정 — searchWord/searchKeyword가 결과를 바꾸지 않음.
           전량 수집 후 로컬 필터를 쓴다(--keyword가 그렇게 동작).

주의: 두 사이트 모두 공개 조회 페이지지만 robots·이용약관을 존중하고
      과도한 요청을 하지 않는다(기본 1회 호출, 페이지네이션은 명시적으로).
"""
import argparse, html, json, re, subprocess, sys, urllib.parse
from datetime import datetime, timezone

# 한글 Windows(cp949)에서도 출력이 깨지거나 멈추지 않게 UTF-8로 고정한다
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

IRIS_URL = "https://www.iris.go.kr/contents/retrieveBsnsAncmList.do"
IRIS_REF = "https://www.iris.go.kr/contents/retrieveBsnsAncmListView.do"
NTIS_URL = "https://www.ntis.go.kr/rndgate/eg/un/ra/mng.do"


def _post(url, data, referer, timeout=25, extra=None):
    """curl 경유 POST.

    urllib을 쓰지 않는 이유: 일부 macOS 환경에서 사내 프록시/자체서명 체인 때문에
    CERTIFICATE_VERIFY_FAILED가 난다(2026-08-03 실측). curl은 시스템 신뢰 저장소를
    쓰므로 동일 요청이 통과한다. subprocess는 표준 라이브러리라 의존성은 늘지 않는다.
    """
    pairs = list(data.items()) + list(extra or [])   # extra는 같은 키 반복 허용
    body = urllib.parse.urlencode(pairs, encoding="utf-8")
    cmd = [
        "curl", "-s", "-m", str(timeout), "-X", "POST", url,
        "-H", f"User-Agent: {UA}",
        "-H", f"Referer: {referer}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
        "--data", body,
    ]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"curl exit {p.returncode}: {p.stderr.decode('utf-8', 'replace')[:200]}")
    return p.stdout.decode("utf-8", errors="replace")


def _epoch_ms(v):
    if not v:
        return ""
    try:
        return datetime.fromtimestamp(int(v) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return str(v)


IRIS_PAGE_SIZE = 10          # 서버 고정 — recordCountPerPage는 무시된다(실측)
IRIS_TABS = {"open": "rcve_prg", "closed": "clos", "all": ""}


def _iris_page(data):
    doc = json.loads(_post(IRIS_URL, data, IRIS_REF))
    return (doc.get("paginationInfo") or {}).get("totalRecordCount"), (doc.get("listBsnsAncm") or [])


def fetch_iris(keyword=None, field="bsnsAncmTl", limit=20, page=1, year=None, tab="open"):
    """IRIS 공고 조회 — 서버 필터를 쓴다.

    파라미터 (2026-08-04 실측, `resources/js/contents/bsnsancm/bsnsAncmList.js`에서 확보):
      bsnsAncmTap : 탭 필터. `rcve_prg`=접수중 / `clos`=마감 / 생략=전체
                    ★ 접수중은 25건 내외라, 이걸 쓰면 페이지 순회가 필요 없다.
      bsnsAncmTl  : 공고명+사업명 검색 / ancmTl : 공고명만
      bsnsYy      : 사업연도
      pageIndex   : 페이지 (recordCountPerPage는 무시 — 항상 10건)

    ⚠️ 정렬 파라미터는 존재하지 않는다. 전체 탭은 공고일 오름차순 고정이므로
       전체를 볼 땐 마지막 페이지가 최신이다. 접수중 탭은 모수가 작아 무관.
    """
    base = {}
    if keyword:
        base[field] = keyword
    if year:
        base["bsnsYy"] = str(year)
    tap = IRIS_TABS.get(tab, "rcve_prg")
    if tap:
        base["bsnsAncmTap"] = tap

    total, raw = _iris_page({**base, "pageIndex": page})
    # 모수가 limit보다 크면 이어서 수집
    p_ = page + 1
    while total and len(raw) < min(limit, total) and (p_ - page) * IRIS_PAGE_SIZE < total:
        _, more = _iris_page({**base, "pageIndex": p_})
        if not more:
            break
        raw += more
        p_ += 1

    rows = []
    for it in raw[:limit]:
        rows.append({
            "source": "IRIS",
            "id": it.get("ancmId"),
            "no": it.get("ancmNo"),
            "title": it.get("ancmTl"),
            "ministry": it.get("blngGovdSe"),
            "agency": it.get("sorgnNm"),
            "business": it.get("sorgnBsnsNm"),
            "year": it.get("bsnsYy"),
            "date": _epoch_ms(it.get("ancmDe")),
            "url": IRIS_REF,
        })
    return {"total": total, "rows": rows,
            "note": f"탭={tab}" + (f" · 키워드={keyword}" if keyword else "")}


_TR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_TAG = re.compile(r"<[^>]+>")
_UID = re.compile(r"roRndUid=(\d+)")          # 상세 딥링크 키
NTIS_VIEW = "https://www.ntis.go.kr/rndgate/eg/un/ra/view.do?roRndUid={uid}&flag=rndList"
NTIS_DL = "https://www.ntis.go.kr/rndgate/eg/cmm/file/download.do"


def parse_ntis_rows(text):
    """NTIS 목록 HTML → 행 리스트. 데이터 행은 7칸이고 2번째가 현황, 5·6번째가 날짜."""
    out = []
    for tr in _TR.findall(text):
        cells = [html.unescape(_TAG.sub("", c)).strip() for c in _TD.findall(tr)]
        cells = [re.sub(r"\s+", " ", c) for c in cells if c.strip()]
        if len(cells) < 6:
            continue
        # 날짜 형태(2026.08.03)가 두 개 이상 있어야 데이터 행
        dates = [c for c in cells if re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", c)]
        if len(dates) < 2:
            continue
        # D-day 칸은 마감된 공고에서 비어 있고, 그때 cells[-1]은 마감일이 된다.
        # 'D-14' / 'D - 9' / 'D-day' 형태일 때만 채운다.
        last = cells[-1]
        dday = last if re.match(r"^D\s*-", last) else ""
        m = _UID.search(tr)                      # 상세 페이지로 가는 유일한 키
        uid = m.group(1) if m else None
        out.append({
            "source": "NTIS",
            "no": cells[0],
            "status": cells[1],
            "title": cells[2],
            "ministry": cells[3],
            "open": dates[0],
            "close": dates[1],
            "dday": dday,
            "uid": uid,
            "detail_url": NTIS_VIEW.format(uid=uid) if uid else None,
            "url": NTIS_URL,
        })
    return out


# 공고현황 코드 (2026-08-04 실측): B=접수중 · P=접수예정 · Y=마감
# ⚠️ B만 쓰면 접수예정을 놓친다 — 준비 기간이 필요한 과제는 접수예정에서 잡아야 한다.
NTIS_STATUS = {"open": ["B", "P"], "ongoing": ["B"], "upcoming": ["P"], "closed": ["Y"]}


def fetch_ntis(limit=20, page=1, keyword=None, status=None):
    """NTIS 공고 조회 — 서버 검색을 쓴다.

    파라미터 (2026-08-04 실측, 목록 페이지 `rndMngForm` 폼에서 확보):
      searchKeyword    : ★ 서버 키워드 검색. 이게 정답이다.
                         (`searchWord`는 폼에 있지만 결과를 바꾸지 않는다 — 실측)
      searchStatusList : 공고현황. B=접수중 / P=접수예정 / Y=마감
                         반복 지정 가능(B와 P를 함께 주면 둘 다)
      searchDeptList   : 부처코드(M10~M99)
      pageUnit         : 페이지당 건수 (50까지 확인)
      pageIndex        : 페이지

    실측 근거: 전체 77,014건 → searchKeyword=인공지능 573건 → +status=B 1건.
    """
    data = {"pageIndex": page, "pageUnit": max(limit, 10)}
    if keyword:
        data["searchKeyword"] = keyword
    codes = NTIS_STATUS.get(status, [status] if status else [])
    txt = _post(NTIS_URL, data, NTIS_URL, extra=[("searchStatusList", c) for c in codes])
    total = None
    m = re.search(r'name="totalCount"[^>]*value="(\d+)"', txt)
    if m:
        total = int(m.group(1))
    rows = parse_ntis_rows(txt)[:limit]
    note = "서버 검색" + (f" · 키워드={keyword}" if keyword else "") + (f" · 현황={status}" if status else "")
    return {"total": total, "rows": rows, "note": note}


_FILE = re.compile(r"fn_fileDownload\('(\d+)',\s*'([^']+)'\)[^>]*>(.*?)</a>", re.S)


def _get(url, referer, timeout=30):
    cmd = ["curl", "-s", "-m", str(timeout), url,
           "-H", f"User-Agent: {UA}", "-H", f"Referer: {referer}"]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"curl exit {p.returncode}")
    return p.stdout.decode("utf-8", errors="replace")


def parse_attachments(detail_html):
    """상세 HTML → 붙임 목록. fn_fileDownload(attachSn, roTextUid) 호출에서 추출."""
    out = []
    for sn, uid, label in _FILE.findall(detail_html):
        name = html.unescape(_TAG.sub("", label)).strip()
        out.append({"attach_sn": sn, "ro_text_uid": uid, "name": name})
    return out


def fetch_detail(uid):
    """NTIS 공고 상세 + 붙임 목록. uid = roRndUid."""
    url = NTIS_VIEW.format(uid=uid)
    h = _get(url, NTIS_URL)
    title = re.search(r"<title>([^<]*)</title>", h)
    return {"uid": uid, "url": url,
            "title": html.unescape(title.group(1)).strip() if title else "",
            "attachments": parse_attachments(h), "html_size": len(h)}


def download_attachment(att, dest, referer_uid):
    """붙임 1건 다운로드. POST download.do (wfUid=attachSn, roTextUid)."""
    cmd = ["curl", "-s", "-m", "60", "-o", str(dest), "-w", "%{http_code}",
           "-X", "POST", NTIS_DL,
           "-H", f"User-Agent: {UA}",
           "-H", f"Referer: {NTIS_VIEW.format(uid=referer_uid)}",
           "-H", "Content-Type: application/x-www-form-urlencoded",
           "--data", f"wfUid={att['attach_sn']}&roTextUid={att['ro_text_uid']}"]
    p = subprocess.run(cmd, capture_output=True)
    return p.stdout.decode().strip()


SELFTEST_HTML = """
<table><tr><th>순번</th><th>현황</th><th>공고명</th></tr>
<tr><td>77012</td><td>접수중</td>
    <td><a href="/rndgate/eg/un/ra/view.do?roRndUid=1274148&flag=rndList">2026년도 기관고유사업 공고</a></td>
    <td>해양수산부</td><td>2026.08.03</td><td>2026.08.17</td><td>D-14</td></tr>
<tr><td>전체</td><td>경찰청</td><td>고용노동부</td><td>국방부</td><td>기상청</td><td>법무부</td></tr>
<tr><td>77000</td><td>마감</td><td>2026년도 AI 완전자율운항선박 재공고</td><td>해양수산부</td>
    <td>2026.07.15</td><td>2026.07.22</td><td>2026.07.22</td></tr>
</table>"""


def selftest():
    rows = parse_ntis_rows(SELFTEST_HTML)
    assert len(rows) == 2, f"데이터 행 2개여야 함, 실제 {len(rows)}"
    r = rows[0]
    assert r["no"] == "77012" and r["status"] == "접수중", r
    assert r["open"] == "2026.08.03" and r["close"] == "2026.08.17", r
    assert "기관고유사업" in r["title"], r
    # 상세 딥링크 키 — 없으면 붙임까지 갈 수 없다(2026-08-03 실측 결함)
    assert r["uid"] == "1274148", r
    assert r["detail_url"].endswith("roRndUid=1274148&flag=rndList"), r
    atts = parse_attachments(
        '''<a onclick="fn_fileDownload('1400999', '20260722ABC')">1. 입찰공고문.hwp</a>''')
    assert len(atts) == 1 and atts[0]["attach_sn"] == "1400999", atts
    assert atts[0]["name"].endswith(".hwp"), atts
    # 부처 필터 행(날짜 0개)은 걸러져야 한다
    assert all("경찰청" != x["no"] for x in rows)
    # 마감 행: D-day 칸이 비어 날짜가 밀려 들어오면 dday를 채우지 않는다(2026-08-03 실측 버그)
    closed = [x for x in rows if x["status"] == "마감"]
    assert len(closed) == 1 and closed[0]["dday"] == "", closed
    assert closed[0]["close"] == "2026.07.22", closed
    assert _epoch_ms(788886000000).startswith("199"), _epoch_ms(788886000000)
    assert _epoch_ms(None) == ""
    print("selftest OK — 2행 추출·필터행 제외·마감행 dday 공란·상세UID 추출·붙임 파싱·epoch 변환 정상")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", choices=["iris", "ntis", "detail"])
    ap.add_argument("--uid", help="detail 모드: NTIS roRndUid")
    ap.add_argument("--download-dir", help="detail 모드: 붙임 저장 경로")
    ap.add_argument("--keyword")
    ap.add_argument("--field", default="bsnsAncmTl", choices=["ancmTl", "bsnsAncmTl"],
                    help="IRIS 검색 대상 (기본 bsnsAncmTl=공고명+사업명)")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--year", help="IRIS 사업연도(bsnsYy) 필터")
    ap.add_argument("--tab", default="open", choices=["open", "closed", "all"],
                    help="IRIS 탭 (기본 open=접수중)")
    ap.add_argument("--status", default="open",
                    choices=["open", "ongoing", "upcoming", "closed"],
                    help="NTIS 공고현황 — open=접수중+접수예정(기본) / ongoing=접수중만 / upcoming=접수예정만")
    ap.add_argument("--all-status", action="store_true", help="NTIS: 현황 필터 없이 전체")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.source:
        ap.error("source(iris|ntis|detail) 또는 --selftest 필요")

    if a.source == "detail":
        if not a.uid:
            ap.error("detail 모드는 --uid 필요")
        try:
            d = fetch_detail(a.uid)
        except Exception as e:
            print(f"FETCH_FAILED: {type(e).__name__}: {e}", file=sys.stderr); return 2
        print(f"{d['title']}  ({d['html_size']:,}B)")
        print(f"  {d['url']}")
        for i, att in enumerate(d["attachments"], 1):
            print(f"  [{i}] {att['name']}")
        if a.download_dir and d["attachments"]:
            import os
            os.makedirs(a.download_dir, exist_ok=True)
            for i, att in enumerate(d["attachments"], 1):
                ext = os.path.splitext(att["name"])[1] or ".bin"
                dest = os.path.join(a.download_dir, f"{i:02d}{ext}")
                code = download_attachment(att, dest, a.uid)
                size = os.path.getsize(dest) if os.path.exists(dest) else 0
                print(f"      → {dest} HTTP {code} {size:,}B")
        return 0

    try:
        res = (fetch_iris(a.keyword, a.field, a.limit, a.page, a.year, a.tab) if a.source == "iris"
               else fetch_ntis(a.limit, a.page, a.keyword,
                               None if a.all_status else a.status))
    except Exception as e:                      # fetch 실패와 결과 0을 구별한다
        print(f"FETCH_FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if res.get("total") is not None:
        print(f"총 {res['total']}건 (표시 {len(res['rows'])})")
    else:
        print(f"표시 {len(res['rows'])}건" + (f" · {res['note']}" if res.get("note") else ""))
    if not res["rows"]:
        print("결과 0건 (fetch는 성공)")
    for r in res["rows"]:
        if r["source"] == "IRIS":
            print(f"  {r['date']} | {r['ministry']} | {r['agency']} | {r['title']}")
        else:
            print(f"  {r['open']}~{r['close']} {r['dday']:>6} | {r['status']} | {r['ministry']} | {r['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
