from PySide6.QtCore import QThread, Signal


class EstimateWorker(QThread):
    """Runs an estimator function on each file in a background thread.
    Emits `result(path, size_bytes)` per file. size_bytes == -1 on error.
    """
    result = Signal(str, int)
    finished_all = Signal()

    def __init__(self, files, estimator_fn):
        super().__init__()
        self._files = list(files)
        self._fn = estimator_fn
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        for f in self._files:
            if self._cancel:
                return
            try:
                size = int(self._fn(f))
            except Exception:
                size = -1
            if self._cancel:
                return
            self.result.emit(f, size)
        self.finished_all.emit()


class BatchWorker(QThread):
    progress = Signal(int, int)   # done, total
    log = Signal(str)
    finished_ok = Signal(int)     # processed count

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def _is_cancelled(self):
        return self._cancel

    def run(self):
        def progress_cb(done, total):
            self.progress.emit(done, total)

        def log_cb(msg):
            self.log.emit(msg)

        kwargs = dict(self._kwargs)
        kwargs.update(progress_cb=progress_cb, log_cb=log_cb, cancel_cb=self._is_cancelled)
        try:
            n = self._fn(*self._args, **kwargs)
            self.finished_ok.emit(n or 0)
        except Exception as e:
            self.log.emit(f"ERROR: {e}")
            self.finished_ok.emit(0)
