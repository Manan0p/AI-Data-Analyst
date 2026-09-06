import logging
import sys
from pythonjsonlogger.json import JsonFormatter
from app.config import settings


def setup_logging():
    """Configure root logger with structured JSON formatting for observability."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    if settings.log_format.lower() == "json":
        formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)


def setup_sentry():
    """Conditionally configure Sentry error tracking if SENTRY_DSN is provided."""
    if settings.sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                traces_sample_rate=1.0,
            )
            logging.getLogger(__name__).info("Sentry SDK successfully initialized")
        except Exception as exc:
            logging.getLogger(__name__).warning("Failed to initialize Sentry SDK: %s", exc)
