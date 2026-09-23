import os
import socket
import subprocess
import sys
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch,Mock
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psutil
from core.socket_inventory import build_inventory
from core.connection_control import process_target_from_row,terminate_process,ProcessTarget

class InventoryProcessTests(unittest.TestCase):
    def test_all_ports_protocols_and_bind(self):
        addr=lambda ip,port:NS(ip=ip,port=port)
        connections=[NS(pid=900,family=socket.AF_INET,type=socket.SOCK_STREAM,laddr=addr('127.0.0.1',3000),raddr=None,status='LISTEN'),
          NS(pid=900,family=socket.AF_INET6,type=socket.SOCK_STREAM,laddr=addr('::',49152),raddr=None,status='LISTEN'),
          NS(pid=None,family=socket.AF_INET,type=socket.SOCK_DGRAM,laddr=addr('0.0.0.0',5353),raddr=None,status='NONE'),
          NS(pid=900,family=socket.AF_INET,type=socket.SOCK_STREAM,laddr=addr('192.168.1.2',55234),raddr=addr('1.1.1.1',443),status='ESTABLISHED')]
        with patch('core.socket_inventory.psutil.Process',return_value=Mock(create_time=Mock(return_value=123),name=Mock(return_value='test.exe'))):rows=build_inventory(connections)
        self.assertEqual(len(rows),4)
        self.assertEqual({r['port'] for r in rows},{3000,49152,5353,55234})
        self.assertEqual(rows[0]['scope'],'Solo PC')
        self.assertEqual(sum(r['listening'] for r in rows),2)
        self.assertIn('IPv6',{r['family'] for r in rows})
    def test_protected_identity(self):
        for pid in (0,4,os.getpid(),None):
            with self.assertRaises(ValueError):process_target_from_row(dict(pid=pid,process_created=12))
    def test_pid_reuse_never_terminates(self):
        proc=Mock(create_time=Mock(return_value=15))
        with patch('core.connection_control.psutil.Process',return_value=proc):
            with self.assertRaises(RuntimeError):terminate_process(ProcessTarget(99999,12,'test'))
        proc.terminate.assert_not_called()
    def test_access_denied(self):
        proc=Mock(create_time=Mock(return_value=12),terminate=Mock(side_effect=psutil.AccessDenied(99999)))
        with patch('core.connection_control.psutil.Process',return_value=proc):
            with self.assertRaises(PermissionError):terminate_process(ProcessTarget(99999,12,'test'))
    def test_real_owned_child_only(self):
        child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])
        try:
            target=ProcessTarget(child.pid,psutil.Process(child.pid).create_time(),'test child')
            self.assertIn('terminato',terminate_process(target))
            child.wait(timeout=2)
        finally:
            if child.poll() is None:child.terminate();child.wait(timeout=2)
