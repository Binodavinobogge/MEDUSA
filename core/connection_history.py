import time
from collections import deque


class ConnectionHistory:
    """
    Mantiene una cronologia temporanea delle connessioni
    osservate da MEDUSA.

    Non salva nulla su disco.

    Per ora mantiene gli eventi degli ultimi 60 secondi.
    """

    def __init__(self, retention_seconds=60):
        self.retention_seconds = retention_seconds

        self.events = deque()

        self.known_connections = set()

    # =================================================
    # IDENTIFICATORE CONNESSIONE
    # =================================================

    def _connection_key(
        self,
        service,
        connection
    ):
        """
        Crea un identificatore abbastanza stabile
        per distinguere una connessione dalle altre.
        """

        return (
            service,
            connection.get("pid"),
            connection.get("local"),
            connection.get("remote"),
            connection.get("status"),
        )

    # =================================================
    # AGGIORNAMENTO
    # =================================================

    def update(self, ports):
        """
        Riceve le porte dello snapshot corrente.

        Registra solamente le connessioni nuove rispetto
        allo snapshot precedente.
        """

        now = time.monotonic()

        current_connections = set()

        # ---------------------------------------------
        # ANALIZZA SNAPSHOT
        # ---------------------------------------------

        for service, info in ports.items():

            for connection in info.get(
                "connections",
                []
            ):

                key = self._connection_key(
                    service,
                    connection
                )

                current_connections.add(
                    key
                )

                # Connessione appena comparsa
                if key not in self.known_connections:

                    self.events.append(
                        {
                            "timestamp": now,

                            "service": service,

                            "port": info.get(
                                "port"
                            ),

                            "pid": connection.get(
                                "pid"
                            ),

                            "process": connection.get(
                                "process"
                            ),

                            "local": connection.get(
                                "local"
                            ),

                            "remote": connection.get(
                                "remote"
                            ),

                            "status": connection.get(
                                "status"
                            ),

                            "direction": connection.get(
                                "direction"
                            ),
                        }
                    )

        self.known_connections = (
            current_connections
        )

        # ---------------------------------------------
        # ELIMINA EVENTI VECCHI
        # ---------------------------------------------

        self._cleanup(
            now
        )

    # =================================================
    # CLEANUP
    # =================================================

    def _cleanup(self, now=None):

        if now is None:
            now = time.monotonic()

        limit = (
            now
            - self.retention_seconds
        )

        while (
            self.events
            and
            self.events[0]["timestamp"]
            < limit
        ):

            self.events.popleft()

    # =================================================
    # EVENTI RECENTI
    # =================================================

    def get_recent_events(
        self,
        service=None
    ):

        self._cleanup()

        events = list(
            self.events
        )

        if service is None:
            return events

        return [
            event
            for event in events
            if event["service"] == service
        ]

    # =================================================
    # CONTEGGIO
    # =================================================

    def get_recent_count(
        self,
        service=None
    ):

        return len(
            self.get_recent_events(
                service
            )
        )

    # =================================================
    # ARRICCHISCE LO SNAPSHOT
    # =================================================

    def enrich_snapshot(
        self,
        snapshot
    ):

        ports = snapshot.get(
            "ports",
            {}
        )

        self.update(
            ports
        )

        for service, info in ports.items():

            recent_events = (
                self.get_recent_events(
                    service
                )
            )

            info[
                "recent_events"
            ] = recent_events

            info[
                "recent_count"
            ] = len(
                recent_events
            )

        snapshot[
            "recent_events"
        ] = self.get_recent_events()

        snapshot[
            "recent_connection_count"
        ] = len(
            snapshot[
                "recent_events"
            ]
        )

        return snapshot