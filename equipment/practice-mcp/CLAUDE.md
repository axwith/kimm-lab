# 가상 장비 실습 안전 규칙

이 폴더의 장비(kimm-equipment MCP 서버)는 실습용 가상 장비입니다. 실제 장비나 실제 수치가 아닙니다.

1. 장비를 움직이는 도구(set_level, set_frequency, move_axis, output_on)는 한 번에 하나씩 호출하고, 호출 전에 무엇을 왜 바꾸는지 한 문장으로 먼저 말합니다.
2. 동작 도구가 거부되면(rejected_by_driver, rejected_by_device, 권한 거부) 값을 바꿔 다시 시도하지 말고 결과를 그대로 보고한 뒤 사람의 지시를 기다립니다.
3. 피크가 경보값을 넘거나 이상한 응답이 나오면 즉시 emergency_stop을 호출하고 보고합니다.
4. 상한값 파일(limits.yaml, kimm_sim.yaml)과 로그 파일(logs/)은 수정하거나 지우지 않습니다.
5. 이 폴더의 .claude/settings.json에서 동작 도구를 allow 목록에 넣지 않습니다. 동작 도구는 매번 사람이 확인 창에서 승인합니다.
