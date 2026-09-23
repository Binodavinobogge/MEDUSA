"""Offline deterministic checks; no external network or fake production data."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from collections import namedtuple
import socket
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, Qt, QPoint
from PySide6.QtTest import QTest
from core.network_monitor import MONITORED_PORTS, get_network_snapshot
from core.connection_history import ConnectionHistory
from core.network_worker import NetworkWorker
from ui.widget import MedusaWidget


def fixture():
    ports={name:{'name':name,'port':port,'status':'OFF','reason':'Nessuna connessione rilevata','connections':[],'recent_count':0} for name,port in MONITORED_PORTS.items()}
    for name,n in [('HTTPS',8),('DNS',5),('SMB',6)]:
        info=ports[name];info.update(status='ACTIVE',active=True,reason='Connessione reale rilevata',recent_count=3)
        for i in range(n):
            info['connections'].append({'process':['brave.exe','svchost.exe','System','msedge.exe'][i%4],'pid':[12420,892,4,7180][i%4],'local':f'192.168.1.24:{52000+i}','remote':f'203.0.113.{24+i}:{info["port"]}','status':'ESTABLISHED' if name!='DNS' else 'UDP','direction':'OUTBOUND'})
    return {'ports':ports,'connections':14,'recent_connection_count':11,'ipv4':14,'ipv6':0,'local_ips':['192.168.1.24'],'download_bps':12400,'upload_bps':3100}


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.window=MedusaWidget(start_worker=False,settings=QSettings(self.tmp.name+'/settings.ini',QSettings.IniFormat))
        self.window.resize(800,1000);self.window.show();QTest.qWait(50)
    def tearDown(self):
        self.window.close();self.window.deleteLater();self.app.processEvents();self.tmp.cleanup()
    def test_live_view_collapse_selection_filter(self):
        w=self.window;data=fixture();w.apply_network_snapshot(data);QTest.qWait(80)
        https=w.port_rows['HTTPS'];self.assertEqual(https.table.rowCount(),4)
        https.more.click();self.assertEqual(https.table.rowCount(),8)
        c=https.connections[2];w.select_endpoint('HTTPS',c)
        self.assertIn(c['local'],w.endpoint.text())
        w.radar_section.header.click();QTest.qWait(300);self.assertFalse(w.radar.isVisible());self.assertFalse(w.radar.timer.isActive())
        w.radar_section.header.click();self.assertTrue(w.radar.isVisible())
        w.filter.setCurrentText('IPv6');self.assertEqual(w.radar.nodes,[])
        w.filter.setCurrentText('Tutti');self.assertEqual(len(w.radar.nodes),19)
        https.table.selectRow(0);https.copy_selected();self.assertIn('203.0.113.',QApplication.clipboard().text())
        self.assertFalse(hasattr(w,"animation"))
        # Recovery from errors must clear stale-state warning.
        w.handle_network_error('AccessDenied');self.assertTrue(w.error.isVisible())
        w.apply_network_snapshot(data);self.assertFalse(w.error.isVisible())
        empty=fixture()
        for info in empty['ports'].values():info['connections']=[]
        w.apply_network_snapshot(empty);self.assertEqual(len(w.radar.nodes),0)
        self.assertEqual(https.table.rowCount(),0)
    def test_animation_reversal_minimize_and_hidden_timers(self):
        w=self.window;w.apply_network_snapshot(fixture());QTest.qWait(100)
        section=w.radar_section;initial=section.body.height()
        section.set_open(False);QTest.qWait(100)
        self.assertGreater(section.body.height(),0)
        self.assertLess(section.body.height(),initial)
        section.set_open(True);QTest.qWait(300)
        self.assertTrue(w.radar.isVisible())
        self.assertEqual(section.body.maximumHeight(),16777215)
        w.showMinimized();phase=w.radar.phase;QTest.qWait(80)
        self.assertEqual(w.radar.phase,phase)
        self.assertFalse(w.chart.timer.isActive())
        w.showNormal();QTest.qWait(80)
        self.assertGreater(w.radar.phase,phase)
        section.set_open(False);QTest.qWait(300)
        self.assertFalse(w.radar.timer.isActive())

    def test_desktop_widget_restore_and_live_services(self):
        w=self.window;data=fixture();w.apply_network_snapshot(data)
        w.resize(740,600);w.move(20,40);QTest.qWait(20)
        geometry=w.geometry();w.compact_button.click();QTest.qWait(40)
        self.assertEqual(w.width(),320)
        self.assertFalse(w.workspace.isVisible());self.assertFalse(w.radar.timer.isActive())
        self.assertTrue(w.mini_rows['HTTPS'][0].isVisible())
        self.assertFalse(w.mini_rows['RDP'][0].isVisible())
        for info in data['ports'].values():info.update(active=False,status='OFF',connections=[])
        w.apply_network_snapshot(data);self.assertTrue(w.mini_empty.isVisible())
        w.handle_network_error('test');self.assertFalse(w.error.isVisible())
        self.assertIn('ERRORE',w.mini_status.text())
        w.compact_button.click();QTest.qWait(40)
        self.assertEqual(w.geometry(),geometry);self.assertTrue(w.workspace.isVisible())

    def test_mascot_menu_and_public_ip(self):
        w=self.window;w.apply_network_snapshot(fixture());w.public_ip_ready('8.8.8.8')
        self.assertIn('8.8.8.8',w.radar.mascot_hint)
        cx,cy,_=w.radar.radar_geometry()
        QTest.mouseClick(w.radar,Qt.LeftButton,pos=QPoint(int(cx),int(cy)))
        self.assertTrue(w.mascot_menu.isVisible())
        action=w.mascot_menu.actions()[0];self.assertTrue(action.isEnabled());action.trigger()
        self.assertEqual(QApplication.clipboard().text(),'8.8.8.8');w.mascot_menu.close()
        w.public_ip_failed();w.show_mascot_menu()
        self.assertFalse(w.mascot_menu.actions()[0].isEnabled());w.mascot_menu.close()

    def test_history_excludes_listeners_and_expires(self):
        history=ConnectionHistory(60)
        c={'pid':1,'local':'0.0.0.0:445','remote':'—','status':'LISTEN'}
        ports={'SMB':{'port':445,'connections':[c]}}
        with patch('core.connection_history.time.monotonic',return_value=100):
            history.update(ports);self.assertEqual(history.get_recent_count(),0)
            ports['SMB']['connections'].append({**c,'remote':'192.0.2.1:445','status':'ESTABLISHED'})
            history.update(ports);history.update(ports);self.assertEqual(history.get_recent_count(),1)
        with patch('core.connection_history.time.monotonic',return_value=161):self.assertEqual(history.get_recent_count(),0)
    def test_collector_families_and_listener(self):
        addr=namedtuple('addr','ip port');conn=namedtuple('conn','family type laddr raddr status pid')
        rows=[conn(socket.AF_INET,socket.SOCK_STREAM,addr('192.0.2.2',50000),addr('192.0.2.3',443),'ESTABLISHED',10),conn(socket.AF_INET6,socket.SOCK_STREAM,addr('::1',22),(),'LISTEN',11)]
        with patch('core.network_monitor.psutil.net_connections',return_value=rows),patch('core.network_monitor.get_process_name',return_value='test.exe'),patch('core.network_monitor.get_windows_service_status',return_value='UNKNOWN'):
            s=get_network_snapshot()
        self.assertEqual(s['connections'],1);self.assertEqual(s['ipv4'],1);self.assertEqual(s['ipv6'],0)
        self.assertTrue(s['ports']['SSH']['listening']);self.assertEqual(s['local_ips'],['192.0.2.2'])
    def test_worker_clean_stop(self):
        worker=NetworkWorker(.1)
        with patch('core.network_worker.get_network_snapshot',return_value=fixture()),patch('core.network_worker.get_network_speed',return_value={'download_bps':1,'upload_bps':2}):
            worker.start();QTest.qWait(150);worker.stop();self.assertTrue(worker.wait(1000))
    def test_ipv6_and_many_rows(self):
        d=fixture();c=d['ports']['HTTPS']['connections'][0]
        d['ports']['HTTPS']['connections']=[{**c,'pid':i,'remote':f'[2001:db8::{i+1}]:443'} for i in range(120)]
        self.window.apply_network_snapshot(d);self.window.filter.setCurrentText('IPv6');self.app.processEvents()
        self.assertEqual(len(self.window.radar.nodes),120)
        s=self.window.port_rows['HTTPS'];s.more.click();self.assertEqual(s.table.rowCount(),120)
        self.assertLess(s.table.height(),320)
        self.window.resize(740,520);QTest.qWait(50)
        self.assertGreater(self.window.scroll.verticalScrollBar().maximum(),0)


if __name__=='__main__':unittest.main()
