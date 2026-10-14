# 모의 장비 연동 실습 키트 (가상 진동 시험 장비)

이 폴더의 장비, 주소, 상한값은 모두 실습용 가상값입니다. 한국기계연구원의 실제 장비 정보나 수치를 쓰지 않았습니다. 실제 장비에 적용할 때는 장비 매뉴얼과 시험 절차서의 값으로 바꿔야 합니다.

## 1. 구성

가상 장비 세 대가 pyvisa-sim으로 만들어져 있습니다. 진동 측정기(vibdaq), 가진기 제어기(shaker), 3축 진동대(table)입니다. 장비 정의 파일 `kimm_sim.yaml`에는 장비가 받아들이는 값의 범위가 들어 있어서, 범위를 벗어난 명령에는 장비가 `ERROR`로 답합니다.

드라이버 `kimm_driver.py`가 이 장비들에 명령을 보냅니다. 드라이버는 `limits.yaml`에 적힌 더 좁은 상한을 먼저 확인하고, 그 안의 값이어도 사람이 승인해야 장비에 보냅니다. 비상 정지는 승인 없이 바로 실행합니다. 드라이버를 거친 모든 명령과 결과는 `logs/command_log.jsonl`에 기록됩니다.

이 드라이버를 쓰는 방법은 두 가지입니다. 하나는 파이썬 스크립트 `demo_safety.py`로 직접 부르는 방법이고, 다른 하나는 MCP 서버 `kimm_mcp_server.py`로 감싸 Claude Code가 도구로 부르게 하는 방법입니다. MCP로 부를 때 사람의 승인은 Claude Code의 도구 권한 확인 창이 맡습니다.

| 파일 | 역할 |
|---|---|
| `kimm_sim.yaml` | 가상 장비 정의. 장치 쪽 상한(1차 방어선) |
| `limits.yaml` | 드라이버가 지키는 2차 상한(장치 상한보다 좁음) |
| `kimm_driver.py` | 읽기 전용 함수와 동작 함수를 나눈 드라이버. 상한 확인, 승인, 비상 정지, 이력 기록 |
| `demo_safety.py` | 안전 운용 4요건 시연 스크립트 |
| `kimm_mcp_server.py` | 드라이버를 감싼 MCP 서버(stdio) |
| `practice-mcp/` | Claude Code로 여는 실습 폴더(`.mcp.json`, `.claude/settings.json`, `CLAUDE.md`) |
| `requirements.txt` | 파이썬 패키지 목록 |
| `runs/` | 실제 실행 결과 기록 |
| `logs/command_log.jsonl` | 드라이버 이력 기록(시연 1회분 예시가 들어 있음) |

가상 상한값은 다음과 같습니다.

| 항목 | 장치 상한(kimm_sim.yaml) | 드라이버 상한(limits.yaml) |
|---|---|---|
| 가진 레벨 | 0~0.50 | 0~0.30 |
| 가진 주파수 | 5~2000 Hz | 10~500 Hz |
| 진동대 X·Y 변위 | ±50 mm | ±30 mm |
| 진동대 Z 변위 | ±25 mm | ±15 mm |
| 피크 경보값 | 없음 | 0.8 g를 넘으면 비상 정지 |

## 2. 안전 운용 4요건과 지키는 층

| 요건 | 장치(kimm_sim.yaml) | 드라이버(kimm_driver.py) | Claude Code 권한(practice-mcp) | 이력 기록 |
|---|---|---|---|---|
| ① 동작 명령 전 사람의 승인 | 없음 | `approve` 콜백이 승인해야 전송. 기본은 콘솔 y/n | 동작 도구 4개를 allow에 넣지 않아 호출마다 확인 창이 뜸. 비대화형(`claude -p`)에서는 자동 거부 | 승인·거절 여부를 기록 |
| ② 동작 상한값 제한 | 범위 밖 값에 `ERROR` | 장치보다 좁은 상한을 넘으면 장치에 보내기 전에 거부 | `CLAUDE.md`가 거부된 값을 바꿔 재시도하지 말라고 지시 | 거부 사유를 기록 |
| ③ 비상 정지와 이상 시 중단 | 출력 0, 레벨 0 명령을 받음 | `emergency_stop()`은 승인 없이 즉시 실행. `monitor_once()`가 피크 경보값 초과 시 자동 정지 | `emergency_stop`만 allow에 넣어 확인 없이 바로 실행 | 정지 사유와 정지 뒤 상태를 기록 |
| ④ 모든 명령과 결과의 이력 | 없음 | `logs/command_log.jsonl`에 시각, 세션, 명령, 응답, 결과를 한 줄씩 | Claude Code 쪽 기록은 research-planner 훅(`research-planner/logs/agent_history.jsonl`) | 두 파일을 함께 보면 누가 무엇을 요청했고 장비가 어떻게 답했는지 이어짐 |

## 3. 설치와 실행

### Windows (PowerShell, Python 3.12)

```powershell
cd C:\work\kimm\equipment
python -m pip install -r requirements.txt
python demo_safety.py                    # 승인 요청마다 y 또는 n 입력
python demo_safety.py --scripted --save  # 정해진 답으로 실행하고 runs\demo_safety.out 저장
python demo_safety.py --auto-deny        # 모든 승인 요청 거절
```

### 맥 (강사 시연, /tmp 가상환경)

```bash
/opt/homebrew/bin/uv venv /tmp/kimm-venv --python 3.12
/opt/homebrew/bin/uv pip install --python /tmp/kimm-venv/bin/python -r requirements.txt
/tmp/kimm-venv/bin/python demo_safety.py --scripted --save
```

`pip install mcp`만 하면 2.x가 설치되는데, 2.x에는 FastMCP가 없습니다(MCPServer로 이름이 바뀜). 그래서 `requirements.txt`에서 `mcp==1.30.0`으로 고정했습니다.

### Claude Code에서 MCP 서버 쓰기 (practice-mcp)

```powershell
cd C:\work\kimm\equipment\practice-mcp
claude
```

- `.mcp.json`은 `python ..\kimm_mcp_server.py`를 실행합니다. 파이썬이 `python`이 아닌 다른 경로라면 실행 전에 `$env:KIMM_PYTHON = "C:\경로\python.exe"`처럼 지정합니다. 맥에서는 `KIMM_PYTHON=/tmp/kimm-venv/bin/python claude`로 엽니다.
- 처음 열면 폴더 신뢰 확인 창이 뜹니다. 신뢰해야 `.claude/settings.json`의 allow 규칙(읽기 도구, 비상 정지)이 적용됩니다. 문서에 따르면 신뢰한 폴더에서는 이 폴더 설정의 `enabledMcpjsonServers`로 서버가 승인됩니다(대화형 화면은 맥·Windows 모두 실물 미확인).
- 동작 도구 확인 창에서 "다시 묻지 않기"를 고르면 그 도구가 로컬 설정의 allow로 저장되어 이후 확인 창이 뜨지 않습니다. 실습에서는 매번 1회 승인만 고릅니다. 이것을 아예 막으려면 동작 도구 4개를 `permissions.ask`에 넣습니다. ask 규칙은 allow보다 우선해서 `--allowedTools`로 허용해도 확인을 다시 요구합니다(`runs/mcp/08`에서 확인).
- `permissions.disableBypassPermissionsMode`를 `disable`로 두어, 확인 창을 모두 건너뛰는 모드로 들어가지 못하게 했습니다.

참가자에게 시켜 볼 말: "가상 장비 상태 알려 줘", "피크 읽어 줘", "가진 레벨을 0.2로 올려 줘"(확인 창), "레벨 0.45로 올려 줘"(드라이버 거부), "비상 정지해 줘".

## 4. 시연 순서 (12분)

1. (1분) 이 장비가 가상이라는 점, 장치 상한과 드라이버 상한 표를 보여 줍니다.
2. (2분) `python demo_safety.py`를 대화형으로 실행합니다. 첫 승인 요청에 n을 입력해 레벨이 0.10 그대로인 것을 보여 주고, 두 번째에 y를 입력해 0.20으로 바뀐 것을 보여 줍니다. 요건 ①입니다.
3. (2분) 같은 실행에서 레벨 0.45, 주파수 800 Hz, Z축 20 mm가 승인 요청도 없이 거부되는 장면을 보여 줍니다. 이어서 드라이버 상한을 일부러 넓힌 경우 장치가 `ERROR`로 거부하는 장면을 보여 줍니다. 요건 ②입니다.
4. (2분) 출력을 켠 뒤 이상 피크 1.25 g를 주입하면 감시 함수가 비상 정지를 실행하고, 출력 0, 레벨 0이 되는 장면을 보여 줍니다. 요건 ③입니다.
5. (1분) 마지막에 출력되는 이번 세션 로그와 `logs/command_log.jsonl` 원본을 보여 줍니다. 요건 ④입니다.
6. (4분) `practice-mcp`에서 Claude Code를 열고 상태 읽기(확인 없이 실행), 레벨 0.2 설정(확인 창), 레벨 0.45(서버에서 거부), 비상 정지(확인 없이 실행)를 차례로 보여 준 뒤 같은 로그 파일에 `source: mcp` 줄이 추가된 것을 보여 줍니다.

시연이 막히면 `runs/demo_safety.out`과 `runs/mcp/` 기록을 대신 보여 줍니다.

## 5. 장비 기능을 MCP 서버나 CLI 도구로 만드는 일반 절차

| 단계 | 할 일 | 이 키트의 파일 |
|---|---|---|
| 1. 매뉴얼 확보 | 장비의 명령 목록, 응답 형식, 허용 범위, 비상 정지 절차를 매뉴얼에서 찾아 정리합니다 | `kimm_sim.yaml`(매뉴얼 내용을 가상 장비로 옮긴 것) |
| 2. 읽기 전용 드라이버 | 식별, 상태, 측정값 읽기처럼 장비를 움직이지 않는 함수부터 만들고 확인합니다 | `kimm_driver.py`의 `identify`, `status`, `read_peak` |
| 3. 모의 장비 시험 | 실제 장비에 연결하기 전에 같은 명령을 모의 장비에 보내 응답과 오류를 확인합니다 | `kimm_sim.yaml` + pyvisa-sim, `runs/demo_safety.out` |
| 4. 상한·승인·로그 추가 | 동작 함수에 드라이버 상한, 사람 승인, 비상 정지, 이력 기록을 붙입니다 | `limits.yaml`, `kimm_driver.py`의 `_act`, `emergency_stop`, `_log`, `demo_safety.py` |
| 5. 도구 등록 | 드라이버를 MCP 서버나 CLI로 감싸 등록하고, 읽기 도구만 자동 허용, 동작 도구는 확인 창, 비상 정지는 항상 허용으로 권한을 나눕니다 | `kimm_mcp_server.py`, `practice-mcp/.mcp.json`, `practice-mcp/.claude/settings.json`, `practice-mcp/CLAUDE.md` |

CLI 도구로 만들 때는 5단계에서 MCP 서버 대신 `python kimm_cli.py set-level 0.2` 같은 명령줄 프로그램을 만들고, Claude Code 권한 규칙에서 읽기 명령만 `Bash(python kimm_cli.py status*)`처럼 허용합니다. 상한과 로그는 드라이버에 있으므로 그대로 적용됩니다.

## 6. 실제 실행 결과 (2026-10-12, 맥)

`runs/demo_safety.out`은 `--scripted --save` 실행 결과입니다. 승인 거절 뒤 미전송, 드라이버 상한 거부 3건, 장치 상한 거부 2건, 이상 피크에 따른 비상 정지, 이번 세션 로그 20줄이 들어 있습니다.

`runs/mcp/`는 Claude Code 2.1.296(`--model sonnet`)으로 practice-mcp 복사본에서 실행한 기록입니다.

| 파일 | 확인한 것 | 결과 |
|---|---|---|
| `00_mcp_list.txt` | `claude mcp list` | 비대화형으로는 폴더 신뢰를 줄 수 없어 "Pending approval"로 표시됨. 같은 폴더의 `claude -p` 실행에서는 서버가 connected |
| `01_untrusted.txt` | 신뢰 전 상태 읽기 | 프로젝트 allow 규칙이 무시되어 `get_status`도 권한 거부 |
| `02_status.txt` | 같은 설정 파일을 `--settings`로 준 상태 읽기 | 확인 없이 실행, 상태 반환 |
| `03_action_denied.txt` | 레벨 0.20 설정 | 비대화형에서 권한 거부, 장비에 전달 안 됨 |
| `04_allowed_over_limit.txt` | `--allowedTools`로 허용 후 레벨 0.45 | 서버(드라이버)가 `rejected_by_driver`로 거부, Claude는 규칙대로 재시도하지 않고 멈춤 |
| `05_axis_over_limit.txt` | 허용 후 Z축 20 mm | `rejected_by_driver` |
| `06_mixed.txt` | 레벨 0.20(허용), 출력 켜기(미허용), 비상 정지 | 레벨 설정 완료, 출력 켜기는 권한 거부, 비상 정지는 확인 없이 실행 |
| `07_command_log_from_mcp.jsonl` | MCP 서버가 남긴 이력 | 상태 읽기, 거부 2건, 레벨 설정, 비상 정지가 `source: mcp`로 기록됨 |
| `08_ask_rule_vs_allowedtools.txt` | ask 규칙을 넣었을 때 | `--allowedTools`로 허용해도 권한 거부 |

검증 환경 메모: 일부 실행(04~08)은 강사 PC 환경 문제로 `ENABLE_TOOL_SEARCH=false`를 붙여 돌렸습니다. 참가자 PC처럼 일반 로그인 환경에서는 이 설정이 필요 없을 것으로 보지만, 교육 전 리허설에서 확인합니다. 또 비대화형 실행은 폴더 신뢰를 줄 수 없어서, 같은 `.claude/settings.json`을 `--settings`로 다시 넘겨 적용했습니다.

## 7. Windows에서 실측하지 않은 부분

- `pip install -r requirements.txt` 설치와 `demo_safety.py` 실행(코드는 pathlib과 UTF-8 파일 쓰기만 써서 경로·인코딩 문제는 없도록 작성)
- `.mcp.json`의 `${KIMM_PYTHON:-python}`과 `${KIMM_LAB_DIR:-..}`가 Windows에서 같은 방식으로 풀리는지
- 대화형 Claude Code의 폴더 신뢰 창, 동작 도구 확인 창의 실제 문구와 선택지
- PowerShell 창에서 한글 출력이 깨지지 않는지(Python 3.12는 콘솔에 UTF-8로 출력하지만, `>`로 파일에 옮기면 PowerShell 5.1은 UTF-16으로 저장하므로 `--save`를 쓰는 편이 안전)
