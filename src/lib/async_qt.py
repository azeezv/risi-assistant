from PyQt6.QtCore import QThread, QObject, pyqtSignal
import asyncio

class AsyncQtWorker(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, coro, loop):
        super().__init__()
        self.coro = coro
        self.loop = loop
        self.task = None

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.task = self.loop.create_task(self.coro)
        self.task.add_done_callback(self._on_task_done)
        self.loop.run_forever()

    def _on_task_done(self, task):
        try:
            result = task.result()
            self.result.emit(result)
        except asyncio.CancelledError:
            pass  # Task was cancelled, expected behavior
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class AsyncQtThread:
    def __init__(self, coro):
        self.thread = QThread()
        self.loop = asyncio.new_event_loop()
        self.worker = AsyncQtWorker(coro, self.loop)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

    def start(self):
        self.thread.start()
    
    def stop(self):
        if self.thread.isRunning():
            if self.worker.task and not self.worker.task.done():
                self.loop.call_soon_threadsafe(self.worker.task.cancel)
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.quit()
            self.thread.wait()