import logging
import os
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def _is_writable_dir(p: Path) -> bool: # _ private function to preven being imported
    try:
        p.mkdir(parents=True, exist_ok=True) # Make directory
        probe = p / ".write_test" # File
        probe.write_text("ok", encoding="utf-8") #Write to dorectory if writable
        probe.unlink(missing_ok=True) # Delete file afterward
        return True # If
    except Exception:
        return False


def _resolve_log_dir() -> Path: # Resolve current directory
    base_dir = Path(__file__).resolve().parent #
    in_container = Path("/.dockerenv").exists() # .dockerenv is available in docker directory

    possible_direc = [
        os.getenv("LOG_DIR"),
        "/app/logs" if in_container else None,  # only in Docker/Linux container
        str(base_dir),                     # local fallback
        "/tmp/logs",                       # last resort
    ]

    for raw in possible_direc: # Looping through all paths
        if not raw: # If the current is not reached; keep looping
            continue
        p = Path(raw)
        if _is_writable_dir(p): # If writable,
            logging.getLogger(__name__).info(f"Using log directory: {p}")
            return p

    raise RuntimeError("No writable log directory found. Set LOG_DIR explicitly.")

# Logger build func
def _build_logger(name: str, file_path: Path) -> logging.Logger: #Log files
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = True # Parse log outputs to other folders/ directories

    if not logger.handlers:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch(exist_ok=True)

        handler = logging.FileHandler(file_path, mode="a", encoding="utf-8") #Mode of write
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    return logger

# Calling _resolve_log_dir func
parent_dir = _resolve_log_dir()

# Creating paths to the files depending on the dir.
db_log_file_path = parent_dir / "db_logs.log"
api_log_file_path = parent_dir / "api_log.log"
streamlit_log_file_path = parent_dir / "streamlit_log.log"

# Make log files in directory
for p in (db_log_file_path, api_log_file_path, streamlit_log_file_path):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch(exist_ok=True)

db_logger = _build_logger("db_logger", db_log_file_path)
api_logger = _build_logger("api_logger", api_log_file_path)
streamlit_logger = _build_logger("streamlit_logger", streamlit_log_file_path)