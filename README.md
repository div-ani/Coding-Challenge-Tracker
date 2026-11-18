# ⚡ Coding Challenge Tracker (College Mini-Project)

A full-stack Flask web application to track upcoming competitive programming contests and curated hackathons, calculate personalized fit/match scores, convert all dates to Indian Standard Time (IST), and analyze Codeforces practice histories to recommend targeted problems in your weakest areas.

---

## 🚀 Features

1. **Events & Contests Tracker (`/`):**
   - Fetches upcoming Codeforces contests dynamically via Codeforces API (`contest.list?gym=false`).
   - 1-hour cache to avoid rate-limiting.
   - Curated college and global hackathons loaded from `data/hackathons.json`.
   - **Time Conversion:** All UTC timestamps converted to **Indian Standard Time (IST: Asia/Kolkata)** using Python's standard `zoneinfo`.
   - **Fit Labels:** Evaluates user rating vs contest division:
     - Div 4: `< 1400`
     - Div 3: `< 1600`
     - Div 2: `< 2100`
     - Div 1: `>= 1900`
     - Labels: `"Good fit"`, `"A stretch"`, `"Easier than your level"`.
   - **Hackathon Ranking:**
     - Match Score: `+1` per matching interest topic and `+1` if hackathon level matches your experience level.
     - Sorted descending by score with tie-breaking by earliest start date.
   - **Google Calendar Integration:** One-click pre-filled calendar event URLs.
   - **Email Reminder Subscriptions:** Save reminder requests (1 day or 1 hour before) into SQLite (`tracker.db`).

2. **Practice Analytics & Dashboard (`/dashboard`):**
   - Fetches practice history via `user.status?handle=<HANDLE>`.
   - Filters unique accepted (`verdict == 'OK'`) problems.
   - Computes **Typical Rating** (median rating of solved problems).
   - Identifies the **2 Weakest Topics** (topics with lowest solve counts).
   - Visualizes topic solve counts and difficulty distribution using **Chart.js**.
   - **Targeted Problem Recommendations:** 5 unsolved problems in your 2 weak areas starting around typical rating (+100 steps).
   - **Shuffle Button:** Draws 5 new problem candidates via AJAX without reloading the page.

3. **Database (`tracker.db`):**
   - SQLite tables for email reminders and user preferences.

4. **Automated Unit Tests (`tests/test_logic.py`):**
   - Comprehensive test suite covering IST conversion, fit labels, median rating, weakest topic detection, and recommendation filtering.

---

## 📁 Directory Structure

```
├── app.py                  # App entrypoint / factory & routes
├── config.py               # App configuration (paths, cache, secret key)
├── models.py               # SQLite schema / DB helper functions
├── services/
│   ├── codeforces.py       # Codeforces API caller with 1-hour cache & IST conversion
│   ├── analyzer.py         # Typical rating (median) & weakest topics logic
│   └── recommender.py      # Problem recommendation, shuffle & hackathon ranking
├── static/
│   ├── css/style.css       # Clean responsive CP-themed styling
│   └── js/charts.js        # Chart.js visualization & AJAX shuffle handler
├── templates/
│   ├── base.html           # Base layout with navbar & reminder modal
│   ├── index.html          # Events list (contests + hackathons)
│   ├── dashboard.html      # Practice analytics & recommended problems
│   └── reminders.html      # Stored email reminders table
├── data/
│   ├── hackathons.json     # Curated hackathons JSON
│   └── sample_problems.json# Curated recommendation problem pool
├── tests/
│   └── test_logic.py       # Unit tests
└── requirements.txt        # Python dependencies
```

---

## 🛠️ How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Flask Server
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 3. Run Unit Tests
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
All 16 test cases will execute and verify the core logic.
