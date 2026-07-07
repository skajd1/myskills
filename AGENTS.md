# 개인 Codex 스킬 저장소 운영 지침

이 저장소는 사용자의 개인 Codex 스킬 컬렉션이자 로컬 스킬 저장소입니다. Codex는 이 파일을 저장소 운영 규칙으로 읽고 따라야 합니다.

## 스킬 인덱스

### skill-manager

이 저장소 자체를 관리하는 메인 스킬입니다. 개인 스킬 생성, 수정, 이름 변경, 삭제, 검증, 커밋, GitHub 푸시, `AGENTS.md`와 `.gitignore` 정합성 정리에 사용합니다.

### cover-letter-tailor

기업명, 직무, JD, 자기소개서 문항을 바탕으로 기존 경험 자료를 활용해 한국어 자기소개서 답변을 맞춤 작성합니다.

### humanize-korean

AI가 쓴 티가 나는 한국어 문장을 의미와 사실관계는 유지한 채 더 자연스러운 사람 문장으로 윤문합니다.

### inspection-uploader

Outlook으로 받은 검사 PDF를 스캔하고 고객사를 식별한 뒤, 승인된 파일을 SharePoint 업로드용으로 준비합니다.

### ssh-runner

사용자가 지정한 SSH 서버에 접속해 제한된 원격 명령을 실행하고 결과를 요약합니다.

### youtube-shorts-pipeline

한국어 YouTube Shorts 자동화 작업에서 주제 발굴, 대본 작성, 메타데이터 작성, 제작 흐름을 지원합니다.

## 저장소 운영 규칙

- 최상위 폴더 하나는 개인 스킬 하나를 의미합니다.
- 각 스킬은 해당 작업을 수행하는 데 필요한 지침과 리소스에 집중합니다.
- 각 스킬 폴더의 필수 파일은 `SKILL.md`입니다.
- `agents/openai.yaml`, `references/`, `scripts/`, `assets/`, `tests/`는 스킬에 실제로 필요할 때만 둡니다.
- 시스템 제공 스킬, 캐시, 임시 파일, 생성 미리보기, 로그, 로컬 스크래치 출력, superpowers 설계/계획 문서는 Git에 추적하지 않습니다.
- 개인 스킬을 추가, 삭제, 이름 변경하면 이 파일의 스킬 인덱스도 함께 갱신합니다.
- 이 저장소에서 스킬 변경이 발생하고 GitHub 반영이 필요하면 `skill-manager` 스킬을 사용해 검증, 선택적 staging, commit, push 절차를 진행합니다.
- GitHub에서 사람이 읽는 소개와 사용법은 `README.md`에 둡니다.
