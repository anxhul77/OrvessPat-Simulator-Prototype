"""Analytics workspace — debugger-grade session instrumentation.

The dashboard is a live instrumentation console over the telemetry stream:
strip charts with specification reference lines, an XY trajectory scope,
error/latency distributions, a severity-filtered event audit log, SIH spec
compliance table, capture pause/clear controls, and CSV performance-log export.
All statistics are accumulated from live ticks (mock telemetry source).
"""

from __future__ import annotations

import csv
import math
import os
import time
from collections import deque
from typing import Any, Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pages.workspaces import AnalysisWorkspace, _ScientificPlot, pg
from ui.widgets import Metric, StatusPill

# Palette (matches workstation theme)
ACCENT = "#42d6c5"
ORANGE = "#ef8c63"
GOLD = "#efc95c"
PURPLE = "#b58cff"
BLUE = "#6da9ff"
RED = "#e06c75"
GREEN = "#4ec9b0"

# Specification / consistency thresholds
SPEC_MAX_ERROR = 10.0        # px, SIH tracking error
SPEC_MIN_FPS = 20.0          # SIH processing speed
SPEC_MAX_ACQ = 2.0           # s
SPEC_MAX_REACQ = 1.0         # s
SPEC_MAX_LOSS_PCT = 5.0      # %
CHI2_95_2DOF = 5.991         # NIS gate, 2 degrees of freedom
DEADLINE_MS = 50.0           # per-frame processing budget (20 FPS)

TRACE_WINDOW = 300           # samples kept on strip charts
EXPORT_CAP = 20000           # samples kept for CSV export
PCTL_WINDOW = 1000           # samples used for percentile estimates
EVENT_CAP = 400              # rows kept in the event log

LOCK_LEVEL = {"TARGET LOST": 0.0, "REACQUIRING": 0.35, "SEARCHING": 0.65, "LOCKED": 1.0}

SEVERITY_COLORS = {"INFO": BLUE, "OK": GREEN, "WARN": GOLD, "ERROR": RED}

SPEC_ROWS = [
    ("Acquisition Time", "≤ 2.0 s", "acq", "s", lambda s: s["acq"] <= SPEC_MAX_ACQ),
    ("Re-acquisition Time", "≤ 1.0 s", "reacq", "s", lambda s: s["reacq"] <= SPEC_MAX_REACQ),
    ("Tracking Error (mean)", "≤ 10 px", "mean_err", "px", lambda s: s["mean_err"] <= SPEC_MAX_ERROR),
    ("Target Loss", "< 5 %", "loss_pct", "%", lambda s: s["loss_pct"] < SPEC_MAX_LOSS_PCT),
    ("Processing Speed", "≥ 20 FPS", "fps_mean", "FPS", lambda s: s["fps_mean"] >= SPEC_MIN_FPS),
]


def _percentile(ordered: list[float], q: float) -> float:
    """Linear-interpolated percentile over an already-sorted list."""
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * q / 100.0
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


class _StripChart(_ScientificPlot):
    """Time-series chart with persistent horizontal specification reference lines."""

    def __init__(self, title: str, y_label: str = "", ref_lines: list | None = None, minimum_height: int = 128):
        refs = ref_lines or []
        super().__init__(title, "t / s", y_label, minimum_height)
        self._refs = refs
        self._apply_refs()

    def _apply_refs(self) -> None:
        if self.plot_widget is None:
            return
        for value, color, label in self._refs:
            line = pg.InfiniteLine(
                pos=value, angle=0,
                pen=pg.mkPen(color, width=1, style=Qt.DashLine),
                label=label,
                labelOpts={"color": color, "position": 0.9},
            )
            self.plot_widget.addItem(line)

    def set_series(self, series: Iterable[tuple[str, Iterable[float], Iterable[float] | None, str]]) -> None:
        super().set_series(series)
        self._apply_refs()


class _HistogramPlot(QWidget):
    """Binned distribution plot (bar rendering with painted fallback)."""

    def __init__(self, title: str, x_label: str, color: str, bins: int = 22, parent: QWidget | None = None):
        super().__init__(parent)
        self.title = title
        self.x_label = x_label
        self.color = color
        self.bins = bins
        self.setMinimumHeight(128)
        self._bars: list[float] = []
        self._edges: list[float] = []
        if pg is not None:
            self.plot_widget = pg.PlotWidget()
            self.plot_widget.setBackground("#111820")
            self.plot_widget.showGrid(x=True, y=True, alpha=0.18)
            self.plot_widget.setTitle(title, color="#c1d0d5", size="9pt")
            self.plot_widget.setLabel("bottom", x_label)
            self.plot_widget.setLabel("left", "count")
            self.plot_widget.getAxis("left").setTextPen("#71848e")
            self.plot_widget.getAxis("bottom").setTextPen("#71848e")
            self.plot_widget.setMenuEnabled(False)
            self.plot_widget.hideButtons()
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.plot_widget)
        else:
            self.plot_widget = None

    def set_values(self, values: Iterable[float]) -> None:
        values = [v for v in values if math.isfinite(v)]
        if not values:
            return
        lo, hi = min(values), max(values)
        if hi - lo < 1e-9:
            hi = lo + 1.0
        width = (hi - lo) / self.bins
        counts = [0] * self.bins
        for v in values:
            idx = min(self.bins - 1, int((v - lo) / width))
            counts[idx] += 1
        self._bars = [float(c) for c in counts]
        self._edges = [lo + i * width for i in range(self.bins + 1)]
        if self.plot_widget is not None:
            self.plot_widget.clear()
            item = pg.BarGraphItem(
                x=[lo + (i + 0.5) * width for i in range(self.bins)],
                height=self._bars,
                width=width * 0.92,
                brush=pg.mkBrush(self.color),
                pen=pg.mkPen("#111820"),
            )
            self.plot_widget.addItem(item)
            self.plot_widget.enableAutoRange()
        else:
            self.update()

    def paintEvent(self, event) -> None:  # pragma: no cover — fallback only
        if self.plot_widget is not None:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#111820"))
        painter.setPen(QColor("#c1d0d5"))
        painter.drawText(10, 16, self.title)
        if not self._bars:
            return
        peak = max(1.0, max(self._bars))
        bar_w = self.width() / len(self._bars)
        top, bottom = 26, self.height() - 8
        painter.setPen(QPen(QColor(self.color)))
        for i, count in enumerate(self._bars):
            h = (bottom - top) * count / peak
            painter.drawRect(int(i * bar_w) + 1, int(bottom - h), max(1, int(bar_w) - 2), int(h))


class _EventLog(QWidget):
    """Debugger-style timestamped event audit trail with severity filtering."""

    clear_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        bar = QHBoxLayout()
        bar.setSpacing(6)
        title = QLabel("▸ EVENT LOG")
        title.setStyleSheet(f"color:{ACCENT}; font-weight:700; font-size:10px; letter-spacing:1px;")
        bar.addWidget(title)
        bar.addStretch()

        self._sev_checks: dict[str, QCheckBox] = {}
        for sev in ("INFO", "OK", "WARN", "ERROR"):
            chk = QCheckBox(sev)
            chk.setChecked(True)
            chk.setStyleSheet(f"color:{SEVERITY_COLORS[sev]}; font-size:10px;")
            chk.toggled.connect(self._refilter)
            self._sev_checks[sev] = chk
            bar.addWidget(chk)

        self.autoscroll = QCheckBox("AUTOSCROLL")
        self.autoscroll.setChecked(True)
        self.autoscroll.setStyleSheet("color:#858585; font-size:10px;")
        bar.addWidget(self.autoscroll)

        btn_clear = QPushButton("CLEAR")
        btn_clear.setFixedHeight(20)
        btn_clear.clicked.connect(self.clear_log)
        bar.addWidget(btn_clear)
        layout.addLayout(bar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["T+ / s", "FRAME", "SEV", "SOURCE", "MESSAGE"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setFont(QFont("Consolas", 9))
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, 1)

    def _row_visible(self, severity: str) -> bool:
        chk = self._sev_checks.get(severity)
        return chk is None or chk.isChecked()

    def add_event(self, t: float, frame: int, severity: str, source: str, message: str) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        cells = [f"{t:8.2f}", f"{frame:05d}", severity, source, message]
        for col, text in enumerate(cells):
            item = QTableWidgetItem(text)
            if col in (0, 1):
                item.setForeground(QColor("#9aa7b0"))
            elif col == 2:
                item.setForeground(QColor(SEVERITY_COLORS.get(severity, "#cccccc")))
            elif col == 3:
                item.setForeground(QColor(PURPLE))
            else:
                item.setForeground(QColor("#d8dee2"))
            self.table.setItem(row, col, item)
        if not self._row_visible(severity):
            self.table.setRowHidden(row, True)
        while self.table.rowCount() > EVENT_CAP:
            self.table.removeRow(0)
        if self.autoscroll.isChecked():
            self.table.scrollToBottom()

    def clear_log(self) -> None:
        self.table.setRowCount(0)
        self.clear_requested.emit()

    def _refilter(self) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 2)
            self.table.setRowHidden(row, not self._row_visible(item.text()))


class _SessionDashboard(QWidget):
    """Live debugger dashboard accumulating session statistics from telemetry."""

    export_notification = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._t = 0.0
        self._last_wall = None
        self._capturing = True
        self.frames = 0
        self.locked = 0
        self.sum_err = 0.0
        self.sum_sq = 0.0
        self.max_err = 0.0
        self.fps_sum = 0.0
        self.nis_ok_count = 0
        self.deadline_misses = 0
        self.acq: float | None = None
        self.reacq: float | None = None
        self._loss_started: float | None = None
        self._prev: dict[str, Any] = {"lock": None, "nis_ok": True, "err_ok": True, "lat_ok": True, "fps_ok": True, "motion": None}

        # ring buffers for charts / percentiles and full history for export
        self.t_hist = deque(maxlen=TRACE_WINDOW)
        self.err_hist = deque(maxlen=TRACE_WINDOW)
        self.errx_hist = deque(maxlen=TRACE_WINDOW)
        self.erry_hist = deque(maxlen=TRACE_WINDOW)
        self.nis_hist = deque(maxlen=TRACE_WINDOW)
        self.lat_hist = deque(maxlen=TRACE_WINDOW)
        self.lat_all = deque(maxlen=PCTL_WINDOW)
        self.fps_hist = deque(maxlen=TRACE_WINDOW)
        self.lock_hist = deque(maxlen=TRACE_WINDOW)
        self.u_hist = deque(maxlen=TRACE_WINDOW)
        self.v_hist = deque(maxlen=TRACE_WINDOW)
        self.eu_hist = deque(maxlen=TRACE_WINDOW)
        self.ev_hist = deque(maxlen=TRACE_WINDOW)
        self.pu_hist = deque(maxlen=TRACE_WINDOW)
        self.pv_hist = deque(maxlen=TRACE_WINDOW)
        self.export_rows: deque[dict] = deque(maxlen=EXPORT_CAP)

        self._build_ui()
        self.event_log.add_event(0.0, 0, "INFO", "SYSTEM", "Session instrumentation started — capture ACTIVE")

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        # Entire dashboard lives in one vertical scroll area; content stretches
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(14, 10, 14, 12)
        outer.setSpacing(10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(page)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(scroll)

        # --- capture toolbar -------------------------------------------------
        bar = QHBoxLayout()
        bar.setSpacing(8)
        self.rec_led = QLabel("● REC")
        self.rec_led.setStyleSheet(f"color:{GREEN}; font-weight:700; font-size:11px;")
        bar.addWidget(self.rec_led)
        self.clock = QLabel("T+ 0.0 s   ·   0 frames")
        self.clock.setFont(QFont("Consolas", 10))
        self.clock.setStyleSheet("color:#9aa7b0;")
        bar.addWidget(self.clock)
        bar.addStretch()

        self.btn_capture = QPushButton("⏸ PAUSE CAPTURE")
        self.btn_capture.clicked.connect(self._toggle_capture)
        bar.addWidget(self.btn_capture)
        btn_clear = QPushButton("CLEAR SESSION")
        btn_clear.clicked.connect(self._clear_session)
        bar.addWidget(btn_clear)
        btn_export = QPushButton("⬇ EXPORT PERFORMANCE LOG (CSV)")
        btn_export.clicked.connect(self._export_csv)
        bar.addWidget(btn_export)
        outer.addLayout(bar)

        # --- metric cards ----------------------------------------------------
        cards = QGridLayout()
        cards.setSpacing(8)
        self.cards: dict[str, Metric] = {}
        card_specs = [
            ("FPS", "—", ""), ("Latency μ / P95", "—", "ms"),
            ("Mean Error", "—", "px"), ("RMSE", "—", "px"),
            ("Max Error", "—", "px"), ("Lock Retention", "—", "%"),
            ("NIS In-Gate", "—", "%"), ("Deadline Misses", "—", ""),
        ]
        for i, (name, val, unit) in enumerate(card_specs):
            m = Metric(name, val, unit)
            self.cards[name] = m
            cards.addWidget(m, i // 4, i % 4)
        outer.addLayout(cards)

        # --- main splitter: traces | scope+distributions ---------------------
        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        split.setHandleWidth(10)

        # Left column: full-width strip charts, stretching vertically
        traces_wrap = QWidget()
        tl = QVBoxLayout(traces_wrap)
        tl.setContentsMargins(0, 0, 6, 0)
        tl.setSpacing(10)
        hdr = QLabel("▸ SIGNAL TRACES")
        hdr.setStyleSheet(f"color:{ACCENT}; font-weight:700; font-size:10px; letter-spacing:1px; padding: 2px 4px;")
        tl.addWidget(hdr)
        self.trace_error = _StripChart("RADIAL TRACKING ERROR", "px", [(SPEC_MAX_ERROR, RED, "spec ≤10 px")], 170)
        self.trace_xy = _StripChart("ERROR COMPONENTS X / Y", "px", minimum_height=170)
        self.trace_nis = _StripChart("NIS CONSISTENCY", "", [(CHI2_95_2DOF, RED, "χ² 95 %")], 170)
        self.trace_lat = _StripChart("FRAME LATENCY", "ms", [(DEADLINE_MS, RED, "50 ms deadline")], 170)
        self.trace_fps = _StripChart("PROCESSING RATE", "FPS", [(SPEC_MIN_FPS, RED, "spec ≥20")], 170)
        self.trace_lock = _StripChart("LOCK STATE MACHINE", "level", minimum_height=150)
        for chart in [self.trace_error, self.trace_xy, self.trace_nis, self.trace_lat, self.trace_fps, self.trace_lock]:
            tl.addWidget(chart, 1)

        # Right column: spatial scope + distributions, stretching vertically
        right_wrap = QWidget()
        rl = QVBoxLayout(right_wrap)
        rl.setContentsMargins(6, 0, 0, 0)
        rl.setSpacing(10)
        hdr2 = QLabel("▸ SPATIAL SCOPE / DISTRIBUTIONS")
        hdr2.setStyleSheet(f"color:{ACCENT}; font-weight:700; font-size:10px; letter-spacing:1px; padding: 2px 4px;")
        rl.addWidget(hdr2)
        self.scope = _ScientificPlot("XY TRAJECTORY SCOPE  ·  truth / estimate / prediction", "u / px", "v / px", 250)
        self.hist_error = _HistogramPlot("ERROR DISTRIBUTION", "radial error / px", ORANGE)
        self.hist_error.setMinimumHeight(190)
        self.hist_cdf = _ScientificPlot("ERROR CDF  ·  P50 / P95 / P99", "error / px", "cumulative %", 190)
        rl.addWidget(self.scope, 3)
        rl.addWidget(self.hist_error, 2)
        rl.addWidget(self.hist_cdf, 2)

        split.addWidget(traces_wrap)
        split.addWidget(right_wrap)
        split.setSizes([680, 480])
        outer.addWidget(split, 3)

        # --- bottom splitter: event log | spec + summary ---------------------
        bottom = QSplitter(Qt.Horizontal)
        bottom.setChildrenCollapsible(False)
        bottom.setHandleWidth(10)
        self.event_log = _EventLog()

        spec_wrap = QWidget()
        sl = QVBoxLayout(spec_wrap)
        sl.setContentsMargins(10, 4, 0, 4)
        sl.setSpacing(10)
        self.spec_table = QTableWidget(len(SPEC_ROWS), 4)
        self.spec_table.setHorizontalHeaderLabels(["Metric", "Requirement", "Session", "Status"])
        self.spec_table.verticalHeader().setVisible(False)
        self.spec_table.setAlternatingRowColors(True)
        self.spec_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.spec_table.setFont(QFont("Consolas", 9))
        self.spec_table.horizontalHeader().setStretchLastSection(True)
        self.spec_table.setFixedHeight(1 + 26 * (len(SPEC_ROWS) + 1))
        for r, (name, req, _, _, _) in enumerate(SPEC_ROWS):
            self.spec_table.setItem(r, 0, QTableWidgetItem(name))
            self.spec_table.setItem(r, 1, QTableWidgetItem(req))
            self.spec_table.setItem(r, 2, QTableWidgetItem("—"))
            self.spec_table.setItem(r, 3, QTableWidgetItem("—"))
        sl.addWidget(self.spec_table)

        self.summary = QLabel("SESSION SUMMARY  ▸  duration —  ·  frames —  ·  RMSE —  ·  loss —")
        self.summary.setFont(QFont("Consolas", 9))
        self.summary.setStyleSheet("color:#9aa7b0; padding: 4px 6px;")
        self.summary.setWordWrap(True)
        sl.addWidget(self.summary)
        sl.addStretch(1)

        bottom.addWidget(self.event_log)
        bottom.addWidget(spec_wrap)
        bottom.setSizes([560, 520])
        outer.addWidget(bottom, 1)

    # -------------------------------------------------------------- controls
    def _toggle_capture(self) -> None:
        self._capturing = not self._capturing
        if self._capturing:
            self.btn_capture.setText("⏸ PAUSE CAPTURE")
            self.rec_led.setText("● REC")
            self.rec_led.setStyleSheet(f"color:{GREEN}; font-weight:700;")
            self._last_wall = None
            self.event_log.add_event(self._t, self.frames, "INFO", "SYSTEM", "Capture resumed")
        else:
            self.btn_capture.setText("▶ RESUME CAPTURE")
            self.rec_led.setText("❚❚ PAUSED")
            self.rec_led.setStyleSheet(f"color:{GOLD}; font-weight:700;")
            self.event_log.add_event(self._t, self.frames, "WARN", "SYSTEM", "Capture paused — traces frozen")

    def _clear_session(self) -> None:
        self.frames = 0
        self.locked = 0
        self.sum_err = self.sum_sq = self.max_err = 0.0
        self.fps_sum = 0.0
        self.nis_ok_count = 0
        self.deadline_misses = 0
        self.acq = self.reacq = None
        self._t = 0.0
        self._last_wall = None
        for buf in (self.t_hist, self.err_hist, self.errx_hist, self.erry_hist, self.nis_hist,
                    self.lat_hist, self.lat_all, self.fps_hist, self.lock_hist, self.u_hist,
                    self.v_hist, self.eu_hist, self.ev_hist, self.pu_hist, self.pv_hist, self.export_rows):
            buf.clear()
        self.event_log.add_event(0.0, 0, "INFO", "SYSTEM", "Session statistics cleared")

    def _session_stats(self) -> dict:
        n = max(1, self.frames)
        lat_sorted = sorted(self.lat_all)
        return {
            "acq": self.acq if self.acq is not None else float("inf"),
            "reacq": self.reacq if self.reacq is not None else float("inf"),
            "mean_err": self.sum_err / n,
            "max_err": self.max_err,
            "rmse": math.sqrt(self.sum_sq / n),
            "loss_pct": 100.0 * (self.frames - self.locked) / n,
            "lock_pct": 100.0 * self.locked / n,
            "fps_mean": self.fps_sum / n,
            "lat_p95": _percentile(lat_sorted, 95),
            "nis_pct": 100.0 * self.nis_ok_count / n,
        }

    def _export_csv(self) -> None:
        """Write the accumulated session as the SIH performance log deliverable."""
        if not self.export_rows:
            QMessageBox.information(self, "Performance Log", "No captured frames to export yet.")
            return
        stats = self._session_stats()
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, time.strftime("performance_log_%Y%m%d_%H%M%S.csv"))
        columns = ["frame", "t_s", "lock", "u", "v", "est_u", "est_v", "pred_u", "pred_v",
                   "err_x", "err_y", "err_rad", "pred_err", "nis", "latency_ms", "fps", "sigma_u", "sigma_v"]
        with open(path, "w", newline="", encoding="utf-8") as fh:
            fh.write("# OrvessPat Sim — Performance Log (SIH deliverable)\n")
            fh.write(f"# exported,{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            fh.write(f"# duration_s,{self._t:.2f}\n")
            fh.write(f"# frames,{self.frames}\n")
            fh.write(f"# fps_mean,{stats['fps_mean']:.2f}\n")
            fh.write(f"# acquisition_s,{stats['acq']:.2f}\n")
            fh.write(f"# reacquisition_s,{stats['reacq']:.2f}\n")
            fh.write(f"# tracking_error_mean_px,{stats['mean_err']:.3f}\n")
            fh.write(f"# tracking_error_max_px,{stats['max_err']:.3f}\n")
            fh.write(f"# rmse_px,{stats['rmse']:.3f}\n")
            fh.write(f"# lock_retention_pct,{stats['lock_pct']:.2f}\n")
            fh.write(f"# target_loss_pct,{stats['loss_pct']:.2f}\n")
            fh.write(f"# latency_p95_ms,{stats['lat_p95']:.2f}\n")
            fh.write(f"# nis_in_gate_pct,{stats['nis_pct']:.2f}\n")
            fh.write(f"# deadline_misses,{self.deadline_misses}\n")
            writer = csv.DictWriter(fh, fieldnames=columns)
            writer.writeheader()
            writer.writerows(self.export_rows)
        self.event_log.add_event(self._t, self.frames, "OK", "SYSTEM", f"Performance log exported → {os.path.basename(path)}")
        QMessageBox.information(
            self, "Performance Log",
            f"Performance log written:\n{path}\n\nFrames: {self.frames}\nDuration: {self._t:.1f} s\nRMSE: {stats['rmse']:.2f} px\nLock retention: {stats['lock_pct']:.1f} %",
        )

    # -------------------------------------------------------------- telemetry
    def update_telemetry(self, d: Any) -> None:
        if not self._capturing:
            return
        now = time.monotonic()
        if self._last_wall is not None:
            self._t += min(1.0, now - self._last_wall)
        self._last_wall = now

        u, v = float(d.u), float(d.v)
        eu, ev = float(d.est_u), float(d.est_v)
        pu, pv = float(d.pred_u), float(d.pred_v)
        err_x, err_y = eu - u, ev - v
        err_rad = float(d.track_error)
        pred_err = math.hypot(pu - u, pv - v)
        nis, lat, fps = float(d.nis), float(d.latency), float(d.fps)
        lock = str(d.lock)
        frame = int(d.frame)

        self.frames += 1
        if lock == "LOCKED":
            self.locked += 1
        self.sum_err += err_rad
        self.sum_sq += err_rad * err_rad
        self.max_err = max(self.max_err, err_rad)
        self.fps_sum += fps
        nis_ok = nis <= CHI2_95_2DOF
        if nis_ok:
            self.nis_ok_count += 1
        lat_ok = lat <= DEADLINE_MS
        if not lat_ok:
            self.deadline_misses += 1
        err_ok = err_rad <= SPEC_MAX_ERROR
        fps_ok = fps >= SPEC_MIN_FPS
        self.acq, self.reacq = float(d.acq_time), float(d.reacq_time)

        for buf, val in ((self.t_hist, self._t), (self.err_hist, err_rad), (self.errx_hist, err_x),
                         (self.erry_hist, err_y), (self.nis_hist, nis), (self.lat_hist, lat),
                         (self.lat_all, lat), (self.fps_hist, fps), (self.u_hist, u), (self.v_hist, v),
                         (self.eu_hist, eu), (self.ev_hist, ev), (self.pu_hist, pu), (self.pv_hist, pv)):
            buf.append(val)
        self.lock_hist.append(LOCK_LEVEL.get(lock, 0.0))
        self.export_rows.append({
            "frame": frame, "t_s": f"{self._t:.3f}", "lock": lock, "u": f"{u:.2f}", "v": f"{v:.2f}",
            "est_u": f"{eu:.2f}", "est_v": f"{ev:.2f}", "pred_u": f"{pu:.2f}", "pred_v": f"{pv:.2f}",
            "err_x": f"{err_x:.3f}", "err_y": f"{err_y:.3f}", "err_rad": f"{err_rad:.3f}",
            "pred_err": f"{pred_err:.3f}", "nis": f"{nis:.3f}", "latency_ms": f"{lat:.2f}",
            "fps": f"{fps:.1f}", "sigma_u": f"{float(d.sigma_u):.2f}", "sigma_v": f"{float(d.sigma_v):.2f}",
        })

        self._audit_events(lock, nis_ok, lat_ok, err_ok, fps_ok, frame, str(d.motion_model))
        self._refresh_cards(err_rad, lat, fps)
        self._refresh_charts()
        self._refresh_spec_table()

    def _audit_events(self, lock: str, nis_ok: bool, lat_ok: bool, err_ok: bool, fps_ok: bool, frame: int, motion: str) -> None:
        prev = self._prev
        t = self._t

        # lock state machine transitions
        if lock != prev["lock"]:
            if lock == "TARGET LOST":
                self._loss_started = t
                self.event_log.add_event(t, frame, "ERROR", "TRACKER", "Target lost — entering search")
            elif lock == "SEARCHING":
                self.event_log.add_event(t, frame, "WARN", "TRACKER", "Search pattern active")
            elif lock == "REACQUIRING":
                self.event_log.add_event(t, frame, "WARN", "TRACKER", "Candidate acquired — confirming lock")
            elif lock == "LOCKED":
                if self._loss_started is not None:
                    duration = t - self._loss_started
                    self._loss_started = None
                    verdict = "OK" if duration <= SPEC_MAX_REACQ else "WARN"
                    self.event_log.add_event(t, frame, verdict, "TRACKER", f"Lock restored after {duration:.2f} s (reacquisition)")
                else:
                    self.event_log.add_event(t, frame, "OK", "TRACKER", "Lock established (acquisition)")
            prev["lock"] = lock

        # threshold edges (log transitions only, not sustained states)
        if nis_ok and not prev["nis_ok"]:
            self.event_log.add_event(t, frame, "OK", "FILTER", "NIS back inside χ² 95 % gate")
        elif not nis_ok and prev["nis_ok"]:
            self.event_log.add_event(t, frame, "WARN", "FILTER", "NIS gate violation — innovation inconsistent")
        prev["nis_ok"] = nis_ok

        if err_ok and not prev["err_ok"]:
            self.event_log.add_event(t, frame, "OK", "LOCALIZATION", "Tracking error back within 10 px spec")
        elif not err_ok and prev["err_ok"]:
            self.event_log.add_event(t, frame, "WARN", "LOCALIZATION", "Tracking error exceeds 10 px spec")
        prev["err_ok"] = err_ok

        if lat_ok and not prev["lat_ok"]:
            self.event_log.add_event(t, frame, "OK", "TIMING", "Frame latency back under 50 ms deadline")
        elif not lat_ok and prev["lat_ok"]:
            self.event_log.add_event(t, frame, "WARN", "TIMING", "Frame deadline miss (> 50 ms)")
        prev["lat_ok"] = lat_ok

        if fps_ok and not prev["fps_ok"]:
            self.event_log.add_event(t, frame, "OK", "SYSTEM", "Processing rate recovered above 20 FPS")
        elif not fps_ok and prev["fps_ok"]:
            self.event_log.add_event(t, frame, "ERROR", "SYSTEM", "Processing rate below 20 FPS spec")
        prev["fps_ok"] = fps_ok

        if motion != prev["motion"]:
            self.event_log.add_event(t, frame, "INFO", "SCENARIO", f"Motion model changed → {motion}")
            prev["motion"] = motion

    def _refresh_cards(self, err_rad: float, lat: float, fps: float) -> None:
        s = self._session_stats()
        lat_sorted = sorted(self.lat_all)
        self.cards["FPS"].set_value(f"{fps:.1f}")
        self.cards["Latency μ / P95"].set_value(f"{lat:.0f} / {s['lat_p95']:.0f}", "ms")
        self.cards["Mean Error"].set_value(f"{s['mean_err']:.2f}", "px")
        self.cards["RMSE"].set_value(f"{s['rmse']:.2f}", "px")
        self.cards["Max Error"].set_value(f"{s['max_err']:.2f}", "px")
        self.cards["Lock Retention"].set_value(f"{s['lock_pct']:.1f}", "%")
        self.cards["NIS In-Gate"].set_value(f"{s['nis_pct']:.1f}", "%")
        self.cards["Deadline Misses"].set_value(str(self.deadline_misses))
        self.clock.setText(f"T+ {self._t:.1f} s   ·   {self.frames} frames")
        err_sorted = sorted(self.err_hist)
        p50 = _percentile(err_sorted, 50)
        p95 = _percentile(err_sorted, 95)
        p99 = _percentile(err_sorted, 99)
        self.summary.setText(
            f"SESSION SUMMARY  ▸  duration {self._t:.1f} s  ·  frames {self.frames}  ·  RMSE {s['rmse']:.2f} px  ·  "
            f"error P50/P95/P99 {p50:.1f}/{p95:.1f}/{p99:.1f} px  ·  "
            f"loss {s['loss_pct']:.2f} %  ·  deadline misses {self.deadline_misses}"
        )

    def _refresh_charts(self) -> None:
        t = list(self.t_hist)
        self.trace_error.set_series([("radial error", t, list(self.err_hist), ORANGE)])
        self.trace_xy.set_series([
            ("error X", t, list(self.errx_hist), BLUE),
            ("error Y", t, list(self.erry_hist), PURPLE),
        ])
        self.trace_nis.set_series([("NIS", t, list(self.nis_hist), ACCENT)])
        self.trace_lat.set_series([("latency", t, list(self.lat_hist), GOLD)])
        self.trace_fps.set_series([("fps", t, list(self.fps_hist), GREEN)])
        self.trace_lock.set_series([("lock level", t, list(self.lock_hist), BLUE)])
        self.scope.set_series([
            ("truth", list(self.u_hist), list(self.v_hist), GOLD),
            ("estimate", list(self.eu_hist), list(self.ev_hist), ACCENT),
            ("prediction", list(self.pu_hist), list(self.pv_hist), ORANGE),
        ])
        self.hist_error.set_values(list(self.err_hist))
        err_sorted = sorted(self.err_hist)
        if err_sorted:
            cdf_x = [_percentile(err_sorted, q) for q in range(0, 101, 5)]
            cdf_y = list(range(0, 101, 5))
            self.hist_cdf.set_series([("CDF", cdf_x, cdf_y, ACCENT)])

    def _refresh_spec_table(self) -> None:
        s = self._session_stats()
        for r, (_, req, key, unit, ok) in enumerate(SPEC_ROWS):
            val = s[key]
            precision = 1 if key == "fps_mean" else 2
            self.spec_table.item(r, 2).setText(f"{val:.{precision}f} {unit}")
            passed = ok(s)
            status = self.spec_table.item(r, 3)
            status.setText("✓ PASS" if passed else "✗ FAIL")
            status.setForeground(Qt.green if passed else Qt.red)


class AnalyticsWorkspace(QWidget):
    """Analytics section: debugger dashboard + classic performance analysis views."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.dashboard = _SessionDashboard()
        self.analysis = AnalysisWorkspace()
        self.tabs.addTab(self.dashboard, "Debug Dashboard")
        self.tabs.addTab(self.analysis, "Performance Analysis")
        layout.addWidget(self.tabs)

    def update_telemetry(self, d: Any) -> None:
        self.dashboard.update_telemetry(d)
        self.analysis.update_telemetry(d)
