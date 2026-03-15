"""
Enterprise-Grade Skill Organism Evolution Runner
Production-hardened wrapper with:
- File integrity verification (SHA-256 checksums)
- Atomic registry updates with backup/rollback
- Structured JSON logging with rotation
- Health gate: abort cycle if ecosystem is critically degraded
- Telemetry retention management
- Exit codes for CI/CD integration
- Lockfile to prevent concurrent execution
"""

import json
import hashlib
import logging
import os
import shutil
import signal
import sys
import time
import fcntl
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

# Ensure skill-organism modules are importable
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from organism import SkillOrganism, setup_logging

# ─── Constants ───────────────────────────────────────────────────
VERSION = "1.0.0"
LOCKFILE = SCRIPT_DIR / ".evolution.lock"
BACKUP_DIR = SCRIPT_DIR / "backups"
LOG_DIR = SCRIPT_DIR / "logs"
MAX_BACKUPS = 30  # Keep 30 days of backups
MAX_LOG_SIZE_MB = 50
TELEMETRY_RETENTION_DAYS = 90
HEALTH_GATE_THRESHOLD = 0.3  # Abort if >30% skills are critical
REGISTRY_PATH = SCRIPT_DIR / "skill_registry.json"
TELEMETRY_DB = SCRIPT_DIR / "skill_telemetry.db"

logger = logging.getLogger("enterprise_runner")


# ─── Exit Codes ──────────────────────────────────────────────────
EXIT_SUCCESS = 0
EXIT_GENERAL_FAILURE = 1
EXIT_LOCK_CONFLICT = 2
EXIT_INTEGRITY_FAILURE = 3
EXIT_HEALTH_GATE_BLOCKED = 4
EXIT_ROLLBACK_TRIGGERED = 5


# ─── Utilities ───────────────────────────────────────────────────

def sha256_file(path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def acquire_lock() -> Optional[int]:
    """Acquire exclusive lockfile. Returns file descriptor or None."""
    try:
        fd = os.open(str(LOCKFILE), os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.write(fd, f"{os.getpid()}\n".encode())
        return fd
    except (OSError, BlockingIOError):
        return None


def release_lock(fd: int) -> None:
    """Release lockfile."""
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        LOCKFILE.unlink(missing_ok=True)
    except OSError:
        pass


def setup_enterprise_logging() -> None:
    """Configure structured JSON logging with file rotation."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOG_DIR / "evolution.log"

    # Rotate if too large
    if log_file.exists() and log_file.stat().st_size > MAX_LOG_SIZE_MB * 1024 * 1024:
        rotated = LOG_DIR / f"evolution.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        shutil.move(str(log_file), str(rotated))

    # JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            if record.exc_info and record.exc_info[0]:
                log_entry["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_entry)

    # File handler (JSON)
    file_handler = logging.FileHandler(str(log_file))
    file_handler.setFormatter(JSONFormatter())

    # Console handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


# ─── Core Functions ──────────────────────────────────────────────

def create_backup() -> Path:
    """Create timestamped backup of registry. Returns backup path."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"skill_registry_{timestamp}.json"

    if REGISTRY_PATH.exists():
        shutil.copy2(str(REGISTRY_PATH), str(backup_path))
        checksum = sha256_file(backup_path)
        logger.info(f"Backup created: {backup_path.name} (sha256: {checksum[:16]}...)")
    else:
        logger.warning("No registry to back up")
        return backup_path

    # Prune old backups
    backups = sorted(BACKUP_DIR.glob("skill_registry_*.json"), reverse=True)
    for old_backup in backups[MAX_BACKUPS:]:
        old_backup.unlink()
        logger.info(f"Pruned old backup: {old_backup.name}")

    return backup_path


def rollback(backup_path: Path) -> bool:
    """Restore registry from backup."""
    if not backup_path.exists():
        logger.error(f"Backup not found: {backup_path}")
        return False

    try:
        shutil.copy2(str(backup_path), str(REGISTRY_PATH))
        logger.warning(f"ROLLBACK: Registry restored from {backup_path.name}")
        return True
    except OSError as e:
        logger.critical(f"ROLLBACK FAILED: {e}")
        return False


def verify_registry_integrity(path: Path) -> bool:
    """Validate registry JSON structure and required fields."""
    try:
        with open(path, "r") as f:
            data = json.load(f)

        # Structure checks
        if "ecosystem" not in data:
            logger.error("Integrity: missing 'ecosystem' key")
            return False
        if "skills" not in data:
            logger.error("Integrity: missing 'skills' key")
            return False

        required_fields = {
            "id", "name", "version", "status", "fitness_score",
            "usage_count", "category", "health", "generation",
            "mutation_count"
        }

        for i, skill in enumerate(data["skills"]):
            missing = required_fields - set(skill.keys())
            if missing:
                logger.error(f"Integrity: skill[{i}] missing fields: {missing}")
                return False

            # Range checks
            if not 0 <= skill["fitness_score"] <= 1.0:
                logger.error(f"Integrity: skill '{skill['id']}' fitness out of range: {skill['fitness_score']}")
                return False

            if skill["status"] not in ("active", "dormant", "deprecated"):
                logger.error(f"Integrity: skill '{skill['id']}' invalid status: {skill['status']}")
                return False

            if skill["generation"] < 0:
                logger.error(f"Integrity: skill '{skill['id']}' negative generation")
                return False

        logger.info(f"Integrity check passed: {len(data['skills'])} skills valid")
        return True

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Integrity check failed: {e}")
        return False


def check_health_gate(organism: SkillOrganism) -> bool:
    """Pre-flight health gate: abort if ecosystem is critically degraded."""
    total = len(organism.skills)
    if total == 0:
        logger.error("Health gate: no skills in registry")
        return False

    critical_count = sum(
        1 for s in organism.skills.values()
        if s.health == "critical"
    )
    deprecated_count = sum(
        1 for s in organism.skills.values()
        if s.status == "deprecated"
    )

    critical_ratio = critical_count / total
    deprecated_ratio = deprecated_count / total

    logger.info(
        f"Health gate: {total} skills, "
        f"{critical_count} critical ({critical_ratio:.1%}), "
        f"{deprecated_count} deprecated ({deprecated_ratio:.1%})"
    )

    if critical_ratio > HEALTH_GATE_THRESHOLD:
        logger.error(
            f"Health gate BLOCKED: {critical_ratio:.1%} critical "
            f"exceeds threshold {HEALTH_GATE_THRESHOLD:.1%}"
        )
        return False

    if deprecated_ratio > 0.8:
        logger.error(
            f"Health gate BLOCKED: {deprecated_ratio:.1%} deprecated "
            "exceeds 80% threshold — mass deprecation detected"
        )
        return False

    return True


def manage_telemetry_retention() -> None:
    """Prune telemetry data older than retention period."""
    if not TELEMETRY_DB.exists():
        return

    try:
        import sqlite3
        conn = sqlite3.connect(str(TELEMETRY_DB))
        cutoff = (datetime.utcnow() - timedelta(days=TELEMETRY_RETENTION_DAYS)).isoformat()
        cursor = conn.execute(
            "DELETE FROM invocations WHERE timestamp < ?", (cutoff,)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted > 0:
            logger.info(f"Telemetry retention: pruned {deleted} records older than {TELEMETRY_RETENTION_DAYS}d")
    except Exception as e:
        logger.warning(f"Telemetry retention skipped: {e}")


# ─── Main Entry Point ────────────────────────────────────────────

def run_evolution_cycle() -> int:
    """Execute one enterprise-grade evolution cycle. Returns exit code."""
    cycle_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    start_time = time.monotonic()

    setup_enterprise_logging()
    logger.info(f"{'='*60}")
    logger.info(f"EVOLUTION CYCLE START — ID: {cycle_id} — Runner v{VERSION}")
    logger.info(f"{'='*60}")

    # ── Step 1: Acquire lock ──
    lock_fd = acquire_lock()
    if lock_fd is None:
        logger.error("Another evolution cycle is already running (lock conflict)")
        return EXIT_LOCK_CONFLICT

    try:
        # ── Step 2: Pre-flight integrity check ──
        logger.info("Phase 1: Pre-flight integrity check")
        if REGISTRY_PATH.exists():
            pre_checksum = sha256_file(REGISTRY_PATH)
            logger.info(f"Registry checksum (pre): {pre_checksum[:16]}...")

            if not verify_registry_integrity(REGISTRY_PATH):
                logger.error("Pre-flight integrity check FAILED — aborting")
                return EXIT_INTEGRITY_FAILURE
        else:
            logger.error(f"Registry not found at {REGISTRY_PATH}")
            return EXIT_INTEGRITY_FAILURE

        # ── Step 3: Create backup ──
        logger.info("Phase 2: Creating backup")
        backup_path = create_backup()

        # ── Step 4: Initialize organism ──
        logger.info("Phase 3: Initializing organism")
        organism = SkillOrganism(
            registry_path=REGISTRY_PATH,
            telemetry_db=TELEMETRY_DB,
            log_dir=LOG_DIR,
        )

        # ── Step 5: Health gate ──
        logger.info("Phase 4: Health gate check")
        if not check_health_gate(organism):
            return EXIT_HEALTH_GATE_BLOCKED

        # ── Step 6: Telemetry retention ──
        logger.info("Phase 5: Telemetry retention management")
        manage_telemetry_retention()

        # ── Step 7: Run evolution cycle ──
        logger.info("Phase 6: Running evolution cycle")
        result = organism.evolve()

        if "error" in result:
            logger.error(f"Evolution cycle failed: {result['error']}")
            logger.warning("Initiating rollback...")
            if rollback(backup_path):
                return EXIT_ROLLBACK_TRIGGERED
            return EXIT_GENERAL_FAILURE

        # ── Step 8: Post-flight integrity check ──
        logger.info("Phase 7: Post-flight integrity check")
        if not verify_registry_integrity(REGISTRY_PATH):
            logger.error("Post-flight integrity check FAILED — rolling back")
            if rollback(backup_path):
                return EXIT_ROLLBACK_TRIGGERED
            return EXIT_INTEGRITY_FAILURE

        post_checksum = sha256_file(REGISTRY_PATH)
        logger.info(f"Registry checksum (post): {post_checksum[:16]}...")

        # ── Step 9: Generate report ──
        logger.info("Phase 8: Generating report")
        report = organism.report()

        report_path = LOG_DIR / f"evolution_report_{cycle_id}.json"
        with open(report_path, "w") as f:
            json.dump({
                "cycle_id": cycle_id,
                "runner_version": VERSION,
                "pre_checksum": pre_checksum,
                "post_checksum": post_checksum,
                "evolution_result": result,
                "ecosystem_report": report,
            }, f, indent=2)

        elapsed = time.monotonic() - start_time

        # ── Summary ──
        stage = result.get("stage_results", {})
        observe = stage.get("observe", {})
        mutate = stage.get("mutate", {})
        select = stage.get("select", {})
        reproduce = stage.get("reproduce", {})
        heal = stage.get("heal", {})

        logger.info(f"{'='*60}")
        logger.info(f"EVOLUTION CYCLE COMPLETE — {elapsed:.2f}s")
        logger.info(f"  Skills observed: {observe.get('total_skills', 'N/A')}")
        logger.info(f"  Anomalies: {observe.get('anomalies_detected', 0)}")
        logger.info(f"  Mutants created: {mutate.get('mutants_created', 0)}")
        logger.info(f"  Culled: {len(select.get('culled', []))}")
        logger.info(f"  Promoted: {len(select.get('promoted', []))}")
        logger.info(f"  Offspring: {reproduce.get('offspring_created', 0)}")
        logger.info(f"  Critical (healing): {len(heal.get('critical', []))}")
        logger.info(f"  Report: {report_path.name}")
        logger.info(f"{'='*60}")

        return EXIT_SUCCESS

    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        return EXIT_GENERAL_FAILURE

    finally:
        release_lock(lock_fd)
        logger.info("Lock released")


def handle_signal(signum, frame):
    """Graceful shutdown on SIGTERM/SIGINT."""
    logger.warning(f"Received signal {signum} — shutting down gracefully")
    LOCKFILE.unlink(missing_ok=True)
    sys.exit(128 + signum)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    sys.exit(run_evolution_cycle())
