"""Native Qt data visualizations. Geometry is logical, never geographic."""
import hashlib
import math
import time
from collections import deque
from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient, QConicalGradient
from PySide6.QtWidgets import QWidget, QToolTip

CYAN = QColor('#65e7c5')
PURPLE = QColor('#a178ec')
MUTED = QColor('#b5cac5')
LINE = QColor('#4b5d60')
ASSET = str(Path(__file__).resolve().parents[1] / 'assets' / 'jellyfish.png')


def speed(value):
    value = max(0.0, float(value))
    for unit in ('B/s', 'KB/s', 'MB/s', 'GB/s'):
        if value < 1024 or unit == 'GB/s':
            return f'{value:.0f} {unit}' if unit == 'B/s' else f'{value:.1f} {unit}'
        value /= 1024


class StatusLamp(QWidget):
    COLORS={'active':'#00dca5','listening':'#f1cf38','idle':'#52738f','error':'#f16b78'}
    def __init__(self,parent=None):
        super().__init__(parent)
        self.state='idle';self.setFixedSize(24,24)
    def set_state(self,state):
        self.state=state;self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        color=QColor(self.COLORS[self.state]);p.setPen(Qt.NoPen)
        if self.state!='idle':
            for radius,alpha in ((12,12),(10,22),(8.5,38)):
                halo=QColor(color);halo.setAlpha(alpha);p.setBrush(halo)
                p.drawEllipse(QPointF(12,12),radius,radius)
        p.setBrush(color);p.setPen(QPen(color.lighter(120),.8))
        p.drawEllipse(QPointF(12,12),6.5,6.5)


class Jellyfish(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = QPixmap(ASSET).copy(350,245,550,765)
        self.setFixedSize(34, 40)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setCompositionMode(QPainter.CompositionMode_Screen)
        p.drawPixmap(QRectF(5, 3, 24, 33), self.pixmap, QRectF(self.pixmap.rect()))


class Radar(QWidget):
    endpoint_selected = Signal(str, dict)
    mascot_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 370)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName('Radar delle connessioni; Tab per selezionare, frecce per cambiare endpoint')
        self.pixmap = QPixmap(ASSET).copy(350,245,550,765)
        self.nodes = []
        self.hits = []
        self.selected = None
        self.first_seen = {}
        self.paused = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.timer.setInterval(16)
        self.last_tick = None
        self.hovered = None
        self.mascot_hovered=False
        self.mascot_hint="MEDUSA · clic per azioni rapide"
        self.phase = 0.0
        self.clock = time.monotonic()

    def advance(self):
        now=time.monotonic()
        if self.last_tick is not None:
            self.phase+=min(now-self.last_tick,.08)
        self.last_tick=now
        self.update()

    def showEvent(self, event):
        self.last_tick=None
        if not self.paused:
            self.timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self.timer.stop()
        self.last_tick=None
        super().hideEvent(event)

    def set_paused(self, paused):
        self.last_tick=None
        self.paused = paused
        if paused:
            self.timer.stop()
        elif self.isVisible():
            self.timer.start()
        self.update()

    def set_connections(self, ports, family='Tutti'):
        now = self.phase
        nodes = {}
        for service, info in ports.items():
            for c in info.get('connections', []):
                endpoint = c.get('remote')
                if not endpoint or endpoint == '—':
                    continue
                ipv6 = endpoint.startswith('[')
                if family == 'IPv4' and ipv6 or family == 'IPv6' and not ipv6:
                    continue
                key = (service, endpoint)
                nodes.setdefault(key, (service, c))
        self.nodes = sorted(nodes.items())
        self.first_seen = {key: self.first_seen.get(key, now) for key in nodes}
        if self.selected not in nodes:
            self.selected = None
        self.update()

    def radar_geometry(self):
        return self.width()/2, self.height()/2, min(self.width()*.41,self.height()/2-20)

    def geometry_for(self, key):
        digest = hashlib.sha256(repr(key).encode()).digest()
        angle = int.from_bytes(digest[:2], 'big') / 65535 * 2 * math.pi
        fraction = .28 + digest[2] / 255 * .63
        cx,cy,radius=self.radar_geometry()
        return QPointF(cx+math.cos(angle)*radius*fraction,cy+math.sin(angle)*radius*fraction)

    def paintEvent(self, event):
        p=QPainter(self)
        p.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform)
        t=self.phase
        cx,cy,r=self.radar_geometry();center=QPointF(cx,cy)
        # Circular field, with no rectangular grid competing with endpoints.
        field=QRadialGradient(center,r)
        field.setColorAt(0,QColor(12,70,62,60));field.setColorAt(.65,QColor(25,45,46,35));field.setColorAt(1,QColor(29,30,39,0))
        p.setPen(Qt.NoPen);p.setBrush(field);p.drawEllipse(center,r,r)
        # Fading sweep is a display animation, never an active network scan.
        angle=(t*22-62)%360
        if self.nodes:
            sweep=QConicalGradient(center,-angle)
            sweep.setColorAt(0,QColor(62,235,186,42))
            sweep.setColorAt(.12,QColor(62,235,186,0))
            sweep.setColorAt(.999,QColor(62,235,186,0))
            sweep.setColorAt(1,QColor(62,235,186,42))
            p.setBrush(sweep);p.drawEllipse(center,r,r)
        p.setBrush(Qt.NoBrush)
        for i in range(1,8):
            p.setPen(QPen(QColor('#468678') if i<7 else QColor('#76cbb7'),.65 if i<7 else .95))
            p.drawEllipse(center,r*i/7,r*i/7)
        p.setPen(QPen(QColor('#519a8b'),.7));p.drawEllipse(center,r+6,r+6)
        for degree in range(0,360,2):
            a=math.radians(degree);major=degree%30==0
            length=9 if major else (5 if degree%10==0 else 3)
            p.setPen(QPen(QColor('#8de4cd') if major else QColor('#599b8d'),.7))
            p.drawLine(QPointF(cx+math.cos(a)*(r-length),cy+math.sin(a)*(r-length)),QPointF(cx+math.cos(a)*r,cy+math.sin(a)*r))
        for degree in range(0,360,30):
            a=math.radians(degree)
            p.setPen(QPen(QColor('#559789') if degree%90==0 else QColor('#3b6c63'),.7))
            p.drawLine(center,QPointF(cx+math.cos(a)*r,cy+math.sin(a)*r))
        p.setFont(QFont('Consolas',9));p.setPen(CYAN)
        for text,x,y in [('N',cx-8,cy-r-23),('S',cx-8,cy+r+8),('W',cx-r-24,cy-9),('E',cx+r+9,cy-9)]:
            p.drawText(QRectF(x,y,17,18),Qt.AlignCenter,text)
        self.hits=[]
        for key,(service,c) in self.nodes[:100]:
            pos=self.geometry_for(key);self.hits.append((pos,key,service,c))
            selected=key==self.selected or key==self.hovered
            col=PURPLE if service=='DNS' else CYAN
            age=max(0,t-self.first_seen.get(key,t));fade=min(1,age/.45)
            theta=math.degrees(math.atan2(pos.y()-cy,pos.x()-cx))%360
            illumination=max(0,1-((angle-theta)%360)/65)
            p.setOpacity(fade)
            line=QColor(col);line.setAlpha(130 if selected else 48)
            p.setPen(QPen(line,1,Qt.DashLine));p.drawLine(center,pos)
            size=16 if selected else 12+illumination*5
            glow=QRadialGradient(pos,size);glow.setColorAt(0,QColor(col.red(),col.green(),col.blue(),220));glow.setColorAt(.35,QColor(col.red(),col.green(),col.blue(),55));glow.setColorAt(1,QColor(col.red(),col.green(),col.blue(),0))
            p.setPen(Qt.NoPen);p.setBrush(glow);p.drawEllipse(pos,size,size)
            p.setBrush(QColor('#d8fbff') if service!='DNS' else col);dot=4.2 if selected else 3.3+illumination
            p.drawEllipse(pos,dot,dot)
            if age<1.5:
                ring=QColor(col);ring.setAlpha(int(110*(1-age/1.5)))
                p.setPen(QPen(ring,.8));p.setBrush(Qt.NoBrush);p.drawEllipse(pos,5+age*9,5+age*9)
            if selected:
                p.setPen(QPen(col,1));p.setBrush(Qt.NoBrush);p.drawEllipse(pos,7,7)
            p.setOpacity(1)
        # Choose spatially nearby nodes for five short elbow callouts.
        p.setFont(QFont('Consolas',9))
        unused=list(self.hits)
        for left,top in ((True,True),(False,True),(False,None),(True,False),(False,False)):
            if not unused:break
            tx=cx+(-.65 if left else .65)*r;ty=cy+(0 if top is None else (-.65 if top else .65))*r
            hit=min(unused,key=lambda h:(h[0].x()-tx)**2+(h[0].y()-ty)**2);unused.remove(hit)
            pos,key,service,c=hit
            width=min(132,self.width()/2-14)
            x=max(2,cx-r-60) if left else min(self.width()-width-2,cx+r+60-width)
            y=cy-22 if top is None else (cy-r+10 if top else cy+r-44)
            if self.width()<480 and top is not None:y=cy-r-44 if top else cy+r+18
            if top is None:
                if self.width()<620:continue
                width=105;x=min(self.width()-width-2,cx+r+10);y=cy-38
            host,_,port=c['remote'].rpartition(':')
            host=p.fontMetrics().elidedText(host,Qt.ElideMiddle,int(width))
            rect=QRectF(x,y,width,34)
            anchor=QPointF(x+width*.55 if left else x+width*.45,y+35 if top else y-3)
            elbow=QPointF(anchor.x()+(-12 if left else 12),anchor.y())
            p.setBrush(Qt.NoBrush);p.setPen(QPen(QColor('#89d9c5'),.8));path=QPainterPath(pos);path.lineTo(elbow);path.lineTo(anchor);p.drawPath(path)
            p.setPen(QColor('#d0e8df'))
            p.drawText(rect,Qt.AlignLeft if left else Qt.AlignRight,host+'\n:'+port)
        p.setPen(QPen(QColor('#b8ffdf') if self.mascot_hovered else QColor('#7bd5bb'),1.8 if self.mascot_hovered else .9));p.setBrush(QColor('#284e49'));p.drawEllipse(center,31,31)
        bob=math.sin(t*1.7)*1.2;stretch=1+math.sin(t*1.7)*.02
        p.setCompositionMode(QPainter.CompositionMode_Screen)
        p.drawPixmap(QRectF(cx-16.5,cy-23+bob,33,46*stretch),self.pixmap,QRectF(self.pixmap.rect()))
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        if not self.nodes:
            p.setFont(QFont('Segoe UI',9));p.setPen(MUTED)
            p.drawText(QRectF(0,cy+55,self.width(),20),Qt.AlignCenter,'Nessun endpoint remoto osservato')
        if self.hasFocus():
            p.setPen(QPen(CYAN,1,Qt.DotLine));p.setBrush(Qt.NoBrush);p.drawRect(self.rect().adjusted(2,2,-3,-3))

    def leaveEvent(self,event):
        self.hovered=None;self.mascot_hovered=False;self.update();QToolTip.hideText()
        super().leaveEvent(event)

    def over_mascot(self,point):
        cx,cy,_=self.radar_geometry()
        return (point.x()-cx)**2+(point.y()-cy)**2<=31**2

    def mouseMoveEvent(self, event):
        self.mascot_hovered=self.over_mascot(event.position())
        if self.mascot_hovered:
            self.hovered=None;self.setCursor(Qt.PointingHandCursor);self.update()
            QToolTip.showText(event.globalPosition().toPoint(),self.mascot_hint,self)
            return
        found = next((h for h in self.hits if (h[0]-event.position()).manhattanLength()<13),None)
        self.hovered=found[1] if found else None
        self.update()
        self.setCursor(Qt.PointingHandCursor if found else Qt.ArrowCursor)
        if found:
            _,_,service,c=found
            QToolTip.showText(event.globalPosition().toPoint(),f'{service} · {c["process"]}\n{c["remote"]}',self)
        else:
            QToolTip.hideText()

    def mousePressEvent(self,event):
        if event.button()!=Qt.LeftButton:return
        if self.over_mascot(event.position()):
            self.mascot_clicked.emit();return
        found=next((h for h in self.hits if (h[0]-event.position()).manhattanLength()<13),None)
        if found:
            _,self.selected,service,c=found
            self.endpoint_selected.emit(service,c);self.update()

    def keyPressEvent(self,event):
        if event.key() in (Qt.Key_Return,Qt.Key_Enter,Qt.Key_Space):
            self.mascot_clicked.emit();return
        if event.key() in (Qt.Key_Right,Qt.Key_Left) and self.nodes:
            keys=[k for k,_ in self.nodes[:100]]
            i=keys.index(self.selected) if self.selected in keys else -1
            self.selected=keys[(i+(1 if event.key()==Qt.Key_Right else -1))%len(keys)]
            service,c=dict(self.nodes)[self.selected]
            self.endpoint_selected.emit(service,c);self.update()
        else:super().keyPressEvent(event)


class TrafficChart(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.samples=deque(maxlen=90)
        self.paused=False
        self.timer=QTimer(self);self.timer.setInterval(33);self.timer.timeout.connect(self.update)
        self.setMinimumHeight(88)
        self.setAccessibleName('Traffico totale del PC negli ultimi 60 secondi')

    def showEvent(self,event):
        if not self.paused:self.timer.start()
        super().showEvent(event)
    def hideEvent(self,event):
        self.timer.stop();super().hideEvent(event)
    def set_paused(self,paused):
        self.paused=paused
        if paused:self.timer.stop()
        elif self.isVisible():self.timer.start()
    def add_sample(self,down,up):
        now=time.monotonic()
        self.samples.append((now,max(0,down),max(0,up)))
        while self.samples and self.samples[0][0]<now-60:self.samples.popleft()
        self.update()

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height();top,bottom=19,h-18
        p.setPen(QPen(LINE,1))
        for i in range(4):
            y=top+(bottom-top)*i/3;p.drawLine(QPointF(8,y),QPointF(w-8,y))
        peak=max([v for _,d,u in self.samples for v in (d,u)]+[1024])
        now=time.monotonic()
        for j,col in ((1,CYAN),(2,PURPLE)):
            path=QPainterPath()
            for i,s in enumerate(self.samples):
                x=8+max(0,1-(now-s[0])/60)*(w-16)
                y=bottom-s[j]/peak*(bottom-top)
                if i:path.lineTo(x,y)
                else:path.moveTo(x,y)
            p.setPen(QPen(col,1.5));p.drawPath(path)
        p.setFont(QFont('Consolas',8));p.setPen(MUTED)
        p.drawText(8,12,f'Scala {speed(peak)}')
        p.drawText(8,h-3,'−60 s');p.drawText(w-44,h-3,'ora')
