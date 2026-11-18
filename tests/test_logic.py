import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from services.codeforces import convert_utc_to_ist, get_fit_label, generate_gcal_link
from services.analyzer import calculate_median, find_weakest_topics, analyze_practice_history
from services.recommender import get_recommended_problems, rank_hackathons, round_rating

class TestCodingChallengeTrackerLogic(unittest.TestCase):

    # ----------------------------------------------------
    # 1. IST Date Conversion Tests
    # ----------------------------------------------------
    def test_utc_timestamp_to_ist(self):
        # 0 UTC is 1970-01-01 05:30:00 in IST
        utc_ts = 0
        ist_dt, ist_str = convert_utc_to_ist(utc_ts)
        self.assertEqual(ist_dt.hour, 5)
        self.assertEqual(ist_dt.minute, 30)
        self.assertIn("01 Jan 1970", ist_str)
        self.assertIn("IST", ist_str)

    def test_iso_string_to_ist(self):
        # 2026-11-25T10:00:00Z + 5:30 -> 15:30 (03:30 PM)
        iso_str = "2026-11-25T10:00:00Z"
        ist_dt, ist_str = convert_utc_to_ist(iso_str)
        self.assertEqual(ist_dt.day, 25)
        self.assertEqual(ist_dt.hour, 15)
        self.assertEqual(ist_dt.minute, 30)
        self.assertIn("03:30 PM IST", ist_str)

    # ----------------------------------------------------
    # 2. Contest Fit-Label Logic Tests
    # ----------------------------------------------------
    def test_fit_labels_div4(self):
        # Div 4 target: < 1400
        self.assertEqual(get_fit_label("Codeforces Round (Div. 4)", 1100), "Good fit")
        self.assertEqual(get_fit_label("Codeforces Round (Div. 4)", 1500), "Easier than your level")

    def test_fit_labels_div3(self):
        # Div 3 target: 1400 to 1599
        self.assertEqual(get_fit_label("Codeforces Round (Div. 3)", 1200), "A stretch")
        self.assertEqual(get_fit_label("Codeforces Round (Div. 3)", 1500), "Good fit")
        self.assertEqual(get_fit_label("Codeforces Round (Div. 3)", 1750), "Easier than your level")

    def test_fit_labels_div2(self):
        # Div 2 target: 1600 to 2099
        self.assertEqual(get_fit_label("Codeforces Round (Div. 2)", 1300), "A stretch")
        self.assertEqual(get_fit_label("Codeforces Round (Div. 2)", 1800), "Good fit")
        self.assertEqual(get_fit_label("Codeforces Round (Div. 2)", 2300), "Easier than your level")

    def test_fit_labels_div1(self):
        # Div 1 target: >= 1900
        self.assertEqual(get_fit_label("Codeforces Round (Div. 1)", 1600), "A stretch")
        self.assertEqual(get_fit_label("Codeforces Round (Div. 1)", 2200), "Good fit")

    # ----------------------------------------------------
    # 3. Median Rating Calculation Tests
    # ----------------------------------------------------
    def test_median_empty(self):
        self.assertEqual(calculate_median([]), 800)

    def test_median_odd_elements(self):
        ratings = [800, 1200, 1000]
        self.assertEqual(calculate_median(ratings), 1000)

    def test_median_even_elements(self):
        ratings = [1000, 1200, 1400, 1600]
        # (1200 + 1400) / 2 = 1300
        self.assertEqual(calculate_median(ratings), 1300)

    def test_round_rating(self):
        self.assertEqual(round_rating(1240), 1200)
        self.assertEqual(round_rating(1260), 1300)
        self.assertEqual(round_rating(600), 800)

    # ----------------------------------------------------
    # 4. Weakest Topic Identification Tests
    # ----------------------------------------------------
    def test_weakest_topics_identification(self):
        tag_counts = {
            'implementation': 15,
            'math': 12,
            'greedy': 8,
            'dp': 2,
            'strings': 1,
            'graphs': 6
        }
        weakest = find_weakest_topics(tag_counts, n=2)
        # Lowest counts are 'strings' (1) and 'dp' (2)
        self.assertEqual(weakest, ['strings', 'dp'])

    def test_analyze_practice_history(self):
        dummy_submissions = [
            {'verdict': 'OK', 'problem': {'contestId': 100, 'index': 'A', 'rating': 1200, 'tags': ['math', 'greedy']}},
            {'verdict': 'OK', 'problem': {'contestId': 100, 'index': 'A', 'rating': 1200, 'tags': ['math', 'greedy']}}, # Duplicate accepted
            {'verdict': 'WRONG_ANSWER', 'problem': {'contestId': 100, 'index': 'B', 'rating': 1400, 'tags': ['dp']}},
            {'verdict': 'OK', 'problem': {'contestId': 101, 'index': 'A', 'rating': 1400, 'tags': ['math']}},
            {'verdict': 'OK', 'problem': {'contestId': 102, 'index': 'A', 'rating': 1200, 'tags': ['implementation', 'brute force', 'data structures', 'trees', 'strings']}}
        ]
        result = analyze_practice_history(dummy_submissions)
        self.assertEqual(result['total_solved'], 3)
        self.assertEqual(result['typical_rating'], 1200)
        self.assertEqual(result['tag_counts']['math'], 2)
        self.assertEqual(result['tag_counts']['greedy'], 1)
        self.assertEqual(result['tag_counts']['dp'], 0)
        self.assertEqual(result['tag_counts']['graphs'], 0)
        # Lowest 2 are dp and graphs (tied at 0)
        self.assertIn('dp', result['weakest_topics'])
        self.assertIn('graphs', result['weakest_topics'])

    # ----------------------------------------------------
    # 5. Recommendation Filtering Tests
    # ----------------------------------------------------
    def test_recommendation_filters_solved_problems(self):
        # Suppose user has already solved problem 4A and 71A
        solved_keys = {'4_A', '71_A'}
        recommendations = get_recommended_problems(
            weak_topics=['strings', 'math'],
            typical_rating=800,
            solved_keys=solved_keys,
            count=5,
            shuffle=False
        )
        self.assertTrue(len(recommendations) > 0)
        for p in recommendations:
            key = f"{p['contestId']}_{p['index']}"
            self.assertNotIn(key, solved_keys)

    def test_recommendation_matches_weak_topics(self):
        recommendations = get_recommended_problems(
            weak_topics=['dp', 'graphs'],
            typical_rating=1400,
            solved_keys=set(),
            count=5,
            shuffle=False
        )
        self.assertEqual(len(recommendations), 5)
        for p in recommendations:
            p_tags_lower = [t.lower() for t in p['tags']]
            has_tag = ('dp' in p_tags_lower) or ('graphs' in p_tags_lower)
            self.assertTrue(has_tag)

    # ----------------------------------------------------
    # 6. Hackathon Scoring & Calendar Link Tests
    # ----------------------------------------------------
    def test_hackathon_ranking_score(self):
        sample_hacks = [
            {
                "id": "h1",
                "name": "Web & AI Sprint",
                "start_time": "2026-12-01T10:00:00Z",
                "end_time": "2026-12-02T10:00:00Z",
                "mode": "online",
                "topics": ["web", "AI"],
                "level": "Beginner",
                "link": "https://example.com/h1"
            },
            {
                "id": "h2",
                "name": "Cloud Summit",
                "start_time": "2026-11-20T10:00:00Z",
                "end_time": "2026-11-21T10:00:00Z",
                "mode": "offline",
                "topics": ["cloud"],
                "level": "Advanced",
                "link": "https://example.com/h2"
            }
        ]
        # User interests = ["web", "AI"], level = "Beginner"
        # h1 should get +1 (web) + 1 (AI) + 1 (Beginner) = score 3
        # h2 should get score 0
        ranked = rank_hackathons(sample_hacks, user_interests=["web", "AI"], user_level="Beginner")
        self.assertEqual(ranked[0]['id'], "h1")
        self.assertEqual(ranked[0]['score'], 3)
        self.assertEqual(ranked[1]['id'], "h2")
        self.assertEqual(ranked[1]['score'], 0)

    def test_google_calendar_link_generation(self):
        dt1 = datetime(2026, 12, 1, 10, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc)
        link = generate_gcal_link("Test Event", dt1, dt2, "Details", "Online")
        self.assertIn("calendar.google.com/calendar/render", link)
        self.assertIn("20261201T100000Z%2F20261201T120000Z", link)
        self.assertIn("text=Test+Event", link)

if __name__ == '__main__':
    unittest.main()
