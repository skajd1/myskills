---
name: cover-letter-tailor
description: Use when the user provides a company name, job description/JD, role, or self-introduction prompts and wants Korean 자기소개서/cover-letter answers tailored from existing application materials, polished for final Markdown output.
---

# Cover Letter Tailor

## Overview

Produce company- and role-specific Korean 자기소개서 answers by combining the user's existing self-introduction archive with the provided company name, JD, and prompts. Preserve truthful experience, improve fit and fluency, and deliver a final `.md` artifact.

## Required Inputs

Proceed when the user provides at least:

- 기업명
- 직무명 or JD
- 자기소개서 문항

JD가 이미지, 표, 또는 링크의 발췌로 제공되면 실제 공고 내용을 먼저 충실하게 전사한다. 전사한 JD와 이후의 해석·추천은 반드시 구분한다.

If one is missing, ask only for the missing item. If the user provides a maximum character limit, write to 80-95% of that maximum unless they explicitly ask for a shorter answer or the field is a short-answer prompt. Otherwise preserve a concise, submission-ready length.

## Source Review

Before drafting, inspect the current workspace for existing 자기소개서 files:

- Read `개인_경험_역량_분석.md` first if present. Treat it as the user's reusable experience/competency profile.
- If the workspace profile is missing, read `references/user-profile.md` as the bundled snapshot.
- Read `README.md`, `자소서_작업_워크플로우.md`, `자소서_작성_규격.md`, `자소서_작성_요령.md`, `자소서_템플릿.md`, and `humanizer_사용법.md` if present.
- Read relevant company/role files under `result/` first, then adjacent files with reusable experiences.
- Extract reusable evidence: project, role, action, technology, metric, result, value, and prior company-tailoring sentence.
- Watch for stale company names in reused text. Never leave another company's name in the final answer unless it is part of an experience.

## Workflow

1. Build a brief company/JD analysis.
   - Record the supplied JD in the output before analyzing it. Preserve the job title, responsibilities, required qualifications, preferred qualifications, and stated technology stack or selection details when provided.
   - Label the transcription as `실제 JD` and label any interpretation separately as `기업/JD 분석`.
   - Identify business domain, role mission, required skills, operating environment, and likely evaluation keywords.
   - If current facts are needed or the user asks for detailed/current company analysis, browse and cite sources.
2. Map each prompt to the best existing experience.
   - Prefer experience with concrete technologies and measurable outcomes.
   - Avoid inventing credentials, projects, metrics, or company facts.
3. Draft each answer.
   - Apply `자소서_작성_요령.md` when it exists, including JD-first analysis, company-need framing, STAR evidence, concrete nouns, and natural submission-ready Korean.
   - Use `지원 동기 -> 근거 경험 -> 입사 후 기여` for motivation prompts.
   - Use `상황 -> 과제 -> 행동 -> 결과 -> 직무 연결` for experience prompts.
   - If a maximum character limit is provided, target 80-95% of the maximum and never stop at a compressed summary.
   - End with company- and role-specific contribution, not a generic pledge.
4. Polish Korean.
   - Correct spelling, spacing, awkward grammar, repeated endings, and vague expressions.
   - Keep the user's voice: direct, technical, outcome-oriented, and sincere.
   - Remove inflated claims and unsupported superlatives.
   - Apply the installed `humanize-korean` guidance when the Korean sounds AI-generated: preserve facts, numbers, company names, role names, project names, and technical terms while reducing translationese, mechanical pivots, repeated connectives, and uniform sentence rhythm.
5. Save the final result as Markdown in `result/기업명/직무명YYMM.md` when the project structure is available.
   - Use the repository's current naming and formatting rules.
   - If YYMM is unknown, use `미기재` in metadata and a clear filename without date.

## Output Format

Create or update a `.md` file under `result/기업명/` using this structure:

```markdown
# 기업명 - 직무명 (YYMM)

- 기업: 기업명
- 직무: 직무명
- 지원시기: YYMM
- 상태: 초안

## 실제 JD

- 출처: 사용자 제공 JD

### 주요 업무

...

### 필수 역량

...

### 우대 역량

...

## 기업/JD 분석

...

## 문항 1. 문항 원문

- 제한: 000자 이내

### 답변 제목

[핵심 메시지]

### 답변

최종 답변
```

Include `작성 조건` under a prompt when the application specifies required sub-points.

## Quality Gate

Before final response, verify:

- Every prompt has one `답변 제목` and one `답변`.
- `실제 JD` is present before `기업/JD 분석`, and faithfully separates supplied responsibilities, qualifications, and stated technology or selection details from the analysis.
- Company name, role name, and contribution sentence match the target company.
- No unrelated company names remain.
- Character limits are respected when provided, and answers with a maximum limit use at least 80% of that maximum unless the user asked for brevity.
- AI-style phrasing has been checked against `humanize-korean` principles without changing meaning or factual details.
- The file is valid Markdown and saved under `result/기업명/`, which is ignored by Git for real company application drafts.

For detailed writing criteria, read `references/evaluation.md` when drafting or reviewing final answers.
