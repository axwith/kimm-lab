#!/usr/bin/env python3
"""기획 문서 검사 — 필수 절 누락과 증빙 없는 "보유"를 결정론적으로 잡는다.

  python3 60-scripts/check_planner.py 20-scenarios/2026-10-12-주제.md
  python3 60-scripts/check_planner.py 30-papers/주제/2026-10-12-plan.md --json
  python3 60-scripts/check_planner.py <파일> --type plan
  python3 60-scripts/check_planner.py --selftest

문서 종류는 경로로 정한다(70-kb/profile → profile, 15-market → market, 20-scenarios → scenario,
30-papers → paper, 40-plans → plan). 다른 곳에 있으면 --type 으로 지정한다.

검사 항목:
  1. 필수 절        frameworks/ 의 기준 문서가 정한 ## 절이 모두 있는가
  2. 시나리오 하위 절 시나리오마다 ### 절 8개가 있는가
  3. 증빙 없는 보유  표에서 상태가 "보유"인 행의 증빙 열이 비었거나 "미확인"인가
  4. 지어낸 결과    기대 결과물 절에 퍼센트·p 값 같은 결과 수치가 있는가

이 검사는 형식만 본다. 내용이 맞는지, 근거가 타당한지는 /review 와 사람이 본다.

종료 코드: 0 통과, 1 위반 있음, 2 종류를 정할 수 없음
"""
import argparse, json, re, sys, tempfile
from pathlib import Path

# 한글 Windows(cp949)에서도 출력이 깨지거나 멈추지 않게 UTF-8로 고정한다
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REQUIRED = {
    "profile": ["분야", "현재 연구", "방법·장비·데이터", "성과", "목표", "제약", "관심 주제", "비공개 항목"],
    "scenario": ["비교표", "미확인"],
    "market": ["한 줄 결론", "수요자와 불편", "시장 규모", "정책·예산", "기업·제품", "반대 신호",
               "연구 주제로 이어지는 빈틈", "미확인"],
    "paper": ["가제와 핵심 기여", "연구 질문과 가설", "IMRaD 골격", "그림·표 계획", "필요한 실험·분석",
              "분석 방법", "선행연구 위치", "목표 저널·학회", "일정", "저자와 기여", "미확인"],
    "plan": ["목표", "단계별 내용과 방법", "자원 대조표", "인력과 역할", "예산 항목", "위험과 대응",
             "성과 지표", "일정표", "연결할 과제", "미확인"],
}
SCENARIO_SUB = ["연구 질문", "가설", "방법과 필요한 실험·분석", "필요한 자원", "기대 결과물",
                "차별점과 근거", "위험과 대안", "첫 4주에 할 일"]
PATH_TYPE = [("70-kb/profile", "profile"), ("15-market", "market"), ("20-scenarios", "scenario"), ("30-papers", "paper"), ("40-plans", "plan")]
EMPTY_EVIDENCE = {"", "-", "—", "미확인", "없음", "?"}
RESULT_NUM = re.compile(r"\d+(\.\d+)?\s*%|p\s*[<=]\s*0?\.\d+", re.I)


def detect(path, forced):
    if forced:
        return forced
    p = str(path).replace("\\", "/")
    for key, t in PATH_TYPE:
        if key in p:
            return t
    return None


def headings(text, level):
    mark = "#" * level + " "
    return [l[len(mark):].strip() for l in text.splitlines() if l.startswith(mark) and not l.startswith(mark + "#")]


def check_required(text, kind):
    have = headings(text, 2)
    return [f"필수 절 없음: ## {h}" for h in REQUIRED[kind] if not any(x.startswith(h) for x in have)]


def check_scenarios(text):
    out = []
    blocks = re.split(r"^## (?=시나리오)", text, flags=re.M)[1:]
    if not blocks:
        return ["시나리오가 하나도 없음 (## 시나리오 N: 제목)"]
    for b in blocks:
        title = b.splitlines()[0].strip()
        body = re.split(r"^## ", b, flags=re.M)[0]
        have = headings(body, 3)
        for h in SCENARIO_SUB:
            if not any(x.startswith(h) for x in have):
                out.append(f"[{title}] 하위 절 없음: ### {h}")
    return out


def check_evidence(text):
    out, header = [], None
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip().startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if header is None:
            header = cells
            continue
        st = next((j for j, h in enumerate(header) if "상태" in h), None)
        ev = next((j for j, h in enumerate(header) if "증빙" in h), None)
        if st is None or ev is None or st >= len(cells) or ev >= len(cells):
            continue
        if cells[st].startswith("보유") and cells[ev] in EMPTY_EVIDENCE:
            out.append(f"{i}행: 상태가 '보유'인데 증빙이 비었음 → {cells[0]}")
    return out


def check_results(text):
    out = []
    for m in re.finditer(r"^#{2,3} 기대 결과물.*?(?=^#{2,3} |\Z)", text, flags=re.M | re.S):
        for line in m.group(0).splitlines()[1:]:
            if RESULT_NUM.search(line):
                out.append(f"기대 결과물에 결과 수치가 있음 (가설로 바꿀 것): {line.strip()[:80]}")
    return out


def run(path, forced=None):
    kind = detect(path, forced)
    if kind is None:
        return None, ["문서 종류를 정할 수 없음 — --type profile|market|scenario|paper|plan"]
    text = Path(path).read_text(encoding="utf-8")
    v = check_required(text, kind)
    if kind == "scenario":
        v += check_scenarios(text)
    v += check_evidence(text) + check_results(text)
    return kind, v


def selftest():
    good_s = """# t
## 비교표
| 시나리오 | 새로움 |
|---|---|
| 1 | 3 |
## 시나리오 1: 가
### 연구 질문
### 가설
### 방법과 필요한 실험·분석
### 필요한 자원
| 자원 | 상태 | 증빙 |
|---|---|---|
| 진동대 | 보유 | 70-kb/assets/보유역량.md 3행 |
### 기대 결과물
논문 1편 (가설: 감쇠비가 온도에 따라 달라진다)
### 차별점과 근거
### 위험과 대안
### 첫 4주에 할 일
## 미확인
"""
    bad_s = good_s.replace("| 진동대 | 보유 | 70-kb/assets/보유역량.md 3행 |", "| 진동대 | 보유 | 미확인 |") \
                  .replace("### 가설\n", "").replace("(가설: 감쇠비가 온도에 따라 달라진다)", "정확도 12% 향상")
    with tempfile.TemporaryDirectory() as d:
        sd = Path(d) / "20-scenarios"; sd.mkdir()
        g = sd / "g.md"; g.write_text(good_s, encoding="utf-8")
        b = sd / "b.md"; b.write_text(bad_s, encoding="utf-8")
        o = Path(d) / "x.md"; o.write_text("# x", encoding="utf-8")
        p = Path(d) / "40-plans"; p.mkdir(); pf = p / "p.md"; pf.write_text("## 목표\n", encoding="utf-8")
        m = Path(d) / "15-market"; m.mkdir(); mf = m / "m.md"; mf.write_text("## 한 줄 결론\n## 미확인\n", encoding="utf-8")
        kg, vg = run(g); _, vb = run(b); ko, _ = run(o); kp, vp = run(pf); km, vm = run(mf)
    checks = [
        (kg == "scenario" and vg == [], f"정상 시나리오 통과 {vg}"),
        (any("### 가설" in x for x in vb), "하위 절 누락 검출"),
        (any("증빙이 비었음" in x for x in vb), "증빙 없는 보유 검출"),
        (any("결과 수치" in x for x in vb), "지어낸 결과 수치 검출"),
        (ko is None, "종류 미정 처리"),
        (kp == "plan" and len(vp) == len(REQUIRED["plan"]) - 1, "기획서 필수 절 누락 9개 검출"),
        (km == "market" and len(vm) == len(REQUIRED["market"]) - 2, "시장 조사 필수 절 누락 6개 검출"),
    ]
    bad = [m for ok, m in checks if not ok]
    if bad:
        print("selftest 실패:", bad); return 1
    print(f"selftest 통과 — {len(checks)}개 항목"); return 0


def main():
    ap = argparse.ArgumentParser(description="기획 문서 형식 검사")
    ap.add_argument("path", nargs="?")
    ap.add_argument("--type", choices=list(REQUIRED))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.path or not Path(a.path).exists():
        ap.error("검사할 파일 경로가 필요합니다")
    kind, v = run(a.path, a.type)
    if a.json:
        print(json.dumps({"file": a.path, "type": kind, "violations": v}, ensure_ascii=False, indent=2))
    elif kind is None:
        print(v[0])
    elif v:
        print(f"❌ {a.path} ({kind}) 위반 {len(v)}건")
        for x in v:
            print("  -", x)
    else:
        print(f"✅ {a.path} ({kind}) 통과")
    sys.exit(2 if kind is None else (1 if v else 0))


if __name__ == "__main__":
    main()
