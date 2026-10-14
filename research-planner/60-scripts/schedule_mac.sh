#!/bin/bash
# research-planner 자동 실행 등록 (macOS crontab)
# 매일 18:00 /wrap, 매주 월 08:30 /weekly. 조건: claude CLI 설치·로그인.
# RP_SCHEDULED=1: 세션 종료 훅이 예약 실행 세션은 대기열에 남기지 않게 한다.
# 사용: research-planner 폴더에서  bash 60-scripts/schedule_mac.sh   해제: crontab -e 에서 두 줄 삭제
DIR="$(cd "$(dirname "$0")/.." && pwd)"; CLAUDE="$(command -v claude)"
[ -n "$CLAUDE" ] || { echo "claude 명령을 찾지 못했습니다"; exit 1; }
( crontab -l 2>/dev/null | grep -v "research-planner-auto"
  echo "0 18 * * * cd \"$DIR\" && RP_SCHEDULED=1 \"$CLAUDE\" -p \"/wrap\" --permission-mode acceptEdits > logs/schedule-wrap.log 2>&1 # research-planner-auto"
  echo "30 8 * * 1 cd \"$DIR\" && RP_SCHEDULED=1 \"$CLAUDE\" -p \"/weekly\" --permission-mode acceptEdits --allowedTools \"Bash(python3 *)\" \"Bash(python *)\" WebFetch WebSearch > logs/schedule-weekly.log 2>&1 # research-planner-auto"
) | crontab -
echo "등록했습니다. 확인: crontab -l"
