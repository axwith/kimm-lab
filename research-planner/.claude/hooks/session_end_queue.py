"""Claude Code 훅(SessionEnd): 세션이 끝나면 그 세션의 도구 이력을 90-log/_queue/ 에 원자료로 남긴다.

모델을 부르지 않는다. 요약은 다음 세션 시작 때 CLAUDE.md 규칙이 /wrap 형식으로 만든다.
logs/agent_history.jsonl(log_tool.py가 쓰는 파일)에서 이 세션 줄만 골라 옮긴다.
같은 세션을 /resume 으로 이어 쓰다 다시 끝내면, 앞서 대기열에 넘긴 줄은 빼고 새 줄만 남긴다.
예약 실행(60-scripts/run_*.cmd, schedule_mac.sh 가 RP_SCHEDULED=1 을 건다)은 남기지 않는다.
어떤 오류가 나도 종료 코드 0으로 끝나 세션 종료를 막지 않는다.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def already_queued(queue: Path, session: str) -> str:
    """이 세션으로 이미 만든 대기열 파일(처리 끝난 _done 포함)의 마지막 줄 시각 중 가장 늦은 것."""
    last = ""
    for f in list(queue.glob(f"*-{session}.jsonl")) + list((queue / "_done").glob(f"*-{session}.jsonl")):
        try:
            with f.open(encoding="utf-8") as fh:
                last = max(last, json.loads(fh.readline()).get("last_time", ""))
        except (OSError, ValueError):
            continue
    return last


def main() -> None:
    if os.environ.get("RP_SCHEDULED") == "1":
        return
    data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")
    session = (data.get("session_id") or "")[:8]
    history = project / "logs" / "agent_history.jsonl"
    queue = project / "90-log" / "_queue"
    if not session or not history.exists():
        return
    since = already_queued(queue, session)
    lines, last_time = [], ""
    for line in history.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        t = rec.get("time", "")
        if rec.get("session") == session and t > since:
            lines.append(line)
            last_time = max(last_time, t)
    if not lines:  # 도구를 하나도 안 쓴 세션(또는 새로 쓴 것이 없는 세션)은 남기지 않는다
        return
    queue.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")  # 파일명에 콜론을 쓰지 않는다(Windows)
    out = queue / f"{stamp}-{session}.jsonl"
    meta = {"session": session, "ended": datetime.now().astimezone().isoformat(timespec="seconds"),
            "reason": data.get("reason", ""), "transcript": data.get("transcript_path", ""),
            "last_time": last_time}
    out.write_text(json.dumps(meta, ensure_ascii=False) + "\n" + "\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        try:  # Windows에서 stderr가 cp949일 때 인코딩 오류로 종료 코드가 바뀌지 않게
            sys.stderr.buffer.write(f"session_end_queue.py 기록 실패: {exc}\n".encode("utf-8", "replace"))
        except Exception:
            pass
    sys.exit(0)
