"""Claude Code 훅: 에이전트가 쓴 도구와 결과 요약을 logs/agent_history.jsonl에 한 줄씩 남긴다.

무엇을 언제 시켰고 어떻게 끝났는지 나중에 확인하려고 남긴다.
.claude/settings.json의 PostToolUse(성공 뒤), PostToolUseFailure(실패 뒤) 훅에 등록한다.
PreToolUse(실행 전)에도 등록하면 사람이 거절해 실행되지 않은 요청까지 "요청" 줄로 남는다.
어떤 오류가 나도 종료 코드 0으로 끝나, 기록 실패가 작업을 막지 않게 한다.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

LIMIT = 300  # 결과 요약 최대 글자 수


def short(value) -> str:
    """긴 값을 한 줄 요약으로 줄인다."""
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    value = " ".join(value.split())
    return value if len(value) <= LIMIT else value[:LIMIT] + " ...(생략)"


def what_was_done(tool: str, tool_input: dict) -> str:
    """도구별로 사람이 읽을 핵심 입력만 뽑는다."""
    for key in ("command", "file_path", "pattern", "url", "skill", "description", "prompt"):
        if key in tool_input:
            return short(f"{key}: {tool_input[key]}")
    return short(tool_input)


def main() -> None:
    data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")
    log_path = project / "logs" / "agent_history.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    event = data.get("hook_event_name", "")
    stage = {"PreToolUse": "요청", "PostToolUse": "성공", "PostToolUseFailure": "실패"}.get(event, event)
    tool = data.get("tool_name", "")
    record = {
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "session": data.get("session_id", "")[:8],
        "agent": data.get("agent_type") or "main",   # 서브에이전트가 쓴 도구면 그 이름
        "tool": tool,
        "input": what_was_done(tool, data.get("tool_input") or {}),
        "stage": stage,
        "result": short(data.get("error") or data.get("tool_response") or ""),
        "permission_mode": data.get("permission_mode", ""),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # 기록 실패는 화면에 짧게만 알리고 작업은 계속한다
        print(f"log_tool.py 기록 실패: {exc}", file=sys.stderr)
    sys.exit(0)
