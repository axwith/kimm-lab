# 막힐 때 대응표 — 오후 실습

운영 원칙: 실습은 각자 자기 PC로 합니다. 3분 넘게 막히면 손을 들고, 자리를 돌던 보조강사가 1:1로 붙습니다. 강사는 전체 진행을 멈추지 않습니다. 5분 안에 안 풀리면 강사 화면을 보며 따라가고, 쉬는 시간에 다시 봅니다.

근거 표시: (문서) 제조사 공식 문서, (이슈) 제조사 저장소 이슈, (실측) 1차 리허설 기록(강의 폴더 `_lab-archive\runs\`, 배포본에 없음), (운영) 기존 과정 운영 경험. 제조사 문서·이슈 하나만 근거인 행은 "단독"을 붙였고 교육 당일 화면에서 다시 확인합니다.

보조강사 칸: ○ 보조강사가 처리, △ 보조강사가 1차 대응하고 안 되면 강사, × 강사가 전체 안내

## 설치·로그인

| # | 증상 | 원인 | 현장 조치 | 보조강사 | 근거 |
|---|------|------|-----------|----------|------|
| 1 | Code 탭을 누르면 업그레이드 안내가 뜸 | 계정에 Claude Code가 포함된 유료 좌석이 없음(무료 플랜 불가) | 기관 관리자에게 좌석 배정 확인. 당일 해결이 안 되면 강사 화면을 보며 진행 | △ | (문서) 단독 |
| 2 | 로그인 후 `Claude Code access has not been granted for this account` | 기관 조직에서 해당 사용자 역할에 Claude Code 권한이 없음 | 기관 관리자(Owner)에게 역할 변경 요청. 그동안 강사 화면을 보며 진행 | △ | (문서) 단독 |
| 3 | 결제·좌석 미확정으로 로그인 자체가 안 됨 | 계정 결제 미완료 | 사전 안내 메일에서 확인할 항목. 당일엔 강사 화면을 보며 진행 | × | (운영) |
| 4 | `unable to get local issuer certificate`, `SELF_SIGNED_CERT_IN_CHAIN`, `TLS connect error` | 사내 프록시가 TLS를 검사함 | IT 부서에서 사내 인증서 파일을 받아 `NODE_EXTRA_CA_CERTS` 로 지정. 당일 해결이 어려우면 강사 핫스팟(소수 인원) | △ | (문서) 단독 |
| 5 | 앱이 계속 연결 중, 응답 없음 | 허용 도메인(`api.anthropic.com`, `claude.ai`, `claude.com`, `platform.claude.com`, `downloads.claude.ai`)이 막힘 | 다른 PC에서도 같은지 확인. 기관망 전체 문제면 강사 화면 시연으로 전환 | × | (문서) 단독 |
| 6 | CLI 설치 뒤 `'claude' is not recognized` | 설치 폴더가 PATH에 아직 안 잡힘 | 새 PowerShell 창을 열고 다시 실행. 그래도 안 되면 데스크톱 앱만 씀(실습은 앱 기준) | ○ | (문서) 단독 |
| 7 | `Claude Code does not support 32-bit Windows` | `Windows PowerShell (x86)` 창에서 설치함 | x86이 붙지 않은 `Windows PowerShell` 을 열고 다시 설치 | ○ | (문서) 단독 |
| 8 | `irm is not recognized` 또는 `The token '&&' is not a valid statement separator` | PowerShell용 명령을 CMD에 넣었거나 그 반대 | 프롬프트가 `PS C:\` 로 시작하는 PowerShell에서 `irm https://claude.ai/install.ps1 \| iex` 실행 | ○ | (문서) 단독 |
| 9 | `.venv\Scripts\Activate.ps1` 에서 `running scripts is disabled on this system` | PowerShell 실행 정책이 스크립트를 막음 | 활성화하지 말고 `.\.venv\Scripts\python.exe` 를 직접 씀. 꼭 활성화해야 하면 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (이 창에서만 적용) | ○ | (문서) 단독, (운영) |
| 10 | "Git is required" 안내가 뜨고 세션이 안 열림 | 데스크톱 앱 구버전(1.49585.0 이전)이 Git을 요구함 | 앱 업데이트 또는 Git for Windows 설치 | ○ | (문서) 단독 |

## Python·패키지

| # | 증상 | 원인 | 현장 조치 | 보조강사 | 근거 |
|---|------|------|-----------|----------|------|
| 11 | `python` 을 치면 Microsoft Store가 열리거나 아무 출력이 없음 | Python 미설치 상태에서 Windows의 앱 실행 별칭이 동작함 | `py -3.12 --version` 확인. 없으면 python.org 3.12(64-bit) 설치, "Add python.exe to PATH" 체크 | ○ | (운영) |
| 12 | 에이전트가 `python3` 를 불러 실패하거나 Store가 열림 | Windows에는 보통 `python3` 명령이 없음 | 실습 1(`first\`)에서는 요청문에 "파이썬은 `C:\work\kimm\.venv\Scripts\python.exe` 를 써 줘"를 넣음. `research-planner` 는 `CLAUDE.md` 에 Windows 안내가 있음 | ○ | (실측) 1차 리허설 |
| 13 | `pip install` 에서 시간 초과, 인증서 오류 | 사내 프록시가 PyPI 접근을 막음 | `--proxy` 지정, 또는 강사가 준비한 휠 폴더로 `--no-index --find-links` 설치. 안 되면 계산 단계는 강사 화면 결과로 확인 | △ | (운영) |
| 14 | `ModuleNotFoundError: No module named 'pandas'` 같은 오류 | 에이전트가 설치하지 않은 패키지를 씀 | "설치된 numpy·matplotlib 와 표준 라이브러리만 쓰라"고 다시 요청. 설치 명령 승인 창이 뜨면 무엇을 설치하는지 읽고 판단 | ○ | (실측) 1차 리허설 |
| 15 | 설치는 됐는데 에이전트 실행에서 패키지를 못 찾음 | 에이전트가 가상환경이 아닌 시스템 파이썬을 씀(데스크톱 앱은 활성화된 가상환경을 물려받지 않음) | 요청문에 `.venv` 파이썬 경로를 명시 | ○ | (실측), (문서) |
| 16 | 그래프의 한글이 네모(□)로 깨짐 | matplotlib 기본 글꼴에 한글이 없음 | "그래프 글자는 영어로" 또는 "글꼴은 Malgun Gothic(맥은 AppleGothic)으로" 요청 | ○ | (운영) |

## 파일·인코딩·경로

| # | 증상 | 원인 | 현장 조치 | 보조강사 | 근거 |
|---|------|------|-----------|----------|------|
| 17 | 파일을 찾아 달라고 했는데 "파일이 없다"고 함 | 한글이 들어간 경로에서 파일 검색이 빈 결과를 내는 문제가 보고됨 | 실습 폴더를 `C:\work\kimm` 영문 경로로 옮김. 파일 이름은 정확한 경로로 알려 줌(예: `10-literature\2026-10-15-주제-lit-review.md`) | ○ | (이슈) #84966 단독, 미실측 |
| 18 | `File is not valid UTF-8 ...` 메시지와 함께 수정이 거부됨 | 편집 도구가 UTF-8이 아닌 파일(CP949 포함)을 고치지 않음. 파일은 손상되지 않음 | 원본은 두고 UTF-8 사본을 만들어 사본으로 작업하라고 요청 | ○ | (실측) 1차 리허설 |
| 19 | 변환한 CSV를 엑셀로 열면 한글이 깨짐 | 엑셀이 BOM 없는 UTF-8을 CP949로 읽음 | 엑셀용이면 "UTF-8 BOM(utf-8-sig)으로 저장" 요청. 실습 결과 확인은 메모장·앱 파일 창으로 | ○ | (운영) |
| 20 | `PermissionError` 또는 "다른 프로세스가 파일을 사용 중" | 엑셀이 그 CSV를 열고 있어 Windows가 파일을 잠금 | 엑셀을 닫고 다시 시킴 | ○ | (운영) |
| 21 | 인터넷 요청이 `CERTIFICATE_VERIFY_FAILED` 로 실패(실습 1, 공고 검색, 인용 확인) | 사내 프록시가 TLS를 검사하거나, 파이썬 인증서 저장소가 비어 있음(macOS python.org 설치본은 `Install Certificates.command` 를 건너뛰면 이렇게 됨) | 인증서 검증을 끄라는 제안은 거부. 실습 1은 `예비자료\openalex_연도별_논문수.csv` 로, 실습 3은 `examples\연습-관심주제-AI업무\` 결과 예시로 읽으며 진행 | △ | (실측) 2026-10-12 강사 맥 |
| 22 | 조사(`/lit`, `/market`)가 5분 넘게 끝나지 않음 | 검색을 많이 하거나 insane-research가 여러 에이전트를 띄움 | 멈추고 "문헌은 5건만, 웹 검색 위주로 빠르게"를 붙여 다시 요청. 사전 실행은 명령마다 1~2분 반 | ○ | (실측) 2026-10-12 사전 실행 |
| 23 | 편집기 내장 터미널(VS Code 등)에서 한글 입력이 깨지거나 밀림 | 내장 터미널의 한글 조합 표시 문제가 보고됨 | 실습은 데스크톱 앱 입력창에서 함. 터미널이 필요하면 Windows 터미널 앱 사용 | ○ | (이슈) #97389 단독 |

## 권한·모델·한도

| # | 증상 | 원인 | 현장 조치 | 보조강사 | 근거 |
|---|------|------|-----------|----------|------|
| 24 | 승인 창 없이 에이전트가 바로 파일을 고치고 명령을 실행함 | 권한 모드가 Auto 또는 Accept edits. 최근 버전은 설정이 없으면 터미널 세션을 자동 계열 모드로 시작하고, 데스크톱 앱은 폴더별로 마지막에 고른 모드를 기억함 | 입력창 옆 모드 선택기를 **Manual** 로 바꿈. `research-planner\.claude\settings.json` 의 `"defaultMode": "default"` 확인 | ○ | (문서) 단독 |
| 25 | 승인 창이 너무 자주 떠서 진도가 안 나감 | Manual 모드는 파일 수정과 명령 실행마다 묻는 것이 정상 | 실습 1·2는 그대로 진행. 실습 3 이후 경험자는 Accept edits로 바꿔도 됨(명령 실행은 계속 물음) | ○ | (문서) |
| 26 | "세션 한도에 도달했다"는 안내와 함께 멈춤 | 5시간 세션 한도와 주간 한도. claude.ai 대화와 Claude Code가 같은 한도를 나눠 씀. 상위 모델은 한 번에 더 많이 씀 | 모델을 중간 등급으로 바꿈. 이미 걸렸으면 손을 들고 강사 화면을 보며 진행. 리허설 중에도 이 맥 계정이 한도에 걸렸음 | △ | (문서) 단독, (실측) runs 공통 |
| 27 | 모델 목록에 기대한 모델이 없음, 또는 기본값이 최상위 모델 | 계정·좌석 등급과 조직 설정에 따라 기본 모델이 다름 | 모델 드롭다운(CLI는 `/model`)에서 중간 등급 모델로 고름. 당일 목록은 화면에서 확인 | ○ | (문서) 단독 |
| 28 | 되돌리기를 했는데 파일이 원래대로 안 돌아옴 | 되돌리기(체크포인트)는 편집 도구로 바꾼 파일만 되돌리고, 명령 실행으로 바뀐 파일·외부 변경은 복원하지 않음 | `다운로드` 의 `kimm-lab-main.zip` 을 다시 풀어 `C:\work\kimm` 을 새로 만듦 | ○ | (문서) 단독 |
| 29 | 계획 모드에서 승인했는데 다시 자동으로 진행됨 | 계획 승인 선택지 중 "auto mode로 진행"을 고름 | 승인할 때 "수동으로 승인(manually approve edits)" 쪽을 고름. 〔앱 실물 확인 필요: 승인 버튼 문구〕 | ○ | (문서) 단독 |

## 훅·MCP·네트워크

| # | 증상 | 원인 | 현장 조치 | 보조강사 | 근거 |
|---|------|------|-----------|----------|------|
| 30 | 명령을 실행해도 `research-planner\logs\agent_history.jsonl` 이 생기지 않음 | 훅은 `python` 명령으로 실행됨. `python` 이 PATH에 없거나(Store 별칭, `py` 만 설치) 맥에 `python3` 만 있음. 또는 설정을 바꾼 뒤 세션을 새로 열지 않음 | `python --version` 확인. `py` 만 있으면 `.claude\settings.json` 의 `"command": "python"` 을 `"py"` 로. 맥은 `python` 이 `python3` 를 가리키게 설정. 세션을 새로 시작 | △ | (실측) 2026-10-12 사전 실행에서 66줄 기록 |
| 31 | 매 도구 호출마다 훅 오류 문구가 뜸 | `research-planner\.claude\hooks\log_tool.py` 가 없거나 세션을 다른 폴더로 엶 | 파일이 있는지, 세션 폴더가 `research-planner` 인지 확인. 없으면 실습 폴더를 다시 복사 | ○ | (운영) |
| 32 | 모의 장비 MCP 서버가 연결 안 됨, 또는 상태 읽기도 권한 거부됨 | `equipment\practice-mcp` 가 아닌 폴더로 세션을 열었거나, 폴더 신뢰를 하지 않아 허용 규칙·서버 승인이 적용되지 않음, 또는 서버를 실행하는 `python` 에 장비 키트 패키지(pyvisa 1.14.1, pyvisa-sim 0.6.0, PyYAML, mcp 1.30.0)가 없음 | `practice-mcp` 폴더로 새 세션을 열고 신뢰. `KIMM_PYTHON` 사용자 환경 변수를 가상환경 파이썬으로 지정하고 앱 재시작(`C:\work\kimm\README.md` 4단계). `pip install mcp` 만 하면 FastMCP가 없는 2.x가 깔리므로 `equipment\requirements.txt` 로 설치. 안 되면 강사 화면 시연으로 대체(사전 기록은 `_lab-archive\equipment-sim-runs\mcp\`) | △ | (운영) |
| 33 | 실습 중 와이파이가 끊김 | 기관망 장애 | 보조강사 핫스팟(소수 인원 우선). 나머지는 강사 화면과 사전 녹화본으로 따라가고 결과는 강사 화면으로 확인 | × | (운영) BPTC 비상 계획 |

## 플러그인

| # | 증상 | 원인 | 현장 조치 | 보조강사 | 근거 |
|---|------|------|-----------|----------|------|
| 34 | 플러그인 등록이나 `/plugin marketplace add` 에서 시간 초과, 접속 오류, 인증서 오류 | 기관망이 `github.com` 접속을 막거나 사내 프록시가 TLS를 검사함 | 4번 행(인증서)과 같은 조치를 먼저 봄. GitHub가 막혀 있으면 플러그인 없이 진행(research-planner 명령은 웹 검색과 직접 작성으로 대신함) | × | (운영), 사전 확인 항목 |
| 35 | 데스크톱 앱 입력창에서 `/plugin` 이 명령으로 인식되지 않음 | 앱에서 `/plugin` 지원 여부 미확인 | 입력창의 `+` → Plugins 를 먼저 봄. 안 되면 PowerShell에서 `cd C:\work\kimm\research-planner` 후 `claude` 를 실행해 확인 | △ | 〔앱 실물 확인 필요〕 |
| 36 | 설치는 됐는데 `/docs-guide` 같은 명령이 안 보임 | 플러그인은 세션을 시작할 때 읽힘 | 같은 폴더로 새 세션을 열거나 앱을 다시 시작. CLI는 `claude` 를 끝내고 다시 실행 | ○ | (문서) 플러그인 README |
| 37 | `Plugin not found` 또는 마켓 이름 오류 | 마켓 추가를 하지 않았거나 이름을 잘못 씀 | `/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git` 를 먼저 하고, 설치는 `이름@gptaku-plugins` 형식으로 | ○ | `_research/gptaku-plugins-rnd.md` |
| 38 | insane-research가 오래 걸리거나 세션 한도에 걸림 | 여러 에이전트가 함께 검색함 | 깊이 질문에 가장 짧은 쪽을 고름. 한도가 걱정되면 플러그인 대신 "웹 검색으로만" 이라고 요청 | ○ | (운영) |
| 39 | `research-planner` 폴더를 열고 신뢰했는데 플러그인이 등록되지 않음, 또는 등록 중 오류 | 이 폴더 설정(`.claude\settings.json`)이 GitHub에서 gptaku 마켓을 받아 플러그인 6개를 등록하는데, `github.com` 접속이 막혔거나 신뢰 창을 닫음 | 플러그인 없이 진행. 다시 시도하려면 같은 폴더로 새 세션을 열거나, `/start` 가 안내하는 `/plugin marketplace add`·`/plugin install` 명령을 직접 입력 | ○ | 〔앱 실물 확인 필요〕 |
| 40 | `research-planner` 에서 `check_planner.py` 실행이 `python3` 없음으로 실패 | Windows에는 보통 `python3` 명령이 없음(12번 행) | `C:\work\kimm\.venv\Scripts\python.exe 60-scripts\check_planner.py <파일>`(또는 `python`)로 실행해 달라고 요청. 스크립트 출력은 UTF-8로 고정되어 있음 | ○ | (실측) 맥에서 CP949 출력 환경으로 통과 확인, Windows 미실측 |

## 미리 확인할 것 (교육 전날·당일 아침)

1. 강사 PC에서 앱을 열고 Manual 모드, 모델 목록, 계획 모드 승인 버튼 문구, 폴더 신뢰 창을 확인합니다.
2. 기관 PC 한 대에서 README 5단계 확인 명령 세 줄을 돌려 봅니다. 셋째 줄(OpenAlex 접속)이 실패하면 실습 1은 예비 자료로 진행한다고 안내합니다.
3. 기관 PC 한 대에서 실습 1 요청문을 넣어 승인 창이 뜨는지, 한글 경로 문제가 없는지 봅니다.
4. 기관 PC 한 대에서 `C:\work\kimm\research-planner` 를 앱으로 열어 신뢰 뒤 플러그인 6개가 등록되는지 봅니다. 안 되면 플러그인 없이 진행한다고 정합니다.
5. 같은 PC에서 `/grant search 인공지능` 을 한 번 돌려 NTIS·IRIS 접속이 되는지 봅니다.
