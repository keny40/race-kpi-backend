# backend/services/kra_collect_scheduler.py
import os
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from backend.services.kra_collector import collect_once, get_config_from_env

KST = timezone(timedelta(hours=9))


def _now_ts() -> int:
    return int(time.time())


def _now_kst() -> datetime:
    return datetime.now(tz=KST)


def _iso(dt: datetime) -> str:
    return dt.astimezone(KST).replace(microsecond=0).isoformat()


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@dataclass
class CollectSchedulerConfig:
    enabled: bool = True
    interval_sec: int = 60
    lease_name: str = "kra_collect_scheduler"
    lease_ttl_sec: int = 45


class KRACollectScheduler:
    def __init__(self, db_path: str, cfg: CollectSchedulerConfig):
        self.db_path = db_path
        self.cfg = cfg
        self.instance_id = os.getenv("INSTANCE_ID", str(uuid.uuid4()))
        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scheduler_leases (
                  name TEXT PRIMARY KEY,
                  instance_id TEXT NOT NULL,
                  lease_expires_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ops_logs (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts TEXT NOT NULL,
                  source TEXT NOT NULL,
                  level TEXT NOT NULL,
                  message TEXT NOT NULL,
                  detail TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ops_logs_ts ON ops_logs(ts)")
            conn.commit()
        finally:
            conn.close()

    def _log(self, level: str, message: str, detail: str = "") -> None:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO ops_logs(ts, source, level, message, detail) VALUES(?,?,?,?,?)",
                (_iso(_now_kst()), "KRA_COLLECT", level, message[:500], (detail or "")[:2000]),
            )
            conn.commit()
        finally:
            conn.close()

    def _acquire_lease(self) -> bool:
        now = _now_ts()
        expires = now + self.cfg.lease_ttl_sec
        conn = _connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT name, instance_id, lease_expires_at FROM scheduler_leases WHERE name=?",
                (self.cfg.lease_name,),
            ).fetchone()

            if row is None:
                conn.execute(
                    "INSERT INTO scheduler_leases(name, instance_id, lease_expires_at, updated_at) VALUES(?,?,?,?)",
                    (self.cfg.lease_name, self.instance_id, expires, now),
                )
                conn.commit()
                return True

            lease_expires_at = int(row["lease_expires_at"])
            if lease_expires_at < now:
                conn.execute(
                    "UPDATE scheduler_leases SET instance_id=?, lease_expires_at=?, updated_at=? WHERE name=?",
                    (self.instance_id, expires, now, self.cfg.lease_name),
                )
                conn.commit()
                return True

            if row["instance_id"] == self.instance_id:
                conn.execute(
                    "UPDATE scheduler_leases SET lease_expires_at=?, updated_at=? WHERE name=?",
                    (expires, now, self.cfg.lease_name),
                )
                conn.commit()
                return True

            conn.commit()
            return False
        except sqlite3.OperationalError:
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            conn.close()

    def _renew_lease(self) -> None:
        now = _now_ts()
        expires = now + self.cfg.lease_ttl_sec
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "UPDATE scheduler_leases SET lease_expires_at=?, updated_at=? WHERE name=? AND instance_id=?",
                (expires, now, self.cfg.lease_name, self.instance_id),
            )
            conn.commit()
        finally:
            conn.close()

    def _release_lease(self) -> None:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "DELETE FROM scheduler_leases WHERE name=? AND instance_id=?",
                (self.cfg.lease_name, self.instance_id),
            )
            conn.commit()
        finally:
            conn.close()

    def start(self) -> bool:
        if self._running:
            return True

        if not self._acquire_lease():
            self._log("WARN", "lease_not_acquired", "another_instance_running")
            return False

        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._loop, name="kra_collect_scheduler", daemon=True)
        self._thread.start()
        self._running = True
        self._log("INFO", "scheduler_started", f"interval_sec={self.cfg.interval_sec}")
        return True

    def stop(self) -> None:
        self._stop_evt.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self._thread = None
        self._running = False
        self._release_lease()
        self._log("INFO", "scheduler_stopped", "")

    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    def _loop(self) -> None:
        try:
            while not self._stop_evt.is_set():
                self._renew_lease()

                if not self.cfg.enabled:
                    time.sleep(max(1, self.cfg.interval_sec))
                    continue

                env_cfg = get_config_from_env()
                res = collect_once(self.db_path, env_cfg)
                if res.get("ok"):
                    self._log("INFO", "collect_ok", str(res))
                else:
                    self._log("ERROR", "collect_fail", str(res))

                time.sleep(max(5, self.cfg.interval_sec))
        finally:
            self._running = False
            self._release_lease()


_singleton_lock = threading.Lock()
_singleton: Optional[KRACollectScheduler] = None


def get_scheduler() -> KRACollectScheduler:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            db_path = os.getenv("DB_PATH", os.path.join(os.getcwd(), "backend", "races.db"))
            cfg = CollectSchedulerConfig(
                enabled=(os.getenv("KRA_COLLECT_SCHED_ENABLED", "1") == "1"),
                interval_sec=int(os.getenv("KRA_COLLECT_INTERVAL_SEC", "60")),
            )
            _singleton = KRACollectScheduler(db_path=db_path, cfg=cfg)
        return _singleton


def start() -> bool:
    return get_scheduler().start()


def stop() -> None:
    get_scheduler().stop()


def is_running() -> bool:
    return get_scheduler().is_running()
