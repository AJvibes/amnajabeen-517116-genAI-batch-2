import sqlite3
import json
from datetime import datetime
import uuid

DB_FILE = 'argus_scorer.db'

def init_db():
    """Initialize database with arguments table"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS arguments (
            id TEXT PRIMARY KEY,
            argument_text TEXT NOT NULL,
            overall_score REAL,
            logic INTEGER,
            evidence INTEGER,
            clarity INTEGER,
            depth INTEGER,
            bias TEXT,
            explanation TEXT,
            weaknesses TEXT,
            improvement_points TEXT,
            confidence TEXT,
            source TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_argument(data):
    """Save argument to database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    arg_id = data.get('id', str(uuid.uuid4()))
    
    c.execute('''
        INSERT OR REPLACE INTO arguments 
        (id, argument_text, overall_score, logic, evidence, clarity, depth, 
         bias, explanation, weaknesses, improvement_points, confidence, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        arg_id,
        data.get('argument', ''),
        data.get('overall_score', 0),
        data.get('logic', 0),
        data.get('evidence', 0),
        data.get('clarity', 0),
        data.get('depth', 0),
        data.get('bias', 'Medium'),
        data.get('explanation', ''),
        json.dumps(data.get('weaknesses', [])),
        json.dumps(data.get('improvement_points', [])),
        data.get('confidence', 'Medium'),
        data.get('source', ''),
        data.get('created_at', datetime.utcnow().isoformat())
    ))
    
    conn.commit()
    conn.close()
    return arg_id

def get_all_history():
    """Get all arguments from history"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM arguments ORDER BY created_at DESC LIMIT 100')
    rows = c.fetchall()
    
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            'id': row['id'],
            'argument': row['argument_text'],
            'overall_score': row['overall_score'],
            'logic': row['logic'],
            'evidence': row['evidence'],
            'clarity': row['clarity'],
            'depth': row['depth'],
            'bias': row['bias'],
            'explanation': row['explanation'],
            'weaknesses': json.loads(row['weaknesses']) if row['weaknesses'] else [],
            'improvement_points': json.loads(row['improvement_points']) if row['improvement_points'] else [],
            'confidence': row['confidence'],
            'source': row['source'],
            'created_at': row['created_at']
        })
    
    return results

def delete_argument(arg_id):
    """Delete specific argument from history"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM arguments WHERE id = ?', (arg_id,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted