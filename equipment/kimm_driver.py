"""가상 진동 시험 장비 드라이버 (실습용, 실제 장비 아님).

pyvisa-sim 모의 장비(kimm_sim.yaml)에 SCPI 방식 명령을 보낸다.
- 읽기 전용 함수: identify, status, read_peak
- 동작 함수: set_level, set_frequency, move_axis, output_on
  limits.yaml의 2차 상한을 넘으면 장치에 보내지 않고 거부한다.
  넘지 않아도 approve 콜백이 승인해야 보낸다.
- emergency_stop: 승인 없이 즉시 출력을 끄고 레벨을 0으로 만든다.
- 모든 명령, 응답, 거부, 승인 여부를 logs/command_log.jsonl에 한 줄씩 남긴다.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

import pyvisa
import yaml

HERE = Path(__file__).resolve().parent
ADDRESS = {
    "vibdaq": "TCPIP0::192.168.0.10::inst0::INSTR",
    "shaker": "TCPIP0::192.168.0.11::inst0::INSTR",
    "table": "TCPIP0::192.168.0.12::inst0::INSTR",
}


def console_approve(description: str) -> bool:
    """기본 승인 방식: 콘솔에서 사람이 y를 입력해야 보낸다."""
    answer = input(f"[승인 요청] {description}. 보낼까요? (y/N): ")
    return answer.strip().lower() == "y"


def load_limits(path=HERE / "limits.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


class KimmDriver:
    def __init__(self, approve=console_approve, limits=None, log_path=None, source="python"):
        self.approve = approve
        self.limits = limits if limits is not None else load_limits()
        self.log_path = Path(log_path) if log_path else HERE / "logs" / "command_log.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.source = source
        self.session = uuid.uuid4().hex[:8]
        self.rm = pyvisa.ResourceManager(f"{HERE / 'kimm_sim.yaml'}@sim")
        self.dev = {
            name: self.rm.open_resource(addr, read_termination="\n", write_termination="\n")
            for name, addr in ADDRESS.items()
        }

    # ---------- 이력 기록 ----------
    def _log(self, entry: dict) -> None:
        line = {"time": datetime.now().astimezone().isoformat(timespec="seconds"),
                "session": self.session, "source": self.source, **entry}
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    def _ask(self, device: str, command: str) -> str:
        return self.dev[device].query(command)

    # ---------- 읽기 전용 ----------
    def identify(self) -> dict:
        result = {name: self._ask(name, "*IDN?") for name in self.dev}
        self._log({"kind": "read", "action": "identify", "response": result})
        return result

    def status(self) -> dict:
        result = {
            "shaker_output": int(self._ask("shaker", "OUTP?")),
            "shaker_level": float(self._ask("shaker", "LEV?")),
            "shaker_freq_hz": float(self._ask("shaker", "FREQ?")),
            "table_x_mm": float(self._ask("table", "POS:X?")),
            "table_y_mm": float(self._ask("table", "POS:Y?")),
            "table_z_mm": float(self._ask("table", "POS:Z?")),
            "daq_rate": int(self._ask("vibdaq", "ACQ:RATE?")),
        }
        self._log({"kind": "read", "action": "status", "response": result})
        return result

    def read_peak(self) -> float:
        peak = float(self._ask("vibdaq", "MEAS:CH1:PEAK?"))
        self._log({"kind": "read", "action": "read_peak", "command": "MEAS:CH1:PEAK?", "response": peak})
        return peak

    # ---------- 동작 (상한 확인 후 승인) ----------
    def _act(self, action: str, device: str, command: str, violation: str | None) -> dict:
        entry = {"kind": "action", "action": action, "device": device, "command": command,
                 "approver": getattr(self.approve, "__name__", "approve")}
        if violation:
            out = {"result": "rejected_by_driver", "sent": False, "reason": violation}
            self._log({**entry, "approved": None, **out})
            return out
        if not self.approve(f"{device}에 '{command}' 전송"):
            out = {"result": "denied_by_operator", "sent": False, "reason": "사람이 승인하지 않음"}
            self._log({**entry, "approved": False, **out})
            return out
        response = self._ask(device, command)
        if response == "OK":
            out = {"result": "done", "sent": True, "response": response}
        else:
            out = {"result": "rejected_by_device", "sent": True, "response": response,
                   "reason": "장치가 범위 밖 값으로 판단해 거부"}
        self._log({**entry, "approved": True, **out})
        return out

    def set_level(self, level: float) -> dict:
        top = self.limits["shaker"]["level_max"]
        bad = None if 0.0 <= level <= top else f"가진 레벨 {level}이 드라이버 상한 0~{top}을 벗어남"
        return self._act("set_level", "shaker", f"LEV {level:.2f}", bad)

    def set_frequency(self, hz: float) -> dict:
        lo, hi = self.limits["shaker"]["freq_min_hz"], self.limits["shaker"]["freq_max_hz"]
        bad = None if lo <= hz <= hi else f"주파수 {hz} Hz가 드라이버 범위 {lo}~{hi} Hz를 벗어남"
        return self._act("set_frequency", "shaker", f"FREQ {hz:.1f}", bad)

    def move_axis(self, axis: str, mm: float) -> dict:
        axis = axis.lower()
        if axis not in ("x", "y", "z"):
            return self._act("move_axis", "table", f"POS:{axis.upper()} {mm:.1f}", f"없는 축 '{axis}'")
        top = self.limits["table"][f"{axis}_mm"]
        bad = None if abs(mm) <= top else f"{axis.upper()}축 변위 {mm} mm가 드라이버 상한 ±{top} mm를 벗어남"
        return self._act("move_axis", "table", f"POS:{axis.upper()} {mm:.1f}", bad)

    def output_on(self) -> dict:
        level = float(self._ask("shaker", "LEV?"))
        top = self.limits["shaker"]["level_max"]
        bad = None if level <= top else f"현재 레벨 {level}이 상한 {top}을 넘어 출력을 켤 수 없음"
        return self._act("output_on", "shaker", "OUTP 1", bad)

    # ---------- 비상 정지 (승인 없이 즉시) ----------
    def emergency_stop(self, reason: str = "수동 비상 정지") -> dict:
        responses = {"OUTP 0": self._ask("shaker", "OUTP 0"), "LEV 0.00": self._ask("shaker", "LEV 0.00")}
        after = {"shaker_output": int(self._ask("shaker", "OUTP?")),
                 "shaker_level": float(self._ask("shaker", "LEV?"))}
        out = {"result": "stopped", "reason": reason, "response": responses, "after": after}
        self._log({"kind": "emergency_stop", "action": "emergency_stop", "approved": "승인 불필요", **out})
        return out

    def monitor_once(self) -> dict:
        """피크를 한 번 읽고, 경보값을 넘으면 비상 정지한다."""
        peak = self.read_peak()
        alarm = self.limits["monitor"]["peak_alarm_g"]
        if peak > alarm:
            return self.emergency_stop(f"이상 감지: 피크 {peak} g가 경보값 {alarm} g 초과")
        return {"result": "normal", "peak_g": peak, "alarm_g": alarm}

    # ---------- 실습 전용: 이상 상황 흉내 ----------
    def sim_inject_peak(self, value: float) -> None:
        """모의 장비의 측정 피크를 바꾼다. 실제 장비에는 없는 실습 전용 명령이다."""
        response = self._ask("vibdaq", f"SIM:CH1:PEAK {value:.3f}")
        self._log({"kind": "sim_inject", "command": f"SIM:CH1:PEAK {value:.3f}", "response": response})

    def close(self) -> None:
        for d in self.dev.values():
            d.close()
        self.rm.close()
