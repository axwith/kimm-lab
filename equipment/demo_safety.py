"""안전 운용 4요건 시연 (가상 장비).

실행 예:
  python demo_safety.py              # 승인 요청마다 강사가 y/n 입력
  python demo_safety.py --scripted --save   # 정해진 답(첫 요청 n, 이후 y)으로 실행하고 runs/demo_safety.out 저장
  python demo_safety.py --auto-deny  # 모든 승인 요청을 거절 (아무 명령도 장치로 가지 않음)
"""
import argparse
import json
import sys
from pathlib import Path

from kimm_driver import HERE, KimmDriver, console_approve


class Tee:
    """화면과 파일에 같은 내용을 쓴다."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for s in self.streams:
            s.write(text)

    def flush(self):
        for s in self.streams:
            s.flush()


def make_approver(mode: str):
    answers = iter(["n"])  # --scripted: 첫 요청만 거절, 이후는 승인

    def scripted_approve(description: str) -> bool:
        if mode == "auto-approve":
            answer = "y"
        elif mode == "auto-deny":
            answer = "n"
        else:
            answer = next(answers, "y")
        print(f"[승인 요청] {description}. 보낼까요? (y/N): {answer}  (자동 응답)")
        return answer == "y"

    return console_approve if mode == "interactive" else scripted_approve


def title(text: str) -> None:
    print("\n" + "=" * 60 + f"\n{text}\n" + "=" * 60)


def show(label: str, value) -> None:
    print(f"{label}: {json.dumps(value, ensure_ascii=False)}")


def main() -> None:
    p = argparse.ArgumentParser(description="가상 장비 안전 운용 4요건 시연")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--scripted", action="store_const", const="scripted", dest="mode")
    g.add_argument("--auto-approve", action="store_const", const="auto-approve", dest="mode")
    g.add_argument("--auto-deny", action="store_const", const="auto-deny", dest="mode")
    p.add_argument("--save", action="store_true", help="출력을 runs/demo_safety.out 에도 저장")
    args = p.parse_args()
    mode = args.mode or "interactive"

    if args.save:
        out = (HERE / "runs" / "demo_safety.out")
        out.parent.mkdir(exist_ok=True)
        sys.stdout = Tee(sys.__stdout__, out.open("w", encoding="utf-8"))

    drv = KimmDriver(approve=make_approver(mode), source="demo_safety")
    print(f"모드: {mode} / 세션: {drv.session} / 모든 장비와 수치는 가상값입니다.")
    show("장비 식별", drv.identify())
    show("시작 상태", drv.status())
    show("드라이버 상한(limits.yaml)", drv.limits)

    title("요건 1. 장비 동작 명령 전 사람의 승인")
    show("레벨 0.20 설정 요청", drv.set_level(0.20))
    show("거절 뒤 장치 상태", {"shaker_level": drv.status()["shaker_level"]})
    show("같은 요청 다시", drv.set_level(0.20))
    show("승인 뒤 장치 상태", {"shaker_level": drv.status()["shaker_level"]})

    title("요건 2-1. 드라이버 상한: 장치에 보내기 전에 거부 (승인 요청도 뜨지 않음)")
    show("레벨 0.45 (드라이버 상한 0.30)", drv.set_level(0.45))
    show("주파수 800 Hz (드라이버 범위 10~500)", drv.set_frequency(800))
    show("Z축 20 mm (드라이버 상한 ±15)", drv.move_axis("z", 20))
    show("X축 25 mm (상한 이내)", drv.move_axis("x", 25))

    title("요건 2-2. 장치 상한: 드라이버 상한을 잘못 풀어 둔 경우에도 장치가 거부")
    safe_limits = drv.limits
    drv.limits = {**safe_limits, "shaker": {**safe_limits["shaker"], "level_max": 1.0},
                  "table": {"x_mm": 100, "y_mm": 100, "z_mm": 100}}
    print("(시연을 위해 드라이버 상한을 일부러 넓힘: 레벨 1.0, 축 ±100 mm)")
    show("레벨 0.80 (장치 상한 0.50)", drv.set_level(0.80))
    show("Z축 40 mm (장치 상한 ±25)", drv.move_axis("z", 40))
    drv.limits = safe_limits
    print("(드라이버 상한 원래대로 복구)")
    show("현재 상태", drv.status())

    title("요건 3. 비상 정지 및 이상 상황 시 중단")
    show("주파수 100 Hz", drv.set_frequency(100))
    show("출력 켜기", drv.output_on())
    show("감시 1회 (정상)", drv.monitor_once())
    print("(모의 장비에 이상 피크 1.25 g를 주입. 실습 전용 명령)")
    drv.sim_inject_peak(1.25)
    show("감시 1회 (이상)", drv.monitor_once())
    show("비상 정지 뒤 상태", drv.status())

    title("요건 4. 모든 명령과 결과의 이력 기록 (이번 세션 로그)")
    print(f"파일: {drv.log_path.relative_to(HERE)}")
    for line in drv.log_path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec["session"] != drv.session:
            continue
        cmd = rec.get("command") or rec.get("action")
        approved = "-"
        if "approved" in rec:
            approved = {True: "승인", False: "거절", None: "묻지 않음"}.get(rec["approved"], rec["approved"])
        result = rec.get("result") or ("읽기" if rec["kind"] == "read" else rec.get("response"))
        print(f"{rec['time']} | {rec['kind']:<14} | {str(cmd):<18} | 승인={approved} | 결과={result}")
    drv.close()


if __name__ == "__main__":
    main()
