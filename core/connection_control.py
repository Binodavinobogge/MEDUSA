"""Explicit, selected TCP/IPv4 disconnect via the documented Windows API."""
import ctypes
import ipaddress
import socket
import sys
from dataclasses import dataclass
import psutil


@dataclass(frozen=True)
class ConnectionTarget:
    pid: int
    created: float
    local_ip: str
    local_port: int
    remote_ip: str
    remote_port: int


def target_from_row(row):
    if row.get('status') != 'ESTABLISHED':
        raise ValueError('Disponibile solo per connessioni TCP stabilite; non UDP o socket in ascolto.')
    if row.get('pid') is None or row.get('process_created') is None:
        raise ValueError('Identità del processo non verificabile: chiusura non disponibile.')
    def endpoint(text):
        host,port=text.rsplit(':',1)
        ip=ipaddress.ip_address(host.strip('[]'))
        if ip.version!=4:raise ValueError('La chiusura IPv6 non è supportata in questa versione.')
        port=int(port)
        if not 1<=port<=65535:raise ValueError('Porta non valida.')
        return str(ip),port
    local=endpoint(row['local']);remote=endpoint(row['remote'])
    return ConnectionTarget(int(row['pid']),float(row['process_created']),*local,*remote)


class TcpRow(ctypes.Structure):
    _fields_=[(name,ctypes.c_uint32) for name in ('state','local_addr','local_port','remote_addr','remote_port')]


def make_tcp_row(target):
    # DWORD address holds network-order bytes in little-endian Windows memory.
    return TcpRow(12,int.from_bytes(socket.inet_aton(target.local_ip),'little'),socket.htons(target.local_port),
                  int.from_bytes(socket.inet_aton(target.remote_ip),'little'),socket.htons(target.remote_port))


def native_delete(target):
    api=ctypes.WinDLL('iphlpapi.dll',use_last_error=True).SetTcpEntry
    api.argtypes=[ctypes.POINTER(TcpRow)];api.restype=ctypes.c_uint32
    row=make_tcp_row(target)
    result=api(ctypes.byref(row))
    if result in (5,317):raise PermissionError('Avvia MEDUSA come amministratore per chiudere connessioni.')
    if result:raise OSError(result,ctypes.FormatError(result))


def close_connection(target):
    if sys.platform!='win32':raise OSError('Chiusura disponibile solo su Windows.')
    process=psutil.Process(target.pid)
    if process.create_time()!=target.created:
        raise RuntimeError('Il processo è cambiato. Seleziona nuovamente la connessione.')
    matches=[c for c in psutil.net_connections(kind='tcp4') if c.pid==target.pid and c.status==psutil.CONN_ESTABLISHED
             and c.laddr and c.raddr and (c.laddr.ip,c.laddr.port,c.raddr.ip,c.raddr.port)==
             (target.local_ip,target.local_port,target.remote_ip,target.remote_port)]
    if not matches:raise RuntimeError('La connessione selezionata non è più attiva. Nessuna azione eseguita.')
    if psutil.Process(target.pid).create_time()!=target.created:raise RuntimeError('Identità del processo cambiata.')
    native_delete(target)
    return 'Windows ha accettato la chiusura. Il monitor aggiornerà i dati; il programma può riconnettersi.'


@dataclass(frozen=True)
class ProcessTarget:
    pid: int
    created: float
    name: str


def process_target_from_row(row):
    import os
    pid=row.get('pid');created=row.get('process_created')
    if pid is None or created is None:
        raise ValueError('Identità del processo non disponibile.')
    if int(pid)<=4 or int(pid)==os.getpid():
        raise ValueError('Processo di sistema essenziale o MEDUSA: azione disabilitata.')
    return ProcessTarget(int(pid),float(created),str(row.get('process','—')))


def terminate_process(target):
    # Reapply restrictions even if invoked outside the UI.
    process_target_from_row(dict(pid=target.pid,process_created=target.created,process=target.name))
    try:
        proc=psutil.Process(target.pid)
        if proc.create_time()!=target.created:
            raise RuntimeError('Il PID appartiene ora a un altro processo. Nessuna azione eseguita.')
        proc.terminate()
        try:proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            raise RuntimeError('Richiesta inviata, ma il processo non risulta ancora terminato. Nessun ulteriore tentativo automatico.')
    except psutil.NoSuchProcess:
        raise RuntimeError('Il processo non è più presente.')
    except psutil.AccessDenied:
        raise PermissionError('Accesso negato: il processo è protetto o richiede privilegi amministrativi.')
    return f'{target.name} (PID {target.pid}) terminato. Un servizio potrebbe riavviarlo automaticamente.'
