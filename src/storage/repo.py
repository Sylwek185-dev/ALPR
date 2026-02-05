# src/storage/repo.py
from datetime import datetime

from src.storage.db import get_conn
from src.billing.pricing import fee_for


def register_entry(plate: str, when: datetime | None = None) -> int:
    """
    Wjazd:
    - jeśli auto już jest na parkingu (status IN) -> błąd (nie tworzymy nowego wpisu)
    """
    when = when or datetime.now()

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, entry_time FROM parking_events WHERE plate=? AND status='IN' ORDER BY id DESC LIMIT 1",
            (plate,)
        ).fetchone()

        if row:
            existing_id = int(row["id"])
            existing_entry = row["entry_time"]
            raise ValueError(
                f"Pojazd {plate} już jest na parkingu (IN). "
                f"Aktywny wjazd id={existing_id}, entry_time={existing_entry}."
            )

        cur = conn.execute(
            "INSERT INTO parking_events(plate, entry_time, status) VALUES (?, ?, 'IN')",
            (plate, when.isoformat(timespec="seconds"))
        )
        return int(cur.lastrowid)


def register_exit(plate: str, when: datetime | None = None) -> dict | None:
    """
    Wyjazd:
    - jeśli brak aktywnego IN -> zapisujemy BLOCKED i zwracamy None
    - jeśli jest IN -> ustawiamy OUT + exit_time + fee_pln
    """
    when = when or datetime.now()

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, entry_time FROM parking_events WHERE plate=? AND status='IN' ORDER BY id DESC LIMIT 1",
            (plate,)
        ).fetchone()

        if not row:
            # audyt próby wyjazdu bez biletu
            conn.execute(
                "INSERT INTO parking_events(plate, entry_time, status) VALUES (?, ?, 'BLOCKED')",
                (plate, when.isoformat(timespec="seconds"))
            )
            return None

        event_id = int(row["id"])
        entry_time = datetime.fromisoformat(row["entry_time"])
        fee = fee_for(entry_time, when)

        conn.execute(
            "UPDATE parking_events SET exit_time=?, fee_pln=?, status='OUT' WHERE id=?",
            (when.isoformat(timespec="seconds"), fee, event_id)
        )

        return {
            "id": event_id,
            "plate": plate,
            "entry_time": entry_time.isoformat(timespec="seconds"),
            "exit_time": when.isoformat(timespec="seconds"),
            "fee_pln": fee,
            "status": "OUT",
        }


def manual_exit(plate: str) -> int:
    """
    Ręczne wypuszczenie (operator).
    """
    when = datetime.now()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO parking_events(plate, entry_time, exit_time, status) VALUES (?, ?, ?, 'MANUAL_EXIT')",
            (plate, when.isoformat(timespec="seconds"), when.isoformat(timespec="seconds"))
        )
        return int(cur.lastrowid)


def list_open() -> list[dict]:
    """Auta aktualnie na parkingu (status IN)"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, plate, entry_time, exit_time, fee_pln, status "
            "FROM parking_events WHERE status='IN' ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def list_last(limit: int = 20) -> list[dict]:
    """Ostatnie N rekordów (historia)"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, plate, entry_time, exit_time, fee_pln, status "
            "FROM parking_events ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def list_all() -> list[dict]:
    """CAŁA historia (do eksportu CSV)"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, plate, entry_time, exit_time, fee_pln, status "
            "FROM parking_events ORDER BY id ASC"
        ).fetchall()
        return [dict(r) for r in rows]
