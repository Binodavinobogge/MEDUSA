"""Asynchronous, bounded public egress IP lookup; no socket inventory is sent."""
import ipaddress
import json
from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


def parse_ip(payload):
    address=ipaddress.ip_address(json.loads(bytes(payload))['ip'])
    if not address.is_global:raise ValueError('Non-public address')
    return str(address)


class PublicIPLookup(QObject):
    result=Signal(str)
    failed=Signal()
    def __init__(self,parent=None):
        super().__init__(parent)
        self.manager=QNetworkAccessManager(self);self.reply=None;self.stopped=False
        self.timer=QTimer(self);self.timer.setInterval(60000);self.timer.timeout.connect(self.refresh)
    def start(self):
        self.timer.start();self.refresh()
    def refresh(self):
        if self.stopped or self.reply is not None:return
        request=QNetworkRequest(QUrl('https://api64.ipify.org?format=json'))
        request.setTransferTimeout(6000)
        self.reply=self.manager.get(request)
        self.reply.finished.connect(self.complete)
    def complete(self):
        reply=self.reply;self.reply=None
        if reply is None:return
        try:
            if self.stopped:return
            if reply.error()!=QNetworkReply.NoError:raise ValueError('Network error')
            if reply.bytesAvailable()>1024:raise ValueError('Unexpected response')
            self.result.emit(parse_ip(reply.readAll()))
        except (ValueError,KeyError,TypeError):
            self.failed.emit()
        finally:reply.deleteLater()
    def stop(self):
        self.stopped=True;self.timer.stop()
        if self.reply is not None:self.reply.abort()
