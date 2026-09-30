"""Engineering workspace views for the scientific UI prototype.

The widgets in this module deliberately stop at the presentation boundary.  All
curves, images, tables, and video frames are deterministic illustrations so a
real tracker can be connected later without making the prototype claim to have
run an algorithm.
"""

from __future__ import annotations

import math
import os
import random
from typing import Any, Iterable

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

try:  # PyQtGraph is optional so the fallback remains useful in a bare install.
    import pyqtgraph as pg
except ImportError:  # pragma: no cover - exercised only when the optional dep is absent
    pg = None


try:
    # The host viewport is developed independently from these pages.
    from ui.viewport import ViewportPanel as _ExternalViewportPanel
except Exception:  # pragma: no cover - current tree uses the local fallback
    _ExternalViewportPanel = None


ACCENT = "#42d6c5"
ORANGE = "#ef8c63"
GOLD = "#efc95c"
PURPLE = "#b58cff"
BLUE = "#6da9ff"
CHARCOAL = "#111820"
GRID = "#293942"
TEXT = "#c9d7dc"
MUTED = "#7e929d"

ANALYSIS_CHART_TITLES = [
    "Error Timeline",
    "Error Histogram",
    "Error CDF",
    "RMSE vs SNR",
    "Background vs RMSE",
    "PSF Width vs RMSE",
    "Detection vs SNR",
    "False Alarm vs SNR",
    "FPS vs Resolution",
    "FPS vs Noise",
    "Prediction Error vs Horizon",
    "Lock Retention vs Velocity",
    "Acquisition vs Uncertainty",
    "Fixed EAL vs Adaptive EAL",
]

PERFORMANCE_METRICS = [
    ("FPS", "60.0", ""),
    ("Mean Latency", "18.2", "ms"),
    ("P95 Latency", "23.8", "ms"),
    ("Acquisition Time", "0.83", "s"),
    ("Reacquisition", "0.42", "s"),
    ("Lock Retention", "98.4", "%"),
    ("Detection Probability", "97.2", "%"),
    ("False Alarm Probability", "0.8", "%"),
    ("Centroid RMSE", "3.14", "px"),
    ("Angular RMSE", "0.021", "deg"),
    ("Max Tracking Error", "8.7", "px"),
    ("5 s Prediction RMSE", "6.42", "px"),
    ("Target Loss Rate", "1.6", "%"),
]

LOG_SPECS = {
    "Detection": [
        "Timestamp",
        "Frame",
        "Detection",
        "Candidate Count",
        "Confidence",
        "False Alarm",
        "Latency",
    ],
    "Localization": [
        "Ground Truth U",
        "Ground Truth V",
        "Estimated U",
        "Estimated V",
        "X Error",
        "Y Error",
        "Radial Error",
        "RMSE",
    ],
    "Tracking": [
        "Lock State",
        "Missed Frames",
        "Loss Duration",
        "Tracking Error",
        "Reacquisition",
    ],
    "Prediction": [
        "Horizon",
        "Predicted U",
        "Predicted V",
        "Actual U",
        "Actual V",
        "Prediction Error",
        "Sigma U",
        "Sigma V",
        "Mahalanobis Distance",
    ],
    "Filter": [
        "Innovation",
        "Innovation Covariance",
        "NIS",
        "Covariance Trace",
        "Rejected Measurement",
        "Outlier Count",
    ],
    "Camera / Control": [
        "Commanded Pan",
        "Actual Pan",
        "Commanded Tilt",
        "Actual Tilt",
        "Pan Error",
        "Tilt Error",
        "Saturation",
        "Delay",
        "FOV Violation",
    ],
    "Search": [
        "Search Duration",
        "Search Path Length",
        "Amplitude",
        "Orientation",
        "Coverage",
        "Acquisition",
        "Reacquisition",
    ],
    "Computation": [
        "Frame Latency",
        "Detection Latency",
        "Localization Latency",
        "Filter Latency",
        "Control Latency",
        "CPU",
        "RAM",
        "GPU",
        "Dropped Frames",
        "Deadline Misses",
    ],
}


def _value(data: Any, key: str, default: Any = None) -> Any:
    """Read a telemetry field from either a dataclass or a mapping."""

    if data is None:
        return default
    if isinstance(data, dict):
        return data.get(key, default)
    return getattr(data, key, default)


def _series(seed: int, count: int, center: float, amplitude: float, frequency: float, phase: float = 0.0) -> list[float]:
    """Return a deterministic, illustrative trigonometric curve."""

    rng = random.Random(seed)
    return [
        center
        + amplitude * math.sin(frequency * i + phase)
        + amplitude * 0.25 * math.cos(frequency * 0.37 * i + phase * 0.5)
        + rng.uniform(-amplitude * 0.035, amplitude * 0.035)
        for i in range(count)
    ]


def _xy_path(seed: int, count: int, cx: float, cy: float, ax: float, ay: float, fx: float, fy: float) -> tuple[list[float], list[float]]:
    """Build a seeded path used only as a visual placeholder."""

    rng = random.Random(seed)
    xs: list[float] = []
    ys: list[float] = []
    for i in range(count):
        t = i / max(1, count - 1) * math.tau * 2.2
        xs.append(cx + ax * math.sin(fx * t) + rng.uniform(-0.8, 0.8))
        ys.append(cy + ay * math.cos(fy * t + 0.4) + rng.uniform(-0.7, 0.7))
    return xs, ys


def _caption(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("class", "page-kicker")
    label.setWordWrap(True)
    label.setMinimumWidth(0)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return label


def _compact_combo(items: Iterable[str], minimum: int = 95) -> QComboBox:
    combo = QComboBox()
    combo.addItems(list(items))
    combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
    combo.setMinimumContentsLength(4)
    combo.setMinimumWidth(minimum)
    combo.setMaximumWidth(max(minimum, 220))
    combo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
    return combo


def _toolbar_scroll(widget: QWidget, height: int = 42) -> QScrollArea:
    widget.setMinimumWidth(0)
    widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
    area = QScrollArea()
    area.setWidget(widget)
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    area.setFixedHeight(height)
    area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return area


def _section(title: str, subtitle: str = "") -> QGroupBox:
    box = QGroupBox(title)
    box.setProperty("class", "section")
    if subtitle:
        box.setToolTip(subtitle)
    return box


def _read_only_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> QTableWidget:
    values = [list(row) for row in rows]
    table = QTableWidget(len(values), len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSortingEnabled(False)
    table.setMinimumWidth(0)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    table.horizontalHeader().setMinimumSectionSize(32)
    table.horizontalHeader().setDefaultSectionSize(64)
    table.verticalHeader().setDefaultSectionSize(25)
    table.setFont(QFont("Consolas", 9))
    for row_index, row in enumerate(values):
        for column_index, item in enumerate(row):
            table.setItem(row_index, column_index, QTableWidgetItem(str(item)))
    table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return table


class _ScientificPlot(QWidget):
    """Small PyQtGraph wrapper with a non-empty painter fallback."""

    def __init__(self, title: str, x_label: str = "sample", y_label: str = "value", minimum_height: int = 190, parent: QWidget | None = None):
        super().__init__(parent)
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self._series: list[tuple[str, list[float], list[float], str]] = []
        self.setMinimumHeight(minimum_height)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if pg is not None:
            self.plot_widget = pg.PlotWidget()
            self.plot = self.plot_widget
            self.plot_widget.setMinimumSize(120, minimum_height)
            self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.plot_widget.setBackground(CHARCOAL)
            self.plot_widget.showGrid(x=True, y=True, alpha=0.18)
            self.plot_widget.setTitle(f"{title}  ·  MOCK DATA", color="#c1d0d5", size="10pt")
            self.plot_widget.setLabel("bottom", x_label)
            self.plot_widget.setLabel("left", y_label)
            self.plot_widget.getAxis("left").setTextPen("#71848e")
            self.plot_widget.getAxis("bottom").setTextPen("#71848e")
            self.plot_widget.getAxis("left").setPen(GRID)
            self.plot_widget.getAxis("bottom").setPen(GRID)
            self.plot_widget.setMenuEnabled(False)
            self.plot_widget.hideButtons()
            self._legend = self.plot_widget.addLegend(
                offset=(10, 10), labelTextColor=TEXT,
                brush=pg.mkBrush(17, 24, 32, 205), pen=pg.mkPen(GRID),
            )
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.plot_widget)
        else:
            self.plot_widget = None
            self.plot = None
            self._legend = None
            self.setProperty("class", "plot-fallback")

    def set_axis_labels(self, x_label: str, y_label: str) -> None:
        self.x_label = x_label
        self.y_label = y_label
        if self.plot_widget is not None:
            self.plot_widget.setLabel("bottom", x_label)
            self.plot_widget.setLabel("left", y_label)

    def set_series(self, series: Iterable[tuple[str, Iterable[float], Iterable[float] | None, str]]) -> None:
        normalized: list[tuple[str, list[float], list[float], str]] = []
        for name, values, x_values, color in series:
            ys = list(values)
            xs = list(x_values) if x_values is not None else list(range(len(ys)))
            normalized.append((name, xs, ys, color))
        self._series = normalized
        if self.plot_widget is not None:
            self.plot_widget.clear()
            self._legend.clear()
            self.plot_widget.setTitle(f"{self.title}  ·  MOCK DATA", color="#c1d0d5", size="10pt")
            self.plot_widget.setLabel("bottom", self.x_label)
            self.plot_widget.setLabel("left", self.y_label)
            self.plot_widget.showGrid(x=True, y=True, alpha=0.18)
            for name, xs, ys, color in normalized:
                self.plot_widget.plot(xs, ys, pen=pg.mkPen(color, width=1.8), name=name, antialias=True)
            self.plot_widget.enableAutoRange()
        else:
            self.update()

    def set_values(self, values: Iterable[float], name: str = "mock signal", color: str = ACCENT, x_values: Iterable[float] | None = None) -> None:
        self.set_series([(name, list(values), x_values, color)])

    def paintEvent(self, event) -> None:  # pragma: no cover - fallback only
        if self.plot_widget is not None:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(CHARCOAL))
        painter.setPen(QPen(QColor(GRID), 1))
        for x in range(45, self.width(), 52):
            painter.drawLine(x, 28, x, self.height() - 28)
        for y in range(34, max(35, self.height() - 20), 32):
            painter.drawLine(40, y, self.width() - 10, y)
        painter.setPen(QColor("#c1d0d5"))
        painter.drawText(10, 17, f"{self.title}  ·  MOCK DATA")
        painter.setPen(QColor(MUTED))
        painter.drawText(self.width() // 2 - 25, self.height() - 7, self.x_label)
        if not self._series:
            return
        all_values = [value for _, _, values, _ in self._series for value in values]
        low = min(all_values)
        high = max(all_values)
        span = max(1e-9, high - low)
        width = max(1, self.width() - 58)
        height = max(1, self.height() - 56)
        for name, xs, values, color in self._series:
            if not values:
                continue
            painter.setPen(QPen(QColor(color), 2))
            points = [
                QPointF(45 + index * width / max(1, len(values) - 1), 28 + (high - value) * height / span)
                for index, value in enumerate(values)
            ]
            for first, second in zip(points, points[1:]):
                painter.drawLine(first, second)


class _FallbackSensorViewport(QWidget):
    """Local placeholder used only until the host viewport module is present."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.telemetry = None
        self.setMinimumSize(290, 220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_telemetry(self, data: Any) -> None:
        self.telemetry = data
        self.update()

    def paintEvent(self, event) -> None:  # pragma: no cover - simple fallback rendering
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#151c22"))
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#24353d"), 1))
        for x in range(0, self.width(), 32):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 32):
            painter.drawLine(0, y, self.width(), y)
        painter.setPen(QPen(QColor(ACCENT), 1))
        painter.drawRect(18, 18, max(1, self.width() - 36), max(1, self.height() - 36))
        painter.setPen(QColor("#91a9b2"))
        painter.drawText(28, 36, "CAMERA 01 / SENSOR")
        painter.drawText(28, 54, "DEMO VIEW · MOCK TELEMETRY")
        data = self.telemetry
        u = float(_value(data, "u", 320.0))
        v = float(_value(data, "v", 240.0))
        est_u = float(_value(data, "est_u", u + 2.0))
        est_v = float(_value(data, "est_v", v - 1.0))
        sx = self.width() / 640.0
        sy = self.height() / 480.0
        target = QPointF(u * sx, v * sy)
        estimate = QPointF(est_u * sx, est_v * sy)
        painter.setPen(QPen(QColor(GOLD), 2))
        painter.drawLine(target.x() - 8, target.y(), target.x() + 8, target.y())
        painter.drawLine(target.x(), target.y() - 8, target.x(), target.y() + 8)
        painter.setPen(QPen(QColor(ACCENT), 2))
        painter.drawEllipse(estimate, 5, 5)
        painter.setPen(QPen(QColor(ORANGE), 1, Qt.DashLine))
        painter.drawLine(target, estimate)


class _FallbackViewportPanel(QWidget):
    def __init__(self, title: str, mode: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.viewport = _FallbackSensorViewport(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.viewport)


class _ImagePreview(QWidget):
    """Dark illustrative frame used for original, processed, and ROI views."""

    def __init__(self, label: str, kind: str = "original", seed: int = 1, parent: QWidget | None = None):
        super().__init__(parent)
        self.label = label
        self.kind = kind
        self.seed = seed
        self.setMinimumSize(220, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event) -> None:  # pragma: no cover - rendering is visual
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#11191f"))
        rng = random.Random(self.seed)
        for _ in range(170):
            x = rng.randrange(max(1, self.width()))
            y = rng.randrange(max(1, self.height()))
            level = rng.randrange(23, 68) if self.kind == "original" else rng.randrange(28, 82)
            painter.setPen(QColor(level, level + 5, level + 8))
            painter.drawPoint(x, y)
        painter.setPen(QPen(QColor("#29414b"), 1))
        for x in range(0, self.width(), 28):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 28):
            painter.drawLine(0, y, self.width(), y)
        cx = self.width() * (0.53 if self.kind != "roi" else 0.5)
        cy = self.height() * (0.48 if self.kind != "roi" else 0.52)
        if self.kind == "processed":
            painter.setPen(QPen(QColor(ACCENT), 2))
            painter.drawEllipse(QPointF(cx, cy), 11, 8)
            painter.drawText(12, self.height() - 14, "THRESHOLD / CENTROID OVERLAY")
        elif self.kind == "roi":
            painter.setPen(QPen(QColor(PURPLE), 2))
            painter.drawRect(QRectF(cx - 46, cy - 36, 92, 72))
            painter.setPen(QPen(QColor(GOLD), 2))
            painter.drawLine(cx - 9, cy, cx + 9, cy)
            painter.drawLine(cx, cy - 9, cx, cy + 9)
            painter.drawText(12, self.height() - 14, "PREDICTED ROI / MOCK OVERLAY")
        else:
            painter.setPen(QPen(QColor(GOLD), 2))
            painter.drawLine(cx - 8, cy, cx + 8, cy)
            painter.drawLine(cx, cy - 8, cx, cy + 8)
            painter.drawText(12, self.height() - 14, "SENSOR FRAME / MOCK SIGNAL")
        painter.setPen(QColor("#b2c2c8"))
        painter.drawText(12, 20, self.label)


def _make_viewport(title: str = "CAMERA 01 / SENSOR", mode: str = "sensor", parent: QWidget | None = None) -> QWidget:
    if _ExternalViewportPanel is not None:
        try:
            return _ExternalViewportPanel(title=title, mode=mode, parent=parent)
        except Exception:
            pass
    return _FallbackViewportPanel(title=title, mode=mode, parent=parent)


class _EstimatorDiagram(QWidget):
    """Painter diagram for measurement, filtered state, and uncertainty."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumSize(260, 160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.measurements = _series(12, 34, 0.0, 18.0, 0.42)
        self.filtered = _series(31, 34, 0.0, 11.0, 0.35, 0.3)

    def paintEvent(self, event) -> None:  # pragma: no cover - rendering is visual
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(CHARCOAL))
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(GRID), 1))
        for x in range(38, self.width(), 42):
            painter.drawLine(x, 30, x, self.height() - 27)
        for y in range(34, self.height() - 20, 28):
            painter.drawLine(34, y, self.width() - 12, y)
        painter.setPen(QColor("#c1d0d5"))
        painter.drawText(10, 18, "MEASUREMENT → FILTER / UNCERTAINTY · MOCK")
        if not self.measurements:
            return
        low = min(self.measurements + self.filtered) - 4
        high = max(self.measurements + self.filtered) + 4
        span = max(1, high - low)
        width = max(1, self.width() - 50)
        height = max(1, self.height() - 62)

        def point(index: int, value: float) -> QPointF:
            return QPointF(38 + index * width / max(1, len(self.measurements) - 1), 30 + (high - value) * height / span)

        painter.setPen(QPen(QColor(GOLD), 1))
        for index, value in enumerate(self.measurements):
            p = point(index, value)
            painter.drawEllipse(p, 2.2, 2.2)
        painter.setPen(QPen(QColor(ACCENT), 2))
        filtered_points = [point(index, value) for index, value in enumerate(self.filtered)]
        for first, second in zip(filtered_points, filtered_points[1:]):
            painter.drawLine(first, second)
        painter.setPen(QPen(QColor(PURPLE), 1, Qt.DashLine))
        for index, value in enumerate(self.filtered):
            p = point(index, value)
            painter.drawEllipse(p, 9 + 2 * math.sin(index * 0.3), 6 + math.cos(index * 0.22))
        painter.setPen(QColor(GOLD))
        painter.drawText(42, self.height() - 9, "measurement")
        painter.setPen(QColor(ACCENT))
        painter.drawText(132, self.height() - 9, "filtered state")


class _SearchDiagram(QWidget):
    """Illustrative oriented covariance ellipse and search path."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumSize(280, 190)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.path = _xy_path(73, 160, 0.0, 0.0, 74.0, 48.0, 1.15, 1.45)

    def paintEvent(self, event) -> None:  # pragma: no cover - rendering is visual
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(CHARCOAL))
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(GRID), 1))
        for x in range(0, self.width(), 32):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 32):
            painter.drawLine(0, y, self.width(), y)
        cx = self.width() * 0.5
        cy = self.height() * 0.53
        painter.setPen(QColor("#c1d0d5"))
        painter.drawText(12, 19, "2σ UNCERTAINTY ELLIPSE / SEARCH PATH · MOCK")
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(18)
        painter.setPen(QPen(QColor(PURPLE), 2))
        painter.drawEllipse(QRectF(-82, -51, 164, 102))
        painter.setPen(QPen(QColor("#765fa9"), 1, Qt.DashLine))
        painter.drawEllipse(QRectF(-52, -32, 104, 64))
        painter.restore()
        points = [QPointF(cx + x, cy + y) for x, y in zip(*self.path)]
        painter.setPen(QPen(QColor(ORANGE), 2))
        for first, second in zip(points, points[1:]):
            painter.drawLine(first, second)
        painter.setPen(QPen(QColor(ACCENT), 2))
        painter.drawEllipse(QPointF(cx, cy), 4, 4)
        painter.setPen(QColor(PURPLE))
        painter.drawText(12, self.height() - 12, "oriented covariance")
        painter.setPen(QColor(ORANGE))
        painter.drawText(142, self.height() - 12, "adaptive sweep")


class _PipelineButton(QToolButton):
    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setToolTip(f"Open {text} workspace view")
        self.setMinimumWidth(108)


class TrackingWorkspace(QWidget):
    """Pipeline-oriented tracking workspace with mock scientific views."""

    selected = Signal(str)
    notification = Signal(str)

    PIPELINE_STAGES = (
        "Camera Frame",
        "Preprocessing",
        "Detection",
        "Candidate Filter",
        "Localization",
        "Kalman Filter",
        "Prediction",
        "Adaptive Search",
    )
    CANONICAL_COMPONENTS = (
        "Detector",
        "Preprocessing",
        "Candidate Filter",
        "Localization",
        "ROI",
        "Kalman Filter",
        "Prediction",
        "Adaptive Search",
    )
    STAGE_COMPONENT = {
        "Camera Frame": "Detector",
        "Preprocessing": "Preprocessing",
        "Detection": "Detector",
        "Candidate Filter": "Candidate Filter",
        "Localization": "Localization",
        "Kalman Filter": "Kalman Filter",
        "Prediction": "Prediction",
        "Adaptive Search": "Adaptive Search",
        "Detector": "Detector",
        "ROI": "ROI",
    }

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._telemetry = None
        self.selected_component = "Detector"
        self.selected_stage = "Camera Frame"
        self.stage_buttons: dict[str, _PipelineButton] = {}
        self._component_pages: dict[str, QWidget] = {}
        self._build_ui()
        self.select_stage("Camera Frame")

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("TRACKING WORKSPACE")
        title.setProperty("class", "section-title")
        header.addWidget(title)
        header.addWidget(_caption("PIPELINE INSPECTION  /  MOCK SIGNAL PATH"))
        header.addStretch(1)
        self.inspector_status = QLabel("INSPECTOR: Detector")
        self.inspector_status.setProperty("class", "status-pill")
        header.addWidget(self.inspector_status)
        root.addLayout(header)

        pipeline_scroll = QScrollArea()
        pipeline_scroll.setWidgetResizable(True)
        pipeline_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        pipeline_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pipeline_scroll.setFrameShape(QFrame.NoFrame)
        pipeline_host = QWidget()
        pipeline = QHBoxLayout(pipeline_host)
        pipeline.setContentsMargins(0, 0, 0, 0)
        pipeline.setSpacing(3)
        for index, stage in enumerate(self.PIPELINE_STAGES):
            if index:
                arrow = QLabel("›")
                arrow.setAlignment(Qt.AlignCenter)
                arrow.setProperty("class", "page-kicker")
                pipeline.addWidget(arrow)
            button = _PipelineButton(stage)
            button.clicked.connect(lambda checked=False, name=stage: self.select_stage(name))
            self.stage_buttons[stage] = button
            pipeline.addWidget(button)
        pipeline.addStretch(1)
        pipeline_scroll.setWidget(pipeline_host)
        self.pipeline_scroll = pipeline_scroll
        self.pipeline_buttons = self.stage_buttons
        root.addWidget(pipeline_scroll)

        body = QSplitter(Qt.Horizontal)
        body.setChildrenCollapsible(False)
        self.visual_stack = QStackedWidget()
        self._build_component_pages()
        for component in ("Detector", "Preprocessing", "Candidate Filter", "Localization", "ROI", "Kalman Filter", "Prediction", "Adaptive Search"):
            self.visual_stack.addWidget(self._component_pages[component])

        visual_panel = QWidget()
        visual_layout = QVBoxLayout(visual_panel)
        visual_layout.setContentsMargins(0, 0, 5, 0)
        self.visual_heading = QLabel("CAMERA FRAME / DETECTOR")
        self.visual_heading.setProperty("class", "section-title")
        visual_layout.addWidget(self.visual_heading)
        visual_layout.addWidget(self.visual_stack, 1)
        self.main_visual = self.visual_stack
        body.addWidget(visual_panel)

        inspector = self._build_inspector()
        self.inspector = inspector
        body.addWidget(inspector)
        body.setStretchFactor(0, 4)
        body.setStretchFactor(1, 1)
        body.setSizes([900, 270])
        root.addWidget(body, 1)

    def _build_component_pages(self) -> None:
        self._component_pages["Detector"] = self._build_detector_page()
        self._component_pages["Preprocessing"] = self._build_preprocessing_page()
        self._component_pages["Candidate Filter"] = self._build_candidate_page()
        self._component_pages["Localization"] = self._build_localization_page()
        self._component_pages["ROI"] = self._build_roi_page()
        self._component_pages["Kalman Filter"] = self._build_estimator_page()
        self._component_pages["Prediction"] = self._build_prediction_page()
        self._component_pages["Adaptive Search"] = self._build_search_page()

    def _build_detector_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        views = QSplitter(Qt.Horizontal)
        sensor = _make_viewport("CAMERA 01 / SENSOR", "sensor", page)
        self.sensor_viewport_panel = sensor
        processed = _make_viewport("CAMERA 01 / PROCESSED", "processed", page)
        self.processed_viewport_panel = processed
        views.addWidget(sensor)
        views.addWidget(processed)
        views.setStretchFactor(0, 1)
        views.setStretchFactor(1, 1)
        views.setMinimumHeight(220)
        layout.addWidget(views, 2)
        table_box = _section("DETECTION CANDIDATES", "Original and processed views are illustrative.")
        table_layout = QVBoxLayout(table_box)
        table_layout.setContentsMargins(8, 8, 8, 8)
        table_layout.addWidget(_caption("MOCK CANDIDATE TABLE  /  THRESHOLD AND SCORE VALUES ARE DISPLAY ONLY"))
        rows = [
            ("C-01", "321.4", "219.2", "84", "0.94", "0.91", "SELECTED"),
            ("C-02", "276.8", "241.7", "38", "0.71", "0.52", "REJECTED"),
            ("C-03", "418.2", "188.6", "24", "0.58", "0.35", "REJECTED"),
            ("C-04", "152.1", "309.4", "19", "0.46", "0.21", "REJECTED"),
        ]
        self.candidate_table = _read_only_table(["ID", "U (px)", "V (px)", "AREA", "PEAK", "SCORE", "STATUS"], rows)
        self.candidate_table.setMaximumHeight(175)
        table_layout.addWidget(self.candidate_table)
        layout.addWidget(table_box, 1)
        return page

    def _build_preprocessing_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        views = QSplitter(Qt.Horizontal)
        views.addWidget(_ImagePreview("ORIGINAL SENSOR FRAME", "original", 9, page))
        views.addWidget(_ImagePreview("PREPROCESSED FRAME", "processed", 17, page))
        layout.addWidget(views, 2)
        profile = _ScientificPlot("PREPROCESSING INTENSITY PROFILE", "pixel index", "normalized intensity", 190, page)
        profile.set_values(_series(41, 96, 0.42, 0.22, 0.16), "before / after mock", ACCENT)
        layout.addWidget(profile, 1)
        return page

    def _build_candidate_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        split = QSplitter(Qt.Horizontal)
        plot = _ScientificPlot("CANDIDATE SCORE SPACE", "candidate index", "score", 240, page)
        plot.set_series([
            ("candidate score", _series(50, 22, 0.55, 0.30, 0.31), None, GOLD),
            ("threshold", [0.68] * 22, None, ORANGE),
        ])
        table = _read_only_table(
            ["Candidate", "Area", "Compactness", "Prediction Δ", "Decision"],
            [
                ("C-01", "84 px²", "0.88", "2.4 px", "KEEP"),
                ("C-02", "38 px²", "0.64", "18.1 px", "DROP"),
                ("C-03", "24 px²", "0.71", "31.7 px", "DROP"),
                ("C-04", "19 px²", "0.52", "42.3 px", "DROP"),
            ],
        )
        split.addWidget(plot)
        split.addWidget(table)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 1)
        layout.addWidget(_caption("CANDIDATE FILTER / MOCK RANKING WITH DETERMINISTIC DISPLAY CURVES"))
        layout.addWidget(split, 1)
        return page

    def _build_localization_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        split = QSplitter(Qt.Horizontal)
        localization_roi = _make_viewport("CAMERA 01 / ROI", "roi", page)
        self.localization_roi_viewport = localization_roi
        split.addWidget(localization_roi)
        comparison = _ScientificPlot("LOCALIZATION METHOD COMPARISON", "method", "error (px)", 220, page)
        comparison.set_series([
            ("binary centroid", [1.85, 1.72, 1.94, 1.82, 1.77], list(range(5)), GOLD),
            ("weighted centroid", [0.78, 0.74, 0.81, 0.69, 0.75], list(range(5)), ACCENT),
            ("Gaussian fit", [0.51, 0.46, 0.49, 0.44, 0.48], list(range(5)), PURPLE),
        ])
        split.addWidget(comparison)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        layout.addWidget(split, 2)
        detail = _read_only_table(
            ["Method", "Bias U", "Bias V", "1σ U", "1σ V", "Runtime"],
            [
                ("Binary Centroid", "+0.21 px", "−0.14 px", "1.22", "1.18", "0.4 ms"),
                ("Weighted Centroid", "+0.08 px", "−0.05 px", "0.64", "0.59", "0.7 ms"),
                ("Gaussian Fit", "+0.03 px", "−0.02 px", "0.42", "0.39", "3.2 ms"),
            ],
        )
        detail.setMaximumHeight(160)
        layout.addWidget(detail, 1)
        return page

    def _build_roi_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        split = QSplitter(Qt.Horizontal)
        roi_viewport = _make_viewport("CAMERA 01 / ROI", "roi", page)
        self.roi_viewport_panel = roi_viewport
        split.addWidget(roi_viewport)
        roi_plot = _ScientificPlot("ROI WINDOW / LOCAL SIGNAL", "pixel offset (px)", "normalized intensity", 220, page)
        roi_plot.set_series([
            ("ROI profile", _series(67, 80, 0.31, 0.25, 0.19), None, ACCENT),
            ("ROI boundary", [0.52] * 80, None, PURPLE),
        ])
        split.addWidget(roi_plot)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        layout.addWidget(split, 1)
        layout.addWidget(_caption("ROI SIZE 21 × 21 PX  /  PREDICTED WINDOW  /  MOCK OVERLAY"))
        return page

    def _build_estimator_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        diagram = _EstimatorDiagram(page)
        layout.addWidget(diagram, 2)
        state_plot = _ScientificPlot("MEASUREMENT / FILTERED STATE", "frame", "position (px)", 175, page)
        state_plot.set_series([
            ("measurement", _series(81, 64, 320, 7.2, 0.23), None, GOLD),
            ("filtered", _series(83, 64, 320, 4.6, 0.20, 0.2), None, ACCENT),
        ])
        layout.addWidget(state_plot, 1)
        return page

    def _build_prediction_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        horizon = _ScientificPlot("PREDICTION HORIZON", "horizon (s)", "position (px)", 270, page)
        xs = [i * 0.1 for i in range(61)]
        measured = [320 + 18 * math.sin(x * 0.9) for x in xs]
        predicted = [320 + 18 * math.sin((x + 0.12) * 0.9) for x in xs]
        sigma = [2.0 + x * 0.65 for x in xs]
        horizon.set_series([
            ("filtered position", measured, xs, ACCENT),
            ("predicted position", predicted, xs, ORANGE),
            ("+2σ", [y + s for y, s in zip(predicted, sigma)], xs, PURPLE),
            ("−2σ", [y - s for y, s in zip(predicted, sigma)], xs, PURPLE),
        ])
        layout.addWidget(horizon, 1)
        layout.addWidget(_caption("5 S HORIZON  /  UNCERTAINTY BOUNDS ARE ILLUSTRATIVE, NOT A LIVE FORECAST"))
        return page

    def _build_search_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        search_split = QSplitter(Qt.Horizontal)
        scene = _make_viewport("CAMERA 01 / SEARCH SCENE", "scene", page)
        self.search_scene_viewport = scene
        search_split.addWidget(scene)
        search_split.addWidget(_SearchDiagram(page))
        search_split.setStretchFactor(0, 1)
        search_split.setStretchFactor(1, 1)
        layout.addWidget(search_split, 2)
        path_plot = _ScientificPlot("ADAPTIVE SEARCH COVERAGE", "time (s)", "offset (px)", 175, page)
        xs = [i / 20.0 for i in range(100)]
        path_plot.set_series([
            ("search u", [24 * math.sin(x * 1.15) for x in xs], xs, ORANGE),
            ("search v", [18 * math.cos(x * 0.92 + 0.4) for x in xs], xs, ACCENT),
        ])
        layout.addWidget(path_plot, 1)
        return page

    def _build_inspector(self) -> QWidget:
        panel = QGroupBox("PIPELINE INSPECTOR")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 12, 10, 10)
        self.inspector_component = QLabel("Detector")
        self.inspector_component.setProperty("class", "section-title")
        layout.addWidget(self.inspector_component)
        layout.addWidget(_caption("CANONICAL COMPONENT"))
        self.inspector_stack = QStackedWidget()
        for component in self.CANONICAL_COMPONENTS:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 12, 0, 0)
            page_layout.addWidget(QLabel("STATUS"))
            status = QLabel("MOCK VIEW READY")
            status.setProperty("class", "status-pill")
            page_layout.addWidget(status)
            page_layout.addSpacing(8)
            details = {
                "Detector": "Original / processed frame and candidate extraction.",
                "Preprocessing": "Display-only intensity conditioning preview.",
                "Candidate Filter": "Ranked candidate table and threshold cue.",
                "Localization": "ROI comparison of illustrative methods.",
                "ROI": "Predicted window and local signal profile.",
                "Kalman Filter": "Measurement, filtered state, and uncertainty.",
                "Prediction": "Horizon curve with illustrative bounds.",
                "Adaptive Search": "Oriented ellipse and sweep path.",
            }
            page_layout.addWidget(QLabel(details[component]))
            page_layout.addStretch(1)
            self.inspector_stack.addWidget(page)
        layout.addWidget(self.inspector_stack, 1)
        roi_button = QPushButton("OPEN ROI COMPONENT")
        roi_button.clicked.connect(lambda: self.select_stage("ROI"))
        layout.addWidget(roi_button)
        layout.addWidget(_caption("No backend command is issued from this inspector."))
        panel.setMinimumWidth(220)
        panel.setMaximumWidth(360)
        return panel

    def select_stage(self, name: str) -> None:
        """Select a pipeline or canonical component and notify the host."""

        if name not in self.STAGE_COMPONENT:
            return
        component = self.STAGE_COMPONENT[name]
        self.selected_stage = name
        self.selected_component = component
        for stage, button in self.stage_buttons.items():
            button.setChecked(stage == name)
        self.inspector_component.setText(component)
        self.inspector_status.setText(f"INSPECTOR: {component}")
        self.inspector_stack.setCurrentIndex(self.CANONICAL_COMPONENTS.index(component))
        page = self._component_pages.get(component)
        if page is not None:
            self.visual_stack.setCurrentWidget(page)
        heading = {
            "Camera Frame": "CAMERA FRAME / DETECTOR",
            "Detection": "DETECTION / ORIGINAL + PROCESSED",
            "ROI": "ROI / PREDICTED WINDOW",
            "Kalman Filter": "KALMAN FILTER / ESTIMATOR",
            "Adaptive Search": "ADAPTIVE SEARCH / UNCERTAINTY",
        }.get(name, name.upper())
        self.visual_heading.setText(heading)
        self.selected.emit(component)

    def update_telemetry(self, data: Any) -> None:
        """Forward optional telemetry to any compatible viewport child."""

        self._telemetry = data
        for widget in self.findChildren(QWidget):
            viewport = getattr(widget, "viewport", None)
            setter = getattr(viewport, "set_telemetry", None)
            if callable(setter):
                setter(data)
            elif callable(getattr(widget, "set_telemetry", None)) and widget is not self:
                widget.set_telemetry(data)


class _MetricChip(QFrame):
    def __init__(self, name: str, value: str, unit: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "metric")
        self.setMinimumWidth(112)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(1)
        self.name_label = QLabel(name.upper())
        self.name_label.setProperty("class", "metric-title")
        self.value_label = QLabel(f"{value} {unit}".strip())
        self.value_label.setProperty("class", "metric-value")
        layout.addWidget(self.name_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: Any, unit: str = "") -> None:
        self.value_label.setText(f"{value} {unit}".strip())


class AnalysisWorkspace(QWidget):
    """Selectable performance chart workspace with compact metrics and filters."""

    notification = Signal(str)
    CHART_TITLES = tuple(ANALYSIS_CHART_TITLES)
    METRIC_NAMES = tuple(name for name, _, _ in PERFORMANCE_METRICS)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._chart_definitions = self._make_chart_definitions()
        self.metric_widgets: dict[str, _MetricChip] = {}
        self._build_ui()
        self.metrics = self.metric_widgets
        self._apply_chart(ANALYSIS_CHART_TITLES[0])

    def _make_chart_definitions(self) -> dict[str, dict[str, Any]]:
        definitions: dict[str, dict[str, Any]] = {}
        for index, title in enumerate(ANALYSIS_CHART_TITLES):
            n = 36 if index < 3 else 12
            x = list(range(n))
            if title == "Error Timeline":
                x = [i * 0.25 for i in range(80)]
                ys = [abs(2.7 + 1.7 * math.sin(i * 0.17) + 0.55 * math.cos(i * 0.47)) for i in range(80)]
                series = [("radial error", ys, x, ORANGE)]
                labels = ("time (s)", "error (px)")
            elif title == "Error Histogram":
                x = [0.25 * i for i in range(16)]
                ys = [4 + int(22 * math.exp(-((value - 2.4) ** 2) / 2.7)) for value in x]
                series = [("sample count", ys, x, GOLD)]
                labels = ("error bin (px)", "count")
            elif title == "Error CDF":
                x = [0.2 * i for i in range(31)]
                ys = [min(1.0, 1 - math.exp(-value / 2.6)) for value in x]
                series = [("empirical CDF", ys, x, ACCENT)]
                labels = ("error (px)", "cumulative probability")
            elif title == "RMSE vs SNR":
                x = [5 + i * 2.5 for i in range(11)]
                series = [("centroid RMSE", [6.5 / math.sqrt(1 + value / 4) + 0.22 for value in x], x, ACCENT)]
                labels = ("SNR (dB)", "RMSE (px)")
            elif title == "Background vs RMSE":
                x = [i / 10 for i in range(11)]
                series = [("centroid RMSE", [2.3 + 5.2 * value * value for value in x], x, ORANGE)]
                labels = ("background level", "RMSE (px)")
            elif title == "PSF Width vs RMSE":
                x = [0.5 + i * 0.25 for i in range(11)]
                series = [("localization RMSE", [0.34 + 0.22 * (value - 1.5) ** 2 for value in x], x, PURPLE)]
                labels = ("PSF width (px)", "RMSE (px)")
            elif title == "Detection vs SNR":
                x = [0 + i * 3 for i in range(11)]
                series = [("detection probability", [0.58 + 0.41 / (1 + math.exp(-(value - 12) / 4)) for value in x], x, ACCENT)]
                labels = ("SNR (dB)", "probability")
            elif title == "False Alarm vs SNR":
                x = [0 + i * 3 for i in range(11)]
                series = [("false alarm probability", [0.22 * math.exp(-value / 10) + 0.006 for value in x], x, ORANGE)]
                labels = ("SNR (dB)", "probability")
            elif title == "FPS vs Resolution":
                x = [320, 480, 640, 800, 960, 1280]
                series = [("throughput", [91, 78, 60, 51, 43, 31], x, BLUE)]
                labels = ("resolution (px)", "FPS")
            elif title == "FPS vs Noise":
                x = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
                series = [("throughput", [62, 61, 60, 59, 57, 53], x, BLUE)]
                labels = ("noise sigma", "FPS")
            elif title == "Prediction Error vs Horizon":
                x = [0.5 + i * 0.5 for i in range(10)]
                series = [("prediction RMSE", [2.2 + 1.8 * value ** 1.18 for value in x], x, ORANGE)]
                labels = ("horizon (s)", "error (px)")
            elif title == "Lock Retention vs Velocity":
                x = [i * 2 for i in range(9)]
                series = [("lock retention", [99.2 - 0.23 * value ** 1.45 for value in x], x, ACCENT)]
                labels = ("velocity (px/s)", "retention (%)")
            elif title == "Acquisition vs Uncertainty":
                x = [1 + i * 1.5 for i in range(9)]
                series = [("acquisition time", [0.38 + 0.11 * value ** 1.2 for value in x], x, GOLD)]
                labels = ("uncertainty (px)", "time (s)")
            else:  # Fixed EAL vs Adaptive EAL
                x = [0.5 + i * 0.5 for i in range(10)]
                series = [
                    ("fixed EAL", [4.3 + 1.35 * value for value in x], x, ORANGE),
                    ("adaptive EAL", [3.6 + 0.68 * value for value in x], x, ACCENT),
                ]
                labels = ("horizon (s)", "error (px)")
            definitions[title] = {"x": x, "series": series, "labels": labels}
        return definitions

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)
        header = QHBoxLayout()
        title = QLabel("PERFORMANCE ANALYSIS")
        title.setProperty("class", "section-title")
        header.addWidget(title)
        header.addWidget(_caption("SELECTABLE CURVES  /  MOCK RESULTS"))
        header.addStretch(1)
        self.chart_dropdown = _compact_combo(ANALYSIS_CHART_TITLES, 170)
        self.chart_selector = self.chart_dropdown
        self.chart_combo = self.chart_dropdown
        self.chart_dropdown.currentTextChanged.connect(self._apply_chart)
        header.addWidget(QLabel("CHART"))
        header.addWidget(self.chart_dropdown)
        root.addLayout(header)

        metric_scroll = QScrollArea()
        metric_scroll.setWidgetResizable(True)
        metric_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        metric_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        metric_scroll.setFrameShape(QFrame.NoFrame)
        metric_host = QWidget()
        metric_host.setMinimumWidth(0)
        metric_host.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        metric_layout = QHBoxLayout(metric_host)
        metric_layout.setContentsMargins(0, 0, 0, 0)
        metric_layout.setSpacing(5)
        for name, value, unit in PERFORMANCE_METRICS:
            chip = _MetricChip(name, value, unit, metric_host)
            self.metric_widgets[name] = chip
            metric_layout.addWidget(chip)
        metric_layout.addStretch(1)
        metric_scroll.setWidget(metric_host)
        metric_scroll.setFixedHeight(72)
        root.addWidget(metric_scroll)

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(QLabel("WINDOW"))
        self.dataset_filter = _compact_combo(["Full window", "First half", "Second half"])
        controls_layout.addWidget(self.dataset_filter)
        controls_layout.addWidget(QLabel("TRACES"))
        self.signal_filter = _compact_combo(["All traces", "Primary trace"])
        controls_layout.addWidget(self.signal_filter)
        controls_layout.addWidget(QLabel("SAMPLES"))
        self.aggregation_filter = _compact_combo(["All samples", "Every 2nd sample", "Every 4th sample"])
        controls_layout.addWidget(self.aggregation_filter)
        self.uncertainty_check = QCheckBox("Uncertainty cue")
        self.uncertainty_check.setChecked(True)
        controls_layout.addWidget(self.uncertainty_check)
        controls_layout.addStretch(1)
        self.filter_status = _caption("FULL WINDOW / ALL TRACES · DISPLAY FILTERS ONLY")
        for control in (self.dataset_filter, self.signal_filter, self.aggregation_filter):
            control.currentTextChanged.connect(self._filters_changed)
        self.uncertainty_check.toggled.connect(self._filters_changed)
        root.addWidget(_toolbar_scroll(controls, 46))

        chart_split = QSplitter(Qt.Vertical)
        self.main_plot = _ScientificPlot("Error Timeline", "time (s)", "error (px)", 240, self)
        chart_split.addWidget(self.main_plot)
        secondary_split = QSplitter(Qt.Horizontal)
        self.secondary_error_plot = _ScientificPlot("ERROR DISTRIBUTION", "error (px)", "count", 145, self)
        self.secondary_error_plot.set_series([("error distribution", [3, 8, 16, 21, 18, 10, 5, 2], list(range(8)), ORANGE)])
        self.secondary_latency_plot = _ScientificPlot("LATENCY PROFILE", "frame", "latency (ms)", 145, self)
        self.secondary_latency_plot.set_series([("mean", _series(92, 50, 18.2, 2.1, 0.21), None, ACCENT), ("p95 cue", [23.8] * 50, None, PURPLE)])
        secondary_split.addWidget(self.secondary_error_plot)
        secondary_split.addWidget(self.secondary_latency_plot)
        chart_split.addWidget(secondary_split)
        chart_split.setStretchFactor(0, 3)
        chart_split.setStretchFactor(1, 2)
        root.addWidget(chart_split, 1)
        root.addWidget(self.filter_status)

    def _apply_chart(self, title: str) -> None:
        definition = self._chart_definitions.get(title)
        if definition is None or not hasattr(self, "main_plot"):
            return
        series = []
        dataset = getattr(self, "dataset_filter", None)
        dataset_name = dataset.currentText() if dataset else "Full window"
        traces = definition["series"]
        if self.signal_filter.currentIndex() == 1:
            traces = traces[:1]
        for name, values, xs, color in traces:
            values = list(values)
            xs = list(xs)
            midpoint = max(2, len(values) // 2)
            if dataset_name == "First half":
                values, xs = values[:midpoint], xs[:midpoint]
            elif dataset_name == "Second half":
                values, xs = values[midpoint:], xs[midpoint:]
            step = (1, 2, 4)[self.aggregation_filter.currentIndex()]
            if len(values) // step >= 2:
                values, xs = values[::step], xs[::step]
            series.append((name, values, xs, color))
            if getattr(self, "uncertainty_check", None) and self.uncertainty_check.isChecked() and len(values) > 6 and title in ("Error Timeline", "Prediction Error vs Horizon"):
                spread = [0.35 + 0.02 * i for i in range(len(values))]
                series.append(("illustrative +σ", [v + s for v, s in zip(values, spread)], xs, PURPLE))
                series.append(("illustrative −σ", [v - s for v, s in zip(values, spread)], xs, PURPLE))
        self.main_plot.title = title
        self.main_plot.set_axis_labels(*definition["labels"])
        self.main_plot.set_series(series)

    def _filters_changed(self, checked: Any = None) -> None:
        dataset = self.dataset_filter.currentText()
        signal = self.signal_filter.currentText()
        aggregation = self.aggregation_filter.currentText()
        self.filter_status.setText(f"{dataset.upper()}  /  {signal.upper()}  /  {aggregation.upper()} · MOCK DATA")
        self._apply_chart(self.chart_dropdown.currentText())
        self.notification.emit(f"Analysis view: {dataset}; {signal}; {aggregation}")

    def update_telemetry(self, data: Any) -> None:
        fps = _value(data, "fps")
        latency = _value(data, "latency")
        if fps is not None and "FPS" in self.metric_widgets:
            self.metric_widgets["FPS"].set_value(f"{float(fps):.1f}")
        if latency is not None and "Mean Latency" in self.metric_widgets:
            self.metric_widgets["Mean Latency"].set_value(f"{float(latency):.1f}", "ms")


class _VideoPreview(QWidget):
    """Placeholder video surface with deterministic frame-to-frame motion."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.frame = 0
        self.setMinimumSize(400, 260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_frame(self, frame: int) -> None:
        self.frame = max(0, int(frame))
        self.update()

    def paintEvent(self, event) -> None:  # pragma: no cover - rendering is visual
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#151c22"))
        painter.setRenderHint(QPainter.Antialiasing)
        rng = random.Random(110 + self.frame // 9)
        for _ in range(240):
            x = rng.randrange(max(1, self.width()))
            y = rng.randrange(max(1, self.height()))
            level = rng.randrange(22, 62)
            painter.setPen(QColor(level, level + 3, level + 8))
            painter.drawPoint(x, y)
        painter.setPen(QPen(QColor("#28434d"), 1))
        for x in range(0, self.width(), 36):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 36):
            painter.drawLine(0, y, self.width(), y)
        cx = self.width() * 0.5 + math.sin(self.frame * 0.08) * self.width() * 0.18
        cy = self.height() * 0.52 + math.cos(self.frame * 0.06) * self.height() * 0.14
        painter.setPen(QPen(QColor(GOLD), 2))
        painter.drawLine(cx - 9, cy, cx + 9, cy)
        painter.drawLine(cx, cy - 9, cx, cy + 9)
        painter.setPen(QPen(QColor(ORANGE), 1, Qt.DashLine))
        painter.drawEllipse(QPointF(cx, cy), 26 + 3 * math.sin(self.frame * 0.04), 18 + 2 * math.cos(self.frame * 0.05))
        painter.setPen(QColor("#c1d0d5"))
        painter.drawText(18, 26, "DEMO VIDEO PREVIEW · NO DECODER CONNECTED")
        painter.drawText(18, 45, f"PLACEHOLDER FRAME {self.frame:05d}")
        painter.drawText(18, self.height() - 16, "GROUND TRUTH UNAVAILABLE")


class BenchmarkWorkspace(QWidget):
    """Video replay shell; browse and playback are UI-only demonstration actions."""

    notification = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._selected_file = ""
        self._playing = False
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)
        header = QHBoxLayout()
        title = QLabel("VIDEO BENCHMARK")
        title.setProperty("class", "page-title")
        header.addWidget(title)
        header.addWidget(_caption("REPLAY SHELL  /  DEMO METADATA  /  GROUND TRUTH STATUS"))
        header.addStretch(1)
        self.run_status = QLabel("DEMO READY")
        self.run_status.setProperty("class", "status-pill")
        header.addWidget(self.run_status)
        root.addLayout(header)

        source = _section("VIDEO INPUT")
        source_layout = QGridLayout(source)
        source_layout.setContentsMargins(8, 8, 8, 8)
        source_layout.addWidget(QLabel("Selected file"), 0, 0)
        self.file_edit = QLineEdit("DEMO PLACEHOLDER / no file selected")
        self.file_edit.setReadOnly(True)
        source_layout.addWidget(self.file_edit, 0, 1, 1, 3)
        self.browse_button = QPushButton("BROWSE…")
        self.browse_button.clicked.connect(self._browse)
        source_layout.addWidget(self.browse_button, 0, 4)
        self.metadata_labels: dict[str, QLabel] = {}
        for column, (name, value) in enumerate(
            [("Resolution", "unknown"), ("FPS", "unknown"), ("Frames", "unknown"), ("Duration", "unknown")]
        ):
            source_layout.addWidget(QLabel(name), 1, column * 2)
            label = QLabel(value)
            label.setProperty("class", "telemetry-item")
            self.metadata_labels[name] = label
            source_layout.addWidget(label, 1, column * 2 + 1)
        source_layout.setColumnStretch(1, 1)
        source_layout.setColumnStretch(3, 1)
        source_layout.setColumnStretch(5, 1)
        source_layout.setColumnStretch(7, 1)
        root.addWidget(source)

        body = QSplitter(Qt.Horizontal)
        preview_box = _section("VIDEO PREVIEW")
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        self.preview = _VideoPreview(preview_box)
        self.video_preview = self.preview
        preview_layout.addWidget(self.preview, 1)
        timeline = QHBoxLayout()
        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setRange(0, 300)
        self.timeline_slider = self.timeline
        self.timeline.valueChanged.connect(self._timeline_changed)
        timeline.addWidget(self.timeline, 1)
        self.frame_label = QLabel("FRAME 00000 / DEMO")
        timeline.addWidget(self.frame_label)
        preview_layout.addLayout(timeline)
        playback = QHBoxLayout()
        self.play_button = QPushButton("PLAY ▶")
        self.pause_button = QPushButton("PAUSE")
        self.play_button.clicked.connect(self.play)
        self.pause_button.clicked.connect(self.pause)
        playback.addWidget(self.play_button)
        playback.addWidget(self.pause_button)
        playback.addStretch(1)
        playback.addWidget(_caption("PLACEHOLDER FRAMES ONLY"))
        preview_layout.addLayout(playback)
        body.addWidget(preview_box)

        metadata_box = _section("DEMO METADATA")
        metadata_layout = QVBoxLayout(metadata_box)
        metadata_layout.setContentsMargins(8, 8, 8, 8)
        metadata_layout.addWidget(_caption("FILE PROPERTIES ARE UNKNOWN UNTIL A REAL DECODER IS CONNECTED"))
        self.metadata_note = QLabel("DEMO / UNKNOWN\nGround truth: GROUND TRUTH UNAVAILABLE")
        self.metadata_note.setProperty("class", "telemetry-item")
        metadata_layout.addWidget(self.metadata_note)
        metadata_layout.addStretch(1)
        body.addWidget(metadata_box)
        body.setStretchFactor(0, 3)
        body.setStretchFactor(1, 1)
        root.addWidget(body, 3)

        options = _section("PROCESSING OPTIONS")
        options_content = QWidget()
        options_layout = QHBoxLayout(options_content)
        options_layout.setContentsMargins(8, 6, 8, 6)
        self.bypass_ptz = QCheckBox("Bypass PTZ")
        self.run_detection = QCheckBox("Run Detection")
        self.run_localization = QCheckBox("Run Localization")
        self.generate_log = QCheckBox("Generate Performance Log")
        self.bypass_ptz_check = self.bypass_ptz
        self.run_detection_check = self.run_detection
        self.run_localization_check = self.run_localization
        self.generate_log_check = self.generate_log
        self.bypass_ptz.setChecked(False)
        self.run_detection.setChecked(True)
        self.run_localization.setChecked(True)
        self.generate_log.setChecked(True)
        for checkbox in (self.bypass_ptz, self.run_detection, self.run_localization, self.generate_log):
            options_layout.addWidget(checkbox)
        options_layout.addStretch(1)
        self.run_button = QPushButton("RUN DEMO REPLAY")
        self.run_button.setProperty("class", "primary")
        self.run_button.clicked.connect(self._run_demo)
        options_layout.addWidget(self.run_button)
        options_box_layout = QVBoxLayout(options)
        options_box_layout.setContentsMargins(8, 5, 8, 5)
        options_box_layout.addWidget(_toolbar_scroll(options_content, 38))
        root.addWidget(options)

        results = _section("BENCHMARK RESULTS")
        results_content = QWidget()
        results_layout = QGridLayout(results_content)
        results_layout.setContentsMargins(8, 8, 8, 8)
        benchmark_rows = [
            ("Centroid Error", "N/A"),
            ("RMSE", "N/A"),
            ("Maximum Error", "N/A"),
            ("FPS", "N/A"),
            ("Detection Probability", "N/A"),
            ("Target Loss", "N/A"),
            ("Ground Truth", "GROUND TRUTH UNAVAILABLE"),
        ]
        self.result_labels: dict[str, QLabel] = {}
        for index, (name, value) in enumerate(benchmark_rows):
            results_layout.addWidget(QLabel(name), index // 4, (index % 4) * 2)
            label = QLabel(value)
            label.setProperty("class", "telemetry-item")
            self.result_labels[name] = label
            results_layout.addWidget(label, index // 4, (index % 4) * 2 + 1)
        results_box_layout = QVBoxLayout(results)
        results_box_layout.setContentsMargins(8, 5, 8, 5)
        results_box_layout.addWidget(_toolbar_scroll(results_content, 68))
        root.addWidget(results)

        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._advance_frame)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select local video", "", "Video files (*.mp4 *.mov *.avi *.mkv);;All files (*)")
        if not path:
            return
        self._selected_file = path
        self.file_edit.setText(path)
        for name in ("Resolution", "FPS", "Frames", "Duration"):
            self.metadata_labels[name].setText("unknown")
        self.metadata_note.setText(f"DEMO / SELECTED FILE\n{os.path.basename(path)}\nMetadata: unknown\nGround truth: GROUND TRUTH UNAVAILABLE")
        self.run_status.setText("FILE SELECTED / DEMO")
        self.notification.emit(f"Selected local video for demo replay: {os.path.basename(path)}")

    def _timeline_changed(self, value: int) -> None:
        self.preview.set_frame(value)
        self.frame_label.setText(f"FRAME {value:05d} / DEMO")

    def play(self) -> None:
        self._playing = True
        self._timer.start()
        self.run_status.setText("PLAYING PLACEHOLDER FRAMES")
        self.notification.emit("Video preview playing placeholder frames")

    def pause(self) -> None:
        self._playing = False
        self._timer.stop()
        self.run_status.setText("PAUSED / DEMO")
        self.notification.emit("Video preview paused")

    def _advance_frame(self) -> None:
        next_frame = self.timeline.value() + 1
        if next_frame > self.timeline.maximum():
            next_frame = 0
        self.timeline.setValue(next_frame)

    def _run_demo(self) -> None:
        flags = [
            f"PTZ={'bypass' if self.bypass_ptz.isChecked() else 'enabled'}",
            f"detection={'on' if self.run_detection.isChecked() else 'off'}",
            f"localization={'on' if self.run_localization.isChecked() else 'off'}",
            f"log={'on' if self.generate_log.isChecked() else 'off'}",
        ]
        message = "Demo replay requested — no video processing executed (" + ", ".join(flags) + ")"
        self.run_status.setText("DEMO REQUESTED / NO PROCESSING")
        self.notification.emit(message)

    def update_telemetry(self, data: Any) -> None:
        frame = _value(data, "frame")
        if frame is not None and not self._playing:
            self.timeline.setValue(int(frame) % (self.timeline.maximum() + 1))


def _mock_log_value(category: str, header: str, row: int) -> str:
    """Return a plausible but explicitly synthetic console cell."""

    frame = 1842 + row
    if header == "Timestamp":
        return f"08:42:{12 + row:02d}.0{row + 2}"
    if header == "Frame":
        return str(frame)
    if header == "Detection":
        return "LOCKED" if row != 3 else "SEARCHING"
    if header == "Candidate Count":
        return str(4 + (row % 3))
    if header == "Confidence":
        return f"{0.91 - row * 0.018:.3f}"
    if header == "False Alarm":
        return "0.8%"
    if header == "Latency":
        return f"{18.0 + row * 0.4:.1f} ms"
    if header == "Ground Truth U":
        return f"{321.4 + row * 0.7:.2f}"
    if header == "Ground Truth V":
        return f"{219.2 + row * 0.4:.2f}"
    if header == "Estimated U":
        return f"{321.1 + row * 0.68:.2f}"
    if header == "Estimated V":
        return f"{219.5 + row * 0.37:.2f}"
    if header in ("X Error", "Y Error"):
        return f"{(-0.3 + row * 0.08):+.2f} px"
    if header == "Radial Error":
        return f"{0.38 + row * 0.14:.2f} px"
    if header == "RMSE":
        return f"{3.05 + row * 0.06:.2f} px"
    if header == "Lock State":
        return "LOCKED" if row != 3 else "REACQUIRING"
    if header == "Missed Frames":
        return "0" if row != 3 else "2"
    if header == "Loss Duration":
        return "0 ms" if row != 3 else "33 ms"
    if header == "Tracking Error":
        return f"{2.1 + row * 0.12:.2f} px"
    if header == "Reacquisition":
        return "—" if row != 3 else "0.42 s"
    if header == "Horizon":
        return f"{0.5 + row * 0.5:.1f} s"
    if header in ("Predicted U", "Actual U"):
        return f"{321.0 + row * 0.8 + (0.8 if header == 'Predicted U' else 0):.2f}"
    if header in ("Predicted V", "Actual V"):
        return f"{219.0 + row * 0.4 + (0.5 if header == 'Predicted V' else 0):.2f}"
    if header == "Prediction Error":
        return f"{2.2 + row * 0.41:.2f} px"
    if header in ("Sigma U", "Sigma V"):
        return f"{1.1 + row * 0.09:.2f} px"
    if header == "Mahalanobis Distance":
        return f"{2.0 + row * 0.3:.2f}"
    if header == "Innovation":
        return f"{0.42 - row * 0.03:+.2f}"
    if header == "Innovation Covariance":
        return f"{1.72 + row * 0.04:.2f}"
    if header == "NIS":
        return f"{2.1 + row * 0.12:.2f}"
    if header == "Covariance Trace":
        return f"{3.8 - row * 0.11:.2f}"
    if header == "Rejected Measurement":
        return "NO" if row != 3 else "YES"
    if header == "Outlier Count":
        return "0" if row != 3 else "1"
    if header in ("Commanded Pan", "Actual Pan"):
        return f"{0.24 + row * 0.05 + (0.04 if header == 'Actual Pan' else 0):.2f}°"
    if header in ("Commanded Tilt", "Actual Tilt"):
        return f"{-0.18 + row * 0.03 + (-0.02 if header == 'Actual Tilt' else 0):.2f}°"
    if header in ("Pan Error", "Tilt Error"):
        return f"{0.04 + row * 0.01:.2f}°"
    if header == "Saturation":
        return "NO"
    if header == "Delay":
        return f"{18 + row} ms"
    if header == "FOV Violation":
        return "NO"
    if header == "Search Duration":
        return f"{0.30 + row * 0.03:.2f} s"
    if header == "Search Path Length":
        return f"{42 + row * 3.4:.1f} px"
    if header == "Amplitude":
        return f"{18 + row * 0.8:.1f} px"
    if header == "Orientation":
        return f"{18 + row * 1.5:.1f}°"
    if header == "Coverage":
        return f"{72 + row * 2.0:.1f}%"
    if header in ("Acquisition", "Reacquisition"):
        return f"{0.40 + row * 0.03:.2f} s"
    if header in ("Frame Latency", "Detection Latency", "Localization Latency", "Filter Latency", "Control Latency"):
        base = {"Frame Latency": 16.4, "Detection Latency": 4.3, "Localization Latency": 2.1, "Filter Latency": 0.8, "Control Latency": 1.2}[header]
        return f"{base + row * 0.08:.2f} ms"
    if header == "CPU":
        return f"{12 + row * 0.4:.1f}%"
    if header == "RAM":
        return f"{2.4 + row * 0.01:.2f} GB"
    if header == "GPU":
        return "READY"
    if header == "Dropped Frames":
        return "0" if row != 3 else "1"
    if header == "Deadline Misses":
        return "0"
    return "MOCK"


class DebugWorkspace(QWidget):
    """Read-only technical consoles with local filtering and export signaling."""

    exportRequested = Signal()
    notification = Signal(str)
    LOG_SPECS = LOG_SPECS

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.log_tables: dict[str, QTableWidget] = {}
        self.tables = self.log_tables
        self._log_rows: dict[str, list[list[str]]] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)
        header = QHBoxLayout()
        title = QLabel("TECHNICAL DEBUG")
        title.setProperty("class", "page-title")
        header.addWidget(title)
        header.addWidget(_caption("READ-ONLY CONSOLES  /  PER-FRAME TELEMETRY  /  MOCK LOGS"))
        header.addStretch(1)
        self.console_status = QLabel("MOCK LOG STREAM")
        self.console_status.setProperty("class", "status-pill")
        header.addWidget(self.console_status)
        root.addLayout(header)

        toolbar = _section("LOG CONTROLS")
        toolbar_content = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_content)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.addWidget(QLabel("FILTER"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All rows", "LOCKED", "WARN / SEARCHING", "ERROR / DROPPED", "MOCK rows"])
        toolbar_layout.addWidget(self.filter_combo)
        toolbar_layout.addWidget(QLabel("SEARCH"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search visible cells…")
        toolbar_layout.addWidget(self.search_input, 1)
        self.filter_button = QPushButton("FILTER")
        self.search_button = QPushButton("SEARCH")
        self.clear_button = QPushButton("CLEAR")
        self.restore_button = QPushButton("RESTORE MOCK ROWS")
        self.export_button = QPushButton("EXPORT PLACEHOLDER")
        toolbar_layout.addWidget(self.filter_button)
        toolbar_layout.addWidget(self.search_button)
        toolbar_layout.addWidget(self.clear_button)
        toolbar_layout.addWidget(self.restore_button)
        toolbar_layout.addWidget(self.export_button)
        self.filter_button.clicked.connect(self._apply_filters)
        self.search_button.clicked.connect(self._apply_filters)
        self.search_input.returnPressed.connect(self._apply_filters)
        self.search_input.textChanged.connect(lambda text: self._apply_filters(False))
        self.filter_combo.currentTextChanged.connect(lambda text: self._apply_filters(False))
        self.clear_button.clicked.connect(self._clear_current)
        self.restore_button.clicked.connect(self._restore_current)
        self.export_button.clicked.connect(self._export_placeholder)
        toolbar_box_layout = QVBoxLayout(toolbar)
        toolbar_box_layout.setContentsMargins(8, 5, 8, 5)
        toolbar_box_layout.addWidget(_toolbar_scroll(toolbar_content, 38))
        root.addWidget(toolbar)

        self.tabs = QTabWidget()
        self.log_tabs = self.tabs
        self.tabs.currentChanged.connect(lambda index: self._apply_filters(False))
        for category, headers in LOG_SPECS.items():
            rows = [[_mock_log_value(category, header, row) for header in headers] for row in range(6)]
            self._log_rows[category] = rows
            table = _read_only_table(headers, rows)
            table.setAlternatingRowColors(True)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setToolTip(f"{category} · read-only mock telemetry")
            self.log_tables[category] = table
            self.tabs.addTab(table, category)
        root.addWidget(self.tabs, 1)
        self._apply_filters(False)

    def _current_category(self) -> str:
        index = self.tabs.currentIndex()
        return self.tabs.tabText(index) if index >= 0 else next(iter(LOG_SPECS))

    def _apply_filters(self, announce: bool = True) -> None:
        category = self._current_category()
        table = self.log_tables.get(category)
        if table is None:
            return
        query = self.search_input.text().strip().lower()
        mode = self.filter_combo.currentText()
        for row in range(table.rowCount()):
            values = " ".join(table.item(row, column).text() if table.item(row, column) else "" for column in range(table.columnCount()))
            lower = values.lower()
            matches_search = not query or query in lower
            if mode == "All rows":
                matches_mode = True
            elif mode == "LOCKED":
                matches_mode = "locked" in lower
            elif mode == "WARN / SEARCHING":
                matches_mode = any(token in lower for token in ("searching", "reacquiring", "rejected"))
            elif mode == "ERROR / DROPPED":
                matches_mode = any(token in lower for token in ("error", "yes", "dropped"))
            else:
                matches_mode = True  # every row in this workspace is synthetic
            table.setRowHidden(row, not (matches_search and matches_mode))
        visible = sum(1 for row in range(table.rowCount()) if not table.isRowHidden(row))
        self.console_status.setText(f"{category.upper()} / {visible} VISIBLE")
        if announce:
            self.notification.emit(f"{category} log filter applied: {visible} visible rows")

    def _clear_current(self) -> None:
        category = self._current_category()
        table = self.log_tables.get(category)
        if table is not None:
            table.setRowCount(0)
            self.console_status.setText(f"{category.upper()} / CLEARED")
            self.notification.emit(f"Cleared visible {category} mock log table")

    def _restore_current(self) -> None:
        category = self._current_category()
        table = self.log_tables.get(category)
        if table is None:
            return
        rows = self._log_rows[category]
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                table.setItem(row_index, column_index, QTableWidgetItem(value))
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._apply_filters()

    def _export_placeholder(self) -> None:
        self.exportRequested.emit()
        self.console_status.setText("EXPORT PLACEHOLDER REQUESTED")
        self.notification.emit("Log export requested; no file was written by the prototype")

    def update_telemetry(self, data: Any) -> None:
        frame = _value(data, "frame")
        if frame is None:
            return
        table = self.log_tables.get("Detection")
        if table is None or table.rowCount() == 0:
            return
        headers = [table.horizontalHeaderItem(column).text() for column in range(table.columnCount())]
        if "Frame" in headers:
            frame_column = headers.index("Frame")
            table.item(0, frame_column).setText(str(frame))
        self._apply_filters(False)


__all__ = [
    "ANALYSIS_CHART_TITLES",
    "PERFORMANCE_METRICS",
    "LOG_SPECS",
    "TrackingWorkspace",
    "AnalysisWorkspace",
    "BenchmarkWorkspace",
    "DebugWorkspace",
]
