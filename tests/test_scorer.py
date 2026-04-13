from app.core.scorer import calculate_score
from app.models.resume_models import ParsedResume, ResumeContact
from app.models.scoring_models import FormattingResult


def _resume(
    has_email: bool = True,
    has_phone: bool = True,
    has_exp: bool = True,
    has_edu: bool = True,
    has_skills: bool = True,
    has_summary: bool = True,
) -> ParsedResume:
    contact = ResumeContact(
        email="test@example.com" if has_email else None,
        phone="555-123-4567" if has_phone else None,
        location="Austin, TX",
    )
    return ParsedResume(
        raw_text=(
            "Jane Smith\ntest@example.com\n555-123-4567\nAustin, TX\n\n"
            "SUMMARY\nExperienced software engineer.\n\n"
            "EXPERIENCE\nLed a team of 8. Increased performance by 40%.\n\n"
            "SKILLS\nPython, Docker, Kubernetes\n\n"
            "EDUCATION\nBS Computer Science, UT Austin"
        ),
        contact=contact,
        experience="Led a team of 8. Increased performance by 40%." if has_exp else None,
        education="BS Computer Science, UT Austin" if has_edu else None,
        skills="Python, Docker, Kubernetes" if has_skills else None,
        summary="Experienced software engineer." if has_summary else None,
    )


def _formatting(score: float = 95.0) -> FormattingResult:
    return FormattingResult(score=score, warnings=[], recommendations=[])


class TestScoreRange:
    def test_total_score_is_between_0_and_100(self):
        result = calculate_score(_resume(), _formatting())
        assert 0 <= result.total_score <= 100

    def test_full_resume_scores_above_50(self):
        result = calculate_score(_resume(), _formatting())
        assert result.total_score > 50

    def test_incomplete_resume_scores_lower_than_full(self):
        full_score = calculate_score(_resume(), _formatting()).total_score
        partial = _resume(has_email=False, has_edu=False, has_skills=False)
        partial_score = calculate_score(partial, _formatting()).total_score
        assert full_score > partial_score


class TestCategoryWeights:
    def test_category_weights_sum_to_one(self):
        result = calculate_score(_resume(), _formatting())
        total_weight = sum(c.weight for c in result.categories)
        assert abs(total_weight - 1.0) < 0.001

    def test_weighted_sum_matches_total_score(self):
        result = calculate_score(_resume(), _formatting())
        manual = sum(c.score * c.weight for c in result.categories)
        assert abs(manual - result.total_score) < 0.5


class TestOutputStructure:
    def test_result_has_five_categories(self):
        result = calculate_score(_resume(), _formatting())
        assert len(result.categories) == 5

    def test_recommendations_list_not_too_long(self):
        result = calculate_score(_resume(), _formatting())
        assert len(result.recommendations) <= 8
