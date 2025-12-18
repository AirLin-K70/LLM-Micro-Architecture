import sys
import logging
from loguru import logger
from opentelemetry import trace

class InterceptHandler(logging.Handler):
    """
    拦截标准 logging 消息并重定向到 Loguru。
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def patcher(record):
    """
    将 trace_id 和 span_id 添加到日志记录中，以支持分布式链路追踪关联。
    """
    span = trace.get_current_span()
    if span:
        ctx = span.get_span_context()
        if ctx.is_valid:
            record["extra"]["trace_id"] = format(ctx.trace_id, "032x")
            record["extra"]["span_id"] = format(ctx.span_id, "016x")
        else:
            record["extra"]["trace_id"] = "N/A"
            record["extra"]["span_id"] = "N/A"
    else:
        record["extra"]["trace_id"] = "N/A"
        record["extra"]["span_id"] = "N/A"

def setup_logging():
    """
    配置全局日志设置。
    使用 Loguru 替换标准 logging 处理程序，并设置带有 trace ID 的日志格式。
    """
    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)

    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    logger.configure(
        handlers=[
            {
                "sink": sys.stdout, 
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <magenta>{extra[trace_id]}</magenta> | - <level>{message}</level>",
                "serialize": False
            }
        ],
        patcher=patcher
    )
