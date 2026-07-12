from pathlib import Path
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_PATH = SKILL_DIR / "SKILL.md"
PROFILE_PATH = SKILL_DIR / "references" / "company-role-profile.md"
EXPERIENCE_PROFILE_PATH = SKILL_DIR / "references" / "user-profile.md"


class CoverLetterTailorContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")

    def test_requires_all_evidence_inputs_before_draft(self):
        self.assertIn("제공된 JD 원문", self.skill)
        self.assertIn("기존 경험 자료", self.skill)
        self.assertIn("공식 회사 자료", self.skill)
        self.assertIn(
            "세 종류의 근거가 모두 갖춰질 때까지 Draft 작성을 시작하지 않는다",
            self.skill,
        )

    def test_requires_structured_company_role_profile(self):
        self.assertIn("회사·직무 프로필", self.skill)
        self.assertTrue(PROFILE_PATH.exists())
        profile = PROFILE_PATH.read_text(encoding="utf-8")
        for heading in ["## 회사", "## 직무", "## 작성 앵커"]:
            self.assertIn(heading, profile)

    def test_uses_skill_directory_as_the_only_experience_source(self):
        self.assertTrue(EXPERIENCE_PROFILE_PATH.exists())
        self.assertIn(
            "개인 경험의 기준 파일은 `references/user-profile.md`",
            self.skill,
        )
        self.assertIn(
            "사용자가 경험을 추가하거나 수정하면 이 파일을 업데이트한다.",
            self.skill,
        )
        self.assertIn("작업공간의 경험 파일은 참조하지 않는다.", self.skill)
        self.assertNotIn(
            "Read `개인_경험_역량_분석.md` first", self.skill
        )
        self.assertNotIn(
            "Read relevant company/role files under `result/` first", self.skill
        )

    def test_forbids_primary_experience_reuse(self):
        self.assertIn("동일 경험의 재사용은 금지", self.skill)
        self.assertIn("보조 근거로도 재사용하지 않는다", self.skill)

    def test_requires_draft_approval_before_final(self):
        self.assertIn("명시적 승인 전에는 최종본을 생성하지 않는다", self.skill)
        for heading in [
            "## 공식 자료와 출처",
            "## 회사·직무 프로필",
            "## 문항별 경험 배정",
            "## 사실 확인 필요 항목",
        ]:
            self.assertIn(heading, self.skill)

    def test_requires_source_metadata_and_citations(self):
        for field in [
            "- 자료 제목:",
            "- URL:",
            "- 확인일:",
            "- 답변에 사용하는 사실:",
            "Every company-related fact has an official source",
        ]:
            self.assertIn(field, self.skill)

    def test_uses_draft_answer_label_and_keeps_fact_checks(self):
        for heading in [
            "## 문항별 Draft 답변",
            "## 사실 확인 필요 항목",
            "## Final Output Format",
        ]:
            self.assertIn(heading, self.skill)
        self.assertIn("\nDraft 답변\n", self.skill)


if __name__ == "__main__":
    unittest.main()
