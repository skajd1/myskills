---
name: structured-commit-message
description: Analyze staged or working-tree changes in any Git repository and draft a structured Korean commit message for release-note automation. Use when Codex is asked to write, review, revise, or create a commit in solution, ADMIN, API, web, infrastructure, or library repositories; choose a conventional prefix; summarize affected files, reason, changes, and expected result; read optional repository-specific .commit-message.yml rules; and add machine-readable Release trailers without carrying scopes or components across repositories.
---

# 구조화 커밋 메시지

저장소마다 독립적으로 변경 내용을 분석한다. 다른 저장소에서 사용한 scope,
target, component를 현재 저장소에 재사용하지 않는다.

## 작업 순서

1. 저장소 루트에서 `git status --short`, `git diff --cached --stat`,
   `git diff --cached`로 staged 변경을 확인한다.
2. staged 변경이 없으면 working-tree diff를 확인하되 아직 커밋 대상이
   아니라는 점을 명시한다.
3. 루트에 `.commit-message.yml`이 있으면 처음부터 끝까지 읽고 scope,
   릴리즈 포함·제외 경로, target, component 규칙을 우선 적용한다.
4. 설정 파일이 없으면 현재 저장소의 디렉터리와 변경 목적에서 짧고 안정적인
   scope, target, component를 추론한다. 다른 프로젝트의 고유 명칭은 쓰지
   않는다.
5. 서로 다른 목적의 변경이 섞였으면 커밋 분리를 먼저 제안한다.
6. diff에서 확인할 수 없는 변경 내용이나 결과를 만들지 않는다.
7. 사용자가 커밋까지 요청하지 않았다면 메시지만 제안하고 Git 상태를
   변경하지 않는다.

## 제목

`<type>(<scope>): <개요>` 또는 `<type>: <개요>` 형식으로 작성한다.

- `type`: `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `ci`, `build`,
  `chore` 중 하나를 선택한다.
- `scope`: `.commit-message.yml`에 정의된 값을 우선 사용한다. 명확하지
  않으면 생략한다.
- 개요는 한국어 한 줄로 쓰고 마침표를 붙이지 않는다.
- `추가`, `수정`, `개선`, `정리`, `제거`처럼 결과가 드러나게 쓴다.

## 본문

다음 네 섹션만 작성한다.

```text
영향 파일:
- `<경로>`: <파일별 변경 요약>

수정 이유:
- <변경이 필요한 배경이나 문제>

주요 변경:
- <실제로 변경한 동작>

기대 결과:
- <사용자·운영·성능 측면의 결과>
```

영향 파일은 핵심 파일 또는 디렉터리를 최대 8개까지 적는다. 생성 파일,
캐시, 비밀 파일은 포함하지 않는다.

## 릴리즈 메타데이터

`Release-*` 필드는 Git hook 자체가 아니라 태그 파이프라인의 릴리즈노트
분류와 조합을 위한 기계 판독용 값이다.

제품 동작 또는 배포 버전 변경에는 다음 필드를 작성한다.

```text
Release-Note: <외부 사용자가 이해할 수 있는 완전한 문장>
Release-Type: <added|changed|fixed|performance|security|deprecated|removed>
Release-Targets: <현재 저장소 설정 또는 변경 경로로 판정한 대상>
Release-Components: <현재 저장소 설정 또는 변경 경로로 판정한 구성요소>
```

문서, 테스트, CI, 빌드, 내부 리팩터링 등 패치노트 제외 변경에는 다음만
작성한다.

```text
Release-Note: skip
Release-Skip-Reason: <제외 이유>
```

`.commit-message.yml`이 없는 저장소에서 target 또는 component를 확실히
판단할 수 없으면 추측값을 만들지 말고 사용자에게 필요한 값 하나만 묻는다.

## 출력

- 복사해서 바로 사용할 수 있는 하나의 완성된 커밋 메시지를 코드 블록으로
  제시한다.
- 판단이 필요한 항목이 있으면 코드 블록 뒤에 짧게 적는다.
- AI 사용 사실, 자격 증명, 비밀값, 불필요한 구현 과정을 메시지에 넣지
  않는다.
