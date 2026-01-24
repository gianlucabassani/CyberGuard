import sqlite3
import json
import os
from datetime import datetime
from threading import Lock

# Use absolute path to ensure DB is found
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../../data")
DB_PATH = os.getenv("DB_PATH", os.path.join(DATA_DIR, "deployments.db"))

class Database:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Database, cls).__new__(cls)
                    cls._instance._init_db()
        return cls._instance

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row  
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deployments (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    scenario TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    outputs TEXT,
                    error TEXT
                )
            ''')
            conn.commit()

    def create_deployment(self, deployment_id, user_id, scenario):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO deployments (id, user_id, scenario, status, created_at, updated_at, outputs)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (deployment_id, user_id, scenario, 'pending', datetime.now(), datetime.now(), '{}'))
            conn.commit()
        return deployment_id

    def update_deployment(self, deployment_id, status=None, outputs=None, error=None):
        updates = ["updated_at = ?"]
        params = [datetime.now()]

        if status:
            updates.append("status = ?")
            params.append(status)
        if outputs is not None:
            updates.append("outputs = ?")
            params.append(json.dumps(outputs))
        if error is not None:
            updates.append("error = ?")
            params.append(error)

        params.append(deployment_id)
        query = f"UPDATE deployments SET {', '.join(updates)} WHERE id = ?"

        with self._get_connection() as conn:
            conn.execute(query, params)
            conn.commit()

    def get_deployment(self, deployment_id):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM deployments WHERE id = ?", (deployment_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def list_deployments(self):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM deployments ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_deployment(self, deployment_id):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM deployments WHERE id = ?", (deployment_id,))
            conn.commit()