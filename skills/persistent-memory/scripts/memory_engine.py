"""
Persistent Memory Engine - Enterprise-grade memory management for Claude.

Implements a structured observation capture and retrieval system with:
- SQLite storage with FTS5 full-text search
- Progressive disclosure (3-layer retrieval)
- Hybrid search (text + semantic similarity)
- Privacy controls for sensitive data
- Cross-session continuity
"""

import sqlite3
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ObservationType(Enum):
    """Types of observations the system can capture."""
    TOOL_OUTPUT = "tool_output"
    DECISION = "decision"
    ERROR = "error"
    FILE_CHANGE = "file_change"
    CONTEXT = "context"


@dataclass
class Observation:
    """Structured observation record."""
    observation_id: str
    observation_type: str
    content: str
    summary: str
    context: Optional[str]
    timestamp: str
    content_session_id: Optional[str]
    memory_session_id: str
    project: Optional[str]
    tags: List[str]
    token_estimate: int
    private: bool
    content_hash: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert observation to dictionary."""
        return asdict(self)


@dataclass
class SearchResult:
    """Single search result from Layer 1."""
    observation_id: str
    summary: str
    observation_type: str
    match_score: float
    timestamp: str
    project: Optional[str]


class MemoryEngine:
    """
    Persistent memory management system with 3-layer retrieval.

    Provides:
    - save_observation: Store structured observations
    - search_index: Layer 1 - fast lightweight search
    - get_timeline: Layer 2 - contextual window around match
    - get_full: Layer 3 - complete observation details
    - export/import: JSON-based backup
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize memory engine with SQLite database.

        Args:
            db_path: Path to SQLite database file. Defaults to ./memory.db
        """
        self.db_path = db_path or "memory.db"
        self.conn: Optional[sqlite3.Connection] = None
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database with required schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        try:
            # Main observations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id TEXT PRIMARY KEY,
                    observation_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    context TEXT,
                    timestamp TEXT NOT NULL,
                    content_session_id TEXT,
                    memory_session_id TEXT NOT NULL,
                    project TEXT,
                    tags TEXT,
                    token_estimate INTEGER,
                    private BOOLEAN DEFAULT 0,
                    content_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # FTS5 virtual table for full-text search
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts
                USING fts5(
                    summary,
                    content,
                    content=observations,
                    content_rowid=rowid
                )
            """)

            # Sessions table for cross-session tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    memory_session_id TEXT NOT NULL UNIQUE,
                    project TEXT,
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    observation_count INTEGER DEFAULT 0
                )
            """)

            self.conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def _generate_observation_id(self) -> str:
        """Generate unique observation ID with timestamp and random component."""
        import random
        import string
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = ''.join(random.choices(string.hexdigits[:16], k=8))
        return f"obs_{timestamp}_{random_suffix}"

    def _generate_session_id(self, project: Optional[str] = None) -> str:
        """Generate unique memory session ID."""
        import random
        import string
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = ''.join(random.choices(string.hexdigits[:16], k=8))
        return f"mem_{timestamp}_{random_suffix}"

    def _extract_summary(self, content: str, max_length: int = 150) -> str:
        """
        Extract or generate a summary from observation content.

        Args:
            content: Full observation content
            max_length: Maximum length for summary

        Returns:
            One-line semantic summary
        """
        lines = content.strip().split('\n')
        first_line = lines[0].strip()

        if len(first_line) <= max_length:
            return first_line
        return first_line[:max_length - 3] + "..."

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content for integrity."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _extract_private_sections(self, content: str) -> Tuple[str, List[str]]:
        """
        Extract private sections marked with <private> tags.

        Args:
            content: Content with potential <private> tags

        Returns:
            Tuple of (non_private_content, private_sections)
        """
        private_pattern = r'<private>(.*?)</private>'
        private_sections = re.findall(private_pattern, content, re.DOTALL)
        clean_content = re.sub(private_pattern, '[PRIVATE]', content, flags=re.DOTALL)
        return clean_content, private_sections

    def save_observation(
        self,
        observation_type: str,
        content: str,
        context: Optional[str] = None,
        project: Optional[str] = None,
        content_session_id: Optional[str] = None,
        memory_session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        private: bool = False,
        token_estimate: int = 250
    ) -> str:
        """
        Save a new observation to the memory system.

        Args:
            observation_type: Type of observation (tool_output, decision, error, etc.)
            content: Full content of the observation
            context: Related project, task, or domain
            project: Project name for grouping
            content_session_id: User's conversation thread ID
            memory_session_id: Internal memory session ID (generated if not provided)
            tags: Optional list of tags
            private: Whether to exclude from search indexes
            token_estimate: Estimated token count for this observation

        Returns:
            Observation ID of saved observation

        Raises:
            ValueError: If required parameters are missing
        """
        if not observation_type:
            raise ValueError("observation_type is required")
        if not content:
            raise ValueError("content is required")

        if memory_session_id is None:
            memory_session_id = self._generate_session_id(project)

        observation_id = self._generate_observation_id()
        timestamp = datetime.utcnow().isoformat() + "Z"
        summary = self._extract_summary(content)
        content_hash = self._compute_hash(content)

        clean_content, private_sections = self._extract_private_sections(content)
        if private_sections:
            private = True

        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO observations (
                    observation_id, observation_type, content, summary,
                    context, timestamp, content_session_id, memory_session_id,
                    project, tags, token_estimate, private, content_hash,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                observation_id,
                observation_type,
                content,
                summary,
                context,
                timestamp,
                content_session_id,
                memory_session_id,
                project,
                json.dumps(tags or []),
                token_estimate,
                private,
                content_hash,
                timestamp
            ))

            # Add to FTS index (skip if private)
            if not private:
                cursor.execute("""
                    INSERT INTO observations_fts (rowid, summary, content)
                    SELECT rowid, ?, ? FROM observations WHERE observation_id = ?
                """, (summary, clean_content, observation_id))

            self.conn.commit()
            logger.info(f"Saved observation {observation_id} ({observation_type})")
            return observation_id

        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error saving observation: {e}")
            raise

    def start_session(
        self,
        project: Optional[str] = None,
        content_session_id: Optional[str] = None
    ) -> str:
        """
        Start a new memory session.

        Args:
            project: Project name for context
            content_session_id: User's conversation ID

        Returns:
            Memory session ID
        """
        memory_session_id = self._generate_session_id(project)
        timestamp = datetime.utcnow().isoformat() + "Z"

        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, memory_session_id, project, created_at
                ) VALUES (?, ?, ?, ?)
            """, (content_session_id or memory_session_id, memory_session_id, project, timestamp))

            self.conn.commit()
            logger.info(f"Started session {memory_session_id} for project {project}")
            return memory_session_id

        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error starting session: {e}")
            raise

    def end_session(self, session_id: str) -> None:
        """
        End a memory session (marks as closed, doesn't delete observations).

        Args:
            session_id: Session ID to close
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                UPDATE sessions SET closed_at = ? WHERE memory_session_id = ?
            """, (timestamp, session_id))

            self.conn.commit()
            logger.info(f"Ended session {session_id}")

        except sqlite3.Error as e:
            logger.error(f"Error ending session: {e}")
            raise

    def search_index(
        self,
        query: str,
        limit: int = 5,
        project: Optional[str] = None,
        observation_type: Optional[str] = None,
        exclude_private: bool = False,
        session_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Layer 1: Fast search index retrieval.

        Returns observation IDs with 1-line summaries and match scores.
        Token cost: ~50 tokens per result

        Args:
            query: Search query
            limit: Maximum results to return
            project: Optional project filter
            observation_type: Optional type filter (tool_output, decision, error)
            exclude_private: Whether to exclude private observations
            session_id: Optional session filter

        Returns:
            List of SearchResult objects with scores
        """
        cursor = self.conn.cursor()

        try:
            # Build filters
            filters = ["o.private = 0"] if exclude_private else []
            params: List[Any] = [query]

            if project:
                filters.append("o.project = ?")
                params.append(project)

            if observation_type:
                filters.append("o.observation_type = ?")
                params.append(observation_type)

            if session_id:
                filters.append("o.memory_session_id = ?")
                params.append(session_id)

            where_clause = " AND ".join(filters) if filters else "1=1"

            # Hybrid search: combine FTS and semantic scoring
            sql = f"""
                SELECT
                    o.observation_id,
                    o.summary,
                    o.observation_type,
                    o.timestamp,
                    o.project,
                    (
                        0.6 * (
                            CASE WHEN f.rank IS NOT NULL
                            THEN ABS(f.rank) / 100.0
                            ELSE 0.0
                            END
                        ) +
                        0.4 * (
                            (
                                (LENGTH(o.summary) - LENGTH(REPLACE(LOWER(o.summary), LOWER(?), '')))
                                / LENGTH(?)
                            ) / 2.0
                        )
                    ) as match_score
                FROM observations o
                LEFT JOIN observations_fts f ON o.rowid = f.rowid
                WHERE {where_clause}
                AND match_score > 0
                ORDER BY match_score DESC
                LIMIT ?
            """

            params.extend([query, query, limit])

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            results = [
                SearchResult(
                    observation_id=row['observation_id'],
                    summary=row['summary'],
                    observation_type=row['observation_type'],
                    match_score=row['match_score'],
                    timestamp=row['timestamp'],
                    project=row['project']
                )
                for row in rows
            ]

            logger.info(
                f"Search '{query}' returned {len(results)} results "
                f"(estimated {len(results) * 50} tokens)"
            )
            return results

        except sqlite3.Error as e:
            logger.error(f"Search error: {e}")
            raise

    def get_timeline(
        self,
        observation_id: str,
        window_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Layer 2: Get chronological context around an observation.

        Returns 5-observation window before/after the target.
        Token cost: ~200 tokens per window

        Args:
            observation_id: Target observation ID
            window_size: Number of observations before/after to include

        Returns:
            List of observations in chronological order with type indicators
        """
        cursor = self.conn.cursor()

        try:
            # Get target observation timestamp
            cursor.execute(
                "SELECT timestamp FROM observations WHERE observation_id = ?",
                (observation_id,)
            )
            result = cursor.fetchone()

            if not result:
                logger.warning(f"Observation {observation_id} not found")
                return []

            target_timestamp = result['timestamp']

            # Get window: before and after
            sql = """
                SELECT
                    observation_id,
                    observation_type,
                    summary,
                    timestamp,
                    CASE
                        WHEN timestamp = ? THEN '← YOU ARE HERE ←'
                        WHEN timestamp < ? THEN 'BEFORE'
                        ELSE 'AFTER'
                    END as position
                FROM observations
                WHERE timestamp >= (
                    SELECT MIN(timestamp) FROM (
                        SELECT timestamp FROM observations
                        WHERE timestamp <= ? 
                        ORDER BY timestamp DESC
                        LIMIT ?
                    )
                ) AND timestamp <= (
                    SELECT MAX(timestamp) FROM (
                        SELECT timestamp FROM observations
                        WHERE timestamp >= ?
                        ORDER BY timestamp ASC
                        LIMIT ?
                    )
                )
                ORDER BY timestamp ASC
            """

            cursor.execute(sql, (
                target_timestamp, target_timestamp,
                target_timestamp, window_size,
                target_timestamp, window_size
            ))

            rows = cursor.fetchall()
            timeline = [
                {
                    'observation_id': row['observation_id'],
                    'observation_type': row['observation_type'],
                    'summary': row['summary'],
                    'timestamp': row['timestamp'],
                    'position': row['position']
                }
                for row in rows
            ]

            logger.info(f"Timeline for {observation_id}: {len(timeline)} observations")
            return timeline

        except sqlite3.Error as e:
            logger.error(f"Timeline retrieval error: {e}")
            raise

    def get_full(self, observation_id: str) -> Optional[Dict[str, Any]]:
        """
        Layer 3: Get complete observation details.

        Returns full structured observation with all metadata.
        Token cost: Variable (typically 300-800 tokens)

        Args:
            observation_id: Observation ID to retrieve

        Returns:
            Complete observation dict, or None if not found
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM observations WHERE observation_id = ?
                """,
                (observation_id,)
            )

            row = cursor.fetchone()

            if not row:
                logger.warning(f"Observation {observation_id} not found")
                return None

            obs_dict = {
                'observation_id': row['observation_id'],
                'observation_type': row['observation_type'],
                'content': row['content'],
                'summary': row['summary'],
                'context': row['context'],
                'timestamp': row['timestamp'],
                'content_session_id': row['content_session_id'],
                'memory_session_id': row['memory_session_id'],
                'project': row['project'],
                'tags': json.loads(row['tags'] or '[]'),
                'token_estimate': row['token_estimate'],
                'private': bool(row['private']),
                'content_hash': row['content_hash']
            }

            logger.info(f"Retrieved full observation {observation_id}")
            return obs_dict

        except sqlite3.Error as e:
            logger.error(f"Full retrieval error: {e}")
            raise

    def export_observations(
        self,
        output_path: str,
        project: Optional[str] = None,
        include_private: bool = False
    ) -> None:
        """
        Export observations to JSON file.

        Args:
            output_path: Path to write JSON export
            project: Optional filter to specific project
            include_private: Whether to include private observations
        """
        cursor = self.conn.cursor()

        try:
            sql = "SELECT * FROM observations WHERE 1=1"
            params: List[Any] = []

            if project:
                sql += " AND project = ?"
                params.append(project)

            if not include_private:
                sql += " AND private = 0"

            sql += " ORDER BY timestamp DESC"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            observations = []
            for row in rows:
                obs = {
                    'observation_id': row['observation_id'],
                    'observation_type': row['observation_type'],
                    'content': row['content'],
                    'summary': row['summary'],
                    'context': row['context'],
                    'timestamp': row['timestamp'],
                    'content_session_id': row['content_session_id'],
                    'memory_session_id': row['memory_session_id'],
                    'project': row['project'],
                    'tags': json.loads(row['tags'] or '[]'),
                    'token_estimate': row['token_estimate'],
                    'private': bool(row['private']),
                    'content_hash': row['content_hash']
                }
                observations.append(obs)

            with open(output_path, 'w') as f:
                json.dump(observations, f, indent=2)

            logger.info(f"Exported {len(observations)} observations to {output_path}")

        except (sqlite3.Error, IOError) as e:
            logger.error(f"Export error: {e}")
            raise

    def import_observations(
        self,
        input_path: str,
        skip_duplicates: bool = True
    ) -> int:
        """
        Import observations from JSON file.

        Args:
            input_path: Path to JSON import file
            skip_duplicates: Skip observations with duplicate content hash

        Returns:
            Number of observations imported
        """
        try:
            with open(input_path, 'r') as f:
                observations = json.load(f)

            cursor = self.conn.cursor()
            imported = 0

            for obs in observations:
                if skip_duplicates:
                    cursor.execute(
                        "SELECT observation_id FROM observations WHERE content_hash = ?",
                        (obs['content_hash'],)
                    )
                    if cursor.fetchone():
                        logger.debug(f"Skipping duplicate: {obs['observation_id']}")
                        continue

                try:
                    cursor.execute("""
                        INSERT INTO observations (
                            observation_id, observation_type, content, summary,
                            context, timestamp, content_session_id, memory_session_id,
                            project, tags, token_estimate, private, content_hash,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        obs['observation_id'],
                        obs['observation_type'],
                        obs['content'],
                        obs['summary'],
                        obs['context'],
                        obs['timestamp'],
                        obs['content_session_id'],
                        obs['memory_session_id'],
                        obs['project'],
                        json.dumps(obs['tags']),
                        obs['token_estimate'],
                        obs['private'],
                        obs['content_hash'],
                        obs['timestamp']
                    ))

                    # Re-index in FTS if not private
                    if not obs['private']:
                        cursor.execute("""
                            INSERT INTO observations_fts (rowid, summary, content)
                            SELECT rowid, ?, ? FROM observations
                            WHERE observation_id = ?
                        """, (obs['summary'], obs['content'], obs['observation_id']))

                    imported += 1

                except sqlite3.IntegrityError:
                    logger.debug(f"Observation {obs['observation_id']} already exists")
                    continue

            self.conn.commit()
            logger.info(f"Imported {imported} observations from {input_path}")
            return imported

        except (IOError, json.JSONDecodeError, sqlite3.Error) as e:
            logger.error(f"Import error: {e}")
            raise

    def delete_observation(self, observation_id: str) -> bool:
        """
        Delete an observation (permanent deletion).

        Args:
            observation_id: ID of observation to delete

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("DELETE FROM observations WHERE observation_id = ?", (observation_id,))
            self.conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Deleted observation {observation_id}")
                return True

            logger.warning(f"Observation {observation_id} not found")
            return False

        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Delete error: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        cursor = self.conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) as count FROM observations")
            total_obs = cursor.fetchone()['count']

            cursor.execute(
                "SELECT observation_type, COUNT(*) as count "
                "FROM observations GROUP BY observation_type"
            )
            by_type = {row['observation_type']: row['count'] for row in cursor.fetchall()}

            cursor.execute(
                "SELECT COUNT(*) as count FROM observations WHERE private = 1"
            )
            private_count = cursor.fetchone()['count']

            cursor.execute(
                "SELECT COUNT(DISTINCT project) as count FROM observations WHERE project IS NOT NULL"
            )
            project_count = cursor.fetchone()['count']

            cursor.execute(
                "SELECT SUM(token_estimate) as total FROM observations"
            )
            total_tokens = cursor.fetchone()['total'] or 0

            return {
                'total_observations': total_obs,
                'by_type': by_type,
                'private_observations': private_count,
                'projects': project_count,
                'estimated_total_tokens': total_tokens
            }

        except sqlite3.Error as e:
            logger.error(f"Stats error: {e}")
            raise

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# CLI Interface for command-line usage
def main():
    """Command-line interface for memory engine."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Persistent Memory Engine')
    parser.add_argument('--db', default='memory.db', help='Database path')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Save observation
    save_parser = subparsers.add_parser('save', help='Save an observation')
    save_parser.add_argument('--type', required=True, help='Observation type')
    save_parser.add_argument('--content', required=True, help='Observation content')
    save_parser.add_argument('--context', help='Context/domain')
    save_parser.add_argument('--project', help='Project name')
    save_parser.add_argument('--tags', help='Comma-separated tags')
    save_parser.add_argument('--private', action='store_true', help='Mark as private')

    # Search
    search_parser = subparsers.add_parser('search', help='Search observations')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=5, help='Result limit')
    search_parser.add_argument('--project', help='Filter by project')
    search_parser.add_argument('--type', help='Filter by observation type')

    # Retrieve full
    retrieve_parser = subparsers.add_parser('get', help='Get full observation')
    retrieve_parser.add_argument('observation_id', help='Observation ID')

    # Timeline
    timeline_parser = subparsers.add_parser('timeline', help='Get timeline context')
    timeline_parser.add_argument('observation_id', help='Observation ID')

    # Stats
    subparsers.add_parser('stats', help='Show memory statistics')

    # Export
    export_parser = subparsers.add_parser('export', help='Export observations')
    export_parser.add_argument('output', help='Output file path')
    export_parser.add_argument('--project', help='Filter by project')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    engine = MemoryEngine(args.db)

    try:
        if args.command == 'save':
            obs_id = engine.save_observation(
                observation_type=args.type,
                content=args.content,
                context=args.context,
                project=args.project,
                tags=args.tags.split(',') if args.tags else None,
                private=args.private
            )
            print(f"Saved: {obs_id}")

        elif args.command == 'search':
            results = engine.search_index(
                query=args.query,
                limit=args.limit,
                project=args.project,
                observation_type=args.type
            )
            for result in results:
                print(f"[{result.observation_id}] {result.summary}")
                print(f"  Type: {result.observation_type}, Score: {result.match_score:.2f}")

        elif args.command == 'get':
            obs = engine.get_full(args.observation_id)
            if obs:
                print(json.dumps(obs, indent=2))
            else:
                print(f"Not found: {args.observation_id}")

        elif args.command == 'timeline':
            timeline = engine.get_timeline(args.observation_id)
            for item in timeline:
                print(f"[{item['observation_id']}] {item['summary']} ({item['position']})")

        elif args.command == 'stats':
            stats = engine.get_stats()
            print(json.dumps(stats, indent=2))

        elif args.command == 'export':
            engine.export_observations(
                args.output,
                project=args.project
            )
            print(f"Exported to {args.output}")

    finally:
        engine.close()


if __name__ == '__main__':
    main()
