"""终端日志输出，将每一步运行结果打印到控制台。"""

import logging
import sys
import traceback


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("ai_polish")
    if logger.handlers:
        return logger

    # Windows 终端默认编码可能导致中文乱码
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.propagate = False
    return logger


log = setup_logger()


def log_step(step: str, message: str, level: str = "info") -> None:
    """记录一个业务步骤。"""
    text = f"[{step}] {message}"
    getattr(log, level, log.info)(text)


def log_error(step: str, message: str, exc: Exception | None = None) -> None:
    """记录错误，并可选输出异常堆栈。"""
    log.error(f"[{step}] {message}")
    if exc is not None:
        log.error(f"[{step}] 异常类型: {type(exc).__name__}: {exc}")
        for line in traceback.format_exc().strip().splitlines():
            log.error(f"  {line}")
