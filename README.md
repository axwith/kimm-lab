# 실습 폴더 — Claude Code 활용 교육 오후 실습 (한국기계연구원, 2026-10-15)

이 예제들은 교안의 일부이며 별도 납품 소프트웨어가 아닙니다.

이 폴더 전체를 참가자 PC의 `C:\work\kimm` 으로 복사해 씁니다. 실습 가이드는 `KIMM-ClaudeCode활용교육-오후-실습가이드`(PDF·PPTX)입니다.

## 폴더 구성

| 경로 | 내용 | 쓰는 실습 |
|------|------|-----------|
| `first\` | 규칙도 스킬도 없는 빈 폴더. 인터넷이 막혔을 때 쓰는 예비 자료(`예비자료\openalex_연도별_논문수.csv`)와 강사 결과 그래프(`예비자료\모범결과\`)만 있음 | 실습 1 |
| `research-planner\` | 연구 기획 워크스페이스. 규칙 파일(`CLAUDE.md`, 교육용 규칙 절 포함), 명령 13개(`/start` `/lit` `/grant` `/market` `/scenario` `/plan` `/paper` `/review` `/proposal` `/wrap` `/onboarding` `/kb` `/weekly`), 실습 스킬 `/lab2` `/lab2b` `/lab3` `/lab4`, 검토 담당 3개, 이력 훅과 세션 종료 대기열 훅, 검사·예약 실행 스크립트(`60-scripts`), 강의 뒤 KB 구축 안내(`KB-구축가이드.md`), 강사 따라 하기 자료(`examples\강사-따라하기\`), gptaku 플러그인 6개 자동 등록 설정. 이 폴더는 배포 zip에만 들어 있고 강의 폴더 `lab\` 에는 없음(`ops/make_dist.sh` 가 원본에 `ops/rp-overlay` 덧씌우기를 적용해 넣음). 사용법은 `research-planner\README.md` | 실습 2~4, 더 해 보기 |
| `equipment\` | 모의 장비(pyvisa-sim)와 MCP 서버. 실습 4 ③은 `equipment\practice-mcp` 폴더로 세션을 엶 | 실습 4 ③ |
| `.venv\` | 3단계에서 만드는 가상환경 | 전체 |
| `TROUBLESHOOTING.md` | 막힐 때 대응표 | 강사·보조강사 |
| `requirements.txt` | 실습용 Python 패키지(버전 고정) | 전원 |

## 자료 출처

| 자료 | 출처 | 구분 |
|------|------|------|
| 연도별 논문 수 예비 자료 | OpenAlex(openalex.org, 데이터 CC0), 2026-10-12 조회 | 공개 |
| 강사 따라 하기 자료 | `research-planner\examples\강사-따라하기\`. 강사 소개, 공개 세미나 자료 2건, 공개 저장소 README 2건(`inbox\` 5개)과 `/onboarding` 인터뷰답(`인터뷰답.md`). 실습 2 트랙 1에서 씀 | 공개 |
| 관심 주제 예시 프로필 | `research-planner\examples\연습-관심주제-AI업무\`, 이번 과업에서 만든 가상 인물 | 가상 |
| 진동시험 예시 프로필 | `research-planner\examples\가상연구자-진동시험\`, 가상 인물. 덱에서 다루지 않음 | 가상 |
| 모의 장비 | pyvisa-sim 가상 장비 정의 | 모의 |

실습 중에 Claude Code가 인터넷에서 찾는 자료(논문, 공고, 기사)는 모두 공개 자료입니다. 요청문에는 공개해도 되는 주제만 씁니다. 기계연의 실제 시험 데이터, 미공개 연구 자료, 기관 과제명, 장비 정보는 이 폴더와 요청문에 넣지 않습니다.

## Windows 기준 실행 절차

교육 전날까지 끝내 두면 당일 환경 점검이 짧아집니다. 아래 명령은 **PowerShell**에서 실행합니다. 시작 메뉴에서 `Windows PowerShell`을 엽니다. `Windows PowerShell (x86)`은 32비트라 쓰지 않습니다.

### 1. Python 3.12 확인

```powershell
py -3.12 --version
python --version
```

- `Python 3.12.x`가 나오면 다음 단계로 갑니다.
- 둘 다 안 되거나 Microsoft Store가 열리면 python.org에서 Python 3.12 Windows 설치 파일(64-bit)을 받아 설치합니다. 설치 첫 화면에서 **"Add python.exe to PATH"** 를 반드시 체크합니다. 설치 후 PowerShell 창을 새로 엽니다.
- research-planner의 이력 훅은 `python` 명령으로 실행됩니다. `python --version` 도 동작하는지 확인해 둡니다.

### 2. 실습 폴더 복사

받은 `kimm` 폴더(이 README가 있는 폴더)를 `C:\work\kimm` 으로 복사합니다. 한글이 들어간 경로(예: `바탕 화면`, `문서`)에 두지 않습니다.

```powershell
Test-Path C:\work\kimm\first
Test-Path C:\work\kimm\research-planner\CLAUDE.md
Test-Path C:\work\kimm\equipment\practice-mcp\.mcp.json
```

셋 다 `True`가 나오면 됩니다.

### 3. 가상환경 만들기

```powershell
cd C:\work\kimm
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe --version
```

`py`가 없으면 `python -m venv .venv` 로 만듭니다. 가상환경은 `C:\work\kimm\.venv` 에 둡니다. 가상환경은 **활성화하지 않고** 그 안의 파이썬을 직접 부르는 방식을 권합니다. 실행 정책 문제를 피할 수 있습니다.

활성화해서 쓰고 싶다면 `.\.venv\Scripts\Activate.ps1` 을 실행합니다. `running scripts is disabled on this system` 오류가 나면 지금 연 창에서만 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` 를 실행한 뒤 다시 활성화합니다. 기관 정책으로 이것도 막혀 있으면 활성화하지 말고 `.\.venv\Scripts\python.exe` 를 직접 씁니다.

### 4. 패키지 설치

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r equipment\requirements.txt
```

두 번째 줄은 실습 4 ③ 모의 장비(MCP)용입니다.

사내 프록시가 있는 경우 `pip install` 이 시간 초과나 인증서 오류로 실패할 수 있습니다. IT 부서에 프록시 주소를 받아 `--proxy http://주소:포트` 를 붙이거나, 강사가 준비한 휠 파일 폴더로 설치합니다(`--no-index --find-links <폴더>`). 〔현장 IT 확인 필요〕

모의 장비 MCP 서버는 데스크톱 앱이 실행합니다. 앱은 가상환경 활성화를 물려받지 않으므로, 사용자 환경 변수 `KIMM_PYTHON` 을 지정하고 **앱을 다시 시작**합니다. Windows 데스크톱 앱은 사용자·시스템 환경 변수를 물려받습니다(제조사 문서). 이 방법이 Windows에서 그대로 동작하는지는 실측하지 않았습니다. 안 되면 시스템 파이썬에 `python -m pip install --user -r equipment\requirements.txt` 로 설치합니다.

```powershell
[Environment]::SetEnvironmentVariable("KIMM_PYTHON", "C:\work\kimm\.venv\Scripts\python.exe", "User")
```

### 5. 확인 명령

```powershell
.\.venv\Scripts\python.exe -c "import numpy, matplotlib; print('ok')"
.\.venv\Scripts\python.exe research-planner\60-scripts\check_planner.py --selftest
.\.venv\Scripts\python.exe -c "import urllib.request; print(urllib.request.urlopen('https://api.openalex.org/works?filter=publication_year:2025&per-page=1', timeout=20).status)"
```

첫 줄은 `ok`, 둘째 줄은 `selftest 통과`, 셋째 줄은 `200` 이 나오면 됩니다. 셋째 줄이 인증서 오류(`CERTIFICATE_VERIFY_FAILED`)로 실패하면 사내 프록시나 파이썬 인증서 문제입니다. 실습 1은 예비 자료로 진행할 수 있습니다.

### 6. 실습 전 폴더 백업

```powershell
Copy-Item C:\work\kimm C:\work\kimm_backup -Recurse
```

되돌리기 기능은 에이전트가 명령 실행으로 바꾼 파일을 복원하지 않습니다(제조사 문서). 막히면 이 백업에서 다시 시작합니다.

### 7. 실습 2 자료 준비(선택)

써 본 분은 실습 2에서 내 자료로 워크스페이스를 만듭니다. 참가자는 공개 자료 10개 이내를 미리 준비합니다(선택). 기관 내부 자료와 미공개 자료는 넣지 않습니다. 준비하지 않은 분은 강사 따라 하기 자료로 진행합니다. 실습 4의 예약 실행(매일 `/wrap`, 매주 `/weekly`)은 CLI(`claude` 명령)가 있어야 등록할 수 있습니다.

## macOS 기준 (병기)

터미널 앱에서 실행합니다. 폴더는 `~/work/kimm` 처럼 영문 경로에 둡니다.

```bash
python3.12 --version          # 없으면 python.org 설치 파일 또는 Homebrew로 3.12 설치
cd ~/work/kimm
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r equipment/requirements.txt
.venv/bin/python research-planner/60-scripts/check_planner.py --selftest
cp -R ~/work/kimm ~/work/kimm_backup
```

macOS에는 `python` 명령이 없는 경우가 많습니다. 이력 훅은 `python` 명령으로 실행되므로 `python --version` 이 안 되면 TROUBLESHOOTING.md의 30번 행을 봅니다. python.org에서 받은 macOS용 파이썬은 인증서 설치 단계(`Install Certificates.command`)를 건너뛰면 인터넷 요청이 인증서 오류로 실패합니다(2026-10-12 강사 맥에서 확인).

## Claude Code 데스크톱 앱 준비

근거 문서: [Get started with the desktop app](https://code.claude.com/docs/en/desktop-quickstart), [Desktop application](https://code.claude.com/docs/en/desktop), [Advanced setup](https://code.claude.com/docs/en/setup) (2026-10-12 확인). 화면 이름은 영문 문서 기준이며, 한국어 화면에서 어떻게 표시되는지는 교육 전 실물로 확인합니다.

### 설치

1. 계정을 확인합니다. Claude Code는 Pro, Max, Team, Enterprise 구독이 있어야 하며 무료 플랜으로는 쓸 수 없습니다. 기관 계정(Team 등)이면 좌석에 Claude Code가 포함됐는지 관리자에게 확인합니다.
2. Windows x64용 설치 파일을 받습니다: `https://claude.ai/api/desktop/win32/x64/setup/latest/redirect` (ARM64 PC는 ARM64 설치 파일). macOS는 Universal 빌드 하나입니다.
3. 설치 파일을 실행하고, 시작 메뉴에서 Claude를 엽니다.
4. Anthropic 계정으로 로그인합니다. 기관 계정이면 기관이 안내한 로그인 방식을 따릅니다. 〔앱 실물 확인 필요: 로그인 화면 문구〕

데스크톱 앱에는 Claude Code가 들어 있어 CLI를 따로 설치하지 않아도 됩니다(제조사 문서). CLI도 쓰려면 PowerShell에서 `irm https://claude.ai/install.ps1 | iex` 로 설치하고, 새 창에서 `claude --version` 으로 확인합니다.

### 실습 폴더 열기

1. 화면 위쪽 가운데의 **Code** 탭을 누릅니다. 유료 플랜 업그레이드 안내가 뜨면 계정에 Claude Code 권한이 없는 것입니다.
2. 환경에서 **Local** 을 고릅니다(Cloud, SSH, WSL은 쓰지 않습니다).
3. **Select folder** 를 눌러 실습 1은 `C:\work\kimm\first`, 실습 2부터는 `C:\work\kimm\research-planner`, 실습 4 ③은 `C:\work\kimm\equipment\practice-mcp` 를 고릅니다.
4. 보내기 버튼 옆 모델 드롭다운에서 모델을 확인합니다. 실습은 중간 등급 모델(예: Sonnet)로 합니다. 〔앱 실물 확인 필요: 당일 목록에 보이는 모델 이름〕
5. 보내기 버튼 옆 권한 모드 선택기가 **Manual** 인지 확인합니다. 이전 버전 앱에서는 **Ask permissions** 로 표시됐습니다. 〔앱 실물 확인 필요: 한국어 화면 표기〕 앱의 모드 선택기에서 한 번 고른 모드는 폴더별로 기억되므로(제조사 문서), 시작할 때마다 화면에서 확인합니다.

### 폴더 신뢰와 플러그인

`research-planner` 를 처음 열면 "이 폴더를 신뢰하시겠습니까" 창이 뜹니다. 신뢰하면 이 폴더 설정(`.claude\settings.json`)에 적힌 gptaku-plugins 마켓(github.com/fivetaku/gptaku_plugins)과 플러그인 6개가 등록됩니다. 기관망에서 `github.com` 이 막혀 있으면 플러그인 없이 진행합니다. 명령은 웹 검색과 직접 작성으로 대신합니다.

### Windows에서 Git for Windows

Git for Windows가 없으면 에이전트가 명령 실행에 PowerShell을 씁니다. 실습은 Git 없이도 진행할 수 있습니다. 데스크톱 앱 구버전(1.49585.0 이전)은 로컬 세션 시작 때 Git 설치를 요구했으므로, "Git is required" 안내가 뜨면 앱을 최신으로 업데이트하거나 Git for Windows를 설치합니다(제조사 문서).

### 네트워크

허용이 필요한 도메인: `api.anthropic.com`, `claude.ai`, `claude.com`, `platform.claude.com`, 설치·업데이트용 `downloads.claude.ai`. 실습 1·3은 `api.openalex.org`, `www.ntis.go.kr`, `www.iris.go.kr`, 플러그인 등록은 `github.com` 에 접속합니다. 사내 프록시가 TLS를 검사하면 `unable to get local issuer certificate` 같은 오류가 납니다. 이때는 IT 부서에 사내 인증서 파일을 받아 `NODE_EXTRA_CA_CERTS` 환경 변수로 지정합니다(제조사 문서 단독 근거, 현장 확인 필요).

## 강사용 메모

- 오후 실습의 사전 실행 기록(2026-10-12, 중간 등급 모델, 헤드리스)은 강의 폴더 `_lab-archive\rehearsal-r3-20261012\` 에 있습니다(배포본에 없음). 실습 1은 28초, 실습 3 다섯 명령은 합계 약 7분 30초였습니다.
- r6(2026-10-14, `_lab-archive\rehearsal-r6-plugins-20261014\`): 플러그인 세 개(docs-guide 71초, insane-search 79초, show-me-the-prd 91초) 모두 성공. insane-search 공고 장은 이후 실습 3 `/grant fit`으로 옮겼습니다. `/wrap` 뒤 새 세션이 `90-log` 최신 기록을 읽고 요약하는 것도 확인했습니다.
- r7(2026-10-14, `_lab-archive\rehearsal-r7-onboarding-20261014\`): 덧씌우기를 적용한 배포본으로 `/onboarding` 트랙 1 92초·트랙 2 60초, `/grant fit` 75초·116초, 세션 종료 훅 대기열 생성, 다음 세션 대기열 자동 정리 37초를 확인했습니다. Windows·데스크톱 앱의 세션 종료 훅·예약 등록·선택지 표시와 자료 10개 흡수 시간은 미검증입니다.
- 이전 판의 진동시험 연구 워크스페이스(`research\`, 정답 스크립트 포함)는 `_lab-archive\research-vibration-20261012\` 로 옮겼습니다. 오전 시연용이며 배포하지 않습니다.
