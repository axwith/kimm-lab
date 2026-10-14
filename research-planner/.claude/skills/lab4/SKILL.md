---
name: lab4
description: "기계연 오후 실습 4 — 내 공간으로 키우기. 전체 흐름을 먼저 보여 주고 자동 실행 등록 여부를 고른 뒤, 반복한 일을 스킬로 만들기, 훅 이력 확인, /wrap과 다음 세션 기록 회수, KB 구축 계획, 자동 실행(/wrap 매일·/weekly 매주) 등록을 STEP 1~5로 안내합니다. '/lab4', '실습 4' 요청에 사용합니다."
---

# /lab4 — 실습 4 · 내 공간으로 키우기

공통 규칙: `.claude/skills/_공통규칙.md` (흐름·막힐 때·정리 방식)

## 전체 보기 (맨 먼저 그대로 출력)

```
실습 4 — 내 공간으로 키우기

목표: 오늘 만든 공간을 내일도 쓰게 만듭니다. 반복한 일은 스킬로, 한 일은 기록으로,
공고 확인과 기록 정리는 예약으로 돌립니다.

STEP 1. 만들기 — 오늘 두 번 이상 시킨 일을 스킬 하나로 만듭니다
STEP 2. 검토하기 — 훅이 남긴 이력에서 오늘 한 일을 확인합니다
STEP 3. 개선하기 — /wrap 기록을 다음 세션이 먼저 읽는지 봅니다
STEP 4. 기획하기 — KB를 어떤 자료로 키울지 계획합니다
STEP 5. 만들기 — 매일 /wrap, 매주 /weekly(새 공고 스캔)를 예약합니다

끝나면 남는 것: .claude/skills/trend/ 내 스킬, 90-log/ 오늘 기록, KB 키우기 계획, 예약 실행 등록
```

## 선택 (AskUserQuestion)

- header `자동 실행`, question "STEP 5 자동 실행도 등록할까요?"
  - "등록까지" — 이 PC에 예약 작업을 만듭니다. 나중에 지울 수 있습니다
  - "STEP 4까지만" — 예약은 집에서 KB-구축가이드.md 를 보고 합니다

## 자동 셋업

- `logs/agent_history.jsonl` 이 있는지, 몇 줄인지 봅니다(Read 도구). 없으면 STEP 2에 "훅이 아직 기록을 남기지 않았습니다 — 막히면 표 참조"를 붙입니다.
- `90-log/` 에 오늘 기록과 `_queue/` 대기 파일이 있는지 봅니다.
- "등록까지"를 골랐으면 `claude --version` 이 되는지 봅니다(예약 실행에 필요).
- 한 줄 보고: "실습 4 준비 완료. 이력 {N}줄, 오늘 기록 {있음/없음}, 예약 {가능/CLI 없음/건너뜀}."

## 브리핑 + 진행 안내

````
■ 이번 실습에서 쓰는 것
| 이름 | 한 줄 정의 | 어디에 |
|---|---|---|
| 스킬 | 이름·설명·지킬 규칙을 적은 파일. "/이름"으로 부름 | .claude\skills\ |
| 훅 | 도구를 쓸 때·세션이 끝날 때 자동으로 도는 스크립트 | .claude\settings.json |
| /wrap | 오늘 한 일·확정한 것·미확인·다음 행동을 기록 | 90-log\ |
| 예약 실행 | 정한 시각에 /wrap, /weekly 를 혼자 돌림 | Windows 작업 스케줄러 |

핵심: 대화는 사라져도 파일은 남습니다. 다음 세션은 그 파일부터 읽고 시작합니다.

■ STEP 1. 만들기 — 스킬
```
.claude/skills/trend/SKILL.md 를 만들어 줘. "/trend {검색어}" 라고 하면 OpenAlex 에서 그 검색어의 2015~2025 연도별 논문 수를 세어 10-literature/ 에 CSV 와 그래프를 저장하고, 확인용 API 주소를 함께 알려 주는 스킬이야.
```
- 파일 만들기 승인 창에서 내용을 읽고 허용합니다
- 새 세션에서:
```
/trend "battery recycling"
```
- (오전 조합) /skillers-suda:skillers-suda 로 같은 일을 스킬로 만들 수도 있습니다
확인할 것: 새 세션에서 /trend 가 불리고, 바꿀 규칙 하나를 말해 고쳤습니다

■ STEP 2. 검토하기 — 훅이 남긴 이력
```
.claude\settings.json 의 hooks 부분을 설명해 줘
```
- 다른 PowerShell 창에서 최근 기록을 봅니다:
```
Get-Content C:\work\kimm\research-planner\logs\agent_history.jsonl -Encoding UTF8 -Tail 10
```
확인할 것: 실습 3에서 한 일(검색, 파일 쓰기, 검사)이 시각 순으로 남았습니다

■ STEP 3. 개선하기 — 기록을 다음 세션으로
```
/wrap
```
- 90-log 의 오늘 파일을 엽니다. 같은 폴더에서 새 세션을 열고:
```
이어서 할 일을 알려 줘
```
- 새 세션이 읽었다고 말한 파일과 요약(한 일·미확인·다음 행동)을 기록과 대조합니다
- /wrap 을 잊고 창을 닫아도 훅이 90-log\_queue 에 원자료를 남기고, 다음 세션이 먼저 정리합니다
확인할 것: 새 세션이 실제로 읽은 파일 경로와 세 항목이 기록에 맞습니다

■ STEP 4. 기획하기 — KB 키우기 계획
- KB-구축가이드.md 를 열고:
```
내 자료로 KB를 키우려면 다음 묶음에 뭘 넣어야 할지 /kb gaps 보고 정리해 줘
```
확인할 것: 다음 묶음에 넣을 자료 세 가지를 적었습니다

■ STEP 5. 만들기 — 자동 실행 ("등록까지"를 고른 분만)
- 다른 PowerShell 창에서:
```
powershell -ExecutionPolicy Bypass -File C:\work\kimm\research-planner\60-scripts\schedule_windows.ps1
```
- 매일 18:00 /wrap, 매주 월 08:30 /weekly(새 공고 스캔)가 등록됩니다
- 확인: Get-ScheduledTask -TaskName research-planner-*
- 지우려면: Unregister-ScheduledTask -TaskName research-planner-wrap -Confirm:$false  (research-planner-weekly 도 같은 방식)
확인할 것: 두 작업(research-planner-wrap, research-planner-weekly)이 보입니다

■ 강사 결과와 비교하려면
오후 덱 「훅이 남긴 이력」「/wrap이 남긴 기록」 장의 사전 실행 화면

막히면 "도와줘", 끝나면 "완료".
````

## 막히면

| 증상 | 이렇게 다시 말합니다 |
|---|---|
| 새 세션에서 /trend 가 없음 | 스킬은 새 세션부터 보입니다. 그래도 없으면 ".claude/skills/trend/SKILL.md 앞머리(name, description)를 확인해 줘" |
| logs\agent_history.jsonl 이 없음 | 훅이 `python` 으로 돕니다. PowerShell에서 `python --version` 확인. `py` 만 되면 ".claude\settings.json 의 command 를 py 로 바꿔 줘" 후 새 세션 |
| /wrap 뒤 새 세션이 기록을 안 읽음 | "CLAUDE.md 규칙대로 90-log 최신 파일부터 읽어 줘" |
| 예약 등록이 권한 오류 | 관리자 권한이 없는 PC일 수 있습니다. STEP 4까지만 하고 집에서 등록합니다 |
| `claude` 명령이 없다고 나옴 | 예약 실행은 CLI가 필요합니다. 오늘은 건너뛰고 README 의 CLI 설치를 봅니다 |

## 정리 (완료·/wrap·끝)

먼저 회고 한 줄을 묻고("가장 쓸모 있었던 것 한 줄 적어 주세요") 답을 받은 뒤 아래를 합니다. 완료 시각은 `YYYY-MM-DD HH:MM`, `.lab-progress.json` 의 `last_activity` 에도 같은 시각을 적습니다.

1. 확인: `.claude/skills/trend/SKILL.md`, `90-log/{오늘}.md`, (STEP 5) 예약 등록 결과.
2. `90-log/실습/lab4.md`: 완료 시각, 만든 스킬 이름, 이력 줄 수, 새 세션 회수 확인 여부, 다음 KB 묶음 세 가지, 예약 등록 여부, 회고 한 줄.
3. `.lab-progress.json` 의 `done` 에 `lab4` 추가.
4. 마무리 안내: "오늘 결과는 research-planner 폴더에 그대로 남습니다. 강의 뒤에는 KB-구축가이드.md 대로 자료를 묶음으로 넣으세요. 덱 마지막 장의 설문을 부탁드립니다."
