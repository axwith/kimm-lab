# research-planner 자동 실행 등록 (Windows 작업 스케줄러)
# - 매일 18:00   60-scripts\run_wrap.cmd   : claude -p "/wrap"   오늘 기록과 대기열(90-log\_queue) 정리
# - 매주 월 08:30 60-scripts\run_weekly.cmd : claude -p "/weekly" 새 공고 스캔 → 50-grants\{날짜}-weekly.md
# 조건: Claude Code CLI 설치·로그인(claude --version 이 동작). 데스크톱 앱만 있으면 동작하지 않는다.
# 예약 실행은 승인 창에 답할 사람이 없으므로 파일 편집·대기열 옮기기·python 스크립트·웹 조회만 허용한다(run_*.cmd 참고).
# 사용: research-planner 폴더에서  powershell -ExecutionPolicy Bypass -File 60-scripts\schedule_windows.ps1
# 해제: Unregister-ScheduledTask -TaskName research-planner-wrap -Confirm:$false
#       Unregister-ScheduledTask -TaskName research-planner-weekly -Confirm:$false
# 이 파일은 UTF-8(BOM 포함)로 저장한다. BOM이 없으면 Windows PowerShell 5.1이 한글을 CP949로 읽어 깨진다.
# schtasks /TR 대신 ScheduledTasks 명령을 쓰는 이유: 경로에 공백이 있을 때 따옴표 전달이 PowerShell 버전마다 달라 깨진다.
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Host "claude 명령을 찾지 못했습니다. CLI를 먼저 설치하세요: irm https://claude.ai/install.ps1 | iex"; exit 1 }
$rp = Split-Path -Parent $PSScriptRoot
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1)
$jobs = @(
  @{ Name = "research-planner-wrap";   Cmd = "run_wrap.cmd";   Trigger = (New-ScheduledTaskTrigger -Daily -At "18:00") },
  @{ Name = "research-planner-weekly"; Cmd = "run_weekly.cmd"; Trigger = (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "08:30") }
)
foreach ($j in $jobs) {
  $cmd = Join-Path $PSScriptRoot $j.Cmd
  $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$cmd`"" -WorkingDirectory $rp
  try {
    Register-ScheduledTask -TaskName $j.Name -Action $action -Trigger $j.Trigger -Settings $settings -Force -ErrorAction Stop | Out-Null
    Write-Host "등록: $($j.Name) → $cmd"
  } catch {
    Write-Host "등록 실패: $($j.Name) — $($_.Exception.Message)"; exit 1
  }
}
Write-Host "등록했습니다. 확인: Get-ScheduledTask -TaskName research-planner-*   지금 한 번 돌려 보기: Start-ScheduledTask -TaskName research-planner-wrap"
Write-Host "결과 로그: $rp\logs\schedule-wrap.log, $rp\logs\schedule-weekly.log (PC가 꺼져 있던 시각의 작업은 켜진 뒤 실행됩니다)"
