# matplotlib 한글 글꼴 지정 — 공식 문서 확인 (2026-10-14)

## 가정 (사전 실행이라 묻지 않고 정한 것)

- CSV에는 주제 5개(AI 에이전트·돌봄 로봇·폐배터리 재활용·수면 웨어러블·배달 로봇)가 들어 있어, 한 장에 5칸으로 나눠 그렸습니다. 주제별 논문 수 차이가 600배(8편~4,844편)라 한 축에 합치면 작은 주제가 안 보이기 때문입니다. 칸마다 세로축 눈금이 다릅니다(그림 아래 문구로 표시).
- 글꼴은 이 Mac에 설치된 Apple SD Gothic Neo를 썼습니다. 다른 컴퓨터에서는 스크립트가 후보(AppleGothic, Nanum Gothic, Malgun Gothic, Noto Sans CJK KR) 중 설치된 첫 글꼴을 고릅니다.
- 그래프 스크립트는 `60-scripts/plot_openalex_bar.py` 에 두었습니다(쓰기 허용 범위 안).

## 공식 문서 기준 방법

DejaVu Sans(기본 글꼴)는 한글을 지원하지 않으므로, `font.family` 목록 맨 앞에 한글 글꼴을 붙이고 끝에 일반 계열(`sans-serif`)을 남깁니다.

```python
matplotlib.rcParams['font.family'] = ['Apple SD Gothic Neo', 'sans-serif']
```

- 대안: `font.family = ['sans-serif']` 로 두고 `font.sans-serif` 목록 앞에 글꼴을 넣는 방법.
- 요소별로 지정하려면 `fontname`·`fontproperties` 인자를 씁니다.
- matplotlib이 볼 수 있는 글꼴 이름은 `matplotlib.font_manager.get_font_names()` 로 확인합니다.
- 3.6 버전부터는 `family=[...]` 목록을 주면 글자마다 목록에서 그 글자를 가진 첫 글꼴로 그립니다(글꼴 대체).

## 참고한 공식 문서 주소

1. 한글 등 비라틴 글자 지정(핵심): https://matplotlib.org/stable/users/explain/text/text_props.html — "Text with non-latin glyphs" 절
2. 글꼴 선택·대체 목록 원리: https://matplotlib.org/stable/users/explain/text/fonts.html

## 산출물

- 그래프: `openalex_연도별_논문수_막대그래프.png` (OpenAlex 2026-10-12 수집 CSV 기준, 직접 눈으로 한글 표시 확인)
- 데이터: `../../first/예비자료/openalex_연도별_논문수.csv` (읽기만 함)

## 미확인

- `axes.unicode_minus = False` 는 스크립트에 넣었지만, 위 두 문서에서는 이 설정에 대한 설명을 찾지 못했습니다(이 그래프에는 음수가 없어 결과에는 영향이 없습니다). 근거는 일반 지식이며 공식 문서 확인은 아직 안 했습니다.
- Windows·Linux에서 같은 코드가 동작하는지는 이 Mac에서만 실행해 확인했습니다.
