import uuid
import contextvars

_trace_id_var = contextvars.ContextVar("trace_id", default=None)


class TraceIdContext:

    @property
    def trace_id(self) -> str:
        return _trace_id_var.get()

    @trace_id.setter
    def trace_id(self, value: str | None):
        if value is None:
            value = str(uuid.uuid4())
        _trace_id_var.set(value)


trace_id_ctx = TraceIdContext()