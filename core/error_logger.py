from datetime import datetime
from pathlib import Path
import json
import traceback

from core.config import PROJECT_DIR


def get_logs_dir():
    """Возвращает путь к папке логов рядом с проектом."""
    logs_dir = PROJECT_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def write_error_log(source, error, context=None):
    """
    Сохраняет подробный лог ошибки.
    Возвращает путь к файлу лога.
    """
    logs_dir = get_logs_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{source}_{timestamp}.log"
    log_path = logs_dir / filename

    error_text = str(error)
    trace = traceback.format_exc()
    if trace.strip() == "NoneType: None":
        trace = "Traceback недоступен (ошибка передана без активного исключения)."

    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "error": error_text,
        "context": context or {},
        "traceback": trace,
    }

    with open(log_path, "w", encoding="utf-8", errors="replace") as f:
        f.write("KuLauncher Error Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(json.dumps(payload, ensure_ascii=False, indent=2))
        f.write("\n")

    return log_path
