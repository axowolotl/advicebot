import sqlite3
import json

DB_NAME = "career_quiz.db"

async def init_db():
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        
        # Table to store questions and JSON-formatted career weights
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                options_json TEXT NOT NULL
            )
        """)
        
        # Table to store user results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_results (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                recommended_career TEXT NOT NULL,
                scores_json TEXT NOT NULL,
                taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if questions already exist; if not, seed default ones
        cursor.execute("SELECT COUNT(*) FROM questions")
        count = cursor.fetchone()[0]
        
        if count == 0:
            sample_questions = [
                (
                    "How do you prefer to solve a difficult problem?",
                    json.dumps([
                        {"label": "Write code or analyze data", "weights": {"Software Engineer": 3, "Data Scientist": 2}},
                        {"label": "Brainstorm visual or written ideas", "weights": {"UX/UI Designer": 3, "Content Creator": 2}},
                        {"label": "Organize a team and delegate tasks", "weights": {"Project Manager": 3, "Entrepreneur": 2}},
                        {"label": "Help someone directly one-on-one", "weights": {"Healthcare Specialist": 3, "Counselor": 2}}
                    ])
                ),
                (
                    "Which work environment sounds most appealing?",
                    json.dumps([
                        {"label": "Remote setup with dual monitors", "weights": {"Software Engineer": 2, "Data Scientist": 3}},
                        {"label": "A bustling design studio or agency", "weights": {"UX/UI Designer": 3, "Content Creator": 2}},
                        {"label": "Fast-paced corporate boardroom", "weights": {"Project Manager": 2, "Entrepreneur": 3}},
                        {"label": "Hospital, clinic, or community center", "weights": {"Healthcare Specialist": 3, "Counselor": 2}}
                    ])
                ),
                (
                    "What gives you the biggest sense of achievement?",
                    json.dumps([
                        {"label": "Automating a boring manual task", "weights": {"Software Engineer": 3, "Data Scientist": 2}},
                        {"label": "Making something look and feel intuitive", "weights": {"UX/UI Designer": 3, "Content Creator": 2}},
                        {"label": "Launching a profitable product or event", "weights": {"Entrepreneur": 3, "Project Manager": 2}},
                        {"label": "Improving someone's physical or mental health", "weights": {"Healthcare Specialist": 2, "Counselor": 3}}
                    ])
                )
            ]
            cursor.executemany(
                "INSERT INTO questions (question_text, options_json) VALUES (?, ?)",
                sample_questions
            )
        db.commit()

async def get_all_questions():
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT id, question_text, options_json FROM questions")
        rows = cursor.fetchall()
        return [
            {"id": r[0], "question": r[1], "options": json.loads(r[2])}
            for r in rows
        ]

async def save_user_result(user_id: int, username: str, career: str, scores: dict):
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO user_results (user_id, username, recommended_career, scores_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                recommended_career=excluded.recommended_career,
                scores_json=excluded.scores_json,
                taken_at=CURRENT_TIMESTAMP
        """, (user_id, username, career, json.dumps(scores)))
        db.commit()

async def get_user_result(user_id: int):
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute(
            "SELECT recommended_career, scores_json, taken_at FROM user_results WHERE user_id = ?",
            (user_id,)
        )
        return cursor.fetchone()
