from PyQt6.QtCore import QThread, QObject, pyqtSignal
import asyncio

class AsyncQtWorker(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, coro_or_factory, loop):
        super().__init__()
        # coro_or_factory may be either a coroutine object or a callable that
        # returns a coroutine (factory). We defer creating the coroutine
        # until we are inside the event loop thread to avoid "never awaited"
        # warnings when the coroutine is created but never scheduled.
        self.coro_or_factory = coro_or_factory
        self.loop = loop
        self.task = None

    def run(self):
        asyncio.set_event_loop(self.loop)
        try:
            # If a factory was provided, call it now (inside the thread's loop)
            if callable(self.coro_or_factory):
                coro = self.coro_or_factory()
            else:
                coro = self.coro_or_factory

            self.task = self.loop.create_task(coro)
            self.task.add_done_callback(self._on_task_done)
            self.loop.run_forever()
        finally:
            # Ensure all pending tasks are cleaned up
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            # Run the loop one more time to allow cancellation to complete
            self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self.loop.close()

    def _on_task_done(self, task):
        try:
            result = task.result()
            self.result.emit(result)
        except asyncio.CancelledError:
            pass  # Task was cancelled, expected behavior
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Stop the event loop after task completes
            self.loop.call_soon_threadsafe(self.loop.stop)
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