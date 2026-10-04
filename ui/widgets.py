from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QRadialGradient
from PySide6.QtWidgets import (QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QSlider, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QSizePolicy, QPlainTextEdit)
import math, random

try:
    import pyqtgraph as pg
except ImportError:
    pg = None

ACCENT = "#42d6c5"
MUTED = "#81909f"


class Section(QGroupBox):
    def __init__(self, title, subtitle=""):
        super().__init__(title)
        self.setProperty("class", "section")
        if subtitle:
            self.setToolTip(subtitle)
        self.body = QGridLayout()
        self.body.setContentsMargins(12, 12, 12, 12)
        self.body.setHorizontalSpacing(12)
        self.body.setVerticalSpacing(8)
        self.setLayout(self.body)

    def add_field(self, label, widget, row, col=0, span=1):
        text = QLabel(label)
        text.setProperty("class", "field-label")
        self.body.addWidget(text, row, col * 2, 1, 1)
        self.body.addWidget(widget, row, col * 2 + 1, 1, span * 2 - 1)
        return widget


def combo(items, current=None, tip=""):
    w = QComboBox(); w.addItems(items)
    if current: w.setCurrentText(current)
    if tip: w.setToolTip(tip)
    return w


def number(value=0, decimals=2, suffix="", minimum=-999999, maximum=999999):
    w = QDoubleSpinBox(); w.setRange(minimum, maximum); w.setDecimals(decimals); w.setValue(value); w.setSuffix(suffix)
    return w


def text(value=""):
    w = QLineEdit(value); return w


def check(label, checked=False):
    w = QCheckBox(label); w.setChecked(checked); return w


class Metric(QFrame):
    def __init__(self, title, value, unit="", tone="normal"):
        super().__init__()
        self.setProperty("class", "metric")
        self.setMinimumHeight(54)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(2)
        
        t = QLabel(title.upper())
        t.setProperty("class", "metric-title")
        t.setStyleSheet("font-size:10px; color:#858585; font-weight:700; letter-spacing:0.8px;")
        
        self.value_label = QLabel(str(value) + (f" {unit}" if unit else ""))
        self.value_label.setProperty("class", f"metric-value {tone}")
        self.value_label.setStyleSheet("font-size:15px; color:#ffffff; font-weight:700;")
        
        lay.addWidget(t)
        lay.addWidget(self.value_label)

    def set_value(self, value, unit=""):
        self.value_label.setText(str(value) + (f" {unit}" if unit else ""))


class StatusPill(QLabel):
    def __init__(self, text="SYSTEM READY", color=ACCENT):
        super().__init__("●  " + text); self.setProperty("class", "status-pill"); self.setStyleSheet(f"color:{color};")


class Plot(QWidget):
    """PyQtGraph-backed plot with a graceful static fallback."""
    def __init__(self, title="LIVE TELEMETRY", color=ACCENT):
        super().__init__(); self.color = color; self.title = title; self.values = [0.0] * 60
        self.setMinimumHeight(150)
        if pg:
            self.plot = pg.PlotWidget()
            self.plot.setBackground("#0b1118"); self.plot.showGrid(x=True, y=True, alpha=.16)
            self.plot.setTitle(title, color="#aab7c4", size="9pt")
            self.plot.getAxis('left').setTextPen('#657788'); self.plot.getAxis('bottom').setTextPen('#657788')
            self.curve = self.plot.plot(pen=pg.mkPen(color, width=2))
            lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.addWidget(self.plot)
        else:
            self.setProperty("class", "plot-fallback")
    def update_values(self, values):
        self.values = list(values)[-100:]
        if pg: self.curve.setData(self.values)
        else: self.update()
    def paintEvent(self, event):
        if pg: return
        p = QPainter(self); p.fillRect(self.rect(), QColor("#0b1118")); p.setPen(QColor("#34434f"))
        for x in range(0, self.width(), 50): p.drawLine(x, 25, x, self.height()-20)
        for y in range(25, self.height()-20, 30): p.drawLine(0, y, self.width(), y)
        p.setPen(QColor(self.color)); pts=[]
        for i,v in enumerate(self.values): pts.append(QPointF(i*self.width()/max(1,len(self.values)-1), self.height()/2-v*20))
        for a,b in zip(pts,pts[1:]): p.drawLine(a,b)
        p.setPen(QColor("#aab7c4")); p.drawText(10,18,self.title)


class CameraView(QWidget):
    def __init__(self):
        super().__init__(); self.telemetry=None; self.setMinimumSize(480,360); self.setProperty("class", "camera-view")
        self.grid_visible = True
        rng = random.Random(48)
        self.noise = [(rng.random(), rng.random(), rng.randint(16, 48)) for _ in range(1600)]
        self.trail = []
        self.follow = True
    def set_telemetry(self, data): self.telemetry=data; self.update()
    def toggle_grid(self):
        self.grid_visible = not self.grid_visible
        self.update()
    def paintEvent(self, event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); r=self.rect(); p.fillRect(r,QColor("#14171b"))
        for nx, ny, level in self.noise:
            p.setPen(QColor(level, level, level)); p.drawPoint(QPointF(nx*r.width(), ny*r.height()))
        p.setPen(QPen(QColor("#18303a"),1))
        if self.grid_visible:
            for x in range(0,r.width(),32): p.drawLine(x,0,x,r.height())
            for y in range(0,r.height(),32): p.drawLine(0,y,r.width(),y)
        p.setPen(QPen(QColor("#2a9b9c"),1)); p.drawRect(20,20,r.width()-40,r.height()-40)
        cx,cy=r.width()/2,r.height()/2
        p.setPen(QPen(QColor("#3d626b"),1)); p.drawLine(cx-28,cy,cx+28,cy); p.drawLine(cx,cy-28,cx,cy+28)
        d=self.telemetry
        if d:
            sx=r.width()/640; sy=r.height()/480
            gt=QPointF(d.u*sx, d.v*sy); est=QPointF(d.est_u*sx,d.est_v*sy); pred=QPointF((d.est_u+6)*sx,(d.est_v-3)*sy)
            glow=QRadialGradient(gt, 19)
            glow.setColorAt(0,QColor(255,255,255,255)); glow.setColorAt(.15,QColor(248,251,255,240)); glow.setColorAt(.45,QColor(210,225,240,70)); glow.setColorAt(1,QColor(210,225,240,0))
            p.setPen(Qt.NoPen); p.setBrush(QBrush(glow)); p.drawEllipse(gt,19,19); p.setBrush(Qt.NoBrush)
            # Illustrative virtual gimbal lock box, not an actuator or control model.
            p.setPen(QPen(QColor("#70c5ad"),1))
            if self.follow:
                p.drawRect(QRectF(est.x()-44,est.y()-34,88,68))
                p.drawLine(QPointF(est.x()-60,est.y()),QPointF(est.x()-44,est.y()))
                p.drawLine(QPointF(est.x()+44,est.y()),QPointF(est.x()+60,est.y()))
                p.drawText(QPointF(est.x()-44,est.y()-42),"VIRTUAL PTZ / "+d.lock)
            p.setPen(QColor("#879ba8")); p.drawText(32,80,"DEMO TELEMETRY · NO PHYSICAL CAMERA CONNECTED")
            p.setPen(QPen(QColor("#e7c66b"),1)); p.drawLine(est,gt)
            p.setPen(QPen(QColor("#efc95c"),2)); p.drawLine(gt.x()-7,gt.y(),gt.x()+7,gt.y()); p.drawLine(gt.x(),gt.y()-7,gt.x(),gt.y()+7)
            p.setPen(QPen(QColor("#42d6c5"),2)); p.drawEllipse(est,5,5)
            p.setPen(QPen(QColor("#ef8c63"),1,Qt.DashLine)); p.drawEllipse(pred,8,8); p.drawEllipse(pred,28+5*math.sin(d.frame*.04),18+3*math.cos(d.frame*.04))
            p.setPen(QPen(QColor("#ef8c63"),1,Qt.DashLine)); p.drawLine(est,pred)
            p.setPen(QColor("#93a6b5")); p.setFont(QFont("Consolas",9)); p.drawText(32,38,f"FRAME {d.frame:05d}     {d.fps:04.1f} FPS"); p.drawText(32,r.height()-28,f"U {d.u:6.2f}   V {d.v:6.2f}   |   EST {d.est_u:6.2f}, {d.est_v:6.2f}")
        p.setPen(QColor("#718291")); p.drawText(32,58,"MONOCHROME / 640×480     FOV 4.0° × 3.0°"); p.drawText(r.width()-160,28,"NORTH  ↑  REF")


def table(headers, rows=4):
    w=QTableWidget(rows,len(headers)); w.setHorizontalHeaderLabels(headers); w.horizontalHeader().setStretchLastSection(True); w.verticalHeader().setVisible(False); w.setAlternatingRowColors(True)
    for i in range(rows):
        for j,h in enumerate(headers): w.setItem(i,j,QTableWidgetItem("—" if i else ("LOCKED" if h=="Status" else f"{(i+1)*1.24:.2f}")))
    return w


def button(label, primary=False):
    b=QPushButton(label); b.setProperty("class", "primary" if primary else "tool-button"); return b
