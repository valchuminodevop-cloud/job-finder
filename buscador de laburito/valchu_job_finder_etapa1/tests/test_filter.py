import unittest

from modules.job_filter import classify_location, detect_seniority, filter_jobs


class TestLocationFilter(unittest.TestCase):
    def test_worldwide_is_eligible(self):
        result = classify_location({"location": "Worldwide", "remote": True})
        self.assertEqual(result["location_status"], "eligible")
        self.assertEqual(result["location_scope"], "WORLDWIDE")

    def test_latam_is_eligible(self):
        result = classify_location({"location": "Remote - LATAM", "remote": True})
        self.assertEqual(result["location_status"], "eligible")
        self.assertEqual(result["location_scope"], "LATAM")

    def test_argentina_is_eligible(self):
        result = classify_location({"location": "Argentina"})
        self.assertEqual(result["location_status"], "eligible")

    def test_remote_without_region_needs_review(self):
        result = classify_location({"location": "Remote", "remote": True})
        self.assertEqual(result["location_status"], "review")

    def test_us_only_is_rejected(self):
        result = classify_location({"location": "Remote — US only", "remote": True})
        self.assertEqual(result["location_status"], "rejected")


class TestSeniority(unittest.TestCase):
    def test_senior_in_description_does_not_override_junior_title(self):
        job = {
            "title": "Junior Frontend Developer",
            "description": "Work with our senior developers.",
        }
        self.assertEqual(detect_seniority(job), "junior")


class TestFilter(unittest.TestCase):
    def test_git_does_not_match_digital(self):
        profile = {
            "target_roles": ["Frontend Developer"],
            "skills": ["git"],
            "job_preferences": {"seniority": ["junior"], "minimum_match_score": 0},
        }
        jobs = [{
            "title": "Junior Frontend Developer",
            "company": "Digital Factory",
            "location": "Worldwide",
            "remote": True,
            "description": "Build frontend interfaces.",
            "skills": [],
        }]
        result = filter_jobs(profile, jobs)
        self.assertEqual(result["jobs"][0]["analysis"]["matched_skills"], [])


if __name__ == "__main__":
    unittest.main()
