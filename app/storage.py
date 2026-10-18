import json
import sqlite3
from pathlib import Path
from threading import RLock
from uuid import uuid4
from datetime import datetime, timezone

class Store:
    def __init__(self,path):
        if path != ':memory:': Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path,check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.lock=RLock()
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, owner TEXT NOT NULL, body TEXT NOT NULL)')
            self.db.execute('CREATE INDEX IF NOT EXISTS cases_owner ON cases(owner)')
    def list(self,owner):
        with self.lock:
            return [json.loads(r['body']) for r in self.db.execute('SELECT body FROM cases WHERE owner=? ORDER BY rowid DESC',(owner,))]
    def get(self,id,owner):
        with self.lock:
            r=self.db.execute('SELECT body FROM cases WHERE id=? AND owner=?',(id,owner)).fetchone()
            return json.loads(r['body']) if r else None
    def save(self,case,owner):
        with self.lock,self.db:
            self.db.execute('INSERT INTO cases VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body WHERE owner=excluded.owner',(case['id'],owner,json.dumps(case,ensure_ascii=False)))
    def create(self,title,owner,demo=False):
        case=dict(id=uuid4().hex,title=title,demo=demo,created_at=datetime.now(timezone.utc).isoformat(),trades=[],reasons={},evidence=[],reviews=[],checklist=[])
        self.save(case,owner)
        return case
