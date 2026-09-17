import socket
import sys
import time

import psutil


MONITORED_PORTS = {
    "HTTPS": 443,
    "DNS": 53,
    "SMB": 445,
    "RDP": 3389,
    "SSH": 22,
}


# =====================================================
# TRAFFICO REALTIME
# =====================================================

_last_network_io = None
_last_network_time = None


# =====================================================
# CACHE SERVIZI WINDOWS
# =====================================================

_service_cache = {}
_service_cache_time = {}

SERVICE_CACHE_SECONDS = 5


# =====================================================
# PROCESSI
# =====================================================

def get_process_name(pid):

    if pid is None:
        return "Sconosciuto"

    if pid == 0:
        return "System Idle"

    if pid == 4:
        return "System"

    try:
        return psutil.Process(
            pid
        ).name()

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess,
    ):
        return f"PID {pid}"


# =====================================================
# SERVIZI WINDOWS
# =====================================================

def get_windows_service_status(
    service_name
):

    if sys.platform != "win32":
        return "UNKNOWN"

    now = time.monotonic()

    last_time = (
        _service_cache_time.get(
            service_name,
            0
        )
    )

    if (
        service_name in _service_cache
        and
        now - last_time
        < SERVICE_CACHE_SECONDS
    ):

        return _service_cache[
            service_name
        ]

    try:

        service = psutil.win_service_get(
            service_name
        )

        status = (
            service.status().lower()
        )

        if status == "running":
            result = "RUNNING"

        elif status == "stopped":
            result = "STOPPED"

        else:
            result = status.upper()

    except Exception:
        result = "UNKNOWN"

    _service_cache[
        service_name
    ] = result

    _service_cache_time[
        service_name
    ] = now

    return result


# =====================================================
# ENDPOINT
# =====================================================

def format_endpoint(address):

    if not address:
        return "—"

    try:

        ip = address.ip
        port = address.port

        # IPv6 più leggibile
        if ":" in ip:
            return f"[{ip}]:{port}"

        return f"{ip}:{port}"

    except AttributeError:
        return "—"


# =====================================================
# TRAFFICO REALTIME
# =====================================================

def get_network_speed():

    global _last_network_io
    global _last_network_time

    current_io = (
        psutil.net_io_counters()
    )

    current_time = (
        time.monotonic()
    )

    if (
        _last_network_io is None
        or
        _last_network_time is None
    ):

        _last_network_io = current_io
        _last_network_time = current_time

        return {
            "download_bps": 0.0,
            "upload_bps": 0.0,
        }

    elapsed = (
        current_time
        - _last_network_time
    )

    if elapsed <= 0:
        elapsed = 0.001

    received_delta = (
        current_io.bytes_recv
        - _last_network_io.bytes_recv
    )

    sent_delta = (
        current_io.bytes_sent
        - _last_network_io.bytes_sent
    )

    download_bps = max(
        0,
        received_delta / elapsed
    )

    upload_bps = max(
        0,
        sent_delta / elapsed
    )

    _last_network_io = current_io
    _last_network_time = current_time

    return {
        "download_bps":
            download_bps,

        "upload_bps":
            upload_bps,
    }


# =====================================================
# SNAPSHOT RETE
# =====================================================

def get_network_snapshot():

    connections = (
        psutil.net_connections(
            kind="inet"
        )
    )

    ports = {}

    process_cache = {}

    for (
        name,
        port
    ) in MONITORED_PORTS.items():

        ports[name] = {

            "name": name,
            "port": port,

            "status": "OFF",

            "listening": False,
            "active": False,

            "reason":
                "Nessuna attività rilevata",

            "connections": [],

            "process_name": None,
            "pid": None,

            "local_address": None,
            "remote_address": None,
        }

    active_connections = 0

    # =================================================
    # SOCKET / CONNESSIONI
    # =================================================

    for conn in connections:

        local_port = (
            conn.laddr.port
            if conn.laddr
            else None
        )

        remote_port = (
            conn.raddr.port
            if conn.raddr
            else None
        )

        if (
            conn.status
            == psutil.CONN_ESTABLISHED
        ):
            active_connections += 1

        for (
            name,
            monitored_port
        ) in MONITORED_PORTS.items():

            local_match = (
                local_port
                == monitored_port
            )

            remote_match = (
                remote_port
                == monitored_port
            )

            if not (
                local_match
                or remote_match
            ):
                continue

            # -----------------------------------------
            # PROCESSO
            # -----------------------------------------

            if conn.pid in process_cache:

                process_name = (
                    process_cache[
                        conn.pid
                    ]
                )

            else:

                process_name = (
                    get_process_name(
                        conn.pid
                    )
                )

                process_cache[
                    conn.pid
                ] = process_name

            # -----------------------------------------
            # LISTENING
            # -----------------------------------------

            if (
                local_match
                and
                conn.status
                == psutil.CONN_LISTEN
            ):

                ports[
                    name
                ]["listening"] = True

                ports[
                    name
                ]["connections"].append(
                    {
                        "pid":
                            conn.pid,

                        "process":
                            process_name,

                        "local":
                            format_endpoint(
                                conn.laddr
                            ),

                        "remote":
                            "—",

                        "status":
                            "LISTEN",

                        "direction":
                            "IN ASCOLTO",
                    }
                )

                continue

            # -----------------------------------------
            # TCP ATTIVO
            # -----------------------------------------

            is_tcp_active = (

                conn.type
                == socket.SOCK_STREAM

                and

                conn.status
                == psutil.CONN_ESTABLISHED
            )

            # -----------------------------------------
            # UDP ATTIVO
            # -----------------------------------------

            is_udp_active = (

                conn.type
                == socket.SOCK_DGRAM

                and

                bool(
                    conn.raddr
                )
            )

            if not (
                is_tcp_active
                or is_udp_active
            ):
                continue

            ports[
                name
            ]["active"] = True

            # -----------------------------------------
            # DIREZIONE
            # -----------------------------------------

            if remote_match:

                direction = "OUTBOUND"

            elif local_match:

                direction = "INBOUND"

            else:

                direction = "—"

            ports[
                name
            ]["connections"].append(
                {
                    "pid":
                        conn.pid,

                    "process":
                        process_name,

                    "local":
                        format_endpoint(
                            conn.laddr
                        ),

                    "remote":
                        format_endpoint(
                            conn.raddr
                        ),

                    "status":
                        (
                            conn.status
                            if conn.status
                            else "UDP"
                        ),

                    "direction":
                        direction,
                }
            )

    # =================================================
    # STATO PORTE
    # =================================================

    for (
        name,
        info
    ) in ports.items():

        if info["active"]:

            info["status"] = "ACTIVE"

            info["reason"] = (
                "Connessione reale "
                "rilevata"
            )

        elif info["listening"]:

            info["status"] = (
                "LISTENING"
            )

            info["reason"] = (
                "Socket locale "
                "in ascolto"
            )

        else:

            info["status"] = "OFF"

            info["reason"] = (
                "Nessuna socket o "
                "connessione rilevata"
            )

        # Connessione principale
        # mostrata nel widget.

        if info["connections"]:

            selected = None

            for connection in (
                info["connections"]
            ):

                if (
                    connection["remote"]
                    != "—"
                ):

                    selected = connection
                    break

            if selected is None:

                selected = (
                    info[
                        "connections"
                    ][0]
                )

            info[
                "process_name"
            ] = selected[
                "process"
            ]

            info[
                "pid"
            ] = selected[
                "pid"
            ]

            info[
                "local_address"
            ] = selected[
                "local"
            ]

            info[
                "remote_address"
            ] = selected[
                "remote"
            ]

    # =================================================
    # SMB
    # =================================================

    smb_service = (
        get_windows_service_status(
            "LanmanServer"
        )
    )

    smb = ports["SMB"]

    smb[
        "service_status"
    ] = smb_service

    if smb["active"]:

        smb["status"] = "ACTIVE"

        smb["reason"] = (
            "Traffico SMB reale "
            "rilevato"
        )

    elif smb_service == "STOPPED":

        smb["status"] = (
            "SERVER_OFF"
        )

        if smb["listening"]:

            smb["reason"] = (
                "TCP/445 risulta "
                "in ascolto a livello "
                "di sistema, ma "
                "LanmanServer è fermo"
            )

        else:

            smb["reason"] = (
                "Il servizio SMB Server "
                "(LanmanServer) è fermo"
            )

    elif smb_service == "RUNNING":

        if smb["listening"]:

            smb["status"] = (
                "LISTENING"
            )

            smb["reason"] = (
                "LanmanServer è attivo "
                "e TCP/445 è in ascolto"
            )

        else:

            smb["status"] = "OFF"

            smb["reason"] = (
                "LanmanServer è attivo "
                "ma TCP/445 non risulta "
                "in ascolto"
            )

    return {

        "ports":
            ports,

        "connections":
            active_connections,
    }