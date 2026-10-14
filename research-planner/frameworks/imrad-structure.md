# IMRaD Structure

> 출처: Workspace_Builder 템플릿 자산의 리서치 문서화 표준과 기존 `20-archetypes/research/examples/sample-research/` 보고서 구조를 Research 단일 에이전트 흐름으로 변환했습니다. 원본 자산은 Apache License 2.0 조건을 따릅니다.

## 목적

IMRaD는 Introduction, Methods, Results, and Discussion 구조로 리서치 보고서를 작성해 질문, 방법, 발견, 해석을 분리하는 보고서 구조 프레임워크입니다.

## 호출 명세

- `commands/report.md` — 보고서 골격을 설계하는 Step 2에서 자동 적용합니다.
- 출력 변경 — `30-papers/{주제}/`에 IMRaD 섹션을 추가합니다.
- 적용 범위 — 학술 보고서, 시장 조사 보고서, 정책 검토, 기술 평가 보고서.

## 구조

- **Introduction** — 질문, 배경, 범위, 왜 중요한지 설명합니다.
- **Methods** — 자료 수집 방식, 출처 등급, 검증 방법, 분석 프레임워크를 기록합니다.
- **Results** — 검증된 발견사항과 데이터를 해석 없이 제시합니다.
- **Discussion** — 의미, 한계, 반대 근거, 시사점, 다음 질문을 정리합니다.

## 산출물 템플릿

```markdown
# [주제] 리서치 보고서

## Introduction

## Methods

## Results

## Discussion

## References
```

## 품질 기준

- Methods에 출처 검증 방법이 빠지면 안 됩니다.
- Results와 Discussion을 섞지 않습니다.
- 한계와 불확실성을 Discussion에 명시합니다.
