# src/storage/db.py
"""
SQLite DB: parking.db

Tabela: parking_events
Opis: Historia zdarzeń parkingowych (ANPR). Rekordów NIE kasujemy.

KOLUMNY:
- id (INTEGER, PK, AUTOINCREMENT)
  Unikalny identyfikator zdarzenia.

- plate (TEXT, NOT NULL)
  Numer rejestracyjny (np. SCZ26114).

- entry_time (TEXT, NOT NULL)
  Czas wjazdu / zdarzenia w ISO8601, np. 2025-12-28T19:37:53

- exit_time (TEXT, NULL)
  Czas wyjazdu (dla OUT/MANUAL_EXIT) lub NULL.

- fee_pln (INTEGER, NULL)
  Naliczona opłata w PLN (np. 60) albo NULL.

- status (TEXT, NOT NULL)
  Status zdarzenia:
  - IN          : auto jest na parkingu (aktywny pobyt)
  - OUT         : auto wyjechało, opłata policzona
  - BLOCKED     : próba wyjazdu bez aktywnego wjazdu (blokada bramki)
  - MANUAL_EXIT : ręczne wypuszczenie przez operatora
  - TEST        : wpis testowy/developerski

ZASADY:
- Jedno auto może mieć maksymalnie jeden aktywny rekord IN (wymuszone unikalnym indeksem).
- Historia zostaje w bazie jako audyt.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/parking.db")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS parking_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT NOT NULL,
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            fee_pln INTEGER,
            status TEXT NOT NULL CHECK(
                status IN ('IN', 'OUT', 'BLOCKED', 'MANUAL_EXIT', 'TEST')
            )
        );
        """)

        # Jeden aktywny wjazd na tablicę (nie da się mieć 2x IN)
        conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uniq_open_plate
        ON parking_events(plate)
        WHERE status='IN';
        """)

        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_plate_status
        ON parking_events(plate, status);
        """)

        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_entry_time
        ON parking_events(entry_time);
        """)
