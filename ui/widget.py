"""MEDUSA native PySide6 interface, connected to the original collector."""
import sys
import platform
import socket
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSettings, Signal, QByteArray, QPropertyAnimation, QEasingCurve, QEvent, QThread, QSize, QRectF, QPoint
from PySide6.QtGui import QFont, QIcon, QKeySequence, QShortcut, QPainter, QPainterPath, QLinearGradient, QColor, QPen
from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QLabel, QPushButton, QToolButton,
    QVBoxLayout, QHBoxLayout, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSizeGrip, QComboBox, QSizePolicy, QMessageBox, QLineEdit, QMenu,
)
from core.network_monitor import MONITORED_PORTS
from core.network_worker import NetworkWorker
from core.public_ip import PublicIPLookup
from core.connection_control import target_from_row, close_connection, process_target_from_row, terminate_process
from ui.graphics import Radar, Jellyfish, TrafficChart, StatusLamp, speed, ASSET


def label(text, name='', mono=False):
    w=QLabel(text)
    w.setObjectName(name)
    w.setTextFormat(Qt.PlainText)
    if mono:w.setProperty('mono',True)
    w.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return w


def layout(parent, horizontal=False, margins=(0,0,0,0), spacing=8):
    box=QHBoxLayout(parent) if horizontal else QVBoxLayout(parent)
    box.setContentsMargins(*margins);box.setSpacing(spacing)
    return box


class DisconnectJob(QThread):
    completed=Signal(bool,str)
    def __init__(self,target,parent=None,operation=close_connection):
        super().__init__(parent);self.target=target;self.operation=operation
    def run(self):
        try:self.completed.emit(True,self.operation(self.target))
        except Exception as exc:self.completed.emit(False,str(exc) or type(exc).__name__)


class Section(QFrame):
    toggled=Signal(bool)
    settled=Signal(bool)
    def __init__(self,title,opened=True,parent=None):
        super().__init__(parent)
        self.setObjectName('section')
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        box=layout(self,spacing=0)
        self.header=QToolButton()
        self.header.setObjectName('sectionHeader')
        self.header.setText(title)
        self.header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
        self.header.setMinimumHeight(40)
        self.header.setCheckable(True)
        self.body=QWidget();self.body.setObjectName('sectionBody')
        box.addWidget(self.header);box.addWidget(self.body)
        self.motion_enabled=True
        self.reveal=QPropertyAnimation(self.body,b'maximumHeight',self)
        self.reveal.setDuration(240)
        self.reveal.setEasingCurve(QEasingCurve.InOutCubic)
        self.reveal.finished.connect(self._settled)
        self.header.toggled.connect(self._toggle)
        self.header.setChecked(opened)
        self._toggle(opened)
    def _toggle(self,opened):
        self.header.setArrowType(Qt.DownArrow if opened else Qt.RightArrow)
        self.reveal.stop()
        if self.isVisible() and self.motion_enabled:
            start=self.body.height() if self.body.isVisible() else 0
            self.body.setVisible(True)
            target=max(1,self.body.layout().sizeHint().height()) if opened and self.body.layout() else 0
            self.reveal.setStartValue(start);self.reveal.setEndValue(target)
            self.reveal.start()
        else:
            self.body.setMaximumHeight(16777215 if opened else 0)
            self.body.setVisible(opened)
        self.header.setAccessibleDescription('Comprimi' if opened else 'Espandi')
        self.toggled.emit(opened)
    def _settled(self):
        opened=self.header.isChecked()
        self.body.setVisible(opened)
        self.body.setMaximumHeight(16777215 if opened else 0)
        self.settled.emit(opened)
    def set_open(self,opened):self.header.setChecked(opened)


class ServiceSection(Section):
    connection_selected=Signal(str,dict)
    close_requested=Signal(str,dict)
    terminate_requested=Signal(dict)
    def __init__(self,name,port,opened=False):
        super().__init__(f'{name}   {port}     ·     In attesa',opened)
        self.name=name;self.port=port;self.connections=[];self.signature=None;self.selected_key=None
        self.expanded_rows=False
        self.header.setText('')
        self.header.setArrowType(Qt.NoArrow)
        self.header.setMinimumHeight(48)
        hr=layout(self.header,True,(12,5,14,5),14)
        self.chevron=label('⌄' if opened else '›','serviceChevron')
        self.lamp=StatusLamp()
        self.service_name=label(name,'serviceName')
        self.port_badge=label(str(port),'portBadge',True)
        self.summary_label=label('In attesa','serviceSummary',True)
        for child in (self.chevron,self.lamp,self.service_name,self.port_badge):hr.addWidget(child)
        hr.addStretch();hr.addWidget(self.summary_label)
        for child in (self.chevron,self.lamp,self.service_name,self.port_badge,self.summary_label):
            child.setAttribute(Qt.WA_TransparentForMouseEvents)
            if isinstance(child,QLabel):child.setTextInteractionFlags(Qt.NoTextInteraction)
        self.header.setAccessibleName(f'{name}, porta {port}, in attesa')
        box=layout(self.body,margins=(12,0,12,10),spacing=5)
        self.reason=label('In attesa del primo rilevamento','muted')
        self.reason.setWordWrap(True)
        box.addWidget(self.reason)
        self.table=QTableWidget(0,4)
        self.table.setHorizontalHeaderLabels(['PROCESSO','PID','ENDPOINT REMOTO','STATO'])
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch)
        self.table.setColumnWidth(0,160);self.table.setColumnWidth(1,62);self.table.setColumnWidth(3,120)
        self.table.setAccessibleName(f'Connessioni {name}; seleziona una riga per indirizzo locale e remoto')
        self.table.itemSelectionChanged.connect(self._selected)
        box.addWidget(self.table)
        self.more=QPushButton('Mostra tutte');self.more.setObjectName('textButton')
        self.more.clicked.connect(self._more);box.addWidget(self.more,0,Qt.AlignLeft)
        self.detail=label('Seleziona una connessione per vedere l’indirizzo locale.','detail',True)
        self.detail.setWordWrap(True);box.addWidget(self.detail)
        self.close_button=QPushButton('Chiudi connessione')
        self.close_button.setObjectName('closeConnection');self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.request_close);box.addWidget(self.close_button,0,Qt.AlignRight)
        self.close_button.setToolTip('Seleziona una connessione TCP IPv4')
        self.terminate_button=QPushButton('Termina processo');self.terminate_button.setObjectName('closeConnection')
        self.terminate_button.setEnabled(False);box.addWidget(self.terminate_button,0,Qt.AlignRight)
        self.terminate_button.clicked.connect(self.request_terminate)
        box.removeWidget(self.close_button);box.removeWidget(self.terminate_button)
        actions=QWidget();action_row=layout(actions,True);action_row.addStretch()
        action_row.addWidget(self.close_button);action_row.addWidget(self.terminate_button);box.addWidget(actions)
        self.recent=label('','muted');box.addWidget(self.recent)
        shortcut=QShortcut(QKeySequence.Copy,self.table)
        shortcut.setContext(Qt.WidgetWithChildrenShortcut);shortcut.activated.connect(self.copy_selected)
    @staticmethod
    def row_key(c):
        return (c.get('pid'),c.get('process_created'),c.get('local'),c.get('remote'),c.get('status'))
    def request_terminate(self):
        i=self.table.currentRow()
        if 0<=i<self.table.rowCount():self.terminate_requested.emit(dict(self.connections[i]))
    def request_close(self):
        i=self.table.currentRow()
        if 0<=i<self.table.rowCount():self.close_requested.emit(self.name,dict(self.connections[i]))
    def _toggle(self,opened):
        super()._toggle(opened)
        self.header.setArrowType(Qt.NoArrow)
        if hasattr(self,'chevron'):self.chevron.setText('⌄' if opened else '›')
    def set_indicator(self,state,description):
        self.lamp.set_state(state)
        self.header.setToolTip(description)
    def copy_selected(self):
        i=self.table.currentRow()
        if 0<=i<len(self.connections):
            c=self.connections[i]
            QApplication.clipboard().setText(f'{c.get("process")}\t{c.get("pid")}\t{c.get("local")}\t{c.get("remote")}\t{c.get("status")}')
    def _more(self):
        self.expanded_rows=not self.expanded_rows;self.render_rows()
    def update_info(self,info):
        conns=info.get('connections',[])
        active=sum(c.get('remote') not in (None,'','—') for c in conns)
        listening=sum(c.get('status')=='LISTEN' for c in conns)
        summary=f'{active} connessioni' if active else (f'{listening} in ascolto' if listening else 'Nessuna connessione')
        self.summary_label.setText(summary)
        state='active' if active else ('listening' if listening and info.get('status')!='SERVER_OFF' else 'idle')
        if info.get('status')=='ERROR':state='error'
        description={'active':'Connessioni attive','listening':'In ascolto','idle':'Inattivo','error':'Errore di lettura'}[state]
        self.set_indicator(state,description+' · '+info.get('reason',''))
        self.header.setAccessibleName(f'{self.name}, porta {self.port}, {description}, {summary}')
        self.header.setProperty('active',bool(active))
        self.header.style().unpolish(self.header);self.header.style().polish(self.header)
        self.reason.setText(info.get('reason',''))
        self.reason.setVisible(not active)
        self.recent.setText(f'{info.get("recent_count",0)} nuove osservate / 60 s')
        self.recent.hide()
        ordered=sorted(conns,key=lambda c:(c.get('remote')=='—',c.get('process',''),str(c.get('pid')),c.get('remote',''),c.get('local','')))
        sig=repr(ordered)
        if sig!=self.signature:
            self.connections=ordered;self.signature=sig;self.render_rows()
    def render_rows(self):
        old_key=self.selected_key
        self.table.blockSignals(True)
        count=len(self.connections) if self.expanded_rows else min(4,len(self.connections))
        self.table.setRowCount(count)
        for i,c in enumerate(self.connections[:count]):
            values=[c.get('process','—'),str(c.get('pid') if c.get('pid') is not None else '—'),c.get('remote','—'),c.get('status','—')]
            for col,value in enumerate(values):
                item=QTableWidgetItem(value)
                if col in (1,2,3):item.setFont(QFont('Consolas',10))
                item.setToolTip(f'{value}\nLocale: {c.get("local","—")}\nDirezione: {c.get("direction","—")}')
                self.table.setItem(i,col,item)
            self.table.setRowHeight(i,29)
        self.table.setFixedHeight(29*min(count,9)+55)
        self.table.setVisible(count>0)
        self.more.setVisible(len(self.connections)>4)
        self.more.setText('Mostra meno' if self.expanded_rows else f'Mostra tutte e {len(self.connections)}')
        self.detail.setVisible(False)
        self.detail.setText('Seleziona una riga · Ctrl+C per copiare i dettagli')
        self.table.blockSignals(False)
        self.selected_key=None;self.close_button.setEnabled(False);self.terminate_button.setEnabled(False)
        for index,c in enumerate(self.connections[:count]):
            if self.row_key(c)==old_key:self.table.selectRow(index);break
    def _selected(self):
        self.selected_key=None;self.close_button.setEnabled(False);self.terminate_button.setEnabled(False)
        i=self.table.currentRow()
        if 0<=i<len(self.connections):
            c=self.connections[i]
            self.selected_key=self.row_key(c)
            try:
                process_target_from_row(c);self.terminate_button.setEnabled(True);self.terminate_button.setToolTip('Termina il processo e tutte le sue connessioni')
            except (ValueError,TypeError) as exc:self.terminate_button.setToolTip(str(exc))
            try:
                target_from_row(c)
                if sys.platform!='win32':raise ValueError('Disponibile solo su Windows.')
                self.close_button.setEnabled(True);self.close_button.setToolTip('Chiudi questa sessione TCP IPv4')
            except (ValueError,KeyError,TypeError) as exc:self.close_button.setToolTip(str(exc))
            self.detail.setText(f'Locale  {c.get("local","—")}   →   Remoto  {c.get("remote","—")}')
            self.detail.show()
            self.connection_selected.emit(self.name,c)
    def select_connection(self,c):
        self.set_open(True)
        for i,row in enumerate(self.connections):
            if row==c:
                if i>=4 and not self.expanded_rows:self.expanded_rows=True;self.render_rows()
                self.table.selectRow(i);self.table.scrollToItem(self.table.item(i,0));break


class PortsSection(Section):
    terminate_requested=Signal(dict)
    close_requested=Signal(str,dict)
    def __init__(self):
        super().__init__('Tutte le porte del PC',True)
        self.rows=[];self.filtered=[];self.signature=None;self.selected_key=None
        box=layout(self.body,margins=(16,8,16,16),spacing=12)
        filters=QWidget();bar=layout(filters,True)
        self.search=QLineEdit();self.search.setPlaceholderText('Cerca porta, processo, PID o indirizzo…');bar.addWidget(self.search,1)
        self.mode=QComboBox();self.mode.addItems(['In ascolto / UDP','Tutte le socket','Solo TCP','Solo UDP']);bar.addWidget(self.mode)
        self.family=QComboBox();self.family.addItems(['IPv4 + IPv6','IPv4','IPv6']);bar.addWidget(self.family)
        box.addWidget(filters)
        note=label('Porte locali osservate · la raggiungibilità da Internet non è verificata.','muted');note.setWordWrap(True);box.addWidget(note)
        self.count=label('In attesa del primo rilevamento','telemetry');box.addWidget(self.count)
        self.table=QTableWidget(0,7);self.table.setHorizontalHeaderLabels(['PORTA','TIPO','INDIRIZZO LOCALE','PROCESSO','PID','STATO','BIND'])
        self.table.verticalHeader().hide();self.table.setShowGrid(False);self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows);self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers);self.table.setFixedHeight(330)
        for col,width in enumerate([65,85,185,150,65,110,155]):self.table.setColumnWidth(col,width)
        self.table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        box.addWidget(self.table)
        self.detail=label('Seleziona una socket per i dettagli e le azioni.','detail',True);self.detail.setWordWrap(True);box.addWidget(self.detail)
        actions=QWidget();ab=layout(actions,True);ab.addStretch()
        self.close_button=QPushButton('Chiudi connessione');self.close_button.setObjectName('closeConnection')
        self.terminate_button=QPushButton('Termina processo');self.terminate_button.setObjectName('closeConnection')
        for button in (self.close_button,self.terminate_button):button.setEnabled(False);ab.addWidget(button)
        box.addWidget(actions)
        self.table.itemSelectionChanged.connect(self.selected)
        self.search.textChanged.connect(self.render);self.mode.currentTextChanged.connect(self.render);self.family.currentTextChanged.connect(self.render)
        self.close_button.clicked.connect(lambda:self.action(False));self.terminate_button.clicked.connect(lambda:self.action(True))
    def action(self,terminate):
        index=self.table.currentRow()
        if 0<=index<len(self.filtered):
            row=dict(self.filtered[index])
            if terminate:self.terminate_requested.emit(row)
            else:self.close_requested.emit(row['protocol'],row)
    def update_rows(self,rows):
        signature=repr(rows)
        if signature!=self.signature:self.rows=rows;self.signature=signature;self.render()
    def render(self,*args):
        key=self.selected_key;query=self.search.text().strip().casefold();mode=self.mode.currentText();family=self.family.currentText()
        self.filtered=[r for r in self.rows if
            (mode!='In ascolto / UDP' or r['listening'] or r['protocol']=='UDP') and
            (mode!='Solo TCP' or r['protocol']=='TCP') and (mode!='Solo UDP' or r['protocol']=='UDP') and
            (family=='IPv4 + IPv6' or r['family']==family) and
            (not query or query in ' '.join(str(r.get(k,'')) for k in ('port','protocol','family','process','pid','local','remote','status')).casefold())]
        scroll=self.table.verticalScrollBar().value()
        self.table.blockSignals(True);self.table.clearSelection();self.table.setCurrentCell(-1,-1);self.table.setRowCount(len(self.filtered))
        index_to_select=None
        for i,r in enumerate(self.filtered):
            values=[str(r['port']),r['protocol']+' '+r['family'],r['local'],r['process'],str(r['pid'] if r['pid'] is not None else '—'),'Associata' if r['protocol']=='UDP' else r['status'],r['scope']]
            for col,value in enumerate(values):
                cell=QTableWidgetItem(value);cell.setToolTip(value);self.table.setItem(i,col,cell)
            self.table.setRowHeight(i,31)
            if ServiceSection.row_key(r)==key:index_to_select=i
        self.table.blockSignals(False);self.selected_key=None
        self.close_button.setEnabled(False);self.terminate_button.setEnabled(False)
        self.detail.setText('Seleziona una socket per i dettagli e le azioni.')
        if index_to_select is not None:self.table.selectRow(index_to_select)
        self.table.verticalScrollBar().setValue(scroll)
        tcp=sum(r['listening'] for r in self.rows);udp=sum(r['protocol']=='UDP' for r in self.rows)
        self.count.setText(f'{len(self.filtered)} socket mostrate / {len(self.rows)} rilevate · {tcp} TCP in ascolto · {udp} UDP')
    def selected(self):
        self.selected_key=None;self.close_button.setEnabled(False);self.terminate_button.setEnabled(False)
        i=self.table.currentRow()
        if not 0<=i<len(self.filtered):return
        r=self.filtered[i];self.selected_key=ServiceSection.row_key(r)
        self.detail.setText(f'{r["local"]} → {r["remote"]} · {r["process"]} · PID {r["pid"]}')
        for button,validator,windows_only in ((self.close_button,target_from_row,True),(self.terminate_button,process_target_from_row,False)):
            try:
                validator(r)
                if windows_only and sys.platform!='win32':raise ValueError('Disponibile solo su Windows.')
                button.setEnabled(True);button.setToolTip('')
            except (ValueError,TypeError,KeyError) as exc:button.setToolTip(str(exc))


class WidgetHandle(QFrame):
    def __init__(self,window):
        super().__init__();self.window=window
        self.setCursor(Qt.SizeAllCursor)
    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton and self.window.windowHandle():
            self.window.windowHandle().startSystemMove()


class TitleBar(QFrame):
    def __init__(self,window):
        super().__init__(window)
        self.window=window;self.setObjectName('titleBar')
        row=layout(self,True,(12,7,8,7),12)
        row.addWidget(Jellyfish())
        title=label('MEDUSA','brandTitle');title.setTextInteractionFlags(Qt.NoTextInteraction)
        row.addWidget(title)
        self.status=label('●  AVVIO','status');row.addWidget(self.status)
        row.addStretch()
        self.down=label('↓ —','download',True);self.up=label('↑ —','upload',True)
        rates=QFrame();rates.setObjectName('headerRates');rb=layout(rates,True,(12,5,12,5),18)
        for caption,value in [('↓ DOWNLOAD',self.down),('↑ UPLOAD',self.up)]:
            group=QWidget();gb=layout(group,spacing=2);gb.addWidget(label(caption,'rateCaption'));gb.addWidget(value);rb.addWidget(group)
        row.addWidget(rates)
        self.pin=QPushButton('PIN');self.pin.setCheckable(True);self.pin.setObjectName('windowControl')
        self.pin.setToolTip('Mantieni sempre in primo piano')
        self.pin.toggled.connect(window.toggle_pin);row.addWidget(self.pin)
        for text,tip,action in [('−','Riduci a icona',window.showMinimized),('×','Chiudi',window.close)]:
            b=QPushButton(text);b.setObjectName('windowControl');b.setToolTip(tip);b.clicked.connect(action);row.addWidget(b)
    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton and self.window.windowHandle():
            self.window.windowHandle().startSystemMove()
    def mouseDoubleClickEvent(self,e):
        if e.button()==Qt.LeftButton:
            self.window.showNormal() if self.window.isMaximized() else self.window.showMaximized()


class MedusaWidget(QWidget):
    def __init__(self,start_worker=True,settings=None):
        super().__init__()
        self.setWindowTitle('MEDUSA');self.setWindowIcon(QIcon(ASSET))
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setObjectName('medusaWindow');self.setMinimumSize(740,520)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._exit_faded=False
        self.settings=settings or QSettings('MEDUSA','Desktop-0.3')
        self.started=time.monotonic();self.snapshot={};self.closing=False;self.worker=None
        self.selected_endpoint=None;self.last_update=None;self.disconnect_job=None
        root=layout(self,spacing=0)
        self.title=TitleBar(self);root.addWidget(self.title)
        self.error=label('','errorBanner');self.error.setWordWrap(True);self.error.hide();root.addWidget(self.error)
        workspace=QWidget();self.workspace=workspace;workspace.setObjectName('workspace');columns=layout(workspace,True,(12,6,12,0),18)
        root.addWidget(workspace,1)
        self.sidebar=QFrame();self.sidebar.setObjectName('sidebar');self.sidebar.setFixedWidth(198)
        side=layout(self.sidebar,margins=(16,14,16,14),spacing=10);columns.addWidget(self.sidebar)
        self.metrics={}
        side.addWidget(label('QUESTO DISPOSITIVO','eyebrow'))
        self.metrics['host']=label(socket.gethostname(),'hostName');self.metrics['host'].setWordWrap(True);side.addWidget(self.metrics['host'])
        side.addWidget(label(platform.system()+' '+platform.release(),'muted'))
        nav=QWidget();navbox=layout(nav,spacing=6)
        self.services_tab=QPushButton('Panoramica');self.ports_tab=QPushButton('Tutte le porte')
        for button in (self.services_tab,self.ports_tab):
            button.setCheckable(True);button.setAutoExclusive(True);button.setObjectName('navButton');button.setMinimumHeight(39);navbox.addWidget(button)
        self.services_tab.setChecked(True);side.addWidget(nav)
        self.services_tab.clicked.connect(lambda:self.show_port_view(False));self.ports_tab.clicked.connect(lambda:self.show_port_view(True))
        for key,caption,value in [('connections','Connessioni attive','—'),('recent','Nuove negli ultimi 60 s','—')]:
            group=QWidget();gb=layout(group,spacing=4)
            gb.addWidget(label(caption,'sideCaption'));v=label(value,'sideValue');gb.addWidget(v);self.metrics[key]=v;side.addWidget(group)
        self.families=label('IPv4  —   ·   IPv6  —','muted');side.addWidget(self.families)
        side.addStretch(1)
        self.local=label('IP LOCALE\n—','telemetry',True);self.local.setWordWrap(True);side.addWidget(self.local)
        self.public_address=None
        self.public_ip=label('IP PUBBLICO\nRilevamento…','telemetry',True);self.public_ip.setWordWrap(True)
        self.public_ip.setToolTip('IP di uscita osservato da ipify. Aggiornamento ogni 60 secondi; VPN e proxy possono cambiare il percorso.');side.addWidget(self.public_ip)
        self.public_refresh=QPushButton('Aggiorna IP');self.public_refresh.setObjectName('compactButton');side.addWidget(self.public_refresh)
        self.ip_lookup=PublicIPLookup(self);self.ip_lookup.result.connect(self.public_ip_ready);self.ip_lookup.failed.connect(self.public_ip_failed)
        self.public_refresh.clicked.connect(self.refresh_public_ip)
        self.metrics['uptime']=label('00:00:00','telemetry',True)
        side.addWidget(label('SESSIONE','eyebrow'));side.addWidget(self.metrics['uptime'])
        self.compact_button=QPushButton('Diventa widget');self.compact_button.setCheckable(True);self.compact_button.setObjectName('compactButton')
        self.compact_button.toggled.connect(self.set_compact);side.addWidget(self.compact_button)
        side.addWidget(label('MEDUSA  0.4.2','versionLabel'))
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setFrameShape(QFrame.NoFrame);columns.addWidget(self.scroll,1)
        self.content=QWidget();self.content.setObjectName('content')
        body=layout(self.content,margins=(0,10,4,16),spacing=16);body.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.content);self.scroll.viewport().setAutoFillBackground(False);self.content.setAutoFillBackground(False)
        heading=QWidget();hb=layout(heading,spacing=5)
        self.page_title=label('Attività di rete','pageTitle');hb.addWidget(self.page_title)
        self.page_caption=label('Connessioni e processi del tuo PC, in tempo reale.','pageCaption');hb.addWidget(self.page_caption);body.addWidget(heading)
        self.radar_section=Section('Radar delle connessioni',self.saved('radar',True));self.radar_section.setObjectName('radarSection');body.addWidget(self.radar_section)
        rb=layout(self.radar_section.body,margins=(0,0,0,8),spacing=4)
        controls=QWidget();cr=layout(controls,True,(14,0,14,0),8)
        cr.addWidget(label('HTTPS · DNS · SMB · RDP · SSH','muted'),1)
        self.filter=QComboBox();self.filter.addItems(['Tutti','IPv4','IPv6']);self.filter.setAccessibleName('Filtro famiglia IP del radar');cr.addWidget(self.filter);rb.addWidget(controls)
        self.radar=Radar();rb.addWidget(self.radar)
        self.radar.mascot_clicked.connect(self.show_mascot_menu)
        self.endpoint=label('Seleziona un punto per vedere processo e indirizzi.','detail');self.endpoint.setWordWrap(True);rb.addWidget(self.endpoint)
        self.radar.endpoint_selected.connect(self.select_endpoint);self.filter.currentTextChanged.connect(self.refresh_radar)
        self.inventory=PortsSection();self.inventory.terminate_requested.connect(self.confirm_terminate)
        self.inventory.close_requested.connect(self.confirm_disconnect);body.addWidget(self.inventory);self.inventory.hide()
        self.services_group=QFrame();self.services_group.setObjectName('servicesGroup');sg=layout(self.services_group,margins=(14,6,14,6),spacing=0)
        body.addWidget(self.services_group)
        self.port_rows={}
        for name,port in MONITORED_PORTS.items():
            section=ServiceSection(name,port,self.saved(name,False));section.setProperty('kind','service')
            section.connection_selected.connect(self.table_selection);section.close_requested.connect(self.confirm_disconnect);section.terminate_requested.connect(self.confirm_terminate)
            sg.addWidget(section);self.port_rows[name]=section
        self.traffic=Section('Traffico del PC',self.saved('traffic',True));body.addWidget(self.traffic)
        traffic_row=layout(self.traffic.body,True,(14,4,14,12),12)
        self.chart=TrafficChart();self.chart.setFixedHeight(82);traffic_row.addWidget(self.chart,1)
        rates=QWidget();rates.setFixedWidth(135);ratebox=layout(rates,spacing=6)
        self.down=label('↓  —','download',True);self.up=label('↑  —','upload',True)
        ratebox.addWidget(self.down);ratebox.addWidget(self.up);ratebox.addWidget(label('Ultimi 60 secondi','muted'));traffic_row.addWidget(rates)
        self.footer=QFrame();foot=layout(self.footer,True,(20,6,8,6),8)
        self.footer_text=label('MEDUSA  0.4.2   ·   In attesa del monitoraggio','muted');foot.addWidget(self.footer_text,1);foot.addWidget(QSizeGrip(self));root.addWidget(self.footer)
        self.sections={'radar':self.radar_section,'traffic':self.traffic,'inventory':self.inventory,**self.port_rows}
        for key,section in self.sections.items():section.toggled.connect(lambda opened,k=key:self.section_changed(k,opened))
        self.window_motion=QPropertyAnimation(self,b'size',self);self.window_motion.setDuration(260);self.window_motion.setEasingCurve(QEasingCurve.InOutCubic)
        self._expanded_state=None;self._expanded_size=None;self._dashboard_geometry=None
        self.widget_panel=QWidget();self.widget_panel.setObjectName('miniPanel');mini=layout(self.widget_panel,margins=(18,14,18,16),spacing=10)
        handle=WidgetHandle(self);mh=layout(handle,True,spacing=8)
        brand=label('MEDUSA','miniBrand');brand.setAttribute(Qt.WA_TransparentForMouseEvents);mh.addWidget(brand,1)
        restore=QPushButton('Apri ↗');restore.setToolTip('Torna alla finestra completa');restore.clicked.connect(lambda:self.compact_button.setChecked(False));mh.addWidget(restore)
        mini.addWidget(handle)
        self.mini_status=label('SERVIZI ATTIVI','rateCaption');mini.addWidget(self.mini_status)
        self.mini_rows={}
        for name,port in MONITORED_PORTS.items():
            row=QFrame();row.setObjectName('miniRow');rr=layout(row,True,(0,8,0,8),10)
            rr.addWidget(label('●','miniDot'));rr.addWidget(label(name,'miniService'),1);rr.addWidget(label(str(port),'portBadge',True))
            count=label('','muted');rr.addWidget(count);mini.addWidget(row);self.mini_rows[name]=(row,count)
        self.mini_empty=label('Nessun servizio attivo','muted');mini.addWidget(self.mini_empty)
        mini.addStretch();root.addWidget(self.widget_panel);self.widget_panel.hide()
        self.setStyleSheet((Path(__file__).resolve().parents[1]/'styles'/'medusa.qss').read_text(encoding='utf-8'))
        available=QApplication.primaryScreen().availableGeometry()
        self.resize(min(1060,available.width()-40),min(850,available.height()-40))
        geometry=self.settings.value('geometry')
        if isinstance(geometry,QByteArray):self.restoreGeometry(geometry)
        # Recover if a previous monitor was disconnected.
        if not any(screen.availableGeometry().intersects(self.frameGeometry()) for screen in QApplication.screens()):
            self.move(available.topLeft())
        self.clock=QTimer(self);self.clock.timeout.connect(self.tick);self.clock.start(1000)
        self.title.pin.setChecked(self.saved('pinned',False))
        if start_worker:
            self.ip_lookup.start()
            self.worker=NetworkWorker(interval=1.0,parent=self)
            self.worker.snapshot_ready.connect(self.apply_network_snapshot)
            self.worker.scan_error.connect(self.handle_network_error)
            self.worker.finished.connect(self.worker_finished)
            self.worker.start()
    def update_mascot_hint(self):
        local=', '.join(self.snapshot.get('local_ips',[])) or 'Non disponibile'
        self.radar.mascot_hint=f"IP pubblico: {self.public_address or 'Non disponibile'}\nIP locale: {local}\nClic oppure Invio per azioni rapide"
    def show_mascot_menu(self):
        self.mascot_menu=QMenu(self)
        copy=self.mascot_menu.addAction('Copia IP pubblico');copy.setEnabled(bool(self.public_address))
        copy.triggered.connect(lambda:QApplication.clipboard().setText(self.public_address or ''))
        self.mascot_menu.addAction('Aggiorna IP pubblico',self.refresh_public_ip)
        self.mascot_menu.addSeparator()
        self.mascot_menu.addAction('Diventa widget',lambda:self.compact_button.setChecked(True))
        cx,cy,_=self.radar.radar_geometry()
        self.mascot_menu.aboutToHide.connect(self.mascot_menu.deleteLater)
        self.mascot_menu.popup(self.radar.mapToGlobal(QPoint(int(cx)+30,int(cy))))
    def refresh_public_ip(self):
        self.public_ip.setText('IP PUBBLICO\nRilevamento…');self.ip_lookup.refresh()
    def public_ip_ready(self,address):
        self.public_address=address;self.update_mascot_hint()
        self.public_ip.setText('IP PUBBLICO\n'+address)
        self.public_ip.setToolTip('Rilevato alle '+time.strftime('%H:%M:%S')+' via ipify. IP di uscita di questa richiesta, non necessariamente di tutte le applicazioni.')
    def public_ip_failed(self):
        self.public_address=None;self.update_mascot_hint()
        self.public_ip.setText('IP PUBBLICO\nNon disponibile')
        self.public_ip.setToolTip('Richiesta a ipify non riuscita. Nuovo tentativo ogni 60 secondi o con Aggiorna IP.')
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.Antialiasing)
        gradient=QLinearGradient(0,0,0,self.height())
        for at,color in [(0,'#155c60'),(.16,'#174c53'),(.36,'#203b44'),(.56,'#252d38'),(.76,'#202530'),(1,'#171c25')]:gradient.setColorAt(at,QColor(color))
        path=QPainterPath();path.addRoundedRect(QRectF(self.rect()).adjusted(.5,.5,-.5,-.5),10,10)
        painter.fillPath(path,gradient);painter.setPen(QPen(QColor(218,230,227,36),1));painter.drawPath(path)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'inventory'):
            self.inventory.table.setFixedHeight(max(120,min(460,self.height()-340)))
    def show_port_view(self,all_ports):
        self.inventory.setVisible(all_ports)
        self.radar_section.setVisible(not all_ports)
        self.services_group.setVisible(not all_ports)
        self.traffic.setVisible(not all_ports)
        self.page_title.setText('Tutte le porte' if all_ports else 'Attività di rete')
        self.page_caption.setText('Porte locali, programmi e indirizzi associati.' if all_ports else 'Connessioni e processi del tuo PC, in tempo reale.')
    def set_compact(self,compact):
        if not hasattr(self,'widget_panel'):return
        self.window_motion.stop()
        if compact:
            self._dashboard_geometry=self.saveGeometry()
            self.workspace.hide();self.title.hide();self.footer.hide();self.error.hide()
            self.widget_panel.show();self.setMinimumSize(300,150)
            self.update_mini()
            available=self.screen().availableGeometry()
            self.resize(320,self.mini_height())
            self.move(available.right()-self.width()-19,available.bottom()-self.height()-19)
        else:
            self.widget_panel.hide();self.workspace.show();self.title.show();self.footer.show()
            self.setMinimumSize(740,520)
            if self._dashboard_geometry:self.restoreGeometry(self._dashboard_geometry)
            if self.title.status.property('error'):self.error.show()
    def mini_height(self):
        count=sum(not row.isHidden() for row,_ in self.mini_rows.values())
        return 112+max(1,count)*47
    def update_mini(self):
        count=0
        for name,(row,value) in self.mini_rows.items():
            info=self.snapshot.get('ports',{}).get(name,{})
            connections=[c for c in info.get('connections',[]) if c.get('status') in ('ESTABLISHED','UDP')]
            active=bool(info.get('active') or info.get('status')=='ACTIVE')
            row.setVisible(active);value.setText(str(len(connections) or len(info.get('connections',[]))))
            count+=active
        self.mini_empty.setVisible(count==0)
        stale=not self.last_update or time.monotonic()-self.last_update>5
        self.mini_status.setText('DATI NON AGGIORNATI' if stale else 'SERVIZI ATTIVI · LIVE')
        if self.compact_button.isChecked():
            self.resize(320,self.mini_height())
            area=self.screen().availableGeometry()
            self.move(max(area.left(),min(self.x(),area.right()-self.width()+1)),max(area.top(),min(self.y(),area.bottom()-self.height()+1)))
    def saved(self,key,default):return self.settings.value(key,default,type=bool)
    def section_changed(self,key,opened):
        self.settings.setValue(key,opened)
        # Keep window geometry stable while panels animate; manual resize remains available.
    def compact_height(self):
        wanted=self.content.sizeHint().height()+self.title.height()+self.footer.height()+28
        self.resize(self.width(),max(self.minimumHeight(),min(self.height(),wanted)))
    def toggle_pin(self,checked):
        self.setWindowFlag(Qt.WindowStaysOnTopHint,checked)
        self.settings.setValue('pinned',checked)
        if self.isVisible():self.show()
        # setWindowFlag hides an already visible window; always restore after startup.
        elif hasattr(self,'sections'):self.show()
    def tick(self):
        elapsed=int(time.monotonic()-self.started)
        self.metrics['uptime'].setText(f'{elapsed//3600:02}:{elapsed//60%60:02}:{elapsed%60:02}')
        if self.last_update and time.monotonic()-self.last_update>5 and not self.closing:
            self.title.status.setText('●  IN ATTESA')
            self.mini_status.setText('DATI NON AGGIORNATI')
            self.footer_text.setText('Dati non aggiornati · attendo il monitoraggio')
    def apply_network_snapshot(self,data):
        if self.closing:return
        self.snapshot=data;self.last_update=time.monotonic();self.error.hide()
        self.inventory.update_rows(data.get("socket_inventory",[]))
        self.title.status.setText('●  ACTIVE');self.title.status.setProperty('error',False)
        self.title.status.setStyleSheet('color: #75f5ce')
        for name,s in self.port_rows.items():s.update_info(data.get('ports',{}).get(name,{}))
        self.metrics['connections'].setText(str(data.get('connections',0)))
        self.metrics['recent'].setText(str(data.get('recent_connection_count',0)))
        self.metrics['recent'].setToolTip('Nuove connessioni osservate sui cinque servizi; il primo campione include quelle già presenti. Le socket in ascolto sono escluse.')
        self.metrics['connections'].setToolTip('Tutte le connessioni TCP ESTABLISHED del PC, anche su porte non monitorate.')
        self.families.setText(f'IPv4  {data.get("ipv4",0)}   ·   IPv6  {data.get("ipv6",0)}')
        ips=data.get('local_ips',[])
        self.local.setText('IP LOCALE\n'+(ips[0] if ips else '—'));self.local.setToolTip('\n'.join(ips));self.update_mascot_hint()
        down,up=data.get('download_bps',0),data.get('upload_bps',0)
        self.down.setText('↓  '+speed(down));self.up.setText('↑  '+speed(up))
        self.title.down.setText(speed(down));self.title.up.setText(speed(up))
        self.update_mini()
        self.chart.add_sample(down,up)
        self.refresh_radar()
        self.footer_text.setText('MEDUSA  0.4.2   ·   Monitoraggio locale · nessun dato inviato')
    def refresh_radar(self,*args):
        self.radar.set_connections(self.snapshot.get('ports',{}),self.filter.currentText())
        if self.selected_endpoint:
            service,c=self.selected_endpoint
            matches=[row for row in self.snapshot.get('ports',{}).get(service,{}).get('connections',[]) if row==c]
            if not matches:
                self.endpoint.setText('La connessione selezionata non è più presente.')
                self.selected_endpoint=None
    def select_endpoint(self,service,c):
        self.services_tab.setChecked(True);self.show_port_view(False)
        self.port_rows[service].select_connection(c)
        self.table_selection(service,c)
    def table_selection(self,service,c):
        self.selected_endpoint=(service,c)
        self.endpoint.setText(f'{service} · {c.get("process","—")} · PID {c.get("pid","—")}\nLocale {c.get("local","—")}  →  Remoto {c.get("remote","—")}')
        self.radar.selected=(service,c.get('remote'));self.radar.update()
    def handle_network_error(self,error):
        if self.closing:return
        self.title.status.setProperty('error',True);self.mini_status.setText('ERRORE · DATI NON AGGIORNATI')
        self.title.status.setText('●  ERRORE');self.title.status.setStyleSheet('color: #f16b78')
        for section in self.port_rows.values():
            section.set_indicator('error','Errore di lettura: dati non aggiornati')
            section.summary_label.setText('Dati non aggiornati')
        self.error.setText('Impossibile aggiornare le connessioni. I dati visualizzati potrebbero essere precedenti.\n'+error+'\nSu Windows, se l’accesso è negato, avvia MEDUSA come amministratore.')
        self.error.setVisible(not self.compact_button.isChecked());self.footer_text.setText('Errore di lettura · nuovo tentativo automatico')
    def confirm_terminate(self,row):
        if self.disconnect_job is not None:return
        try:target=process_target_from_row(row)
        except (ValueError,TypeError) as exc:
            QMessageBox.information(self,'Azione non disponibile',str(exc));return
        box=QMessageBox(self);box.setWindowTitle('Termina processo');box.setIcon(QMessageBox.Warning)
        box.setText(f'{target.name} · PID {target.pid}')
        box.setInformativeText('Il programma verrà terminato insieme a tutte le sue connessioni. I dati non salvati possono andare persi. Continuare?')
        action=box.addButton('Termina processo',QMessageBox.DestructiveRole)
        cancel=box.addButton('Annulla',QMessageBox.RejectRole);box.setDefaultButton(cancel);box.exec()
        if box.clickedButton()!=action or self.closing:return
        job=DisconnectJob(target,self,operation=terminate_process);self.disconnect_job=job
        job.completed.connect(self.disconnect_result);job.finished.connect(self.disconnect_finished)
        self.footer_text.setText('Terminazione del processo selezionato…');job.start()

    def confirm_disconnect(self,service,row):
        if self.disconnect_job is not None:return
        try:target=target_from_row(row)
        except (ValueError,KeyError,TypeError) as exc:
            QMessageBox.information(self,'Chiusura non disponibile',str(exc));return
        box=QMessageBox(self);box.setWindowTitle('Chiudi connessione')
        box.setIcon(QMessageBox.Warning)
        box.setText(f'{service} · {row.get("process","—")} · PID {target.pid}')
        box.setInformativeText(f'{row["local"]} → {row["remote"]}\n\nInterrompi questa sessione? Download o operazioni in corso potrebbero fallire. Il programma rimarrà aperto e potrà riconnettersi.')
        close=box.addButton('Chiudi connessione',QMessageBox.DestructiveRole)
        cancel=box.addButton('Annulla',QMessageBox.RejectRole);box.setDefaultButton(cancel)
        box.exec()
        if box.clickedButton()!=close or self.closing:return
        job=DisconnectJob(target,self);self.disconnect_job=job
        job.completed.connect(self.disconnect_result)
        job.finished.connect(self.disconnect_finished)
        self.footer_text.setText('Chiusura della connessione selezionata…');job.start()
    def disconnect_result(self,success,message):
        if self.closing:return
        if success:QMessageBox.information(self,'Operazione completata',message)
        else:QMessageBox.warning(self,'Operazione non eseguita',message)
    def disconnect_finished(self):
        job=self.disconnect_job;self.disconnect_job=None
        if job:job.deleteLater()
        if self.closing:self.close()

    def changeEvent(self,event):
        super().changeEvent(event)
        if event.type()==QEvent.WindowStateChange and hasattr(self,'radar'):
            self.radar.last_tick=None
            if self.isMinimized():
                self.radar.timer.stop();self.chart.timer.stop()
            else:
                if self.radar.isVisible() and not self.radar.paused:self.radar.timer.start()
                if self.chart.isVisible() and not self.chart.paused:self.chart.timer.start()
    def closeEvent(self,event):
        self.ip_lookup.stop()
        self.settings.setValue('geometry',self._dashboard_geometry if self.compact_button.isChecked() and self._dashboard_geometry else self.saveGeometry())
        if (self.worker and self.worker.isRunning()) or (self.disconnect_job and self.disconnect_job.isRunning()):
            self.closing=True
            if self.worker:self.worker.stop()
            self.title.status.setText('ARRESTO…')
            self.clock.stop();self.radar.timer.stop()
            event.ignore()
        elif sys.platform=='win32' and not self._exit_faded:
            self.closing=True;self.clock.stop();self.radar.timer.stop();self.chart.timer.stop()
            if not hasattr(self,'exit_motion'):
                self.exit_motion=QPropertyAnimation(self,b'windowOpacity',self)
                self.exit_motion.setDuration(140);self.exit_motion.setStartValue(1.0);self.exit_motion.setEndValue(0.0)
                self.exit_motion.finished.connect(self.finish_close);self.exit_motion.start()
            event.ignore()
        else:event.accept()
    def finish_close(self):
        self._exit_faded=True;self.close()
    def worker_finished(self):
        if self.closing:self.close()
