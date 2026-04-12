from app.core.keyword_matcher import match_keywords


class TestMatchedKeywords:
    def test_identical_texts_score_high(self):
        text = "Python developer with SQL machine learning experience"
        result = match_keywords(text, text)
        assert result.score > 70

    def test_shared_keywords_appear_in_matched(self):
        resume = "Experienced Python developer with SQL skills"
        jd = "Looking for a Python developer who knows SQL and cloud platforms"
        result = match_keywords(resume, jd)
        matched_lower = [k.lower() for k in result.matched_keywords]
        assert "python" in matched_lower or "sql" in matched_lower

    def test_no_overlap_scores_low(self):
        resume = "Experienced nurse with patient care and medical documentation"
        jd = "Python developer with Kubernetes Docker and CI/CD pipelines"
        result = match_keywords(resume, jd)
        assert result.score < 50


class TestMissingKeywords:
    def test_missing_keywords_identified(self):
        resume = "Python developer"
        jd = "Python developer with Kubernetes Docker and CI/CD pipelines"
        result = match_keywords(resume, jd)
        assert len(result.missing_keywords) > 0

    def test_missing_capped_at_20(self):
        resume = "Sales associate with retail experience"
        jd = " ".join(f"skill{i}" for i in range(50))
        result = match_keywords(resume, jd)
        assert len(result.missing_keywords) <= 20


class TestEmptyInputs:
    def test_empty_jd_returns_neutral_score(self):
        result = match_keywords("Some resume text", "")
        assert result.score == 50.0

    def test_empty_resume_returns_low_score(self):
        result = match_keywords("", "Python developer with SQL experience")
        assert result.score < 50
