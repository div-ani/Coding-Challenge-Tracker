from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from config import Config
from models import init_db, save_reminder, get_all_reminders, save_user_profile, get_user_profile
from services.codeforces import get_upcoming_contests, get_user_status, get_user_info
from services.analyzer import analyze_practice_history
from services.recommender import get_recommended_problems, rank_hackathons, load_curated_hackathons

# Simple in-memory cache for user solved problem keys to prevent cookie overflow
_user_solved_cache = {}

def create_app():
    """
    Application factory function.
    Initializes Flask, sets up database, and registers routes.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize SQLite database tables
    with app.app_context():
        init_db()

    # ----------------------------------------------------
    # ROUTE: Home / Events List (Contests + Hackathons)
    # ----------------------------------------------------
    @app.route('/', methods=['GET', 'POST'])
    def index():
        # Read user preferences from form submission, query params, or session
        user_rating = request.args.get('rating', type=int)
        user_interests = request.args.get('interests', '')
        user_level = request.args.get('level', '')

        # If user submitted the preferences filter form
        if request.method == 'POST':
            rating_input = request.form.get('rating', '').strip()
            user_interests = request.form.get('interests', '').strip()
            user_level = request.form.get('level', '').strip()

            user_rating = int(rating_input) if rating_input.isdigit() else None

            # Save in session for convenient browsing
            session['user_rating'] = user_rating
            session['user_interests'] = user_interests
            session['user_level'] = user_level
        else:
            # Fall back to session if not in query params
            if user_rating is None and 'user_rating' in session:
                user_rating = session.get('user_rating')
            if not user_interests and 'user_interests' in session:
                user_interests = session.get('user_interests', '')
            if not user_level and 'user_level' in session:
                user_level = session.get('user_level', '')

        # 1. Fetch upcoming Codeforces contests with fit labels
        contests = get_upcoming_contests(user_rating=user_rating)

        # 2. Load and rank curated hackathons
        raw_hackathons = load_curated_hackathons()
        interest_list = [i.strip() for i in user_interests.split(',') if i.strip()]
        hackathons = rank_hackathons(raw_hackathons, user_interests=interest_list, user_level=user_level)

        return render_template(
            'index.html',
            contests=contests,
            hackathons=hackathons,
            user_rating=user_rating,
            user_interests=user_interests,
            user_level=user_level
        )

    # ----------------------------------------------------
    # ROUTE: Save Email Reminder
    # ----------------------------------------------------
    @app.route('/set-reminder', methods=['POST'])
    def set_reminder():
        email = request.form.get('email', '').strip()
        event_id = request.form.get('event_id', '').strip()
        event_name = request.form.get('event_name', '').strip()
        reminder_time = request.form.get('reminder_time', '1 day before').strip()

        if not email or '@' not in email:
            flash("Please enter a valid email address.", "danger")
        else:
            save_reminder(email, event_id, event_name, reminder_time)
            flash(f"Reminder set for '{event_name}' ({reminder_time})! Saved to database.", "success")

        # Redirect back to the referrer or home page
        return redirect(request.referrer or url_for('index'))

    # ----------------------------------------------------
    # ROUTE: View Saved Reminders
    # ----------------------------------------------------
    @app.route('/reminders')
    def reminders():
        all_reminders = get_all_reminders()
        return render_template('reminders.html', reminders=all_reminders)

    # ----------------------------------------------------
    # ROUTE: Practice Dashboard & Analytics
    # ----------------------------------------------------
    @app.route('/dashboard', methods=['GET', 'POST'])
    def dashboard():
        handle = request.args.get('handle', '').strip()
        interests = request.args.get('interests', '').strip()
        level = request.args.get('level', '').strip()

        if request.method == 'POST':
            handle = request.form.get('handle', '').strip()
            interests = request.form.get('interests', '').strip()
            level = request.form.get('level', 'Beginner').strip()

        # Check session if empty
        if not handle and 'cf_handle' in session:
            handle = session.get('cf_handle', '')

        analysis = None
        user_info = None
        recommendations = []
        error_message = None

        if handle:
            # 1. Fetch user info from Codeforces
            user_info = get_user_info(handle)
            current_rating = user_info.get('rating') if user_info else None

            # 2. Fetch submission history
            submissions = get_user_status(handle)

            if submissions is not None:
                # 3. Analyze practice history
                analysis = analyze_practice_history(submissions)

                if analysis:
                    # Save light details in session
                    session['cf_handle'] = handle
                    session['weakest_topics'] = analysis['weakest_topics']
                    session['typical_rating'] = analysis['typical_rating']

                    # Save large set of solved keys in server memory cache
                    _user_solved_cache[handle.lower()] = set(analysis['solved_keys'])

                    # Also update session user rating if available
                    if current_rating:
                        session['user_rating'] = current_rating

                    # Save to SQLite database
                    save_user_profile(
                        handle=handle,
                        rating=current_rating or analysis['typical_rating'],
                        interests=interests,
                        level=level
                    )

                    # 4. Generate 5 problem recommendations
                    recommendations = get_recommended_problems(
                        weak_topics=analysis['weakest_topics'],
                        typical_rating=analysis['typical_rating'],
                        solved_keys=_user_solved_cache.get(handle.lower(), set()),
                        count=5,
                        shuffle=False
                    )
            else:
                error_message = f"Could not find Codeforces user '{handle}'. Please check the username spelling."

        return render_template(
            'dashboard.html',
            handle=handle,
            user_info=user_info,
            analysis=analysis,
            recommendations=recommendations,
            error_message=error_message,
            interests=interests,
            level=level
        )

    # ----------------------------------------------------
    # ROUTE: AJAX Problem Shuffle Endpoint
    # ----------------------------------------------------
    @app.route('/api/recommendations/shuffle', methods=['GET', 'POST'])
    def shuffle_recommendations():
        """
        Draws 5 new unsolved problems from the candidate pool without reloading the page.
        """
        # Try retrieving from session or query params
        weak_topics = request.args.getlist('weak_topics')
        if not weak_topics and 'weakest_topics' in session:
            weak_topics = session.get('weakest_topics', [])

        typical_rating = request.args.get('typical_rating', type=int)
        if typical_rating is None and 'typical_rating' in session:
            typical_rating = session.get('typical_rating', 1200)

        handle = session.get('cf_handle', '').lower()
        solved_keys = _user_solved_cache.get(handle, set())

        if not weak_topics:
            weak_topics = ['dp', 'greedy']

        # Get 5 shuffled problems
        new_problems = get_recommended_problems(
            weak_topics=weak_topics,
            typical_rating=typical_rating or 1200,
            solved_keys=solved_keys,
            count=5,
            shuffle=True
        )

        return jsonify({
            'status': 'success',
            'problems': new_problems
        })

    return app

app = create_app()

if __name__ == '__main__':
    # Run development server
    app.run(debug=True, port=5000)
