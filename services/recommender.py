import os
import json
import random
import requests
import time
from config import Config
from services.codeforces import convert_utc_to_ist, generate_gcal_link

# Cache for Codeforces problemset: {'timestamp': float, 'data': list}
_problemset_cache = {
    'timestamp': 0,
    'data': []
}

def load_sample_problems():
    """
    Loads local curated sample problems from data/sample_problems.json.
    """
    sample_file = os.path.join(Config.BASE_DIR, 'data', 'sample_problems.json')
    if os.path.exists(sample_file):
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sample problems: {e}")
    return []

def get_all_problems():
    """
    Retrieves problems from Codeforces API (with 1-hour cache),
    falling back to data/sample_problems.json if the API is offline.
    """
    global _problemset_cache
    current_time = time.time()

    if _problemset_cache['data'] and (current_time - _problemset_cache['timestamp'] < Config.CACHE_DURATION):
        return _problemset_cache['data']

    try:
        url = "https://codeforces.com/api/problemset.problems"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('status') == 'OK':
            raw_problems = data.get('result', {}).get('problems', [])
            # Keep problems that have contestId, index, name, and rating
            valid_problems = [
                p for p in raw_problems
                if p.get('contestId') and p.get('index') and p.get('rating')
            ]
            if valid_problems:
                _problemset_cache['data'] = valid_problems
                _problemset_cache['timestamp'] = current_time
                return valid_problems
    except Exception as e:
        print(f"Could not fetch problemset from API: {e}. Using local sample pool.")

    # Fallback to local sample problems
    fallback = load_sample_problems()
    _problemset_cache['data'] = fallback
    _problemset_cache['timestamp'] = current_time
    return fallback

def round_rating(rating):
    """
    Rounds a rating to the nearest 100, clamped to at least 800.
    """
    if rating is None or rating < 800:
        return 800
    return int(round(rating / 100.0) * 100)

def get_recommended_problems(weak_topics, typical_rating, solved_keys=None, count=5, shuffle=False):
    """
    Recommends unsolved problems from the user's 2 weak topics.
    Algorithm:
      1. Start search at rating equal to user's typical rating (rounded to nearest 100).
      2. If < 5 found, increment rating by +100 steps.
      3. Filter out problems the user has already solved.
      4. Support shuffle to pick new ones from candidate pool.
    """
    if solved_keys is None:
        solved_keys = set()
    else:
        solved_keys = set(solved_keys)

    all_problems = get_all_problems()
    target_rating = round_rating(typical_rating)

    # Normalize weak topics to lowercase
    weak_set = {t.lower().strip() for t in weak_topics if t}

    # Step 1: Filter problems matching weak topics and not solved
    eligible_problems = []
    for p in all_problems:
        contest_id = p.get('contestId')
        index = p.get('index')
        name = p.get('name')
        key = f"{contest_id}_{index}"

        # Skip if already solved
        if key in solved_keys or name in solved_keys:
            continue

        # Check if problem has at least one weak topic tag
        p_tags = [t.lower() for t in p.get('tags', [])]
        if any(w in p_tags for w in weak_set):
            eligible_problems.append(p)

    # Step 2: Search starting at target_rating, incrementing by +100 steps
    candidate_pool = []
    current_rating = target_rating
    max_rating = 3500

    # Expand search rating upwards by +100
    while len(candidate_pool) < 25 and current_rating <= max_rating:
        matches_at_rating = [p for p in eligible_problems if p.get('rating') == current_rating]
        for p in matches_at_rating:
            if p not in candidate_pool:
                candidate_pool.append(p)
        current_rating += 100

    # If still not enough candidates, search downwards from target_rating - 100 down to 800
    if len(candidate_pool) < count:
        down_rating = target_rating - 100
        while len(candidate_pool) < 25 and down_rating >= 800:
            matches_down = [p for p in eligible_problems if p.get('rating') == down_rating]
            for p in matches_down:
                if p not in candidate_pool:
                    candidate_pool.append(p)
            down_rating -= 100

    # If still empty (e.g. user solved everything or very few problems in sample pool), take any eligible
    if len(candidate_pool) < count:
        for p in eligible_problems:
            if p not in candidate_pool:
                candidate_pool.append(p)

    # Step 3: Select problems (support shuffle)
    if shuffle and len(candidate_pool) > count:
        selected_raw = random.sample(candidate_pool, count)
    else:
        # Default: take top candidates closest to starting rating
        selected_raw = candidate_pool[:count]

    # Format output with direct problem links
    recommended = []
    for p in selected_raw:
        c_id = p.get('contestId')
        idx = p.get('index')
        recommended.append({
            'contestId': c_id,
            'index': idx,
            'name': p.get('name'),
            'rating': p.get('rating'),
            'tags': p.get('tags', []),
            'link': f"https://codeforces.com/contest/{c_id}/problem/{idx}"
        })

    return recommended

def rank_hackathons(hackathons, user_interests=None, user_level=None):
    """
    Ranks hackathons based on user interests and experience level.
    Scoring Rule:
      - Score = +1 for each matching user interest topic
      - +1 if hackathon level matches user experience level
      - Sort descending by score, tie-break by earliest start date.
    """
    if user_interests is None:
        user_interests = []
    if isinstance(user_interests, str):
        # Allow comma separated or string input
        user_interests = [i.strip().lower() for i in user_interests.split(',') if i.strip()]
    else:
        user_interests = [str(i).strip().lower() for i in user_interests if i]

    ranked = []
    for h in hackathons:
        item = dict(h)
        score = 0

        # Topic matching (+1 for each match)
        h_topics = [t.lower().strip() for t in item.get('topics', [])]
        matched_topics = []
        for interest in user_interests:
            if interest in h_topics:
                score += 1
                matched_topics.append(interest)

        # Level matching (+1 if level matches)
        if user_level and str(item.get('level', '')).lower() == str(user_level).lower():
            score += 1
            level_matched = True
        else:
            level_matched = False

        item['score'] = score
        item['matched_topics'] = matched_topics
        item['level_matched'] = level_matched

        # Add formatted IST time and Google Calendar link
        start_iso = item.get('start_time')
        end_iso = item.get('end_time')

        start_dt, start_str = convert_utc_to_ist(start_iso)
        end_dt, end_str = convert_utc_to_ist(end_iso)

        item['start_str'] = start_str
        item['end_str'] = end_str
        item['start_dt'] = start_dt
        item['end_dt'] = end_dt

        item['gcal_link'] = generate_gcal_link(
            title=item.get('name', 'Hackathon'),
            start_dt=start_dt,
            end_dt=end_dt,
            details=f"Hackathon: {item.get('name')}\nMode: {item.get('mode')}\nLink: {item.get('link')}",
            location="Online" if item.get('mode') == 'online' else "In-Person / Offline"
        )

        ranked.append(item)

    # Sort descending by score, tie-break by earliest start date (start_time ISO string)
    ranked.sort(key=lambda h: (-h['score'], h.get('start_time', '')))
    return ranked

def load_curated_hackathons():
    """
    Loads curated hackathons from data/hackathons.json.
    """
    h_file = Config.HACKATHONS_FILE
    if os.path.exists(h_file):
        try:
            with open(h_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading hackathons: {e}")
    return []
