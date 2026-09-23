"""Local TCP/UDP sockets across all ports; no active network scanning."""
import ipaddress
import socket
import psutil


def endpoint(address):
    if not address:return '—'
    return f'[{address.ip}]:{address.port}' if ':' in address.ip else f'{address.ip}:{address.port}'


def build_inventory(connections):
    processes={};rows=[]
    for conn in connections:
        if not conn.laddr or conn.family not in (socket.AF_INET,socket.AF_INET6):continue
        if conn.type not in (socket.SOCK_STREAM,socket.SOCK_DGRAM):continue
        if conn.pid not in processes:
            name='Non disponibile';created=None
            if conn.pid is not None:
                try:
                    proc=psutil.Process(conn.pid)
                    created=proc.create_time();name=proc.name()
                except (psutil.Error,OSError):pass
            processes[conn.pid]=(name,created)
        name,created=processes[conn.pid]
        ip=ipaddress.ip_address(conn.laddr.ip.split('%')[0])
        scope='Solo PC' if ip.is_loopback else ('Tutte le interfacce' if ip.is_unspecified else 'Interfaccia locale')
        tcp=conn.type==socket.SOCK_STREAM
        rows.append(dict(pid=conn.pid,process=name,process_created=created,
            port=conn.laddr.port,protocol='TCP' if tcp else 'UDP',family='IPv4' if conn.family==socket.AF_INET else 'IPv6',
            local=endpoint(conn.laddr),remote=endpoint(conn.raddr),status=conn.status if tcp else 'UDP',
            listening=tcp and conn.status==psutil.CONN_LISTEN,scope=scope))
    return sorted(rows,key=lambda r:(r['port'],r['protocol'],r['family'],r['local'],r['remote'],r['pid'] or -1))
