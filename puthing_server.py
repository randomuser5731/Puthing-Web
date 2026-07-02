#!/usr/bin/env python3
"""
Puthing Around - Secret Universe (Roblox)
=========================================

The cipher awaits. A relic from the forgotten dimension.

Backend dual:
  - Local (SQLite) - for those who seek in shadows
  - Supabase - for the collective consciousness

Endpoints:
  POST /api/verify   { "guess": "..." }  -> echoes from beyond
  GET  /api/stats                         -> records of the chosen
  GET  /api/winner                        -> the victor's name
  GET  /api/hint                          -> whispers from the void

The code never leaves the sanctum.

Usage:
  python puthing_server.py init <code>    # awaken the cipher
  python puthing_server.py serve          # open the portal
  python puthing_server.py stats          # read the records
  python puthing_server.py set-code <new> # alter reality
  python puthing_server.py set-winner <name> # name the victor
  python puthing_server.py reset          # reset all
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

DB_PATH = Path(__file__).parent / "puthing.db"
DEFAULT_PORT = 8787
SUPABASE_URL = os.environ.get("PUTHING_SUPABASE_URL", "https://ovxndyvhpvtvwmubflth.supabase.co")
SUPABASE_KEY = os.environ.get("PUTHING_SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im92eG5keXZocHZ0dndtdWJmbHRoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI5OTI2NzgsImV4cCI6MjA5ODU2ODY3OH0.wT3uI4NR_Z1BLYdMRqoYw0OtVznqRD5pUiLbafMGDRI")


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Creates tables if they don't exist. Does not disturb the existing cipher."""
    conn = get_connection()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS target_code (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                code TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS code_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guess TEXT NOT NULL,
                was_correct INTEGER NOT NULL DEFAULT 0,
                attempted_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
    conn.close()


def set_code(code: str) -> None:
    """Saves (or replaces) the secret code in the database."""
    init_db()
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO target_code (id, code) VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET code = excluded.code
            """,
            (code.strip().lower(),),
        )
    conn.close()


def get_code() -> str | None:
    conn = get_connection()
    row = conn.execute("SELECT code FROM target_code WHERE id = 1").fetchone()
    conn.close()
    return row["code"] if row else None


def log_attempt(guess: str, was_correct: bool) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO code_attempts (guess, was_correct, attempted_at) VALUES (?, ?, ?)",
            (guess, int(was_correct), datetime.now(timezone.utc).isoformat()),
        )
    conn.close()


def get_stats() -> dict:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT COUNT(*) AS total_attempts,
               COALESCE(SUM(was_correct), 0) AS total_solved
        FROM code_attempts
        """
    ).fetchone()
    conn.close()
    return {"total_attempts": row["total_attempts"], "total_solved": row["total_solved"]}


# ---------------------------------------------------------------------------
# Winner management (via Supabase RPC)
# ---------------------------------------------------------------------------

def set_winner(name: str) -> dict:
    """Calls Supabase RPC to set the winner name."""
    try:
        payload = json.dumps({"name": name}).encode("utf-8")
        req = Request(
            f"{SUPABASE_URL}/rest/v1/rpc/set_winner",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            },
            method="POST",
        )
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"winner": "Anonymous", "error": str(e)}


def get_winner() -> dict:
    """Calls Supabase RPC to get the winner name."""
    try:
        req = Request(
            f"{SUPABASE_URL}/rest/v1/rpc/get_winner",
            headers={
                "Content-Type": "application/json",
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            },
            method="POST",
        )
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"winner": "Anonymous", "error": str(e)}


def reset_all() -> dict:
    """Resets the local database and Supabase winner."""
    result = {"local": "ok", "supabase": "ok"}
    try:
        if DB_PATH.exists():
            DB_PATH.unlink()
        init_db()
    except Exception as e:
        result["local"] = str(e)
    try:
        r = set_winner("Anonymous")
        if "error" in r:
            result["supabase"] = r["error"]
    except Exception as e:
        result["supabase"] = str(e)
    return result


def get_hint() -> dict:
    """Returns a progressive hint based on total attempts."""
    try:
        stats = get_stats()
        attempts = stats.get("total_attempts", 0)
        hints = [
            "the path is not on the screen",
            "look where the light does not touch",
            "the first letter is the last letter of the alphabet in reverse",
            "z is not the end",
            "count backwards from z",
            "the answer hides in plain sight",
            "read between the lines",
            "the code is 16 sigils long",
            "throzyckd is not the true code",
            "the cipher whispers: start at the edge",
        ]
        idx = min(attempts, len(hints) - 1)
        return {"attempts": attempts, "hint": hints[idx], "level": idx + 1}
    except Exception as e:
        return {"attempts": 0, "hint": "the void is silent...", "level": 0}


# ---------------------------------------------------------------------------
# Puzzle logic (Wordle-style feedback)
# ---------------------------------------------------------------------------

def compute_feedback(guess: str, code: str) -> list[str]:
    """
    Returns a list with a status for each sigil of `guess`:
      - "correct": sigil aligned with cosmic truth
      - "present": sigil echoes in the void
      - "absent": sigil lost to the void

    Same logic as the verify_code function in Postgres, adapted to Python.
    """
    guess_chars = list(guess)
    code_chars = list(code)
    feedback = ["absent"] * len(guess_chars)
    used = [False] * len(code_chars)

    # first pass: exact matches
    for i, ch in enumerate(guess_chars):
        if i < len(code_chars) and ch == code_chars[i]:
            feedback[i] = "correct"
            used[i] = True

    # second pass: correct letter, wrong position
    for i, ch in enumerate(guess_chars):
        if feedback[i] == "absent":
            for j, code_ch in enumerate(code_chars):
                if not used[j] and ch == code_ch:
                    feedback[i] = "present"
                    used[j] = True
                    break

    return feedback


def verify_code(guess: str) -> dict:
    code = get_code()
    if not code:
        return {"error": "no secret code configured yet"}

    guess = guess.strip().lower()
    feedback = compute_feedback(guess, code)
    is_correct = guess == code

    log_attempt(guess, is_correct)

    return {
        "correct": is_correct,
        "length": len(code),
        "feedback": feedback,
    }


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class PuthingHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # CORS open for seekers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(204, {})

    def do_GET(self):
        if self.path == "/api/stats":
            self._send_json(200, get_stats())
        elif self.path == "/api/winner":
            self._send_json(200, get_winner())
        elif self.path == "/api/hint":
            self._send_json(200, get_hint())
        else:
            self._send_json(404, {"error": "the void does not answer"})

    def do_POST(self):
        if self.path == "/api/verify":
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length) if length else b"{}"

            try:
                data = json.loads(raw_body or b"{}")
            except json.JSONDecodeError:
                self._send_json(400, {"error": "the offering was malformed"})
                return

            guess = str(data.get("guess", ""))
            if not guess:
                self._send_json(400, {"error": "the ritual requires a guess"})
                return

            self._send_json(200, verify_code(guess))
            return

        if self.path == "/api/winner":
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length) if length else b"{}"

            try:
                data = json.loads(raw_body or b"{}")
            except json.JSONDecodeError:
                self._send_json(400, {"error": "the offering was malformed"})
                return

            name = str(data.get("name", ""))
            if not name:
                self._send_json(400, {"error": "the victor needs a name"})
                return

            result = set_winner(name)
            self._send_json(200, result)
            return

        if self.path == "/api/reset":
            result = reset_all()
            self._send_json(200, result)
            return

        self._send_json(404, {"error": "the void does not answer"})

    def log_message(self, format, *args):
        # compact logging
        print(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}")


def serve(port: int) -> None:
    if get_code() is None:
        print(
            "The cipher sleeps.\n"
            "Awaken it first:  python puthing_server.py init <code>",
            file=sys.stderr,
        )
        sys.exit(1)

    server = ThreadingHTTPServer(("localhost", port), PuthingHandler)
    print(f"The portal opens at http://localhost:{port}")
    print("Endpoints: POST /api/verify   GET  /api/stats")
    print("           POST /api/winner   GET  /api/winner")
    print("           GET  /api/hint                         ")
    print("           POST /api/reset    GET  /api/reset")
    print("Ctrl+C to close the portal.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPortal closed.")
        server.shutdown()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Puthing Around cipher management")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="awakens the cipher")
    p_init.add_argument("code", help="the secret code (not logged)")

    p_set = sub.add_parser("set-code", help="alters the cipher")
    p_set.add_argument("code")

    p_winner = sub.add_parser("set-winner", help="names the victor")
    p_winner.add_argument("name")

    p_reset = sub.add_parser("reset", help="reset all data")

    sub.add_parser("hint", help="whispers from the void")

    p_serve = sub.add_parser("serve", help="opens the portal")
    p_serve.add_argument("--port", type=int, default=DEFAULT_PORT)

    sub.add_parser("stats", help="consults the archives")

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        set_code(args.code)
        print(f"Database sanctified at {DB_PATH}")
        print("The cipher sleeps, awaiting seekers.")

    elif args.command == "set-code":
        set_code(args.code)
        print("Reality altered.")

    elif args.command == "set-winner":
        result = set_winner(args.name)
        winner = result.get("winner", "Unknown")
        if "error" in result:
            print(f"Failed to set victor: {result['error']}")
        else:
            print(f"Victor's name set to: {winner}")

    elif args.command == "reset":
        result = reset_all()
        print(f"Local reset: {result['local']}")
        print(f"Supabase reset: {result['supabase']}")

    elif args.command == "hint":
        h = get_hint()
        print(f"[HINT] {h['hint']}")
        print(f"Attempts: {h['attempts']} | Level: {h['level']}")

    elif args.command == "serve":
        serve(args.port)

    elif args.command == "stats":
        stats = get_stats()
        print(f"Total invocations: {stats['total_attempts']}")
        print(f"Breakthroughs:    {stats['total_solved']}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        try:
            from puthing_gui import PuthingGUI
            app = PuthingGUI()
            app.run()
        except ImportError:
            print("GUI not available. Use command line:")
            print("  python puthing_server.py init <code>")
            print("  python puthing_server.py serve")
            input("Press Enter to close...")
    else:
        main()
