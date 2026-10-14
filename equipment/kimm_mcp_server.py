"""가상 진동 시험 장비 MCP 서버 (실습용, stdio).

kimm_driver.KimmDriver를 MCP 도구로 감싼다. 모든 장비와 수치는 가상값이다.

승인 설계
- 사람 승인은 Claude Code의 도구 권한 확인 창이 맡는다. 동작 도구(set_level, set_frequency,
  move_axis, output_on)는 프로젝트 설정의 allow 목록에 넣지 않으므로 호출할 때마다 확인 창이 뜬다.
- 이 서버는 스스로 승인을 만들어 내지 않는다. 호출이 여기까지 왔다는 것은 Claude Code에서
  사람이 승인했다는 뜻이므로, 승인 주체를 "claude_code_permission"으로 로그에 남긴다.
- 드라이버 상한(limits.yaml), 장치 상한(kimm_sim.yaml), 이력 기록은 서버 안에서도 그대로 적용된다.
"""
from typing import Literal

from mcp.server.fastmcp import FastMCP

from kimm_driver import KimmDriver


def claude_code_permission(description: str) -> bool:
    """Claude Code 권한 확인 창을 통과한 호출만 이 서버에 도착한다."""
    return True


drv = KimmDriver(approve=claude_code_permission, source="mcp")
mcp = FastMCP("kimm-equipment")


# ---------- 읽기 전용 도구 ----------
@mcp.tool()
def get_status() -> dict:
    """가상 가진기·3축 진동대·측정기의 현재 상태를 읽는다. 장비를 움직이지 않는다."""
    return {"virtual": True, "session": drv.session, **drv.status()}


@mcp.tool()
def read_peak() -> dict:
    """가상 측정기 CH1의 피크 가속도(g)를 읽는다. 장비를 움직이지 않는다."""
    peak = drv.read_peak()
    return {"virtual": True, "peak_g": peak, "alarm_g": drv.limits["monitor"]["peak_alarm_g"]}


# ---------- 동작 도구 (Claude Code 확인 창 + 상한 + 로그) ----------
@mcp.tool()
def set_level(level: float) -> dict:
    """가상 가진기의 가진 레벨을 설정한다. 드라이버 상한을 넘으면 거부된다."""
    return drv.set_level(level)


@mcp.tool()
def set_frequency(hz: float) -> dict:
    """가상 가진기의 가진 주파수(Hz)를 설정한다. 드라이버 범위를 벗어나면 거부된다."""
    return drv.set_frequency(hz)


@mcp.tool()
def move_axis(axis: Literal["x", "y", "z"], mm: float) -> dict:
    """가상 3축 진동대의 한 축을 지정 변위(mm)로 옮긴다. 축별 상한을 넘으면 거부된다."""
    return drv.move_axis(axis, mm)


@mcp.tool()
def output_on() -> dict:
    """가상 가진기 출력을 켠다. 현재 레벨이 상한을 넘으면 거부된다."""
    return drv.output_on()


# ---------- 비상 정지 (항상 허용) ----------
@mcp.tool()
def emergency_stop(reason: str = "Claude Code에서 비상 정지 요청") -> dict:
    """가상 가진기 출력을 즉시 끄고 레벨을 0으로 만든다. 승인 없이 실행된다."""
    return drv.emergency_stop(reason)


if __name__ == "__main__":
    mcp.run()  # 기본 stdio
