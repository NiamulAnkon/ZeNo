import math
import os
import platform
import sys
from collections import deque

from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, QDateTime
from PyQt5.QtGui import (QColor, QPainter, QPen, QBrush, QFont, QLinearGradient,
                         QPainterPath, QPolygonF, QKeySequence)
from PyQt5.QtWidgets import (QApplication, QWidget, QFrame, QLabel, QPushButton,
                             QHBoxLayout, QVBoxLayout, QGridLayout, QStackedWidget,
                             QLineEdit, QShortcut, QSizeGrip, QGraphicsDropShadowEffect,
                             QScrollArea, QSizePolicy)

try:
    import psutil
except ImportError:  # design values are shown statically
    psutil = None

# ----------------------------------------------------------------- palette
BG1, BG2 = "#08090B", "#111016"
SIDEBAR, TOPBAR, FOOTER = "#0D0E12", "#0A0B0F", "#0B0C10"
PURPLE, PURPLE_D = "#9B6BCA", "#54228B"
LILAC, CYAN = "#B58AE0", "#63C8E8"
GREEN, RED, BLUE = "#22C99A", "#E46B70", "#8E9EFF"
WHITE, MUTED, DIM = "#F5F5F7", "#A5A5AE", "#686B75"
BORDER = "#29252F"

WEIGHTS = {400: 50, 600: 63, 700: 75, 800: 81}

def fnt(px, weight=400):
    f = QFont()
    f.setPixelSize(px)
    f.setWeight(WEIGHTS.get(weight, 50))
    return f


def label(text, px=15, color=MUTED, weight=400, align=None):
    lb = QLabel(text)
    lb.setStyleSheet(
        "background:transparent;color:%s;font-size:%dpx;font-weight:%d;" % (color, px, weight))
    if align:
        lb.setAlignment(align)
    return lb


# ------------------------------------------------------------------- icons
def draw_icon(p, kind, r, color, sw=2.0):
    """Vector icons drawn on a 24x24 grid, scaled into rect r."""
    p.save()
    p.translate(r.topLeft())
    p.scale(r.width() / 24.0, r.height() / 24.0)
    c = QColor(color)
    pen = QPen(c, sw)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    def ln(a, b, c_, d):
        p.drawLine(QPointF(a, b), QPointF(c_, d))

    def poly(*pts):
        p.drawPolyline(QPolygonF([QPointF(x, y) for x, y in pts]))

    def rr(x, y, w, h, rad):
        p.drawRoundedRect(QRectF(x, y, w, h), rad, rad)

    if kind == "home":
        poly((3, 12), (12, 3), (21, 12))
        poly((5, 10), (5, 21), (19, 21), (19, 10))
        poly((10, 21), (10, 14), (14, 14), (14, 21))
    elif kind == "monitor":
        rr(3, 4, 18, 12, 2)
        ln(8, 20, 16, 20)
        ln(12, 16, 12, 20)
        poly((6, 10), (9, 10), (11, 7), (13, 12), (15, 10), (18, 10))
    elif kind == "shield":
        path = QPainterPath()
        path.moveTo(12, 3)
        path.lineTo(20, 6)
        path.lineTo(20, 12)
        path.cubicTo(20, 17, 16, 20, 12, 21)
        path.cubicTo(8, 20, 4, 17, 4, 12)
        path.lineTo(4, 6)
        path.closeSubpath()
        p.drawPath(path)
    elif kind in ("chip", "cpu"):
        rr(6, 6, 12, 12, 2)
        p.drawRect(QRectF(10, 10, 4, 4))
        for v in (9, 12, 15):
            ln(v, 3, v, 6)
            ln(v, 18, v, 21)
            ln(3, v, 6, v)
            ln(18, v, 21, v)
    elif kind == "gpu":
        rr(2.5, 6, 19, 12, 2)
        p.drawEllipse(QPointF(12, 12), 3.5, 3.5)
        ln(6, 21, 18, 21)
    elif kind == "ram":
        rr(3, 7, 18, 10, 1.5)
        for x in (7, 11, 15):
            ln(x, 10, x, 14)
        ln(6, 17, 6, 20)
        ln(18, 17, 18, 20)
    elif kind == "disk":
        rr(3, 5, 18, 14, 3)
        ln(3, 14, 21, 14)
        ln(16, 17, 17, 17)
    elif kind == "store":
        rr(4, 4, 16, 16, 3)
        ln(12, 8, 12, 16)
        ln(8, 12, 16, 12)
    elif kind == "user":
        p.drawEllipse(QPointF(12, 8), 4, 4)
        path = QPainterPath()
        path.moveTo(4, 21)
        path.quadTo(12, 9, 20, 21)
        p.drawPath(path)
    elif kind == "tools":
        ln(5, 19, 14, 10)
        p.drawEllipse(QPointF(17, 7), 3.5, 3.5)
    elif kind == "list":
        for y in (6, 12, 18):
            ln(9, y, 21, y)
            p.drawPoint(QPointF(4, y))
    elif kind == "gear":
        p.drawEllipse(QPointF(12, 12), 3, 3)
        p.drawEllipse(QPointF(12, 12), 7, 7)
        for i in range(8):
            a = i * math.pi / 4
            ln(12 + 7 * math.cos(a), 12 + 7 * math.sin(a),
               12 + 10 * math.cos(a), 12 + 10 * math.sin(a))
    elif kind == "pulse":
        poly((2, 12), (7, 12), (10, 5), (14, 19), (17, 12), (22, 12))
    elif kind == "check":
        poly((5, 12.5), (10, 17.5), (19, 7))
    elif kind == "refresh":
        p.drawArc(QRectF(4, 4, 16, 16), 60 * 16, 280 * 16)
        poly((16.5, 1.5), (16.5, 5.5), (12.5, 5.5))
    elif kind == "download":
        ln(12, 4, 12, 15)
        poly((7, 10), (12, 15), (17, 10))
        ln(5, 20, 19, 20)
    elif kind == "clock":
        p.drawEllipse(QPointF(12, 12), 9, 9)
        poly((12, 7), (12, 12), (16, 14))
    elif kind == "windows":
        p.setPen(Qt.NoPen)
        p.setBrush(c)
        for x, y in ((3, 3), (12.5, 3), (3, 12.5), (12.5, 12.5)):
            p.drawRect(QRectF(x, y, 8.5, 8.5))
    elif kind == "search":
        p.drawEllipse(QPointF(10.5, 10.5), 6.5, 6.5)
        ln(15.5, 15.5, 21, 21)
    elif kind == "bell":
        path = QPainterPath()
        path.moveTo(6, 17)
        path.cubicTo(6, 17, 7, 15, 7, 11)
        path.cubicTo(7, 7, 9, 5, 12, 5)
        path.cubicTo(15, 5, 17, 7, 17, 11)
        path.cubicTo(17, 15, 18, 17, 18, 17)
        path.closeSubpath()
        p.drawPath(path)
        ln(10, 20, 14, 20)
    elif kind == "lock":
        rr(5, 11, 14, 10, 2)
        p.drawArc(QRectF(8, 3, 8, 10), 0, 180 * 16)
    elif kind == "firewall":
        rr(3, 5, 18, 14, 1.5)
        ln(3, 10, 21, 10)
        ln(3, 14.5, 21, 14.5)
        ln(9, 5, 9, 10)
        ln(15, 10, 15, 14.5)
        ln(9, 14.5, 9, 19)
    elif kind == "info":
        p.drawEllipse(QPointF(12, 12), 9, 9)
        ln(12, 11, 12, 17)
        p.drawPoint(QPointF(12, 7.5))
    elif kind == "chevdown":
        poly((6, 9), (12, 15), (18, 9))
    elif kind == "chevup":
        poly((6, 15), (12, 9), (18, 15))
    elif kind == "min":
        ln(6, 12, 18, 12)
    elif kind == "max":
        p.drawRect(QRectF(7, 7, 10, 10))
    elif kind == "close":
        ln(7, 7, 17, 17)
        ln(17, 7, 7, 17)
    p.restore()


class Icon(QWidget):
    def __init__(self, kind, color, size=24, sw=2.0):
        super().__init__()
        self.kind, self.color, self.sw = kind, color, sw
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_kind(self, kind):
        self.kind = kind
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        draw_icon(p, self.kind, QRectF(self.rect()), self.color, self.sw * self.width() / 24.0)


class Dot(QWidget):
    def __init__(self, color, size=10):
        super().__init__()
        self.color = color
        self.setFixedSize(size, size)

    def set_color(self, color):
        self.color = color
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(self.color))
        p.drawEllipse(QRectF(self.rect()))


class CheckBadge(QWidget):
    def __init__(self, size=32, color=GREEN):
        super().__init__()
        self.color = color
        self.setFixedSize(size, size)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(self.color))
        p.drawEllipse(QRectF(self.rect()))
        m = self.width() * 0.2
        draw_icon(p, "check", QRectF(m, m, self.width() - 2 * m, self.height() - 2 * m),
                  "#071A14", 3.2)


class Logo(QWidget):
    """Circular 'Z' emblem with gradient ring."""

    def __init__(self, d, stroke, glow=False):
        super().__init__()
        self.stroke = stroke
        self.setFixedSize(d, d)
        if glow:
            fx = QGraphicsDropShadowEffect(self)
            fx.setBlurRadius(28)
            fx.setOffset(0, 0)
            c = QColor(CYAN)
            c.setAlpha(120)
            fx.setColor(c)
            self.setGraphicsEffect(fx)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self.stroke
        r = QRectF(self.rect()).adjusted(s / 2, s / 2, -s / 2, -s / 2)
        g = QLinearGradient(r.left(), 0, r.right(), 0)
        g.setColorAt(0, QColor(CYAN))
        g.setColorAt(1, QColor(PURPLE))
        p.setPen(QPen(QBrush(g), s))
        p.setBrush(QColor("#090A0D"))
        p.drawEllipse(r)
        p.setPen(QColor(LILAC))
        p.setFont(fnt(int(self.width() * 0.5), 800))
        p.drawText(QRectF(self.rect()), Qt.AlignCenter, "Z")


# ------------------------------------------------------------ custom paints
class Panel(QFrame):
    """Rounded card. hero=True gives the diagonal purple->cyan gradient."""

    def __init__(self, hero=False, deco=None, radius=17):
        super().__init__()
        self.hero, self.deco, self.radius = hero, deco, radius

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(.6, .6, -.6, -.6)
        if self.hero:
            g = QLinearGradient(r.topLeft(), r.bottomRight())
            g.setColorAt(0, QColor("#19131F"))
            g.setColorAt(.55, QColor("#101116"))
            g.setColorAt(1, QColor("#101D25"))
        else:
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, QColor("#191B20"))
            g.setColorAt(1, QColor("#111316"))
        p.setPen(QPen(QColor(BORDER), 1.2))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, self.radius, self.radius)

        if self.deco:
            clip = QPainterPath()
            clip.addRoundedRect(r, self.radius, self.radius)
            p.setClipPath(clip)
            L, T, R, B = r.left(), r.top(), r.right(), r.bottom()
            a = QPainterPath()
            b = QPainterPath()
            if self.deco == "hero":
                a.moveTo(L, T + 55)
                a.cubicTo(L + 74, T + 5, L + 104, T + 5, L + 184, T)
                b.moveTo(R - 145, B)
                b.cubicTo(R - 85, B - 40, R - 55, B - 40, R, B - 70)
                pa, pb, wa, wb, oa, ob = PURPLE, CYAN, 3, 3, .65, .45
            else:  # brand
                a.moveTo(L, B - 32)
                a.cubicTo(L + 90, B - 102, L + 120, B - 12, L + 210, B)
                b.moveTo(R, T + 34)
                b.cubicTo(R - 118, T + 74, R - 68, T + 124, R - 158, B)
                pa, pb, wa, wb, oa, ob = PURPLE, PURPLE, 2, 2, .5, .5
            for path, col, w, o in ((a, pa, wa, oa), (b, pb, wb, ob)):
                c = QColor(col)
                c.setAlphaF(o)
                p.setPen(QPen(c, w))
                p.setBrush(Qt.NoBrush)
                p.drawPath(path)


class Strip(QWidget):
    """Solid bar (sidebar / top bar / footer) with a 1px divider on one edge."""

    def __init__(self, color, edge, alpha=255):
        super().__init__()
        self.color, self.edge, self.alpha = color, edge, alpha

    def paintEvent(self, _):
        p = QPainter(self)
        c = QColor(self.color)
        c.setAlpha(self.alpha)
        p.fillRect(self.rect(), c)
        p.setPen(QColor(BORDER))
        w, h = self.width(), self.height()
        if self.edge == "right":
            p.drawLine(w - 1, 0, w - 1, h)
        elif self.edge == "bottom":
            p.drawLine(0, h - 1, w, h - 1)
        elif self.edge == "top":
            p.drawLine(0, 0, w, 0)


class Sparkline(QWidget):
    def __init__(self, color, values):
        super().__init__()
        self.color = color
        self.values = deque(values, maxlen=len(values))
        self.setFixedHeight(40)

    def push(self, v):
        self.values.append(v)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        n = len(self.values)
        if n < 2:
            return
        w, h = self.width() - 2, self.height() - 4
        pts = [QPointF(1 + i * w / (n - 1), 2 + h - (v / 100.0) * h)
               for i, v in enumerate(self.values)]
        pen = QPen(QColor(self.color), 2.5)
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawPolyline(QPolygonF(pts))


class Bar(QWidget):
    def __init__(self, value):
        super().__init__()
        self.value = value
        self.setFixedHeight(12)

    def set_value(self, v):
        self.value = v
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        r = QRectF(self.rect())
        p.setBrush(QColor(BORDER))
        p.drawRoundedRect(r, 6, 6)
        fill = QRectF(0, 0, max(12.0, r.width() * self.value / 100.0), r.height())
        g = QLinearGradient(fill.topLeft(), fill.topRight())
        g.setColorAt(0, QColor(PURPLE))
        g.setColorAt(1, QColor(PURPLE_D))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(fill, 6, 6)


class Gauge(QWidget):
    def __init__(self, value=92):
        super().__init__()
        self.value = value
        self.setFixedSize(140, 140)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(8, 8, -8, -8)
        p.setPen(QPen(QColor(BORDER), 13))
        p.drawEllipse(r)
        g = QLinearGradient(r.left(), 0, r.right(), 0)
        g.setColorAt(0, QColor(CYAN))
        g.setColorAt(1, QColor(PURPLE))
        pen = QPen(QBrush(g), 13)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(r, 90 * 16, int(-360 * 16 * self.value / 100.0))
        p.setPen(QColor(WHITE))
        p.setFont(fnt(30, 700))
        p.drawText(QRectF(0, 38, self.width(), 40), Qt.AlignCenter, str(self.value))
        p.setPen(QColor(MUTED))
        p.setFont(fnt(15))
        p.drawText(QRectF(0, 76, self.width(), 24), Qt.AlignCenter, "/100")


# ----------------------------------------------------------------- buttons
PILL_CSS = ("QPushButton{background:#24232B;border:1px solid #51435E;border-radius:18px;"
            "color:%s;font-size:13px;padding:0 18px;}"
            "QPushButton:hover{background:#2E2C37;}QPushButton:pressed{background:#1D1C24;}" % WHITE)
GRAD_CSS = ("QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 %s,stop:1 %s);"
            "border:none;border-radius:18px;color:%s;font-size:15px;}"
            "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #A97BD6,stop:1 #6530A3);}"
            "QPushButton:pressed{background:%s;}" % (PURPLE, PURPLE_D, WHITE, PURPLE_D))


def pill(text, css=PILL_CSS, h=36):
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setFixedHeight(h)
    b.setStyleSheet(css)
    return b


def badge(text, fg, bg, border=None):
    lb = QLabel(text)
    lb.setStyleSheet("background:%s;color:%s;font-size:12px;border-radius:13px;padding:5px 14px;%s"
                     % (bg, fg, ("border:1px solid %s;" % border) if border else ""))
    return lb


class NavButton(QPushButton):
    def __init__(self, text, kind):
        super().__init__()
        self.text_, self.kind = text, kind
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        self.setFlat(True)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        on = self.isChecked()
        if on:
            p.setPen(QPen(QColor(PURPLE), 1))
            p.setBrush(QColor("#281A38"))
            p.drawRoundedRect(r, 13, 13)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(LILAC))
            p.drawRoundedRect(QRectF(0, 0, 4, h), 2, 2)
        elif self.underMouse():
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 12))
            p.drawRoundedRect(r, 13, 13)
        draw_icon(p, self.kind, QRectF(20, (h - 24) / 2.0, 24, 24), WHITE if on else LILAC, 2.0)
        p.setPen(QColor(WHITE if on else MUTED))
        p.setFont(fnt(16 if on else 15, 600 if on else 400))
        p.drawText(QRectF(68, 0, w - 78, h), Qt.AlignVCenter | Qt.AlignLeft, self.text_)


class WinButton(QPushButton):
    def __init__(self, kind, danger=False):
        super().__init__()
        self.kind, self.danger = kind, danger
        self.setFixedSize(40, 36)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self.underMouse():
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#C42B3A") if self.danger else QColor(255, 255, 255, 22))
            p.drawRoundedRect(QRectF(self.rect()), 8, 8)
        draw_icon(p, self.kind, QRectF((self.width() - 18) / 2.0, (self.height() - 18) / 2.0, 18, 18),
                  WHITE if self.underMouse() and self.danger else MUTED, 1.8)


# ------------------------------------------------------------------- pieces
def card_header(kind, color, title, right=None):
    row = QHBoxLayout()
    row.setSpacing(12)
    row.addWidget(Icon(kind, color, 24))
    row.addWidget(label(title, 16, WHITE, 600))
    row.addStretch()
    if right is not None:
        row.addWidget(right)
    return row


class MetricCard(Panel):
    def __init__(self, title, kind, color, value, spark_seed=None):
        super().__init__()
        self.setMinimumWidth(150)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(25, 22, 25, 22)
        lay.setSpacing(0)
        lay.addWidget(Icon(kind, color, 30))
        lay.addSpacing(10)
        lay.addWidget(label(title, 16, WHITE, 600))
        lay.addSpacing(8)
        self.val = label("%d%%" % value, 27, WHITE, 700)
        lay.addWidget(self.val)
        lay.addStretch()
        self.spark = self.bar = None
        if spark_seed:
            self.spark = Sparkline(color, spark_seed)
            lay.addWidget(self.spark)
        else:
            self.bar = Bar(value)
            lay.addWidget(self.bar)
            lay.addSpacing(6)

    def set_value(self, v, push=True):
        v = int(round(v))
        self.val.setText("%d%%" % v)
        if self.spark is not None and push:
            self.spark.push(v)
        if self.bar is not None:
            self.bar.set_value(v)


def info_row(left_widget, name, status, status_color=GREEN):
    row = QHBoxLayout()
    row.setSpacing(12)
    row.addWidget(left_widget)
    row.addWidget(label(name, 15, MUTED))
    row.addStretch()
    row.addWidget(label(status, 15, status_color))
    return row


# -------------------------------------------------------------- dashboard
class DashboardPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 25, 20, 25)
        root.setSpacing(25)

        # ---- row 1: hero + metrics
        r1 = QHBoxLayout()
        r1.setSpacing(20)
        r1.addWidget(self._hero(), 579)
        self.cpu = MetricCard("CPU", "cpu", CYAN, 18, [30, 45, 38, 58, 42, 55, 40, 62, 45, 56, 48, 60])
        self.gpu = MetricCard("GPU", "gpu", PURPLE, 32, [35, 48, 42, 60, 45, 62, 50, 66, 52, 60, 55, 68])
        self.ram = MetricCard("RAM", "ram", GREEN, 56, [38, 50, 44, 62, 46, 64, 52, 68, 54, 62, 56, 66])
        self.disk = MetricCard("Storage", "disk", BLUE, 72)
        for m in (self.cpu, self.gpu, self.ram, self.disk):
            r1.addWidget(m, 176)
        root.addLayout(r1, 225)

        # ---- row 2: status cards
        r2 = QHBoxLayout()
        r2.setSpacing(19)
        r2.addWidget(self._health(), 372)
        r2.addWidget(self._security(), 328)
        r2.addWidget(self._drivers(), 308)
        r2.addWidget(self._updates(), 298)
        root.addLayout(r2, 236)

        # ---- row 3: activity + brand
        r3 = QHBoxLayout()
        r3.setSpacing(19)
        r3.addWidget(self._activity(), 735)
        r3.addWidget(self._brand(), 608)
        root.addLayout(r3, 216)

    # hero ---------------------------------------------------------------
    def _hero(self):
        pn = Panel(hero=True, deco="hero", radius=18)
        lay = QHBoxLayout(pn)
        lay.setContentsMargins(79, 20, 30, 20)
        lay.setSpacing(53)
        lay.addWidget(Logo(130, 6, glow=True), 0, Qt.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(0)
        col.addStretch()
        col.addWidget(label(platform.node().upper() or "DESKTOP-KAWSAR", 27, WHITE, 700))
        col.addSpacing(8)
        os_row = QHBoxLayout()
        os_row.setSpacing(10)
        os_row.addWidget(Icon("windows", MUTED, 16))
        if platform.system() == "Windows":
            os_txt = "Windows %s %s" % (platform.release(), "64-bit" if "64" in platform.machine() else "32-bit")
        else:
            os_txt = "Windows 10 Pro 64-bit"
        os_row.addWidget(label(os_txt, 15, MUTED))
        os_row.addStretch()
        col.addLayout(os_row)
        col.addSpacing(26)
        ok = QHBoxLayout()
        ok.setSpacing(14)
        ok.addWidget(CheckBadge(32), 0, Qt.AlignTop)
        t = QVBoxLayout()
        t.setSpacing(4)
        t.addWidget(label("System is healthy!", 17, GREEN, 700))
        t.addWidget(label("Everything looks good.", 15, MUTED))
        ok.addLayout(t)
        ok.addStretch()
        col.addLayout(ok)
        col.addStretch()
        lay.addLayout(col, 1)
        return pn

    # health -------------------------------------------------------------
    def _health(self):
        pn = Panel()
        v = QVBoxLayout(pn)
        v.setContentsMargins(26, 20, 26, 20)
        v.addLayout(card_header("pulse", CYAN, "System Health Overview"))
        body = QHBoxLayout()
        body.setSpacing(24)
        body.addWidget(Gauge(92), 0, Qt.AlignVCenter)
        grid = QGridLayout()
        grid.setVerticalSpacing(16)
        grid.setHorizontalSpacing(10)
        rows = [("Performance", "Excellent"), ("Stability", "Excellent"),
                ("Security", "Good"), ("Overall Health", "Excellent")]
        for i, (name, st) in enumerate(rows):
            grid.addWidget(Dot(GREEN, 9), i, 0)
            grid.addWidget(label(name, 15, MUTED), i, 1)
            grid.addWidget(label(st, 15, GREEN), i, 2)
        grid.setColumnStretch(1, 1)
        body.addLayout(grid, 1)
        v.addStretch()
        v.addLayout(body)
        v.addStretch()
        return pn

    # security -----------------------------------------------------------
    def _security(self):
        pn = Panel()
        v = QVBoxLayout(pn)
        v.setContentsMargins(26, 20, 26, 20)
        v.addLayout(card_header("shield", CYAN, "Security Status",
                                badge("● Secure", GREEN, "#12352D", GREEN)))
        v.addStretch()
        rows = [("shield", CYAN, "Microsoft Defender", "On"),
                ("firewall", RED, "Firewall", "On"),
                ("refresh", CYAN, "Windows Update", "Up to date"),
                ("lock", LILAC, "Secure Boot", "On")]
        for i, (k, c, n, s) in enumerate(rows):
            v.addLayout(info_row(Icon(k, c, 22), n, s))
            if i < len(rows) - 1:
                v.addSpacing(14)
        v.addStretch()
        return pn

    # drivers ------------------------------------------------------------
    def _drivers(self):
        pn = Panel()
        v = QVBoxLayout(pn)
        v.setContentsMargins(26, 20, 26, 20)
        v.addLayout(card_header("gear", LILAC, "Driver Status",
                                badge("↓ Up to date", LILAC, "#281A38")))
        v.addStretch()
        v.addWidget(CheckBadge(46), 0, Qt.AlignHCenter)
        v.addSpacing(12)
        v.addWidget(label("All drivers are up to date!", 16, WHITE, 600, Qt.AlignCenter))
        self.last_checked = label("Last checked: Today, 04:20 AM", 12, MUTED, 400, Qt.AlignCenter)
        v.addWidget(self.last_checked)
        v.addStretch()
        self.check_btn = pill("⟳  Check for Updates")
        self.check_btn.clicked.connect(self.check_updates)
        v.addWidget(self.check_btn)
        return pn

    def check_updates(self):
        # hook: run your real driver scan here
        self.check_btn.setEnabled(False)
        self.check_btn.setText("Checking…")
        self.win.set_status("Checking for updates…", CYAN)

        def done():
            now = QDateTime.currentDateTime().toString("hh:mm AP")
            self.last_checked.setText("Last checked: Today, " + now)
            self.check_btn.setText("⟳  Check for Updates")
            self.check_btn.setEnabled(True)
            self.win.set_status("Ready", GREEN)
        QTimer.singleShot(1500, done)

    # updates ------------------------------------------------------------
    def _updates(self):
        pn = Panel()
        v = QVBoxLayout(pn)
        v.setContentsMargins(26, 20, 26, 20)
        count = QLabel("2")
        count.setFixedSize(30, 30)
        count.setAlignment(Qt.AlignCenter)
        count.setStyleSheet("background:#6C35A0;color:%s;font-size:12px;border-radius:15px;" % WHITE)
        v.addLayout(card_header("download", LILAC, "Available Updates", count))
        v.addStretch()
        for kind, color, name, size in (("windows", CYAN, "Windows 10 Update", "Size: 4.8 GB"),
                                        ("chip", GREEN, "NVIDIA Graphics Driver", "Size: 620 MB")):
            row = QHBoxLayout()
            row.setSpacing(14)
            row.addWidget(Icon(kind, color, 28), 0, Qt.AlignTop)
            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(label(name, 15, WHITE))
            col.addWidget(label(size, 12, MUTED))
            row.addLayout(col)
            row.addStretch()
            v.addLayout(row)
            v.addSpacing(14)
        v.addStretch()
        btn = pill("↓  Install All", GRAD_CSS, 37)
        btn.clicked.connect(self.install_all)
        v.addWidget(btn)
        return pn

    def install_all(self):
        # hook: start your real install job here
        self.win.set_status("Installing updates…", CYAN)
        QTimer.singleShot(2500, lambda: self.win.set_status("Ready", GREEN))
 
    # activity -----------------------------------------------------------
    def _activity(self):
        pn = Panel()
        v = QVBoxLayout(pn)
        v.setContentsMargins(26, 20, 26, 20)
        va = QPushButton("View All →")
        va.setFlat(True)
        va.setCursor(Qt.PointingHandCursor)
        va.setStyleSheet("QPushButton{color:%s;font-size:15px;border:none;background:transparent;}"
                         "QPushButton:hover{color:#8CD9F0;}" % CYAN)
        va.clicked.connect(lambda: self.win.go(7))
        v.addLayout(card_header("clock", CYAN, "Recent Activity", va))
        v.addStretch()
        items = [(GREEN, "System scan completed successfully", "2 minutes ago"),
                 (CYAN, "Driver update installed: NVIDIA Graphics Driver", "5 minutes ago"),
                 (PURPLE, "Downloaded: Windows 10 Update", "8 minutes ago"),
                 (GREEN, "Temporary files cleaned (2.1 GB freed)", "1 hour ago")]
        for i, (c, text, when) in enumerate(items):
            row = QHBoxLayout()
            row.setSpacing(16)
            row.addSpacing(4)
            row.addWidget(Dot(c, 10))
            row.addWidget(label(text, 15, MUTED))
            row.addStretch()
            row.addWidget(label(when, 12, MUTED))
            v.addLayout(row)
            if i < len(items) - 1:
                v.addSpacing(14)
        v.addStretch()
        return pn

    # brand --------------------------------------------------------------
    def _brand(self):
        pn = Panel(hero=True, deco="brand")
        lay = QHBoxLayout(pn)
        lay.setContentsMargins(70, 20, 30, 20)
        lay.setSpacing(50)
        lay.addWidget(Logo(112, 5, glow=True), 0, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(4)
        col.addStretch()
        col.addWidget(label("ZeNo", 34, WHITE, 700))
        col.addWidget(label("All-in-One Windows PC Utility", 15, WHITE))
        col.addSpacing(6)
        col.addWidget(label("Manage  •  Optimize  •  Secure", 15, LILAC))
        col.addSpacing(10)
        ver = QLabel("Version 0.0.1  ⓘ")
        ver.setStyleSheet("background:#21172D;color:%s;font-size:12px;border:1px solid #51435E;"
                          "border-radius:15px;padding:6px 14px;" % LILAC)
        row = QHBoxLayout()
        row.addWidget(ver)
        row.addStretch()
        col.addLayout(row)
        col.addStretch()
        lay.addLayout(col, 1)
        return pn

    # live data ----------------------------------------------------------
    def refresh_metrics(self):
        if not psutil:
            return
        self.cpu.set_value(psutil.cpu_percent())
        self.ram.set_value(psutil.virtual_memory().percent)
        try:
            self.disk.set_value(psutil.disk_usage(os.path.abspath(os.sep)).percent)
        except OSError:
            pass


class PlaceholderPage(QWidget):
    def __init__(self, title, kind):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 25, 20, 25)
        pn = Panel()
        pv = QVBoxLayout(pn)
        pv.addStretch()
        pv.addWidget(Icon(kind, LILAC, 48), 0, Qt.AlignHCenter)
        pv.addSpacing(12)
        pv.addWidget(label(title, 21, WHITE, 700, Qt.AlignCenter))
        pv.addWidget(label("This page is not designed yet.", 15, MUTED, 400, Qt.AlignCenter))
        pv.addStretch()
        v.addWidget(pn)


# ---------------------------------------------------------------- main window
NAV = [("Dashboard", "home"), ("System Monitor", "monitor"), ("Security Center", "shield"),
       ("Driver Manager", "chip"), ("Software Hub", "store"), ("Setup Profiles", "user"),
       ("Windows Toolkit", "tools"), ("Activity Center", "list"), ("Settings", "gear")]


class TopBar(Strip):
    def __init__(self, win):
        super().__init__(TOPBAR, "bottom", 245)
        self.win = win
        self.setFixedHeight(90)
        self._drag = None
        lay = QHBoxLayout(self)
        lay.setContentsMargins(42, 0, 14, 0)
        lay.setSpacing(0)
        self.title_icon = Icon("home", LILAC, 26)
        lay.addWidget(self.title_icon)
        lay.addSpacing(14)
        self.title = label("Dashboard", 21, WHITE, 700)
        lay.addWidget(self.title)
        lay.addStretch(1)

        box = QFrame()
        box.setMinimumWidth(120)
        box.setMaximumWidth(578)
        box.setFixedHeight(48)
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        box.setStyleSheet("QFrame{background:#15151B;border:1px solid %s;border-radius:24px;}" % BORDER)
        bl = QHBoxLayout(box)
        bl.setContentsMargins(20, 0, 20, 0)
        bl.setSpacing(10)
        ic = Icon("search", MUTED, 20)
        ic.setStyleSheet("border:none;background:transparent;")
        bl.addWidget(ic)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search anything... (Ctrl + K)")
        self.search.setStyleSheet("QLineEdit{background:transparent;border:none;color:%s;font-size:15px;}" % WHITE)
        bl.addWidget(self.search)
        lay.addWidget(box)
        self.search_box = box
        lay.addStretch(1)

        bell = QWidget()
        bell.setFixedSize(34, 34)
        bl2 = QVBoxLayout(bell)
        bl2.setContentsMargins(0, 0, 0, 0)
        bl2.addWidget(Icon("bell", LILAC, 28), 0, Qt.AlignCenter)
        dot = Dot(RED, 14)
        dot.setParent(bell)
        dot.move(19, 0)
        lay.addWidget(bell)
        self.compact_widgets = [bell]
        lay.addSpacing(26)

        avatar = QLabel()
        avatar.setFixedSize(38, 38)
        avatar.setStyleSheet("background:#24232B;border:1px solid %s;border-radius:19px;" % MUTED)
        al = QVBoxLayout(avatar)
        al.setContentsMargins(0, 0, 0, 0)
        al.addWidget(Icon("user", MUTED, 24, 1.8), 0, Qt.AlignCenter)
        lay.addWidget(avatar)
        self.compact_widgets.append(avatar)
        lay.addSpacing(8)
        chevron = Icon("chevdown", MUTED, 20, 1.8)
        lay.addWidget(chevron)
        self.compact_widgets.append(chevron)
        lay.addSpacing(20)
        sep = QFrame()
        sep.setFixedSize(1, 48)
        sep.setStyleSheet("background:%s;" % BORDER)
        lay.addWidget(sep)
        self.compact_widgets.append(sep)
        lay.addSpacing(12)
        for kind, danger, slot in (("min", False, win.showMinimized),
                                   ("max", False, win.toggle_max),
                                   ("close", True, win.close)):
            b = WinButton(kind, danger)
            b.clicked.connect(slot)
            lay.addWidget(b)

    # drag the frameless window by the top bar
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and not self.win.isMaximized():
            self._drag = e.globalPos() - self.win.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.win.move(e.globalPos() - self._drag)

    def mouseReleaseEvent(self, _):
        self._drag = None

    def mouseDoubleClickEvent(self, _):
        self.win.toggle_max()

    def resizeEvent(self, event):
        compact = self.width() < 900
        for widget in self.compact_widgets:
            widget.setVisible(not compact)
        self.layout().setContentsMargins(18 if compact else 42, 0, 8 if compact else 14, 0)
        super().resizeEvent(event)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZeNo")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else QRectF(0, 0, 1200, 800).toRect()
        width = min(1200, max(320, int(available.width() * 0.9)))
        height = min(800, max(320, int(available.height() * 0.9)))
        self.setMinimumSize(min(800, width), min(600, height))
        self.resize(width, height)
        self.move(available.center() - self.rect().center())

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, 1)

        sidebar = Strip(SIDEBAR, "right")
        sidebar.setFixedWidth(260)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 24, 18, 18)
        side.setSpacing(8)

        brand = QHBoxLayout()
        brand.setSpacing(12)
        brand.addWidget(Logo(42, 3))
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand_text.addWidget(label("ZeNo", 23, WHITE, 700))
        brand_text.addWidget(label("PC UTILITY", 11, MUTED, 600))
        brand.addLayout(brand_text)
        brand.addStretch()
        side.addLayout(brand)
        side.addSpacing(25)

        self.nav_buttons = []
        for i, (text, kind) in enumerate(NAV):
            button = NavButton(text, kind)
            button.clicked.connect(lambda checked=False, index=i: self.go(index))
            self.nav_buttons.append(button)
            side.addWidget(button)

        side.addStretch()
        side.addLayout(info_row(Dot(GREEN, 9), "System status", "Healthy"))
        body.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.topbar = TopBar(self)
        content_layout.addWidget(self.topbar)

        self.stack = QStackedWidget()
        dashboard_scroll = QScrollArea()
        dashboard_scroll.setWidgetResizable(True)
        dashboard_scroll.setFrameShape(QFrame.NoFrame)
        self.dashboard_page = DashboardPage(self)
        dashboard_scroll.setWidget(self.dashboard_page)
        self.dashboard_scroll = dashboard_scroll
        self.stack.addWidget(dashboard_scroll)
        for text, kind in NAV[1:]:
            self.stack.addWidget(PlaceholderPage(text, kind))
        content_layout.addWidget(self.stack, 1)

        footer = Strip(FOOTER, "top")
        footer.setFixedHeight(42)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(22, 0, 14, 0)
        footer_layout.setSpacing(9)
        self.status_dot = Dot(GREEN, 9)
        self.status_lbl = label("Ready", 13, MUTED)
        footer_layout.addWidget(self.status_dot)
        footer_layout.addWidget(self.status_lbl)
        footer_layout.addStretch()
        footer_layout.addWidget(label("ZeNo  •  Version 0.0.1", 12, DIM))
        footer_layout.addWidget(QSizeGrip(self))
        content_layout.addWidget(footer)
        body.addWidget(content, 1)

        self.nav_buttons[0].setChecked(True)
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.activated.connect(self._focus_search)
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.dashboard_page.refresh_metrics)
        self.metrics_timer.start(2000)

    def _focus_search(self):
        self.topbar.search.setFocus()
        self.topbar.search.selectAll()

    def go(self, idx):
        self.stack.setCurrentIndex(idx)
        self.nav_buttons[idx].setChecked(True)
        text, kind = NAV[idx]
        self.topbar.title.setText(text)
        self.topbar.title_icon.set_kind(kind)

    def set_status(self, text, color=GREEN):
        self.status_lbl.setText(text)
        self.status_dot.set_color(color)

    def toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0, QColor(BG1))
        g.setColorAt(1, QColor(BG2))
        p.fillRect(self.rect(), g)
        w, h = self.width(), self.height()
        a = QPainterPath()
        a.moveTo(0, h * .75)
        a.cubicTo(150, h * .69, 170, h * .84, 300, h * .79)
        a.cubicTo(400, h * .75, 480, h * .70, 590, h * .75)
        c = QColor(PURPLE)
        c.setAlphaF(.22)
        p.setPen(QPen(c, 2))
        p.drawPath(a)
        b = QPainterPath()
        b.moveTo(w * .667, 0)
        b.cubicTo(w * .59, 90, w * .62, 140, w * .546, 205)
        c2 = QColor(CYAN)
        c2.setAlphaF(.12)
        p.setPen(QPen(c2, 2))
        p.drawPath(b)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    QFont.insertSubstitutions("Inter", ["Segoe UI", "Arial", "Helvetica"])
    f = QFont("Inter")
    f.setPixelSize(15)
    app.setFont(f)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
