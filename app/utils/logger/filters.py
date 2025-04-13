from aiologger.levels import LogLevel
from aiologger.filters import Filter
from app.utils.context import trace_id_ctx


class TraceIdFilter(Filter):

    def filter(self, record):
        # 给日志加上 trace_id

        record.trace_id = trace_id_ctx.trace_id

        # 过滤掉没有 trace_id 的日志
        if not record.trace_id:
            return False
        return True


class InfoFilter(Filter):

    # 过滤掉第三方库的日志
    def filter(self, record):
        # 过滤掉 info 以上级别（error 等）日志
        return record.levelno < LogLevel.ERROR

