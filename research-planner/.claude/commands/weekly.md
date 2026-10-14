---
description: "주간 공고 스캔 — 새로 뜬 국가 R&D 공고만 모아 내 프로필·KB 기준으로 거르고, 볼 만한 것만 표로 정리합니다. '이번 주 공고 뭐 있어', '주간 스캔 돌려줘', '새 공고 확인해 줘' 요청과 예약 실행에 사용합니다. 공고 하나를 깊게 볼 때는 /grant 를 씁니다."
---

# /weekly — 주간 공고 스캔

research-lab `/weekly` 를 옮긴 것입니다. 계획서 초안은 쓰지 않고 "볼 만한 공고 목록"까지만 만듭니다.

> 대부분의 주는 "해당 없음"이 정직한 결과입니다. KBSI 실측(2026-08-04): 접수 중·예정 38건 중 자격을 통과한 것은 1건이었습니다. 억지로 후보를 만들지 않습니다.

## 1. 수집 — 새로 뜬 것만

```bash
python 60-scripts/ancm_state.py new --limit 50     # macOS·Linux는 python3
```

출처는 NTIS(국가R&D통합공고)와 IRIS(범부처통합연구지원시스템)입니다. 이미 본 공고는 걸러집니다. 새 공고가 0건이면 여기서 끝냅니다. 한 곳이 실패하면 실패했다고 적고 나머지로 진행합니다.

## 2. 싼 판정부터

제목·부처·마감만으로 거릅니다.
- 마감까지 7일 미만, 조달입찰·수요조사 → 제외
- 프로필(`70-kb/profile/연구프로필.md`)의 분야·관심 주제와 제목이 전혀 겹치지 않음 → 제외
- 제외한 것은 `python 60-scripts/ancm_state.py mark {uid} --verdict skip --note "{사유}"` (macOS는 `python3`)

## 3. 남은 것만 자격 확인

남은 공고만 상세를 받아 `frameworks/rfp-fit-matrix.md` 의 자격 하드 게이트를 봅니다. 주관기관 유형 제한이 가장 큰 병목입니다. 자격을 메울 수 없으면 `skip`.

## 4. 저장

`50-grants/{YYYY-MM-DD}-weekly.md`

| 공고 | 부처 | 마감 | 자격 | 내 KB와 겹치는 것 | 판정(pursue/watch/skip) | 원문 |
|---|---|---|---|---|---|---|

- "내 KB와 겹치는 것"은 `70-kb/assets` 의 증빙 있는 행만 씁니다.
- pursue 가 있으면 다음 행동으로 `/grant fit {공고}` 를 적습니다.
- 끝에 `## 미확인` 을 둡니다.

## 예약 실행

매주 자동으로 돌리려면 `60-scripts/schedule_windows.ps1`(Windows) 또는 `60-scripts/schedule_mac.sh`(macOS)를 한 번 실행합니다. 자세한 것은 `KB-구축가이드.md` 의 "자동으로 돌리기".
