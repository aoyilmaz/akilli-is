"""
Akıllı İş - Arka Plan Görev Yöneticisi (Worker Manager)
"""

from PyQt6.QtCore import QThread, pyqtSignal, QObject
import traceback


class WorkerSignals(QObject):
    """Görev sinyalleri"""

    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QThread):
    """
    Genel amaçlı arka plan işçisi.
    """

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception:
            self.signals.error.emit(traceback.format_exc())
        finally:
            self.signals.finished.emit()


class WorkerManager:
    """
    Görevleri yöneten Singleton sınıf.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.workers = []
        return cls._instance

    def run_task(self, fn, on_result=None, on_error=None, on_progress=None):
        """Yeni bir görevi arka planda başlatır"""
        worker = Worker(fn)

        if on_result:
            worker.signals.result.connect(on_result)
        if on_error:
            worker.signals.error.connect(on_error)
        if on_progress:
            worker.signals.progress.connect(on_progress)

        worker.signals.finished.connect(lambda: self._cleanup_worker(worker))

        self.workers.append(worker)
        worker.start()
        return worker

    def _cleanup_worker(self, worker):
        """Biten işçiyi listeden kaldırır"""
        if worker in self.workers:
            self.workers.remove(worker)
