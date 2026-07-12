---
name: cover-letter-tailor
description: Use when the user provides a company name, job description/JD, role, or self-introduction prompts and wants Korean 자기소개서/cover-letter answers tailored from existing application materials, polished for final Markdown output.
---

# Cover Letter Tailor

## Overview

Produce company- and role-specific Korean 자기소개서 answers by combining the user's existing self-introduction archive with the provided company name, JD, and prompts. Preserve truthful experience, improve fit and fluency, and deliver a final `.md` artifact.

## Required Inputs

Draft를 작성하기 전에 아래 세 종류의 근거를 모두 확보한다.

- 기업명, 직무명, 제공된 JD 원문, 자기소개서 문항과 글자 수 제한
- 기존 경험 자료
- 공식 회사 자료

JD가 이미지, 표, 또는 링크의 발췌로 제공되면 실제 공고 내용을 먼저 충실하게 전사한다. 전사한 JD와 이후의 해석·추천은 반드시 구분한다.

공식 회사 자료는 채용 페이지, 공식 회사·사업 소개, IR·지속가능경영 자료, 뉴스룸 순으로 사용한다. 회사 관련 사실마다 자료 제목, URL, 확인일, 답변에 사용하는 사실을 기록한다. 공식 자료에서 확인되지 않은 회사 사실은 작성하지 않는다.

JD 또는 기존 경험 자료가 없으면 사용자에게 요청한다. 공식 회사 자료가 없으면 공식 자료를 조사한다. 세 종류의 근거가 모두 갖춰질 때까지 Draft 작성을 시작하지 않는다. 최대 글자 수가 제공되면 최종본은 해당 제한의 80-95%를 목표로 한다.

개인 경험의 기준 파일은 `references/user-profile.md`이다. 사용자가 경험을 추가하거나 수정하면 이 파일을 업데이트한다. 작업공간의 경험 파일은 참조하지 않는다.

## Source Review

Before drafting, read the skill-directory sources:

- Read `references/user-profile.md` as the sole reusable experience and competency profile.
- When the user provides an experience update, update `references/user-profile.md` first. Preserve unmodified facts and record the experience's project, role, action, technology, metric, result, and value when supplied.
- Do not read `개인_경험_역량_분석.md`, workspace 자기소개서 files, or adjacent workspace materials as experience sources.
- Read `README.md`, `자소서_작업_워크플로우.md`, `자소서_작성_규격.md`, `자소서_작성_요령.md`, `자소서_템플릿.md`, and `humanizer_사용법.md` only when they exist inside this skill directory.
- Read `references/company-role-profile.md` and fill its fields from the JD and official company materials.
- Extract reusable evidence from `references/user-profile.md`: project, role, action, technology, metric, result, and value.
- Watch for stale company names in reused text. Never leave another company's name in the final answer unless it is part of an experience.

## Workflow

1. Verify the evidence gate.
   - 제공된 JD 원문, 기존 경험 자료, 공식 회사 자료를 확인한다.
   - 하나라도 없으면 JD·경험 자료를 요청하거나 공식 자료를 조사하고, Draft 작성은 중단한다.
2. Build the company-role profile.
   - `references/company-role-profile.md`의 회사, 직무, 작성 앵커 필드를 모두 채운다.
   - 실제 JD는 직무명, 주요 업무, 필수 역량, 우대 역량, 기술 스택과 전형 정보를 보존한다.
   - 공식 자료와 JD를 결합해 `회사·직무가 해결해야 할 문제`를 한 문장으로 정의한다.
3. Map experiences before writing.
   - 문항마다 서로 다른 핵심 경험 하나를 배정한다. 동일 경험의 재사용은 금지하며, 보조 근거로도 재사용하지 않는다.
   - 각 배정에는 경험명, 행동, 결과, 연결하는 프로필 항목, 사용 금지 경험을 기록한다.
   - 독립 경험 수가 부족하면 추가 경험을 요청하고 Draft 작성을 중단한다.
4. Create a Draft, not a final submission.
   - 회사 관련 문장은 공식 자료의 출처와 연결한다.
   - 지원 동기는 `회사·직무 문제 -> 본인 경험 -> 입사 후 기여`로 작성한다.
   - 역량 문항은 `상황 -> 과제 -> 행동 -> 결과 -> 직무 연결`로 작성한다.
   - 회사명만 바꿔도 성립하는 일반론, 확인되지 않은 회사 주장, 문항 간 반복 결론은 쓰지 않는다.
5. Request approval.
   - Draft의 경험 배정, 회사·직무 해석, 답변 방향을 검토하도록 요청한다.
   - 명시적 승인 전에는 최종본을 생성하지 않는다.
6. Generate the final submission version only after approval.
   - 승인 후 글자 수를 조정하고, 맞춤법·문체·반복을 교정한다.
   - Korean이 기계적으로 들리면 humanize-korean guidance를 적용하되, 사실·수치·회사명·직무명·기술명은 바꾸지 않는다.

## Draft Output Format

Create a Draft file under `result/기업명/직무명YYMM_draft.md` using this structure:

```markdown
# 기업명 - 직무명 Draft (YYMM)

- 기업: 기업명
- 직무: 직무명
- 지원시기: YYMM
- 상태: 검토 대기

## 실제 JD

- 출처: 사용자 제공 JD

### 주요 업무

...

### 필수 역량

...

### 우대 역량

...

## 공식 자료와 출처

- 자료 제목:
- URL:
- 확인일:
- 답변에 사용하는 사실:

## 회사·직무 프로필

### 회사

- 사업/서비스:
- 주요 고객 또는 사용자:
- 관련 사업 환경과 과제:
- 공식 자료에서 확인한 최근 방향:

### 직무

- 직무 미션:
- 핵심 산출물:
- 실제 업무 흐름:
- 기술·운영 환경:
- JD 평가 역량:

### 작성 앵커

- 회사·직무가 해결해야 할 문제:
- 지원자가 기여할 지점:
- 사용 금지 일반론 또는 확인되지 않은 주장:

## 회사·직무 해석

...

## 문항별 경험 배정

- 문항:
- 경험명:
- 행동:
- 결과:
- 연결하는 프로필 항목:
- 사용 금지 경험:

## 문항별 Draft 답변

### 문항 1. 문항 원문

- 제한: 000자 이내

### 답변 제목

[핵심 메시지]

### 답변

Draft 답변

## 사실 확인 필요 항목

- 없음 또는 확인이 필요한 사실
```

## Final Output Format

사용자가 Draft를 명시적으로 승인한 뒤에만 `result/기업명/직무명YYMM.md`에 최종본을 생성한다. 최종본에는 지원 메타데이터, 문항 원문, 답변 제목, 답변만 포함한다. URL, 회사·직무 프로필, 경험 배정, 검토 메모는 Draft에만 남긴다.

Include `작성 조건` under a prompt when the application specifies required sub-points.

## Quality Gate

Before handing over a Draft or final response, verify:

- Every prompt has one `답변 제목` and one `답변`.
- `실제 JD` is present before the company-role interpretation and faithfully separates supplied responsibilities, qualifications, and stated technology or selection details.
- The company-role profile has business/service, role mission, key deliverables, and JD evaluation skills filled from the JD and official sources.
- Every company-related fact has an official source with title, URL, check date, and fact used.
- Each prompt has a different primary experience, and no assigned experience appears as supporting evidence in another prompt.
- Each experience maps to the company-role problem or contribution point.
- No unrelated company names, other industry context, generic company-name substitution, or unsupported company claims remain.
- Draft status is `검토 대기` until the user gives explicit approval. Without approval, stop before final output generation.
- Final answers respect the stated character limits and retain only submission-ready content.
- The Draft and final files are valid Markdown under `result/기업명/`, which is ignored by Git for real application work.

For detailed writing criteria, read `references/evaluation.md` when drafting or reviewing final answers.
