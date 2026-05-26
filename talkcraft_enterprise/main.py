#!/usr/bin/env python3
"""TalkCraft Phase 5 — Advanced AI Communication Ecosystem."""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from talkcraft_enterprise.utils.logger import get_logger
from talkcraft_enterprise.utils.config import config

logger = get_logger("main")


def run_server():
    from talkcraft_enterprise.server import TalkCraftEnterpriseServer
    server = TalkCraftEnterpriseServer()
    server.run()


def run_console():
    print("TalkCraft Enterprise v5.0.0")
    print("=" * 50)
    print("Available services:")
    print("  - Multilingual Coaching (5 languages)")
    print("  - AI Avatar System (6 avatars)")
    print("  - Collaborative Rooms (up to 10 participants)")
    print("  - Enterprise Analytics")
    print("  - Behavioral Intelligence")
    print("  - Certification Scoring (4 levels)")
    print("  - Communication Benchmarking (7 categories, 6 roles)")
    print("  - Role-specific Training (6 roles, 10 scenarios)")
    print("  - Recruiter Simulator (5 interview types, 4 personas)")
    print("  - Session Recording & Replay")
    print("=" * 50)
    print("Run with --server for FastAPI server.")


def main():
    parser = argparse.ArgumentParser(description="TalkCraft Enterprise v5.0.0")
    parser.add_argument("--mode", "-m", choices=["server", "console"], default="server")
    parser.add_argument("--host", default=config.server.host, help="Server host")
    parser.add_argument("--port", type=int, default=config.server.port, help="Server port")
    parser.add_argument("--init-db", action="store_true", help="Initialize database and exit")

    args = parser.parse_args()

    if args.init_db:
        from talkcraft_enterprise.database.database import init_db
        init_db()
        print("Database initialized successfully.")
        return

    if args.mode == "server":
        config.server.host = args.host
        config.server.port = args.port
        run_server()
    else:
        run_console()


if __name__ == "__main__":
    main()
