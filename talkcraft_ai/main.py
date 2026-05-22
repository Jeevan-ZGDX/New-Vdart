#!/usr/bin/env python3
"""TalkCraft Phase 3 — AI Conversation Intelligence Launcher."""

import argparse
import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from talkcraft_ai.utils.config import config
from talkcraft_ai.utils.logger import setup_logger, get_logger

logger = get_logger("main")


def run_dashboard():
    logger.info("Starting TalkCraft AI Dashboard (Phase 3)")
    dashboard_path = Path(__file__).resolve().parent / "dashboard" / "app.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent) + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        "--server.port", str(config.dashboard.port),
        "--server.headless", "true",
    ]
    logger.info(f"Launching: {' '.join(cmd)}")
    subprocess.run(cmd, env=env)


def run_server():
    logger.info("Starting TalkCraft AI Server (Phase 3)")
    from talkcraft_ai.server import create_server
    server = create_server()
    server.run()


def run_console():
    logger.info("Starting TalkCraft AI Console Mode (Phase 3)")
    from talkcraft_ai.agents.llm_client import LLMClient
    from talkcraft_ai.scoring.conversation_scorer import ConversationScorer
    from talkcraft_ai.conversation.engine import ConversationEngine
    from talkcraft_ai.conversation.modes import MODES, get_topics_for_mode

    llm = LLMClient()
    scorer = ConversationScorer()
    engine = ConversationEngine(llm, scorer)

    if not llm.is_available():
        logger.warning("LLM API not available. Check your config.")
        print("\n⚠️  LLM API not available!")
        print(f"   Configured endpoint: {config.llm.api_base}")
        print(f"   Model: {config.llm.model}")
        print("\n   Make sure Ollama is running or update config.json with your API endpoint.\n")
        return

    print("\n" + "=" * 60)
    print("  [MIC] TalkCraft AI - Conversation Console Mode")
    print("=" * 60)
    print("\nAvailable modes:")
    for mid, mode in MODES.items():
        print(f"  {mid}: {mode.name}")
    mode_id = input("\nSelect mode (default: casual_conversation): ").strip() or "casual_conversation"
    if mode_id not in MODES:
        mode_id = "casual_conversation"
    mode = MODES[mode_id]
    topics = get_topics_for_mode(mode_id)
    print(f"\nAvailable topics for {mode.name}:")
    for i, t in enumerate(topics, 1):
        print(f"  {i}. {t}")
    topic_input = input("\nSelect topic number or enter custom topic (or leave blank): ").strip()
    topic = ""
    if topic_input.isdigit() and 1 <= int(topic_input) <= len(topics):
        topic = topics[int(topic_input) - 1]
    elif topic_input:
        topic = topic_input
    print(f"\nStarting conversation in {mode.name} mode...")
    if topic:
        print(f"Topic: {topic}")
    print("\n" + "-" * 60)
    print("Commands:")
    print("  Type your message and press Enter")
    print("  Type 'exit' or 'quit' to end")
    print("  Type 'followup' to generate follow-up questions")
    print("  Type 'scores' to see current scores")
    print("-" * 60 + "\n")
    engine.set_mode(mode_id, topic)
    greeting = engine.start_conversation()
    if greeting:
        print(f"🤖 {mode.name}: {greeting.content}\n")
    try:
        while engine.is_active:
            user_input = input("🗣️  You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break
            if user_input.lower() == "followup":
                questions = engine.generate_followup_questions()
                if questions:
                    print("\n💡 Follow-up questions:")
                    for i, q in enumerate(questions, 1):
                        print(f"  {i}. {q}")
                    print()
                continue
            if user_input.lower() == "scores":
                scores = scorer.get_scores_dict()
                print(f"\n📊 Current Scores:")
                for k, v in scores.items():
                    if k != "trend" and k != "total_turns":
                        print(f"  {k}: {v:.0%}" if isinstance(v, float) else f"  {k}: {v}")
                print(f"  Trend: {scores.get('trend', 'N/A')}")
                print()
                continue
            response = engine.process_user_input(user_input)
            if response:
                print(f"🤖 {mode.name}: {response.content}\n")
    except KeyboardInterrupt:
        print("\n")
    finally:
        summary = engine.stop_conversation()
        print("\n" + "=" * 60)
        print("  📋 Session Summary")
        print("=" * 60)
        sc = summary.get("scores", {})
        print(f"  Total Turns: {summary.get('total_turns', 0)}")
        print(f"  Duration: {summary.get('duration', 0):.1f}s")
        print(f"  Average Score: {sc.get('average', 0):.0%}")
        print(f"  Best Score: {sc.get('best', 0):.0%}")
        print(f"  Trend: {sc.get('trend', 'stable').title()}")
        print(f"  Difficulty: {summary.get('difficulty', 'intermediate').title()}")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="TalkCraft Phase 3 — Real-time AI Conversation Intelligence",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["dashboard", "server", "console"],
        default="dashboard",
        help="Launch mode (default: dashboard)",
    )
    parser.add_argument("--host", default=config.server.host, help="Server host")
    parser.add_argument("--port", type=int, default=config.server.port, help="Server port")
    parser.add_argument("--dashboard-port", type=int, default=config.dashboard.port, help="Dashboard port")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    if args.debug:
        setup_logger(level="DEBUG")
    if args.mode == "dashboard":
        config.dashboard.port = args.dashboard_port
        run_dashboard()
    elif args.mode == "server":
        config.server.host = args.host
        config.server.port = args.port
        run_server()
    elif args.mode == "console":
        run_console()


if __name__ == "__main__":
    main()
