"""Phase 1 application container lifecycle process."""

import signal
import threading

import structlog

from yieldlens.config import get_settings
from yieldlens.logging import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    log = structlog.get_logger("yieldlens.runtime")
    stopped = threading.Event()

    def request_stop(signum: int, _frame: object) -> None:
        log.info("shutdown_requested", signal=signum)
        stopped.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    log.info("application_ready", environment=settings.YIELDLENS_ENV, phase=1)
    stopped.wait()
    log.info("application_stopped")


if __name__ == "__main__":
    main()
