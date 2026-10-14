# research-lab

> 국가 R&D 과제를 찾고, 판정하고, 연구개발계획서와 발표자료까지 만드는 리서치 워크스페이스입니다.

문헌 조사·출처 검증·분석 종합 같은 일반 리서치도 하지만, 이 워크스페이스의 중심은 **국가 R&D 과제 파이프라인(P0~P7)** 입니다.

---

## 시작

```bash
claude          # 또는 codex
```

자연어로 요청하면 `.claude/commands/`(Claude) · `.agents/skills/`(Codex)의 워크플로우로 라우팅됩니다.

```
"이번주 뜬 공고 중에 우리랑 맞는 거 찾아줘"      → P0~P1
"이 공고 분석해줘"                              → /rfp
"계획서 초안 잡아줘"                            → /proposal
```

---

## 파이프라인 (P0~P7)

| 단계 | 하는 일 | 산출 위치 |
|---|---|---|
| **P0** 공고 수집 | NTIS·IRIS에서 공고를 긁어온다 (`60-scripts/rnd_ancm.py`) | `20-raw/rfp/<공고>/` |
| **P0.5** 유형 분류 | 조달입찰 / R&D과제 / 기술수요조사 / 사전공고 구분 | — |
| **P1** 적합도 판정 | 자격 하드 게이트 → 요건표 → 매트릭스 → 통과·실패·**무의미** | `30-analysis/rfp/*-fit.md` |
| **P2** 리서치 | 시장기회·트렌드·핵심기술·경쟁·규제 5축 | `30-analysis/rfp/<공고>/` |
| **P3** 아이디어 | 공고가 요구하는 결과에서 역산 | `ideas.md` |
| **P4** 스토리텔링 | 한 줄 서사 확정 | `story.md` |
| **P5** 계획서 | 8장 구조, 3페이즈 분할 후 병합 | `40-reports/rfp/<공고>/proposal.md` |
| **P6** 발표 설계 | 배점 순 스토리보드 | `deck-outline.md` |
| **P7** 슬라이드 | `/insane-slide` 렌더 | `decks/<공고>/` |

**핵심 규율**은 `frameworks/`에 있습니다.

| 파일 | 무엇 |
|---|---|
| `rnd-proposal-pipeline.md` | 전체 흐름 + 게이트 ⓪~⑥ |
| `rfp-fit-matrix.md` | 적합도 판정 규칙 (§1.5 자격 하드 게이트) |
| `output-correctness.md` | 5유형 근거 체계 — ①외부사실 ②전망 ③내부가정 ④연구가설 ⑤목표 |

---

## ⚠️ 예시(데모) 문서 — 실사용 전에 지우세요

이 워크스페이스에는 **파이프라인을 실증한 데모 산출물**이 들어 있습니다. 가상 연구자 페르소나로 실제 공고를 판정해 계획서·슬라이드까지 만든 것으로, **참고용 예시일 뿐 실제 사업 데이터가 아닙니다.**

### 👉 **처음 받으셨다면 [ONBOARDING.md](./ONBOARDING.md) 부터 보세요**

```bash
python3 60-scripts/manifest.py stats   # 골격 88개(0.3MB) / 예시 193개(141.6MB)
bash 60-scripts/reset-demo.sh          # 지워질 목록 확인 (안전)
bash 60-scripts/reset-demo.sh --apply  # 실제 제거
```

제거 목록은 손으로 관리하지 않습니다 — `_meta/MANIFEST.md`의 **규칙**으로 분류하고,
어느 규칙에도 안 걸리는 파일은 **미분류로 잡아냅니다**(`manifest.py check`).
하드코딩 목록은 새 파일이 생기면 낡아서 지워야 할 게 남기 때문입니다.

### 무엇이 예시인가

| 경로 | 내용 | 크기 |
|---|---|---|
| `20-raw/rfp/` | 수집한 공고 원본 3건 (HWP·PDF) | ~109MB |
| `30-analysis/rfp/` | 적합도 판정 2건 + 요건표 2건 + 리서치 | 64KB |
| `40-reports/rfp/2026-nuclear-policy/` | **연구개발계획서 8장** + 게이트로그 + 검토 | 164KB |
| `decks/2026-nuclear-policy/` | 슬라이드 HTML 14장 + PNG | 1.7MB |
| `70-kb/our-assets/` | **가상 연구자 페르소나** KB | 24KB |
| `30-analysis/kbsi-2026-08/`, `40-reports/2026-08-04-kbsi-seminar/` | 세미나 리서치·자료 | 324KB |

### 지우기 전에 읽어볼 만한 것

파이프라인이 어떻게 도는지 보려면 이 세 개면 충분합니다.

1. **`30-analysis/rfp/_comparison-2026-08-03.md`** — 공고 3건을 어떤 기준으로 걸렀는지
2. **`40-reports/rfp/2026-nuclear-policy/proposal-제출본.md`** — 최종 계획서 (내부 추적 표기 제거본)
3. **`40-reports/rfp/2026-nuclear-policy/REVIEW-2026-08-03.md`** — **이 데모가 무엇을 못 했는지.** 외부 검토에서 법령 오독·인건비 모순이 나왔고, 그 교훈이 프레임워크에 역반영돼 있습니다

`gate-log.md`에는 발견 18건과 각각의 역반영 결과가 있습니다.

---

## 폴더

```
00-inbox/      인입 자료 (KB화 대기)
10-questions/  리서치 질문 정의
20-raw/        수집 원본 (공고 HWP·PDF)
30-analysis/   분석·판정
40-reports/    보고서·계획서
50-sources/    출처 등재 (A~E 등급)
60-scripts/    수집·유틸 스크립트
70-kb/         지식 축적 (기관·사업·요건·성과·자산)
90-archive/    종료분
frameworks/    판정·작성 규율 ★
```

---

## 문서

- [ONBOARDING.md](./ONBOARDING.md) — **처음 받았을 때 읽는 문서** (정리 → 채우기 → 첫 실행)
- [_meta/MANIFEST.md](./_meta/MANIFEST.md) — 파일 분류 규칙 (골격/예시/교체대상)
- [CLAUDE.md](./CLAUDE.md) — Claude Code instruction surface
- [AGENTS.md](./AGENTS.md) — Codex instruction surface
- [.agents/skills/](./.agents/skills/) — Codex repo skills
- [_meta/deviations.md](./_meta/deviations.md) — 템플릿 대비 일탈 기록
