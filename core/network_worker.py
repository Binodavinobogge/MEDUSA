import time

from PySide6.QtCore import (
    QThread,
    Signal
)

from core.network_monitor import (
    get_network_snapshot
)

from core.connection_history import (
    ConnectionHistory
)


class NetworkWorker(QThread):

    snapshot_ready = Signal(
        dict
    )

    scan_error = Signal(
        str
    )

    def __init__(
        self,
        interval=1.5,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.interval = interval

        self._running = True

        # ---------------------------------------------
        # MEMORIA RETE
        # ---------------------------------------------

        self.history = ConnectionHistory(
            retention_seconds=60
        )

    # =================================================

    def run(self):

        while self._running:

            start_time = (
                time.monotonic()
            )

            try:

                # -------------------------------------
                # SNAPSHOT ATTUALE
                # -------------------------------------

                data = (
                    get_network_snapshot()
                )

                # -------------------------------------
                # CRONOLOGIA
                # -------------------------------------

                data = (
                    self.history.enrich_snapshot(
                        data
                    )
                )

                # -------------------------------------
                # INVIO ALLA UI
                # -------------------------------------

                self.snapshot_ready.emit(
                    data
                )

            except Exception as error:

                self.scan_error.emit(
                    str(error)
                )

            # -----------------------------------------
            # RISPETTA INTERVALLO
            # -----------------------------------------

            elapsed = (
                time.monotonic()
                - start_time
            )

            remaining = (
                self.interval
                - elapsed
            )

            if remaining > 0:

                self.msleep(
                    int(
                        remaining
                        * 1000
                    )
                )

    # =================================================

    def stop(self):

        self._running = False