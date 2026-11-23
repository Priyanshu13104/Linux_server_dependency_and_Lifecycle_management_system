import logging
from pathlib import Path

from config import LOG_FILE_PATH
from database.operations import save_activity


def setup_logger(log_path=None):
    path = Path(log_path or LOG_FILE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("linux-service-manager")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.FileHandler(path)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
    return logger


def record_activity(service_name, operation, previous_state, new_state,
                    result, error_details=None, db_path=None, log_path=None):
    logger = setup_logger(log_path)
    message = (
        f"service={service_name} operation={operation} "
        f"previous={previous_state or '-'} new={new_state or '-'} "
        f"result={result}"
    )
    if error_details:
        message += f" error={error_details}"
    if result.lower() in {"success", "ok", "recovered"}:
        logger.info(message)
    else:
        logger.warning(message)
    save_activity(
        service_name, operation, previous_state, new_state,
        result, error_details, db_path=db_path,
    )
