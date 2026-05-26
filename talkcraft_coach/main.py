#!/usr/bin/env python3
"""TalkCraft Phase 4 — Advanced Communication Intelligence + Personalized Coaching."""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from talkcraft_coach.utils.logger import get_logger
from talkcraft_coach.utils.config import config

logger = get_logger("main")


def run_server():
    from talkcraft_coach.server import TalkCraftCoachServer
    server = TalkCraftCoachServer()
    server.run()


def run_dashboard():
    from talkcraft_coach.dashboard.app import run_dashboard
    run_dashboard()


def run_console():
    print("TalkCraft Coach Console v4.0.0")
    print("=" * 50)
    print("This is an interactive API module.")
    print("Run with --server for FastAPI server.")
    print("Run with --dashboard for Streamlit UI.")


def main():
    parser = argparse.ArgumentParser(description="TalkCraft Coach v4.0.0")
    parser.add_argument(
        "--mode", "-m",
        choices=["server", "dashboard", "console"],
        default="server",
        help="Run mode (default: server)",
    )
    parser.add_argument("--host", default=config.server.host, help="Server host")
    parser.add_argument("--port", type=int, default=config.server.port, help="Server port")
    parser.add_argument("--init-db", action="store_true", help="Initialize database and exit")

    args = parser.parse_args()

    if args.init_db:
        from talkcraft_coach.database.database import init_db
        init_db()
        print("Database initialized successfully.")
        return

    if args.mode == "server":
        config.server.host = args.host
        config.server.port = args.port
        run_server()
    elif args.mode == "dashboard":
        run_dashboard()
    else:
        run_console()


if __name__ == "__main__":
    main()
