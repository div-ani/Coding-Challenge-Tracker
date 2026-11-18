import time
import requests
import urllib.parse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from config import Config

# Simple in-memory cache for contests
# Format: {'timestamp': float, 'data': list}
_contest_cache = {
    'timestamp': 0,
    'data': []
}

def convert_utc_to_ist(timestamp_or_iso):
    """
    Converts a UTC timestamp (int/float) or ISO 8601 string to Indian Standard Time (IST).
    Uses standard zoneinfo.ZoneInfo("Asia/Kolkata").
    Returns:
        ist_dt: datetime object in Asia/Kolkata
        ist_str: human-friendly formatted string e.g., '25 Nov 2026, 08:05 PM IST'
    """
    ist_zone = ZoneInfo("Asia/Kolkata")

    # If it's an integer or float epoch timestamp
    if isinstance(timestamp_or_iso, (int, float)):
        # Codeforces returns epoch seconds in UTC
        utc_dt = datetime.fromtimestamp(timestamp_or_iso, tz=timezone.utc)
        ist_dt = utc_dt.astimezone(ist_zone)
    elif isinstance(timestamp_or_iso, str):
        # Clean ISO string (replace 'Z' with '+00:00')
        clean_str = timestamp_or_iso.replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            # Assume UTC if naive
            dt = dt.replace(tzinfo=timezone.utc)
        ist_dt = dt.astimezone(ist_zone)
    elif isinstance(timestamp_or_iso, datetime):
        if timestamp_or_iso.tzinfo is None:
            dt = timestamp_or_iso.replace(tzinfo=timezone.utc)
        else:
            dt = timestamp_or_iso
        ist_dt = dt.astimezone(ist_zone)
    else:
        raise ValueError("Unsupported date format")

    # Format into student-friendly readable format
    formatted_str = ist_dt.strftime("%d %b %Y, %I:%M %p IST")
    return ist_dt, formatted_str

def get_fit_label(contest_name, user_rating):
    """
    Computes contest fit label based on user rating.
    Rules:
      - Div 4 target: < 1400
      - Div 3 target: < 1600 (1400 to 1599)
      - Div 2 target: < 2100 (1600 to 2099)
      - Div 1 target: >= 1900
    Labels:
      - 'Good fit' (user rating is within target)
      - 'A stretch' (user rating is below target)
      - 'Easier than your level' (user rating is above target)
    """
    if user_rating is None:
        return None

    name = contest_name.lower()

    # Check for Div 4
    if "div. 4" in name or "div 4" in name:
        if user_rating < 1400:
            return "Good fit"
        else:
            return "Easier than your level"

    # Check for Div 3
    if "div. 3" in name or "div 3" in name:
        if user_rating < 1400:
            return "A stretch"
        elif user_rating < 1600:
            return "Good fit"
        else:
            return "Easier than your level"

    # Check for Div 2
    if "div. 2" in name or "div 2" in name:
        if "div. 1" in name or "div 1" in name:
            # Combined Div 1 + Div 2
            if user_rating < 1600:
                return "A stretch"
            else:
                return "Good fit"
        if user_rating < 1600:
            return "A stretch"
        elif user_rating < 2100:
            return "Good fit"
        else:
            return "Easier than your level"

    # Check for Div 1
    if "div. 1" in name or "div 1" in name:
        if user_rating < 1900:
            return "A stretch"
        else:
            return "Good fit"

    # Default fallback for open / educational contests
    if user_rating < 1400:
        return "A stretch"
    elif user_rating < 2100:
        return "Good fit"
    else:
        return "Easier than your level"

def generate_gcal_link(title, start_dt, end_dt, details="", location=""):
    """
    Generates a pre-filled Google Calendar event URL.
    Format: https://calendar.google.com/calendar/render?action=TEMPLATE&text=...&dates=...&details=...&location=...
    """
    # Convert datetimes to UTC for Google Calendar URL
    start_utc = start_dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    end_utc = end_dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    params = {
        'action': 'TEMPLATE',
        'text': title,
        'dates': f"{start_utc}/{end_utc}",
        'details': details,
        'location': location
    }
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

def get_upcoming_contests(user_rating=None):
    """
    Fetches upcoming Codeforces contests (phase == 'BEFORE').
    Uses 1-hour cache to avoid hitting rate limits.
    """
    global _contest_cache

    current_time = time.time()
    # Check if cache is still fresh (less than 1 hour old)
    if _contest_cache['data'] and (current_time - _contest_cache['timestamp'] < Config.CACHE_DURATION):
        contests = _contest_cache['data']
    else:
        try:
            url = "https://codeforces.com/api/contest.list?gym=false"
            response = requests.get(url, timeout=10)
            data = response.json()

            if data.get('status') == 'OK':
                # Filter for upcoming contests only (phase == 'BEFORE')
                raw_contests = [c for c in data.get('result', []) if c.get('phase') == 'BEFORE']
                # Sort by start time ascending (earliest first)
                raw_contests.sort(key=lambda c: c.get('startTimeSeconds', 0))

                processed = []
                for c in raw_contests:
                    c_id = c.get('id')
                    name = c.get('name', 'Codeforces Round')
                    start_sec = c.get('startTimeSeconds', 0)
                    duration_sec = c.get('durationSeconds', 7200)

                    start_dt, start_str = convert_utc_to_ist(start_sec)
                    end_dt, end_str = convert_utc_to_ist(start_sec + duration_sec)

                    contest_link = f"https://codeforces.com/contests/{c_id}"
                    gcal_link = generate_gcal_link(
                        title=name,
                        start_dt=start_dt,
                        end_dt=end_dt,
                        details=f"Codeforces Contest: {name}\nLink: {contest_link}",
                        location="Online - Codeforces"
                    )

                    processed.append({
                        'id': f"cf-{c_id}",
                        'name': name,
                        'start_str': start_str,
                        'end_str': end_str,
                        'start_timestamp': start_sec,
                        'start_dt': start_dt,
                        'end_dt': end_dt,
                        'duration_hours': round(duration_sec / 3600, 1),
                        'link': contest_link,
                        'gcal_link': gcal_link,
                        'type': 'contest'
                    })

                _contest_cache['data'] = processed
                _contest_cache['timestamp'] = current_time
                contests = processed
            else:
                contests = _contest_cache['data'] if _contest_cache['data'] else []
        except Exception as e:
            # If network error or API down, use cached data if available
            print(f"Error fetching Codeforces contests: {e}")
            contests = _contest_cache['data'] if _contest_cache['data'] else []

    # If API returned no upcoming contests or is unreachable, provide sample upcoming contests
    if not contests:
        contests = get_sample_contests()

    # Attach dynamic fit labels based on user_rating
    results = []
    for c in contests:
        item = dict(c)
        item['fit_label'] = get_fit_label(item['name'], user_rating) if user_rating is not None else None
        results.append(item)

    return results

def get_sample_contests():
    """
    Fallback sample upcoming contests if the Codeforces API cannot be reached.
    """
    sample_raw = [
        {"id": 2045, "name": "Codeforces Round 998 (Div. 3)", "offset_hours": 24, "duration": 7200},
        {"id": 2046, "name": "Educational Codeforces Round 172 (Rated for Div. 2)", "offset_hours": 48, "duration": 7200},
        {"id": 2047, "name": "Codeforces Round 999 (Div. 1 + Div. 2)", "offset_hours": 72, "duration": 9000},
        {"id": 2048, "name": "Codeforces Round 1000 (Div. 4)", "offset_hours": 120, "duration": 7200},
        {"id": 2049, "name": "Codeforces Round 1001 (Div. 1)", "offset_hours": 168, "duration": 7200}
    ]
    base_ts = time.time()
    results = []
    for item in sample_raw:
        start_sec = int(base_ts + item['offset_hours'] * 3600)
        duration_sec = item['duration']
        start_dt, start_str = convert_utc_to_ist(start_sec)
        end_dt, end_str = convert_utc_to_ist(start_sec + duration_sec)
        contest_link = f"https://codeforces.com/contests/{item['id']}"
        gcal_link = generate_gcal_link(
            title=item['name'],
            start_dt=start_dt,
            end_dt=end_dt,
            details=f"Codeforces Contest: {item['name']}\nLink: {contest_link}",
            location="Online - Codeforces"
        )
        results.append({
            'id': f"cf-{item['id']}",
            'name': item['name'],
            'start_str': start_str,
            'end_str': end_str,
            'start_timestamp': start_sec,
            'start_dt': start_dt,
            'end_dt': end_dt,
            'duration_hours': round(duration_sec / 3600, 1),
            'link': contest_link,
            'gcal_link': gcal_link,
            'type': 'contest'
        })
    return results

def get_user_status(handle):
    """
    Fetches the submission history for a given Codeforces handle.
    Calls Codeforces API: user.status?handle=<HANDLE>
    Returns:
        submissions: list of submission dictionaries, or None if error.
    """
    try:
        url = f"https://codeforces.com/api/user.status?handle={urllib.parse.quote(handle)}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('status') == 'OK':
            return data.get('result', [])
        else:
            print(f"Codeforces API error: {data.get('comment')}")
            return None
    except Exception as e:
        print(f"Network error fetching user status for {handle}: {e}")
        return None

def get_user_info(handle):
    """
    Fetches basic user info from Codeforces API: user.info?handles=<HANDLE>
    Returns rating, maxRating, rank, etc.
    """
    try:
        url = f"https://codeforces.com/api/user.info?handles={urllib.parse.quote(handle)}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('status') == 'OK' and data.get('result'):
            return data['result'][0]
        return None
    except Exception as e:
        print(f"Network error fetching user info for {handle}: {e}")
        return None
