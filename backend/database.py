import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'stock_analyzer.db')


class Database:
    def __init__(self):
        self.db_path = DB_PATH

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                added_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                name TEXT NOT NULL,
                searched_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_data (
                cache_key TEXT PRIMARY KEY,
                data_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def get_cached(self, cache_key: str, max_age_hours: int = 72):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT payload, fetched_at FROM cached_data WHERE cache_key = ?",
            (cache_key,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        try:
            fetched_at = datetime.fromisoformat(row['fetched_at'])
        except Exception:
            return None
        age = datetime.utcnow() - fetched_at
        if age > timedelta(hours=max_age_hours):
            return None
        try:
            payload = json.loads(row['payload'])
        except Exception:
            return None
        return {'payload': payload, 'fetched_at': row['fetched_at'], 'age_hours': age.total_seconds() / 3600}

    def set_cached(self, cache_key: str, data_type: str, payload: dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO cached_data (cache_key, data_type, payload, fetched_at) VALUES (?, ?, ?, ?)",
            (cache_key, data_type, json.dumps(payload), datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()

    def get_watchlist(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM watchlist ORDER BY added_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_to_watchlist(self, ticker: str, name: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO watchlist (ticker, name, added_at) VALUES (?, ?, ?)",
                (ticker, name, datetime.utcnow().isoformat())
            )
            conn.commit()
        finally:
            conn.close()

    def remove_from_watchlist(self, ticker: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
        conn.commit()
        conn.close()

    def is_in_watchlist(self, ticker: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM watchlist WHERE ticker = ?", (ticker,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_search_history(self, limit: int = 20):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT ticker, name, MAX(searched_at) as searched_at FROM search_history "
            "GROUP BY ticker ORDER BY searched_at DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_search_history(self, ticker: str, name: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO search_history (ticker, name, searched_at) VALUES (?, ?, ?)",
            (ticker, name, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()

    def clear_search_history(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM search_history")
        conn.commit()
        conn.close()
