import sys
import signal

from talkcraft.utils.logger import setup_logger
from talkcraft.utils.config import config
from talkcraft.engine import TalkCraftEngine


def main():
    logger = setup_logger(
        name="talkcraft",
        level=config.log_level,
        log_file=config.log_file,
    )

    logger.info("=" * 50)
    logger.info("TalkCraft - Real-Time Communication Coach")
    logger.info("=" * 50)
    logger.info(f"Audio: {config.audio.sample_rate}Hz, {config.audio.chunk_duration}s chunks")
    logger.info(f"Model: {config.transcription.model_size} ({config.transcription.compute_type})")
    logger.info(f"Platform: CPU-only inference")
    logger.info("")
    logger.info("Run the dashboard:")
    logger.info("  streamlit run talkcraft/ui/dashboard.py")
    logger.info("")
    logger.info("Or from project root:")
    logger.info("  python -m streamlit run talkcraft/ui/dashboard.py")

    engine = TalkCraftEngine()

    def signal_handler(signum, frame):
        logger.info("Shutdown signal received")
        engine.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        engine.start()
        while engine.is_running:
            signal.pause()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except AttributeError:
        try:
            import time
            while engine.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
