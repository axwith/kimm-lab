# CRAAP Test

> 출처: Workspace_Builder 템플릿 자산 변환. 원본 자산은 Apache License 2.0 조건을 따릅니다.

## 목적

CRAAP Test는 Currency, Relevance, Authority, Accuracy, Purpose 기준으로 출처 신뢰도를 점수화해 핵심 주장에 사용할 수 있는 자료와 참고용 자료를 구분하는 검증 프레임워크입니다.

## 호출 명세

- `/lit` 출처 등급 단계와 `/review` 에서 적용합니다.
- 출력 변경 — `10-literature/sources/source_grades.md`에 CRAAP 점수와 A~E 등급을 추가합니다.
- 적용 범위 — 웹 문서, 보고서, 논문, 언론 기사, 통계 자료, 인터뷰.

## 5개 기준

- **Currency** — 발행일, 업데이트일, 주제의 최신성 요구와 맞는지 확인합니다.
- **Relevance** — 리서치 질문에 직접 관련되는지 확인합니다.
- **Authority** — 저자, 기관, 전문성, 책임 소재를 확인합니다.
- **Accuracy** — 다른 출처와 일치하는지, 원자료가 있는지 확인합니다.
- **Purpose** — 정보 제공, 광고, 정치, 홍보 등 목적과 편향을 확인합니다.

## 점수와 등급

- 80~100점 — A, 핵심 사실로 사용 가능
- 60~79점 — B, 보조 자료로 사용하고 교차 확인 권장
- 40~59점 — C, 참고만 하고 핵심 근거로는 부적합
- 20~39점 — D, 관점 자료로만 기록
- 0~19점 — E, 사용 금지

## 산출물 템플릿

```markdown
## 출처 평가

- 제목:
- URL/DOI:
- Currency:
- Relevance:
- Authority:
- Accuracy:
- Purpose:
- 총점:
- 등급:
- 사용 가능 범위:
```

## 품질 기준

- 핵심 수치의 출처는 A 또는 B를 우선합니다.
- C 이하는 핵심 주장에 단독으로 쓰지 않습니다.
- 목적과 편향이 불분명하면 사용 범위를 제한합니다.
