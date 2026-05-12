import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "english_app.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            phonetic TEXT,
            part_of_speech TEXT,
            meaning TEXT NOT NULL,
            level TEXT DEFAULT '考研',
            frequency INTEGER DEFAULT 0,
            root_affix TEXT,
            derivatives TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS word_meanings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            meaning_type TEXT DEFAULT '熟词生义',
            meaning TEXT NOT NULL,
            example TEXT,
            FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS word_exam_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            point_type TEXT,
            description TEXT NOT NULL,
            example TEXT,
            FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_word_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            status TEXT DEFAULT 'new',
            ease_factor REAL DEFAULT 2.5,
            interval_days INTEGER DEFAULT 0,
            repetitions INTEGER DEFAULT 0,
            correct_streak INTEGER DEFAULT 0,
            next_review_date DATE,
            last_review_date DATE,
            last_review_result TEXT,
            is_marked INTEGER DEFAULT 0,
            FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
            UNIQUE(word_id)
        );

        CREATE TABLE IF NOT EXISTS user_wordbook (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            phonetic TEXT,
            meaning TEXT,
            source TEXT,
            note TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS study_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_date DATE NOT NULL DEFAULT (date('now', 'localtime')),
            words_learned INTEGER DEFAULT 0,
            words_reviewed INTEGER DEFAULT 0,
            quiz_count INTEGER DEFAULT 0,
            quiz_score REAL DEFAULT 0,
            ai_calls INTEGER DEFAULT 0,
            UNIQUE(study_date)
        );

        CREATE TABLE IF NOT EXISTS ai_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT NOT NULL UNIQUE,
            prompt_hash TEXT NOT NULL,
            response TEXT NOT NULL,
            model TEXT,
            tokens_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cost_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            tokens_used INTEGER DEFAULT 0,
            operation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")
