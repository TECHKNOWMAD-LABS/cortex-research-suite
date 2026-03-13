#!/usr/bin/env python3
"""
Enterprise Persistent Memory System - Production Implementation
Captures observations, decisions, errors, and context across sessions.
Uses hybrid search (full-text + semantic scoring) for token-efficient recall.
"""

import sqlite3
import json
import re
import sys
import hashlib
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter, defaultdict
from enum import Enum

# ============================================================================
# Constants and Enums
# ============================================================================

class ObservationType(Enum):
    """Types of observations the system can capture."""
    TOOL_OUTPUT = "tool_output"
    DECISION = "decision"
    ERROR = "error"
    FILE_CHANGE = "file_change"
    CONTEXT = "context"


STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'can', 'if', 'by', 'from', 'as',
    'it', 'its', 'that', 'this', 'these', 'those', 'i', 'you', 'he',
    'she', 'we', 'they', 'my', 'your', 'his', 'her', 'our', 'their'
}

# Synonym clusters for semantic expansion
SYNONYM_CLUSTERS = {
    'decided': {'chose', 'selected', 'picked', 'decided'},
    'error': {'failure', 'exception', 'bug', 'crash', 'error'},
    'api': {'endpoint', 'service', 'interface', 'api'},
    'database': {'db', 'sql', 'postgres', 'mysql', 'database'},
    'frontend': {'ui', 'client', 'web', 'browser', 'frontend'},
    'backend': {'server', 'api', 'service', 'backend'},
    'authentication': {'auth', 'login', 'oauth', 'jwt', 'authentication'},
}


# ============================================================================
# Observation Storage and Schema
# ============================================================================

class Observation:
    """Represents a single observation in the memory system."""

    def __init__(
        self,
        observation_id: str,
        observation_type: str,
        content: str,
        summary: str,
        context: str,
        timestamp: str,
        content_session_id: str,
        memory_session_id: str,
        project: str,
        tags: Optional[List[str]] = None,
        token_estimate: int = 0,
        private: bool = False,
    ):
        self.observation_id = observation_id
        self.observation_type = observation_type
        self.content = content
        self.summary = summary
        self.context = context
        self.timestamp = timestamp
        self.content_session_id = content_session_id
        self.memory_session_id = memory_session_id
        self.project = project
        self.tags = tags or []
        self.token_estimate = token_estimate
        self.private = private
        self.content_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA256 hash of content for integrity checking."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert observation to dictionary for storage."""
        return {
            'observation_id': self.observation_id,
            'observation_type': self.observation_type,
            'content': self.content,
            'summary': self.summary,
            'context': self.context,
            'timestamp': self.timestamp,
            'content_session_id': self.content_session_id,
            'memory_session_id': self.memory_session_id,
            'project': self.project,
            'tags': self.tags,
            'token_estimate': self.token_estimate,
            'private': self.private,
            'content_hash': self.content_hash,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Observation':
        """Create Observation from dictionary."""
        return Observation(**{k: v for k, v in data.items() if k != 'content_hash'})


# ============================================================================
# Database Layer
# ============================================================================

class MemoryDatabase:
    """SQLite-backed persistent storage with FTS5 full-text search."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema with FTS5 table."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        # Main observations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS observations (
                observation_id TEXT PRIMARY KEY,
                observation_type TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT NOT NULL,
                context TEXT,
                timestamp TEXT NOT NULL,
                content_session_id TEXT,
                memory_session_id TEXT NOT NULL,
                project TEXT NOT NULL,
                tags TEXT,
                token_estimate INTEGER DEFAULT 0,
                private INTEGER DEFAULT 0,
                content_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # FTS5 virtual table for full-text search
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
                observation_id UNINDEXED,
                summary,
                content,
                context,
                content=observations,
                content_rowid=rowid
            )
        ''')

        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                memory_session_id TEXT PRIMARY KEY,
                project TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT DEFAULT 'active',
                content_session_id TEXT
            )
        ''')

        # Triggers to keep FTS5 table in sync
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS observations_ai AFTER INSERT ON observations BEGIN
                INSERT INTO observations_fts(observation_id, summary, content, context)
                VALUES (new.observation_id, new.summary, new.content, new.context);
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS observations_ad AFTER DELETE ON observations BEGIN
                INSERT INTO observations_fts(observations_fts, observation_id, summary, content, context)
                VALUES('delete', old.observation_id, old.summary, old.content, old.context);
            END
        ''')

        self.conn.commit()

    def save_observation(self, obs: Observation) -> None:
        """Save observation to database."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO observations
            (observation_id, observation_type, content, summary, context,
             timestamp, content_session_id, memory_session_id, project,
             tags, token_estimate, private, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            obs.observation_id,
            obs.observation_type,
            obs.content,
            obs.summary,
            obs.context,
            obs.timestamp,
            obs.content_session_id,
            obs.memory_session_id,
            obs.project,
            json.dumps(obs.tags),
            obs.token_estimate,
            1 if obs.private else 0,
            obs.content_hash,
        ))
        self.conn.commit()

    def get_observation(self, observation_id: str) -> Optional[Observation]:
        """Retrieve complete observation by ID."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM observations WHERE observation_id = ?', (observation_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_observation(row)

    def delete_observation(self, observation_id: str) -> bool:
        """Delete observation by ID."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM observations WHERE observation_id = ?', (observation_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def list_observations(
        self,
        project: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Observation]:
        """List observations with optional filters."""
        query = 'SELECT * FROM observations WHERE 1=1'
        params = []

        if project:
            query += ' AND project = ?'
            params.append(project)
        if session_id:
            query += ' AND memory_session_id = ?'
            params.append(session_id)

        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [self._row_to_observation(row) for row in cursor.fetchall()]

    def save_session(
        self,
        memory_session_id: str,
        project: str,
        content_session_id: Optional[str] = None,
    ) -> None:
        """Create new memory session."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO sessions
            (memory_session_id, project, start_time, content_session_id, status)
            VALUES (?, ?, ?, ?, 'active')
        ''', (memory_session_id, project, datetime.utcnow().isoformat(), content_session_id))
        self.conn.commit()

    def end_session(self, memory_session_id: str) -> None:
        """Mark session as ended."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE sessions SET status = ?, end_time = ?
            WHERE memory_session_id = ?
        ''', ('ended', datetime.utcnow().isoformat(), memory_session_id))
        self.conn.commit()

    def get_session(self, memory_session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session metadata."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM sessions WHERE memory_session_id = ?', (memory_session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_sessions(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all sessions."""
        query = 'SELECT * FROM sessions WHERE 1=1'
        params = []
        if project:
            query += ' AND project = ?'
            params.append(project)
        query += ' ORDER BY start_time DESC'

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def _row_to_observation(self, row: sqlite3.Row) -> Observation:
        """Convert database row to Observation object."""
        return Observation(
            observation_id=row['observation_id'],
            observation_type=row['observation_type'],
            content=row['content'],
            summary=row['summary'],
            context=row['context'],
            timestamp=row['timestamp'],
            content_session_id=row['content_session_id'],
            memory_session_id=row['memory_session_id'],
            project=row['project'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            token_estimate=row['token_estimate'],
            private=bool(row['private']),
        )

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()


# ============================================================================
# Search Engine
# ============================================================================

class HybridSearchEngine:
    """Combines full-text and semantic similarity for precision recall."""

    def __init__(self, db: MemoryDatabase):
        self.db = db

    def search(
        self,
        query: str,
        project: Optional[str] = None,
        session_id: Optional[str] = None,
        observation_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exclude_private: bool = True,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Execute hybrid search with optional filters."""
        # Get all observations matching filters
        cursor = self.db.conn.cursor()
        where_clauses = ['1=1']
        params = []

        if project:
            where_clauses.append('project = ?')
            params.append(project)
        if session_id:
            where_clauses.append('memory_session_id = ?')
            params.append(session_id)
        if observation_type:
            where_clauses.append('observation_type = ?')
            params.append(observation_type)
        if exclude_private:
            where_clauses.append('private = 0')
        if start_date:
            where_clauses.append('timestamp >= ?')
            params.append(start_date)
        if end_date:
            where_clauses.append('timestamp <= ?')
            params.append(end_date)

        where_sql = ' AND '.join(where_clauses)
        cursor.execute(
            f'SELECT observation_id, summary, context, timestamp, observation_type FROM observations WHERE {where_sql}',
            params
        )
        candidates = cursor.fetchall()

        # Score candidates with hybrid approach
        scored = []
        for row in candidates:
            obs_id = row['observation_id']
            summary = row['summary'] or ''
            context = row['context'] or ''
            searchable = (summary + ' ' + context).lower()

            text_score = self._tf_idf_score(query, searchable)
            semantic_score = self._semantic_similarity(query, summary)
            combined_score = 0.6 * text_score + 0.4 * semantic_score

            if combined_score > 0:
                scored.append({
                    'observation_id': obs_id,
                    'summary': summary,
                    'context': context,
                    'type': row['observation_type'],
                    'timestamp': row['timestamp'],
                    'score': combined_score,
                    'text_score': text_score,
                    'semantic_score': semantic_score,
                })

        # Sort by score and limit
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:limit]

    def _tf_idf_score(self, query: str, document: str) -> float:
        """Calculate TF-IDF score between query and document."""
        query_terms = self._tokenize(query)
        if not query_terms:
            return 0.0

        doc_terms = self._tokenize(document)
        doc_freq = Counter(doc_terms)

        score = 0.0
        for term in query_terms:
            if term in doc_freq:
                tf = doc_freq[term] / len(doc_terms) if doc_terms else 0
                idf = math.log(len(doc_terms) + 1)  # Simplified IDF
                score += tf * idf

        return min(score, 1.0)  # Cap at 1.0

    def _semantic_similarity(self, query: str, document: str) -> float:
        """Calculate semantic similarity using keyword overlap and synonym expansion."""
        query_terms = self._extract_key_terms(query)
        doc_terms = self._extract_key_terms(document)

        if not query_terms or not doc_terms:
            return 0.0

        # Expand with synonyms
        query_expanded = self._expand_with_synonyms(query_terms)
        doc_expanded = self._expand_with_synonyms(doc_terms)

        # Calculate overlap
        overlap = query_expanded & doc_expanded
        union = query_expanded | doc_expanded

        if not union:
            return 0.0

        return len(overlap) / len(union)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text, removing stopwords."""
        tokens = re.findall(r'\b\w+\b', text.lower())
        return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    def _extract_key_terms(self, text: str) -> set:
        """Extract key terms (nouns, important words)."""
        tokens = self._tokenize(text)
        # Weight longer terms as more important (likely compound nouns)
        return set(t for t in tokens if len(t) > 3 or t in {'api', 'db', 'ui', 'ui'})

    def _expand_with_synonyms(self, terms: set) -> set:
        """Expand terms with synonyms from clusters."""
        expanded = set(terms)
        for term in terms:
            for cluster in SYNONYM_CLUSTERS.values():
                if term in cluster:
                    expanded.update(cluster)
        return expanded


# ============================================================================
# Progressive Disclosure Retrieval
# ============================================================================

class ProgressiveRetrieval:
    """3-layer retrieval strategy for token efficiency."""

    def __init__(self, db: MemoryDatabase, search_engine: HybridSearchEngine):
        self.db = db
        self.search_engine = search_engine

    def search_index(
        self,
        query: str,
        project: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """Layer 1: Fast search index with summaries."""
        results = self.search_engine.search(query, project=project, limit=limit)

        # Format for display
        formatted = []
        for r in results:
            formatted.append({
                'observation_id': r['observation_id'],
                'summary': r['summary'],
                'type': r['type'],
                'timestamp': r['timestamp'],
                'score': round(r['score'], 3),
            })

        token_estimate = len(formatted) * 50
        return {
            'layer': 'search_index',
            'query': query,
            'matches': len(formatted),
            'results': formatted,
            'token_estimate': token_estimate,
            'next_layer': 'Use get_timeline(observation_id) for chronological context',
        }

    def get_timeline(self, observation_id: str) -> Dict[str, Any]:
        """Layer 2: Chronological context around observation."""
        obs = self.db.get_observation(observation_id)
        if not obs:
            return {'error': f'Observation {observation_id} not found'}

        # Get surrounding observations (before/after)
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT observation_id, summary, observation_type, timestamp
            FROM observations
            WHERE project = ? AND memory_session_id = ?
            ORDER BY timestamp
        ''', (obs.project, obs.memory_session_id))

        all_obs = cursor.fetchall()
        indices = {row['observation_id']: i for i, row in enumerate(all_obs)}

        if observation_id not in indices:
            context_window = []
        else:
            idx = indices[observation_id]
            start = max(0, idx - 2)
            end = min(len(all_obs), idx + 3)
            context_window = [
                {
                    'observation_id': row['observation_id'],
                    'summary': row['summary'],
                    'type': row['observation_type'],
                    'timestamp': row['timestamp'],
                    'is_focus': row['observation_id'] == observation_id,
                }
                for row in all_obs[start:end]
            ]

        token_estimate = len(context_window) * 40 + 20
        return {
            'layer': 'timeline',
            'observation_id': observation_id,
            'focus_summary': obs.summary,
            'context_window': context_window,
            'token_estimate': token_estimate,
            'next_layer': 'Use get_full(observation_id) for complete content',
        }

    def get_full(self, observation_id: str) -> Dict[str, Any]:
        """Layer 3: Complete observation content."""
        obs = self.db.get_observation(observation_id)
        if not obs:
            return {'error': f'Observation {observation_id} not found'}

        # Estimate tokens in content
        token_estimate = len(obs.content.split()) // 0.75  # Rough approximation

        return {
            'layer': 'full_detail',
            'observation': obs.to_dict(),
            'token_estimate': token_estimate,
        }


# ============================================================================
# Memory Engine - Main API
# ============================================================================

class MemoryEngine:
    """Main API for persistent memory system."""

    def __init__(self, db_path: str):
        self.db = MemoryDatabase(db_path)
        self.search_engine = HybridSearchEngine(self.db)
        self.retrieval = ProgressiveRetrieval(self.db, self.search_engine)

    def start_session(
        self,
        project: str,
        content_session_id: Optional[str] = None,
    ) -> str:
        """Start new memory session."""
        memory_session_id = self._generate_session_id()
        self.db.save_session(memory_session_id, project, content_session_id)
        return memory_session_id

    def end_session(self, session_id: str) -> None:
        """End memory session."""
        self.db.end_session(session_id)

    def resume_session(self, project: str) -> str:
        """Get most recent session for project."""
        sessions = self.db.list_sessions(project=project)
        if sessions and sessions[0]['status'] == 'active':
            return sessions[0]['memory_session_id']
        return self.start_session(project)

    def save_observation(
        self,
        observation_type: str,
        content: str,
        context: str,
        project: str,
        session_id: str,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        private: bool = False,
    ) -> str:
        """Save structured observation."""
        # Auto-generate summary if not provided
        if not summary:
            summary = self._generate_summary(content)

        observation_id = self._generate_observation_id()
        obs = Observation(
            observation_id=observation_id,
            observation_type=observation_type,
            content=content,
            summary=summary,
            context=context,
            timestamp=datetime.utcnow().isoformat(),
            content_session_id=None,  # Can be set by caller
            memory_session_id=session_id,
            project=project,
            tags=tags,
            token_estimate=len(content.split()) // 0.75,
            private=private,
        )
        self.db.save_observation(obs)
        return observation_id

    def search(
        self,
        query: str,
        project: Optional[str] = None,
        session_id: Optional[str] = None,
        observation_type: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """Execute Layer 1 search."""
        return self.retrieval.search_index(query, project=project, limit=limit)

    def get_timeline(self, observation_id: str) -> Dict[str, Any]:
        """Get Layer 2 timeline context."""
        return self.retrieval.get_timeline(observation_id)

    def get_full(self, observation_id: str) -> Dict[str, Any]:
        """Get Layer 3 full observation."""
        return self.retrieval.get_full(observation_id)

    def delete_observation(self, observation_id: str) -> bool:
        """Delete observation."""
        return self.db.delete_observation(observation_id)

    def list_observations(
        self,
        project: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Observation]:
        """List observations with filters."""
        return self.db.list_observations(project=project, session_id=session_id, limit=limit)

    def export_project(self, project: str, output_file: str) -> None:
        """Export all observations for project to JSON."""
        obs_list = self.list_observations(project=project, limit=10000)
        data = {
            'project': project,
            'exported_at': datetime.utcnow().isoformat(),
            'observation_count': len(obs_list),
            'observations': [o.to_dict() for o in obs_list],
        }
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

    def import_project(self, input_file: str) -> int:
        """Import observations from JSON export."""
        with open(input_file, 'r') as f:
            data = json.load(f)

        count = 0
        for obs_data in data.get('observations', []):
            obs = Observation.from_dict(obs_data)
            self.db.save_observation(obs)
            count += 1
        return count

    def _generate_session_id(self) -> str:
        """Generate unique memory session ID."""
        now = datetime.utcnow().strftime('%Y%m%d')
        import secrets
        rand = secrets.token_hex(4)
        return f'mem_{now}_{rand}'

    def _generate_observation_id(self) -> str:
        """Generate unique observation ID."""
        now = datetime.utcnow().strftime('%Y%m%d')
        import secrets
        rand = secrets.token_hex(4)
        return f'obs_{now}_{rand}'

    def _generate_summary(self, content: str) -> str:
        """Generate 1-line summary from content."""
        # Simple heuristic: first sentence or first 100 chars
        sentences = re.split(r'[.!?]+', content)
        first = sentences[0].strip() if sentences else content
        return first[:100] if len(first) > 100 else first

    def close(self) -> None:
        """Close database connection."""
        self.db.close()


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Command-line interface."""
    if len(sys.argv) < 2:
        print_usage()
        return

    db_path = str(Path.home() / '.memory' / 'memory.db')
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = MemoryEngine(db_path)

    try:
        command = sys.argv[1]

        if command == 'save':
            handle_save(engine, sys.argv[2:])
        elif command == 'search':
            handle_search(engine, sys.argv[2:])
        elif command == 'timeline':
            handle_timeline(engine, sys.argv[2:])
        elif command == 'get':
            handle_get(engine, sys.argv[2:])
        elif command == 'delete':
            handle_delete(engine, sys.argv[2:])
        elif command == 'list':
            handle_list(engine, sys.argv[2:])
        elif command == 'sessions':
            handle_sessions(engine, sys.argv[2:])
        elif command == 'export':
            handle_export(engine, sys.argv[2:])
        elif command == 'import':
            handle_import(engine, sys.argv[2:])
        else:
            print(f'Unknown command: {command}')
            print_usage()
    finally:
        engine.close()


def handle_save(engine: MemoryEngine, args: List[str]) -> None:
    """Save observation from CLI."""
    import argparse
    parser = argparse.ArgumentParser(description='Save observation')
    parser.add_argument('--type', required=True, help='Observation type')
    parser.add_argument('--content', required=True, help='Content')
    parser.add_argument('--context', required=True, help='Context')
    parser.add_argument('--project', required=True, help='Project')
    parser.add_argument('--session', help='Session ID (auto-generated if not provided)')
    parser.add_argument('--summary', help='Summary (auto-generated if not provided)')
    parser.add_argument('--tags', help='Comma-separated tags')
    parser.add_argument('--private', action='store_true', help='Mark as private')

    opts = parser.parse_args(args)
    session_id = opts.session or engine.start_session(opts.project)
    tags = opts.tags.split(',') if opts.tags else []

    obs_id = engine.save_observation(
        observation_type=opts.type,
        content=opts.content,
        context=opts.context,
        project=opts.project,
        session_id=session_id,
        summary=opts.summary,
        tags=tags,
        private=opts.private,
    )
    print(f'✓ Saved observation: {obs_id}')


def handle_search(engine: MemoryEngine, args: List[str]) -> None:
    """Search observations from CLI."""
    import argparse
    parser = argparse.ArgumentParser(description='Search observations')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--project', help='Filter by project')
    parser.add_argument('--limit', type=int, default=5, help='Limit results')

    opts = parser.parse_args(args)
    results = engine.search(opts.query, project=opts.project, limit=opts.limit)

    print(f'\n📋 Search Results: {results["matches"]} matches (est. {results["token_estimate"]} tokens)')
    print(f'Query: "{results["query"]}"')
    for i, r in enumerate(results['results'], 1):
        print(f'\n  [{i}] {r["observation_id"]}')
        print(f'      {r["summary"][:80]}...' if len(r["summary"]) > 80 else f'      {r["summary"]}')
        print(f'      Type: {r["type"]} | Score: {r["score"]:.3f}')


def handle_timeline(engine: MemoryEngine, args: List[str]) -> None:
    """Get timeline context from CLI."""
    if not args:
        print('Usage: memory_engine.py timeline <observation_id>')
        return

    obs_id = args[0]
    result = engine.get_timeline(obs_id)

    if 'error' in result:
        print(f'✗ {result["error"]}')
        return

    print(f'\n⏱️  Timeline for {obs_id}')
    print(f'Focus: {result["focus_summary"][:80]}')
    print(f'\nContext window (est. {result["token_estimate"]} tokens):')
    for ctx in result['context_window']:
        marker = ' ← YOU ARE HERE' if ctx['is_focus'] else ''
        print(f'  [{ctx["timestamp"]}] {ctx["type"]}: {ctx["summary"][:60]}...{marker}')


def handle_get(engine: MemoryEngine, args: List[str]) -> None:
    """Get full observation from CLI."""
    if not args:
        print('Usage: memory_engine.py get <observation_id>')
        return

    obs_id = args[0]
    result = engine.get_full(obs_id)

    if 'error' in result:
        print(f'✗ {result["error"]}')
        return

    obs = result['observation']
    print(f'\n📄 Full Observation: {obs["observation_id"]}')
    print(f'Type: {obs["observation_type"]} | Timestamp: {obs["timestamp"]}')
    print(f'Project: {obs["project"]}')
    print(f'\nSummary:\n{obs["summary"]}')
    print(f'\nContent:\n{obs["content"]}')
    print(f'\n(Est. {result["token_estimate"]} tokens)')


def handle_delete(engine: MemoryEngine, args: List[str]) -> None:
    """Delete observation from CLI."""
    if not args:
        print('Usage: memory_engine.py delete <observation_id>')
        return

    obs_id = args[0]
    if engine.delete_observation(obs_id):
        print(f'✓ Deleted observation: {obs_id}')
    else:
        print(f'✗ Observation not found: {obs_id}')


def handle_list(engine: MemoryEngine, args: List[str]) -> None:
    """List observations from CLI."""
    import argparse
    parser = argparse.ArgumentParser(description='List observations')
    parser.add_argument('--project', help='Filter by project')
    parser.add_argument('--session', help='Filter by session')
    parser.add_argument('--limit', type=int, default=20, help='Limit results')

    opts = parser.parse_args(args)
    obs_list = engine.list_observations(
        project=opts.project, session_id=opts.session, limit=opts.limit
    )

    print(f'\n📚 Observations ({len(obs_list)} total)')
    for obs in obs_list:
        print(f'\n  {obs.observation_id}')
        print(f'  {obs.observation_type} | {obs.project} | {obs.timestamp}')
        print(f'  {obs.summary[:70]}...' if len(obs.summary) > 70 else f'  {obs.summary}')


def handle_sessions(engine: MemoryEngine, args: List[str]) -> None:
    """List sessions from CLI."""
    import argparse
    parser = argparse.ArgumentParser(description='List sessions')
    parser.add_argument('--project', help='Filter by project')

    opts = parser.parse_args(args)
    sessions = engine.db.list_sessions(project=opts.project)

    print(f'\n🔔 Sessions ({len(sessions)} total)')
    for sess in sessions:
        status_icon = '🟢' if sess['status'] == 'active' else '⭕'
        print(f'\n  {status_icon} {sess["memory_session_id"]}')
        print(f'    Project: {sess["project"]}')
        print(f'    Started: {sess["start_time"]}')
        if sess['end_time']:
            print(f'    Ended: {sess["end_time"]}')


def handle_export(engine: MemoryEngine, args: List[str]) -> None:
    """Export project from CLI."""
    import argparse
    parser = argparse.ArgumentParser(description='Export project')
    parser.add_argument('project', help='Project name')
    parser.add_argument('--output', help='Output file (default: project-export.json)')

    opts = parser.parse_args(args)
    output_file = opts.output or f'{opts.project}-export.json'
    engine.export_project(opts.project, output_file)
    print(f'✓ Exported to {output_file}')


def handle_import(engine: MemoryEngine, args: List[str]) -> None:
    """Import project from CLI."""
    import argparse
    parser = argparse.ArgumentParser(description='Import project')
    parser.add_argument('input_file', help='Input JSON file')

    opts = parser.parse_args(args)
    count = engine.import_project(opts.input_file)
    print(f'✓ Imported {count} observations from {opts.input_file}')


def print_usage() -> None:
    """Print CLI usage information."""
    print('''
Enterprise Persistent Memory System - CLI

Usage: python3 memory_engine.py <command> [options]

Commands:
  save        Save new observation
  search      Search observations (Layer 1)
  timeline    Get chronological context (Layer 2)
  get         Get full observation (Layer 3)
  delete      Delete observation
  list        List observations
  sessions    List memory sessions
  export      Export project to JSON
  import      Import project from JSON

Examples:
  python3 memory_engine.py save \\
    --type decision \\
    --project myapp \\
    --context database \\
    --content "Chose PostgreSQL for ACID compliance"

  python3 memory_engine.py search "authentication" --project myapp

  python3 memory_engine.py timeline obs_20260313_ab12cd34

  python3 memory_engine.py export myapp --output myapp-backup.json
''')


if __name__ == '__main__':
    main()
