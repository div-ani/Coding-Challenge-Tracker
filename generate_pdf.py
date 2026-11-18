import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and draw footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 810, "Coding Challenge Tracker — Comprehensive Viva Questions & Answers")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(40, 804, 555, 804)

        # Running footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(555, 25, page_str)
        self.drawString(40, 25, "College Mini-Project | Full-Stack Python & Flask")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(40, 35, 555, 35)

        self.restoreState()

def create_viva_pdf(output_filename="Coding_Challenge_Tracker_Viva_Questions.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a')
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#2563eb')
    )

    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        alignment=2,  # Right aligned
        textColor=colors.HexColor('#475569')
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=14,
        spaceAfter=6
    )

    q_title_style = ParagraphStyle(
        'QuestionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#1e40af')
    )

    answer_style = ParagraphStyle(
        'AnswerBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # Title Banner Table
    banner_left = [
        Paragraph("<b>Coding Challenge Tracker</b>", title_style),
        Spacer(1, 3),
        Paragraph("🎓 Comprehensive Viva Voce Questions & Answers", subtitle_style)
    ]
    banner_right = [
        Paragraph("<b>College Mini-Project</b><br/>Full-Stack Python & Flask<br/>Codeforces API & SQLite", meta_style)
    ]

    header_table = Table(
        [[banner_left, banner_right]],
        colWidths=[360, 155]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563eb'), spaceBefore=4, spaceAfter=12))

    # Viva Questions Content Data
    sections = [
        {
            "title": "1. Python & Core Language Concepts",
            "qa": [
                (
                    "Q1. Why did you choose Python 3.10+ for this project?",
                    "Python 3.10+ includes native <b>zoneinfo</b> support for standardized IANA timezone conversions without legacy third-party dependencies (like <code>pytz</code>). It also provides high dictionary performance, pattern matching, clean type hints, and rich standard library modules (<code>sqlite3</code>, <code>json</code>, <code>urllib.parse</code>, <code>unittest</code>)."
                ),
                (
                    "Q2. How is UTC time converted to Indian Standard Time (IST) in your code?",
                    "Codeforces API returns start times as UTC epoch timestamps. We convert them using <code>datetime.fromtimestamp(ts, tz=timezone.utc)</code> followed by <code>.astimezone(ZoneInfo('Asia/Kolkata'))</code>. On Windows machines lacking system timezone databases, the <code>tzdata</code> package provides complete IANA definitions."
                ),
                (
                    "Q3. Why did you calculate 'Typical Rating' using the median instead of arithmetic mean?",
                    "In competitive programming, solve histories contain extreme outliers. If a user solves an 800-rated problem or an abnormal 2400-rated problem, the arithmetic mean is significantly distorted. The <b>median</b> reliably measures the true central tendency of the user's solved difficulty."
                ),
                (
                    "Q4. How is the median calculated when the number of solved problems is even?",
                    "The ratings list is sorted. If length is odd (<code>n % 2 == 1</code>), the middle element <code>ratings[n // 2]</code> is picked. If even, the two middle elements are averaged: <code>round((ratings[n // 2 - 1] + ratings[n // 2]) / 2)</code>."
                ),
                (
                    "Q5. What data structure was used to prevent recommending already solved problems?",
                    "A Python <b>set</b> containing unique keys formatted as <code>f'{contestId}_{index}'</code>. Checking membership in a hash set has <b>O(1)</b> average time complexity, ensuring instantaneous filtering even if the user has solved thousands of problems."
                ),
            ]
        },
        {
            "title": "2. Flask Microframework & Web Architecture",
            "qa": [
                (
                    "Q6. What is Flask and how does it differ from Django?",
                    "Flask is a lightweight WSGI microframework based on Werkzeug and Jinja2. While Django is a large 'batteries-included' framework with built-in ORM and admin interfaces, Flask provides lightweight modularity, minimal overhead, and freedom to select custom storage and caching strategies."
                ),
                (
                    "Q7. What is the Application Factory pattern (create_app()) used in app.py?",
                    "Instead of instantiating <code>app = Flask(__name__)</code> in global scope, the factory function encapsulates configuration loading, database initialization, and route registration inside a callable. This prevents circular imports and allows isolated test client instances."
                ),
                (
                    "Q8. How do Flash Messages function in Flask?",
                    "Flash messages are stored inside a cryptographically signed client session cookie using <code>SECRET_KEY</code>. Once the redirected page retrieves them via Jinja2's <code>get_flashed_messages(with_categories=true)</code>, Flask clears them automatically."
                ),
                (
                    "Q9. What cookie size issue can occur with Flask sessions, and how did you resolve it?",
                    "Flask session cookies have a browser limit of 4 KB. If a user has solved thousands of problems, storing the entire solved keys list in <code>session['solved_keys']</code> triggers cookie overflow warnings. We resolved this by caching solved keys in an in-memory dictionary on the server and only keeping small metadata (handle, weak topics) in the session cookie."
                ),
                (
                    "Q10. Which HTTP methods are implemented in the project?",
                    "<b>GET</b> is used for idempotent data retrieval (<code>/</code>, <code>/dashboard</code>, <code>/reminders</code>, <code>/api/recommendations/shuffle</code>). <b>POST</b> is used for state-changing form submissions (<code>/set-reminder</code> saving to SQLite, and preference filter updates)."
                ),
            ]
        },
        {
            "title": "3. SQLite Database & Storage Management",
            "qa": [
                (
                    "Q11. Why was SQLite selected for this project?",
                    "SQLite is a self-contained, serverless, transactional SQL database engine stored entirely inside a single file (<code>tracker.db</code>). It eliminates external database server setup, making the application portable and immediately runnable on any machine."
                ),
                (
                    "Q12. What is row_factory = sqlite3.Row and why is it beneficial?",
                    "Standard SQLite queries return tuple rows (e.g. <code>row[0]</code>). Setting <code>conn.row_factory = sqlite3.Row</code> enables dictionary-like column access by name (e.g. <code>row['email']</code>, <code>row['event_name']</code>), enhancing code readability and preventing index-shift bugs."
                ),
                (
                    "Q13. How does the application protect against SQL Injection?",
                    "The application strictly utilizes <b>parameterized queries</b> (using <code>?</code> placeholders) rather than string formatting. User inputs are treated strictly as literal data parameters by the SQLite engine, preventing malicious SQL code execution."
                ),
                (
                    "Q14. What is the purpose of ON CONFLICT(handle) DO UPDATE SET in models.py?",
                    "This implements an atomic <b>UPSERT</b> (Update or Insert) operation. If a user profile record with the given handle already exists in the database, it updates the rating and interests; if not, it inserts a new row seamlessly."
                ),
            ]
        },
        {
            "title": "4. Frontend: Semantic HTML5 & Modern CSS",
            "qa": [
                (
                    "Q15. How is the clean white theme structured in CSS?",
                    "CSS Custom Properties (<code>:root</code> variables) define a harmonious color hierarchy: Canvas in soft off-white (<code>#f8fafc</code>) to prevent glare; Cards in pure white (<code>#ffffff</code>) with 1px border (<code>#e2e8f0</code>) and soft depth shadows; Typography in deep slate (<code>#0f172a</code>) for high contrast and readability."
                ),
                (
                    "Q16. How do CSS Grid and Flexbox work together in your design?",
                    "CSS Grid is used for multi-card 2D layouts (<code>repeat(auto-fit, minmax(280px, 1fr))</code>), adapting dynamically to screen resizing. Flexbox is used for 1D component alignments, such as navigation links, badge alignments, and modal action button groups."
                ),
                (
                    "Q17. How does the Email Reminder Modal work without external UI frameworks?",
                    "A lightweight pure CSS fixed backdrop with <code>backdrop-filter: blur(4px)</code> is toggled with a <code>.show</code> class via JavaScript. It provides smooth entrance animations and captures background click events to auto-close."
                ),
            ]
        },
        {
            "title": "5. Vanilla JavaScript & Chart.js Visualizations",
            "qa": [
                (
                    "Q18. How does the 'Shuffle Problems' feature work without a full page reload?",
                    "When the user clicks the Shuffle button, an asynchronous request is triggered using the browser's native <code>fetch()</code> API to <code>/api/recommendations/shuffle</code>. The Flask server randomly samples 5 new unsolved problems from the candidate pool and returns a JSON response. JavaScript dynamically clears and updates the DOM in <code>div#problemsGrid</code>."
                ),
                (
                    "Q19. How does Chart.js render data on the Practice Dashboard?",
                    "Chart.js renders vector data onto HTML5 <code>&lt;canvas&gt;</code> elements using the 2D Canvas Context API. The Python backend encodes topic solve counts into JSON within <code>window.dashboardData</code>, which JavaScript passes directly into the Chart.js dataset config."
                ),
                (
                    "Q20. How are weak topics visually distinguished in the Chart.js graph?",
                    "In <code>static/js/charts.js</code>, labels are mapped through a conditional color function: if a tag is present in <code>data.weakTopics</code>, it is rendered in warm amber (<code>#d97706</code>); otherwise, it receives clean royal blue (<code>#2563eb</code>)."
                ),
            ]
        },
        {
            "title": "6. REST APIs & Algorithmic Logic",
            "qa": [
                (
                    "Q21. How does the 1-hour in-memory API caching work?",
                    "A global cache dictionary records <code>timestamp</code> and <code>data</code>. When a request arrives, if <code>time.time() - timestamp &lt; 3600</code>, cached contest data is returned immediately. This prevents hitting the Codeforces rate limit (maximum 1 request per 2 seconds) and accelerates response times."
                ),
                (
                    "Q22. What are the exact Fit Label rules used for Codeforces Contests?",
                    "Contest divisions are parsed from contest names: <b>Div 4:</b> Target &lt; 1400. If rating &lt; 1400 &rarr; 'Good fit'; else &rarr; 'Easier than your level'. <b>Div 3:</b> Target 1400–1599. If rating &lt; 1400 &rarr; 'A stretch'; 1400–1599 &rarr; 'Good fit'; &ge; 1600 &rarr; 'Easier than your level'. <b>Div 2:</b> Target 1600–2099. If rating &lt; 1600 &rarr; 'A stretch'; 1600–2099 &rarr; 'Good fit'; &ge; 2100 &rarr; 'Easier than your level'. <b>Div 1:</b> Target &ge; 1900. If rating &lt; 1900 &rarr; 'A stretch'; &ge; 1900 &rarr; 'Good fit'."
                ),
                (
                    "Q23. How does the Hackathon Ranking algorithm compute scores and tie-breaks?",
                    "Each hackathon starts with <code>score = 0</code>: <code>+1</code> for each user interest topic matching the hackathon's topic tags, and <code>+1</code> if the hackathon's target level matches the user's experience level. Hackathons are sorted using <code>key=lambda h: (-h['score'], h['start_time'])</code>, which sorts descending by score with tie-breaking by earliest start date."
                ),
                (
                    "Q24. How are Google Calendar URLs generated?",
                    "Pre-filled Google Calendar URLs use the standard template endpoint: <code>https://calendar.google.com/calendar/render?action=TEMPLATE&text=...&dates=...</code> Start and end datetimes are converted to UTC and formatted as <code>YYYYMMDDTHHmmSSZ</code>, then encoded using <code>urllib.parse.urlencode()</code>."
                ),
            ]
        },
        {
            "title": "7. Software Testing & Quality Assurance",
            "qa": [
                (
                    "Q25. What automated unit tests are provided, and why are they vital?",
                    "The suite in <code>tests/test_logic.py</code> covers 16 test cases using Python's standard <code>unittest</code> framework. It validates that core business logic (IST conversion, median calculations, fit label boundaries, hackathon scoring, and problem recommendation filtering) functions accurately before production deployment."
                ),
                (
                    "Q26. What edge cases did your unit tests verify?",
                    "Edge cases verified include: empty submission history returning fallback rating 800; odd and even length median calculations; UTC epoch 0 converting to exactly 05:30 AM IST Jan 1, 1970; exclusion of previously solved problems from recommendations; and score tie-breaking on dates."
                ),
            ]
        }
    ]

    for sec in sections:
        # Section Header Banner
        sec_table = Table(
            [[Paragraph(f"<b>{sec['title']}</b>", section_style)]],
            colWidths=[515]
        )
        sec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('LINELEFT', (0,0), (-1,-1), 3.5, colors.HexColor('#2563eb')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(sec_table)
        story.append(Spacer(1, 5))

        for q_text, a_text in sec['qa']:
            card_content = [
                Paragraph(q_text, q_title_style),
                Spacer(1, 2),
                Paragraph(a_text, answer_style)
            ]
            card_table = Table([[card_content]], colWidths=[515])
            card_table.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#e2e8f0')),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(KeepTogether([card_table, Spacer(1, 4)]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {output_filename}")

if __name__ == '__main__':
    create_viva_pdf()
