import math

# Common algorithmic topics tracked for beginner & college practice
COMMON_TAGS = [
    'implementation',
    'math',
    'greedy',
    'dp',
    'data structures',
    'brute force',
    'graphs',
    'trees',
    'strings'
]

def calculate_median(ratings):
    """
    Computes the median of a list of numeric ratings.
    If the list is empty, returns 800 (Codeforces starting problem rating).
    If odd length, returns middle element.
    If even length, returns average of middle two elements rounded to integer.
    """
    if not ratings:
        return 800

    # Sort the ratings in ascending order
    sorted_ratings = sorted(ratings)
    n = len(sorted_ratings)

    mid = n // 2
    if n % 2 == 1:
        # Odd number of items
        return sorted_ratings[mid]
    else:
        # Even number of items: average of the two middle elements
        return round((sorted_ratings[mid - 1] + sorted_ratings[mid]) / 2)

def find_weakest_topics(tag_counts, n=2):
    """
    Finds the n topics with the lowest solved counts.
    Tie-breaking: alphabetical order of tag names for determinism.
    """
    # Sort tags by solved count ascending, then by tag name ascending
    sorted_tags = sorted(tag_counts.items(), key=lambda item: (item[1], item[0]))
    return [tag for tag, count in sorted_tags[:n]]

def get_rating_distribution(ratings):
    """
    Groups ratings into readable buckets for Chart.js visualization.
    """
    buckets = {
        "< 1000": 0,
        "1000-1199": 0,
        "1200-1399": 0,
        "1400-1599": 0,
        "1600-1899": 0,
        "1900+": 0
    }

    for r in ratings:
        if r < 1000:
            buckets["< 1000"] += 1
        elif r < 1200:
            buckets["1000-1199"] += 1
        elif r < 1400:
            buckets["1200-1399"] += 1
        elif r < 1600:
            buckets["1400-1599"] += 1
        elif r < 1900:
            buckets["1600-1899"] += 1
        else:
            buckets["1900+"] += 1

    return buckets

def analyze_practice_history(submissions):
    """
    Analyzes Codeforces submissions from user.status.
    1. Filters for unique accepted submissions (verdict == 'OK').
    2. Computes typical rating = median rating of unique solved problems.
    3. Tallies problems solved per common tag.
    4. Identifies the two weakest topics.
    5. Computes rating distribution.
    """
    if submissions is None:
        return None

    # Step 1: Keep track of unique solved problems
    solved_problems = {}
    solved_keys = set()

    for sub in submissions:
        # Check if submission is accepted
        if sub.get('verdict') == 'OK':
            prob = sub.get('problem', {})
            contest_id = prob.get('contestId')
            index = prob.get('index')
            name = prob.get('name')

            # Unique key for each problem
            key = f"{contest_id}_{index}" if contest_id and index else name
            if key and key not in solved_problems:
                solved_problems[key] = prob
                solved_keys.add(key)

    # Step 2: Extract ratings of solved problems
    ratings = []
    for prob in solved_problems.values():
        r = prob.get('rating')
        if r is not None and isinstance(r, (int, float)):
            ratings.append(int(r))

    typical_rating = calculate_median(ratings)

    # Step 3: Tally solved problems per common tag
    tag_counts = {tag: 0 for tag in COMMON_TAGS}

    for prob in solved_problems.values():
        tags = prob.get('tags', [])
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in tag_counts:
                tag_counts[tag_lower] += 1

    # Step 4: Find the 2 weakest topics
    weakest_topics = find_weakest_topics(tag_counts, n=2)

    # Step 5: Rating distribution for charts
    rating_dist = get_rating_distribution(ratings)

    return {
        'total_solved': len(solved_problems),
        'typical_rating': typical_rating,
        'weakest_topics': weakest_topics,
        'tag_counts': tag_counts,
        'rating_distribution': rating_dist,
        'solved_keys': list(solved_keys)
    }
