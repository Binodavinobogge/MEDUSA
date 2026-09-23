"""Collect snapshots away from the GUI; never terminate a running scan."""
from PySide6.QtCore import QThread, Signal
from core.network_monitor import get_network_snapshot, get_network_speed
from core.connection_history import ConnectionHistory


class NetworkWorker(QThread):
    snapshot_ready = Signal(dict)
    scan_error = Signal(str)

    def __init__(self, interval=1.0, parent=None):
        super().__init__(parent)
        self.interval = interval
        self.history = ConnectionHistory(retention_seconds=60)

    def run(self):
        import time
        while not self.isInterruptionRequested():
            start = time.monotonic()
            try:
                data = self.history.enrich_snapshot(get_network_snapshot())
                data.update(get_network_speed())
                if not self.isInterruptionRequested():
                    self.snapshot_ready.emit(data)
            except Exception as error:
                self.scan_error.emit(f'{type(error).__name__}: {error}')
            # Short interruptible waits make closing responsive, even mid-interval.
            while not self.isInterruptionRequested() and time.monotonic() - start < self.interval:
                self.msleep(50)

    def stop(self):
        self.requestInterruption()
