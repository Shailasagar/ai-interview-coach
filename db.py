import sqlite3
from datetime import datetime

DB_PATH = "coach.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            session_id TEXT,
            mode TEXT,
            question TEXT,
            transcript TEXT,
            wpm INTEGER,
            word_count INTEGER,
            long_pauses INTEGER,
            fillers INTEGER,
            relevance REAL,
            structure REAL,
            depth REAL
        )
    """)
    return conn


def save_answer(report, session_id, mode):
    voice = report["voice"]
    fb = report["feedback"]
    ok = "error" not in fb
    conn = get_conn()
    conn.execute(
        """INSERT INTO answers
           (created_at, session_id, mode, question, transcript, wpm, word_count,
            long_pauses, fillers, relevance, structure, depth)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            session_id,
            mode,
            report["question"],
            voice["transcript"],
            voice["wpm"],
            voice["word_count"],
            len(voice["pauses"]),
            sum(voice["fillers"].values()),
            fb["relevance"] if ok else None,
            fb["structure"] if ok else None,
            fb["depth"] if ok else None,
        ),
    )
    conn.commit()
    conn.close()