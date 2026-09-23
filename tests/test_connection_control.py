import ctypes
import socket
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import connection_control as cc


def row():return dict(status='ESTABLISHED',pid=123,process_created=100.0,local='192.168.1.2:50000',remote='1.1.1.1:443')

class ConnectionControlTests(unittest.TestCase):
    def test_api_layout(self):
        native=cc.make_tcp_row(cc.target_from_row(row()))
        self.assertEqual(ctypes.sizeof(native),20)
        self.assertEqual(bytes(native)[4:8],socket.inet_aton('192.168.1.2'))
        self.assertEqual(bytes(native)[8:10],(50000).to_bytes(2,'big'))
        self.assertEqual(native.state,12)
    def test_unsupported_rows(self):
        for changes in ({'status':'UDP'},{'status':'LISTEN'},{'remote':'[::1]:443'},{'pid':None},{'process_created':None}):
            with self.assertRaises(ValueError):cc.target_from_row({**row(),**changes})
    def test_exact_match_only(self):
        target=cc.target_from_row(row())
        conn=SimpleNamespace(pid=123,status='ESTABLISHED',laddr=SimpleNamespace(ip='192.168.1.2',port=50000),raddr=SimpleNamespace(ip='1.1.1.1',port=443))
        with patch.object(cc.sys,'platform','win32'),patch.object(cc.psutil,'Process',return_value=Mock(create_time=Mock(return_value=100.0))),patch.object(cc.psutil,'net_connections',return_value=[conn]),patch.object(cc,'native_delete') as delete:
            cc.close_connection(target);delete.assert_called_once_with(target)
            delete.reset_mock();conn.pid=999
            with self.assertRaises(RuntimeError):cc.close_connection(target)
            delete.assert_not_called()
    def test_pid_reuse_and_missing_connection(self):
        with patch.object(cc.sys,'platform','win32'),patch.object(cc.psutil,'Process',return_value=Mock(create_time=Mock(return_value=101.0))),patch.object(cc,'native_delete') as delete:
            with self.assertRaises(RuntimeError):cc.close_connection(cc.target_from_row(row()))
            delete.assert_not_called()
    def test_native_access_denied(self):
        function=Mock(return_value=5)
        dll=Mock(SetTcpEntry=function)
        with patch.object(cc.ctypes,'WinDLL',return_value=dll,create=True):
            with self.assertRaises(PermissionError):cc.native_delete(cc.target_from_row(row()))
