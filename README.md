# My Codex Skills

개인 Codex 스킬을 관리하는 저장소입니다. 이 저장소는 GitHub 백업용 repo이면서, 로컬에서는 Codex 스킬 저장소 루트로 사용합니다.

## 구조

```text
.
├─ AGENTS.md
├─ README.md
├─ .gitignore
├─ skill-manager/
├─ cover-letter-tailor/
├─ humanize-korean/
├─ inspection-uploader/
├─ ssh-runner/
└─ structured-commit-message/
```

- `AGENTS.md`: Codex가 이 저장소에서 따라야 할 운영 규칙
- `README.md`: 사람이 읽는 저장소 소개와 스킬 목록
- `.system/`: Codex 시스템 제공 스킬. Git에 추적하지 않음
- 각 최상위 스킬 폴더: 하나의 개인 스킬

## 스킬 목록

### skill-manager

이 저장소 자체를 관리하는 메인 스킬입니다. 스킬 생성, 수정, 이름 변경, 삭제, 검증, 커밋, GitHub 푸시에 사용합니다.

### cover-letter-tailor

기업명, 직무, JD, 자기소개서 문항을 바탕으로 기존 경험 자료를 활용해 한국어 자기소개서 답변을 맞춤 작성합니다.

### humanize-korean

AI가 쓴 티가 나는 한국어 문장을 의미와 사실관계는 유지한 채 더 자연스러운 사람 문장으로 윤문합니다.

### inspection-uploader

Outlook으로 받은 검사 PDF를 스캔하고 고객사를 식별한 뒤, 승인된 파일을 SharePoint 업로드용으로 준비합니다.

### ssh-runner

OpenSSH 클라이언트와 로컬 전용 호스트 별칭 설정으로 SSH 서버에 접속해 제한된 원격 명령을 실행하고 결과를 요약합니다.

### structured-commit-message

솔루션, ADMIN, API 등 여러 저장소에서 변경 내용을 분석하고 저장소별 설정에 맞는 구조화된 한국어 커밋 메시지와 릴리즈노트 메타데이터를 작성합니다.

## 관리 흐름

스킬을 새로 만들거나 수정한 뒤 GitHub에 반영하려면 Codex에서 `skill-manager`를 사용합니다.

일반 흐름:

1. 변경된 스킬 폴더와 저장소 메타데이터를 확인합니다.
2. 가능한 경우 스킬 validator로 `SKILL.md`를 검증합니다.
3. 의도한 파일만 명시적으로 stage합니다.
4. 커밋합니다.
5. `origin/main`으로 push합니다.

## 추적하지 않는 항목

다음 항목은 Git에 올리지 않습니다.

- `.system/`
- `docs/superpowers/`
- 캐시와 임시 파일
- 로그
- 생성 미리보기
- 로컬 스크래치 출력
- `ssh-runner/config/hosts.conf`의 로컬 SSH 호스트 별칭

## 원격 저장소

현재 원격 저장소는 `git remote get-url origin`으로 확인합니다.
