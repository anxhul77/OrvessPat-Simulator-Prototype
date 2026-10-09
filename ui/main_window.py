"""OrvessPat Sim — Professional Optical Camera Tracking Workstation UI.

Refactored Architecture & Product Identity:
- System: AI-Based Virtual Camera Tracking System for Coarse Alignment of Mobile FSOC Terminals
- Configuration & debugging tool layout: Live Debug Cockpit, Configuration Hub, Pipeline Inspector,
  Analytics Dashboard, Diagnostics, Research
- Interactive Target Loss -> Searching -> Reacquiring -> Locked State Machine
- Restoration of Research Lab (EXP 00-23) & Monte Carlo Statistical Validation
- Top CAD Ribbon Toolbar
- Left Project / Scene Explorer Tree
- Central CAD Viewport Canvas & Dedicated Prediction / Search Workspaces
- Right CAD Parameter Inspector (PropertyStore grid)
- Bottom Simulation Timeline Dock & Telemetry Status Bar
- Visual Palette: VS Code Black Theme colors (#1e1e1e, #252526, #3c3c3c, #007acc)
"""

import math
from collections import deque
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mock.simulation import MockSimulation
from pages.analytics import AnalyticsWorkspace
from pages.config_pages import (
    camera,
    configuration_hub,
    environment,
    live,
    monte_carlo,
    research,
    scenario,
    target,
    tracking,
)
from pages.workspaces import (
    BenchmarkWorkspace,
    DebugWorkspace,
    TrackingWorkspace,
)
from ui.properties import Inspector, PropertyStore
from ui.widgets import Plot

# Workspace stack indexes
WS_LIVE = 0        # Home / Live debug cockpit
WS_CONFIG = 1      # Configuration hub (sidebar over all settings modules)
WS_PIPELINE = 2    # Tracking pipeline inspector
WS_ANALYTICS = 3   # Analytics dashboard
WS_BENCHMARK = 4   # Video benchmark
WS_DEBUG = 5       # Debug console / technical logs
WS_RESEARCH = 6    # Research lab (EXP 00-23)
WS_MONTE = 7       # Monte Carlo validation

STYLE = """
/* ORVESSPAT SIM WORKSTATION — VS CODE DARK COLOR PALETTE */
QWidget {
    background: #1e1e1e;
    color: #cccccc;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11px;
}

QMainWindow {
    background: #1e1e1e;
}

/* Desktop Menu Bar */
QMenuBar {
    background: #181818;
    color: #cccccc;
    border-bottom: 1px solid #333333;
    padding: 2px 4px;
}

QMenuBar::item {
    background: transparent;
    padding: 4px 8px;
    border-radius: 2px;
}

QMenuBar::item:selected {
    background: #2d2d2d;
    color: #ffffff;
}

QMenu {
    background: #252526;
    color: #cccccc;
    border: 1px solid #3c3c3c;
    padding: 4px;
}

QMenu::item {
    padding: 5px 24px 5px 12px;
    border-radius: 2px;
}

QMenu::item:selected {
    background: #04395e;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #3c3c3c;
    margin: 4px 0;
}

/* Ribbon Header Container */
QFrame#cad-ribbon-frame {
    background: #252526;
    border-bottom: 1px solid #3c3c3c;
}

/* Ribbon Tabs */
QTabBar#ribbon-tabs {
    background: #181818;
    border-bottom: 1px solid #3c3c3c;
}

QTabBar#ribbon-tabs::tab {
    background: #181818;
    color: #888888;
    padding: 6px 14px;
    border: 1px solid transparent;
    border-bottom: none;
    font-weight: 700;
    font-size: 10px;
    letter-spacing: 1px;
}

QTabBar#ribbon-tabs::tab:hover {
    background: #252526;
    color: #cccccc;
}

QTabBar#ribbon-tabs::tab:selected {
    background: #252526;
    color: #007acc;
    border: 1px solid #3c3c3c;
    border-top: 2px solid #007acc;
    border-bottom: 1px solid #252526;
}

/* Ribbon Action Groups */
QGroupBox.cad-ribbon-group {
    background: #202021;
    border: 1px solid #333333;
    border-radius: 3px;
    margin-top: 0px;
    padding-top: 4px;
}

QGroupBox.cad-ribbon-group::title {
    subcontrol-origin: margin;
    subcontrol-position: bottom center;
    padding: 2px 4px;
    color: #777777;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* Ribbon Buttons */
QToolButton.cad-ribbon-btn {
    background: #2d2d2d;
    color: #cccccc;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    padding: 4px 8px;
    font-size: 10px;
    font-weight: 600;
}

QToolButton.cad-ribbon-btn:hover {
    background: #37373d;
    border-color: #007acc;
    color: #ffffff;
}

QToolButton.cad-ribbon-btn-primary {
    background: #0e639c;
    color: #ffffff;
    border: 1px solid #1177bb;
    font-weight: 700;
}

QToolButton.cad-ribbon-btn-primary:hover {
    background: #1177bb;
}

/* Panels & Dock Containers */
QFrame.cad-panel {
    background: #252526;
    border: 1px solid #3c3c3c;
}

QLabel.cad-panel-header {
    background: #181818;
    color: #569cd6;
    font-weight: 700;
    font-size: 10px;
    letter-spacing: 1px;
    padding: 7px 10px;
    border-bottom: 1px solid #3c3c3c;
}

/* Project / Scene Explorer Tree + Configuration Sidebar */
QTreeWidget, QListWidget {
    background: #252526;
    color: #cccccc;
    border: none;
    outline: none;
    font-size: 11px;
}

QTreeWidget::item, QListWidget::item {
    padding: 4px 2px;
}

QTreeWidget::item:hover, QListWidget::item:hover {
    background: #2a2d2e;
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background: #04395e;
    color: #ffffff;
}

/* Telemetry Metrics Card Layout */
QFrame.metric {
    background: #252526;
    border: 1px solid #3c3c3c;
    border-left: 3px solid #007acc;
    border-radius: 2px;
    min-height: 52px;
    padding: 6px 10px;
}

QLabel.metric-title {
    color: #858585;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    margin-bottom: 2px;
}

QLabel.metric-value {
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
}

/* Status Bar */
QStatusBar {
    background: #007acc;
    color: #ffffff;
    font-family: 'Consolas', 'Segoe UI', monospace;
    font-size: 11px;
}

/* Splitter Handles */
QSplitter::handle {
    background: #3c3c3c;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

/* Inputs & Form Controls */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
    background: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    border-radius: 2px;
    padding: 4px 6px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #007acc;
}

QPushButton {
    background: #2d2d2d;
    color: #cccccc;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    padding: 5px 12px;
    font-size: 11px;
}

QPushButton:hover {
    background: #37373d;
    border-color: #007acc;
    color: #ffffff;
}

QPushButton.primary {
    background: #0e639c;
    color: #ffffff;
    border: 1px solid #1177bb;
    font-weight: 700;
}

QPushButton.primary:hover {
    background: #1177bb;
}

QGroupBox.section {
    background: #252526;
    border: 1px solid #3c3c3c;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox.section::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #569cd6;
    background: #252526;
    font-weight: 600;
}

QLabel.status-pill {
    background: #0e3a2f;
    border: 1px solid #165b4c;
    color: #4ec9b0;
    padding: 4px 10px;
    font-weight: 600;
    border-radius: 2px;
}

QLabel.telemetry-item {
    color: #cccccc;
    background: #1e1e1e;
    border-bottom: 1px solid #3c3c3c;
    padding: 6px 8px;
    font-family: 'Consolas', monospace;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OrvessPat Sim — AI Virtual Camera Tracking Workstation for FSOC Coarse Alignment")
        self.resize(1600, 960)
        self.setStyleSheet(STYLE)

        # Simulation backend
        self.sim = MockSimulation()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.setInterval(80)

        # Shared property store
        self.store = PropertyStore(self)
        self.store.changed.connect(self._on_property_changed)

        # Build UI Architecture
        self._build_menu_bar()
        
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Ribbon Toolbar
        root_layout.addWidget(self._build_ribbon())

        # 2. Main Splitter (Left Scene Explorer | Central Canvas Viewport | Right Parameter Inspector)
        self.central_splitter = QSplitter(Qt.Horizontal)
        self.central_splitter.setChildrenCollapsible(False)

        # 2a. Left Panel: Project / Scene Explorer Tree
        self.scene_explorer_panel = self._build_scene_explorer()
        self.central_splitter.addWidget(self.scene_explorer_panel)

        # 2b. Center: Stacked Workspaces
        self.workspace_stack = QStackedWidget()
        self._build_workspaces()
        self.central_splitter.addWidget(self.workspace_stack)

        # 2c. Right Panel: Parameter Inspector
        self.inspector_panel = self._build_inspector_panel()
        self.central_splitter.addWidget(self.inspector_panel)

        # Set splitter layout bounds (Scene Explorer ~230px, Canvas ~1090px, Inspector ~280px)
        self.central_splitter.setSizes([230, 1090, 280])
        self.central_splitter.setStretchFactor(0, 0)
        self.central_splitter.setStretchFactor(1, 1)
        self.central_splitter.setStretchFactor(2, 0)
        root_layout.addWidget(self.central_splitter, 1)

        # 3. Bottom Timeline Dock
        root_layout.addWidget(self._build_timeline_panel())

        # 4. Bottom Status Bar
        self.setStatusBar(self._build_statusbar())

        # History buffers for live telemetry plots
        self.history = [deque(maxlen=160) for _ in range(3)]
        for plot in self.findChildren(Plot):
            plot.update_values([2 + math.sin(i * 0.12) + 0.25 * math.cos(i * 0.43) for i in range(100)])

        # Start live simulation demo on launch
        self.start_simulation()

    def _build_menu_bar(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Scenario", lambda: self._toast("New Scenario created"))
        file_menu.addAction("Open Scenario...", lambda: self._toast("Open Scenario dialog"))
        file_menu.addAction("Save Scenario", lambda: self._toast("Scenario saved"))
        file_menu.addAction("Save As...", lambda: self._toast("Save As dialog"))
        file_menu.addSeparator()
        file_menu.addAction("Export Config...", lambda: self._toast("Configuration exported"))
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        # Edit
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Undo", lambda: self._toast("Undo performed"))
        edit_menu.addAction("Redo", lambda: self._toast("Redo performed"))
        edit_menu.addSeparator()
        edit_menu.addAction("Reset Parameters", self.reset_simulation)

        # View
        view_menu = menubar.addMenu("View")
        view_menu.addAction("Live Debug Cockpit", lambda: self._switch_workspace(WS_LIVE))
        view_menu.addAction("Configuration", lambda: self._switch_workspace(WS_CONFIG))
        view_menu.addAction("Tracking Pipeline", lambda: self._switch_workspace(WS_PIPELINE))
        view_menu.addAction("Analytics Dashboard", lambda: self._switch_workspace(WS_ANALYTICS))
        view_menu.addAction("Video Benchmark", lambda: self._switch_workspace(WS_BENCHMARK))
        view_menu.addAction("Debug Console", lambda: self._switch_workspace(WS_DEBUG))
        view_menu.addAction("Research Lab", lambda: self._switch_workspace(WS_RESEARCH))
        view_menu.addAction("Monte Carlo Validation", lambda: self._switch_workspace(WS_MONTE))
        view_menu.addSeparator()
        view_menu.addAction("Toggle Scene Explorer", lambda: self.scene_explorer_panel.setVisible(not self.scene_explorer_panel.isVisible()))
        view_menu.addAction("Toggle Inspector", lambda: self.inspector_panel.setVisible(not self.inspector_panel.isVisible()))
        view_menu.addAction("Toggle Timeline Dock", lambda: self.timeline_panel.setVisible(not self.timeline_panel.isVisible()))
        view_menu.addAction("Reset Layout", self._reset_layout)

        # Simulation
        sim_menu = menubar.addMenu("Simulation")
        sim_menu.addAction("Start ▶", self.start_simulation)
        sim_menu.addAction("Pause ⏸", lambda: self.timer.stop())
        sim_menu.addAction("Stop ■", self.stop_simulation)
        sim_menu.addAction("Reset ↻", self.reset_simulation)
        sim_menu.addSeparator()
        sim_menu.addAction("Trigger Target Loss Demo", self._trigger_loss_demo)
        sim_menu.addAction("Step Frame", lambda: self.tick())

        # Optics
        optics_menu = menubar.addMenu("Optics")
        optics_menu.addAction("Lens & Sensor Parameters", lambda: self._open_configuration("Camera & Optics"))
        optics_menu.addAction("Reticle Grid Toggle", lambda: self.pages["Live Tracking"].camera.toggle_grid())
        optics_menu.addAction("Center Canvas", lambda: self._switch_workspace(WS_LIVE))

        # Target
        target_menu = menubar.addMenu("Target")
        target_menu.addAction("Beacon Signature", lambda: self._open_configuration("Target & Beacon"))
        target_menu.addAction("Trajectory Model", lambda: self.inspector.select("Motion"))

        # Pipeline
        pipeline_menu = menubar.addMenu("Pipeline")
        pipeline_menu.addAction("Tracking Configuration", lambda: self._open_configuration("Tracking Pipeline"))
        pipeline_menu.addAction("Pipeline Inspector", lambda: self._switch_workspace(WS_PIPELINE))
        pipeline_menu.addAction("Localization Engine", lambda: self.inspector.select("Localization"))
        pipeline_menu.addAction("Kalman Filter", lambda: self.inspector.select("Kalman Filter"))
        pipeline_menu.addAction("Adaptive Search", lambda: self.inspector.select("Adaptive Search"))

        # Research
        research_menu = menubar.addMenu("Research")
        research_menu.addAction("Research Lab Experiments", lambda: self._switch_workspace(WS_RESEARCH))
        research_menu.addAction("Monte Carlo Validation", lambda: self._switch_workspace(WS_MONTE))

        # Window
        window_menu = menubar.addMenu("Window")
        window_menu.addAction("Show All Panels", lambda: [p.show() for p in (self.scene_explorer_panel, self.inspector_panel, self.timeline_panel)])

        # Help
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("OrvessPat Sim Documentation", lambda: self._toast("OrvessPat Sim Workstation v1.0"))
        help_menu.addAction("About OrvessPat Sim", lambda: QMessageBox.about(self, "About OrvessPat Sim", "OrvessPat Sim — AI Virtual Camera Tracking System for FSOC Coarse Alignment\nProfessional Workstation UI\n\nVersion 1.0"))

    def _build_ribbon(self) -> QWidget:
        container = QFrame()
        container.setObjectName("cad-ribbon-frame")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Ribbon Tabs Header
        self.ribbon_tabs = QTabBar()
        self.ribbon_tabs.setObjectName("ribbon-tabs")
        tabs = [
            "HOME / LIVE DEBUG",
            "CONFIGURATION",
            "TRACKING PIPELINE",
            "ANALYTICS",
            "DIAGNOSTICS",
            "RESEARCH",
        ]
        for t in tabs:
            self.ribbon_tabs.addTab(t)

        self.ribbon_tabs.currentChanged.connect(self._on_ribbon_tab_changed)
        layout.addWidget(self.ribbon_tabs)

        # Ribbon Action Content Container
        self.ribbon_stack = QStackedWidget()
        self.ribbon_stack.setFixedHeight(54)

        # Panel 0: Home / Live Debug Controls
        p0 = QWidget(); l0 = QHBoxLayout(p0); l0.setContentsMargins(8, 4, 8, 4); l0.setSpacing(8)
        g_sim = QGroupBox("SIMULATION EXECUTION")
        g_sim.setProperty("class", "cad-ribbon-group")
        l_sim = QHBoxLayout(g_sim); l_sim.setContentsMargins(4, 2, 4, 2)
        b_start = QToolButton(); b_start.setText("▶ START"); b_start.setProperty("class", "cad-ribbon-btn-primary"); b_start.clicked.connect(self.start_simulation)
        b_pause = QToolButton(); b_pause.setText("⏸ PAUSE"); b_pause.setProperty("class", "cad-ribbon-btn"); b_pause.clicked.connect(lambda: self.timer.stop())
        b_stop = QToolButton(); b_stop.setText("■ STOP"); b_stop.setProperty("class", "cad-ribbon-btn"); b_stop.clicked.connect(self.stop_simulation)
        b_reset = QToolButton(); b_reset.setText("↻ RESET"); b_reset.setProperty("class", "cad-ribbon-btn"); b_reset.clicked.connect(self.reset_simulation)
        b_step = QToolButton(); b_step.setText("STEP 1f"); b_step.setProperty("class", "cad-ribbon-btn"); b_step.clicked.connect(lambda: self.tick())
        l_sim.addWidget(b_start); l_sim.addWidget(b_pause); l_sim.addWidget(b_stop); l_sim.addWidget(b_reset); l_sim.addWidget(b_step)
        l0.addWidget(g_sim)

        g_view = QGroupBox("CANVAS VIEW")
        g_view.setProperty("class", "cad-ribbon-group")
        l_view = QHBoxLayout(g_view); l_view.setContentsMargins(4, 2, 4, 2)
        b_grid = QToolButton(); b_grid.setText("RETICLE GRID"); b_grid.setProperty("class", "cad-ribbon-btn"); b_grid.clicked.connect(lambda: self.pages["Live Tracking"].camera.toggle_grid())
        b_fit = QToolButton(); b_fit.setText("FIT CANVAS"); b_fit.setProperty("class", "cad-ribbon-btn"); b_fit.clicked.connect(lambda: self._switch_workspace(WS_LIVE))
        l_view.addWidget(b_grid); l_view.addWidget(b_fit)
        l0.addWidget(g_view)

        g_dbg = QGroupBox("DEBUG")
        g_dbg.setProperty("class", "cad-ribbon-group")
        l_dbg = QHBoxLayout(g_dbg); l_dbg.setContentsMargins(4, 2, 4, 2)
        b_loss = QToolButton(); b_loss.setText("TRIGGER LOSS"); b_loss.setProperty("class", "cad-ribbon-btn"); b_loss.clicked.connect(self._trigger_loss_demo)
        b_state = QToolButton(); b_state.setText("STATE VECTOR"); b_state.setProperty("class", "cad-ribbon-btn"); b_state.clicked.connect(lambda: self._switch_workspace(WS_LIVE))
        l_dbg.addWidget(b_loss); l_dbg.addWidget(b_state)
        l0.addWidget(g_dbg)
        l0.addStretch(); self.ribbon_stack.addWidget(p0)

        # Panel 1: Configuration Hub
        p1 = QWidget(); l1 = QHBoxLayout(p1); l1.setContentsMargins(8, 4, 8, 4); l1.setSpacing(8)
        g_cfg = QGroupBox("SETTINGS MODULES")
        g_cfg.setProperty("class", "cad-ribbon-group")
        l_cfg = QHBoxLayout(g_cfg); l_cfg.setContentsMargins(4, 2, 4, 2)
        for label, module in [("SCENARIO", "Scenario"), ("CAMERA & OPTICS", "Camera & Optics"), ("TARGET & BEACON", "Target & Beacon"), ("ENVIRONMENT", "Environment"), ("TRACKING CONFIG", "Tracking Pipeline")]:
            b = QToolButton(); b.setText(label); b.setProperty("class", "cad-ribbon-btn"); b.clicked.connect(lambda _, m=module: self._open_configuration(m))
            l_cfg.addWidget(b)
        l1.addWidget(g_cfg); l1.addStretch(); self.ribbon_stack.addWidget(p1)

        # Panel 2: Tracking Pipeline
        p2 = QWidget(); l2 = QHBoxLayout(p2); l2.setContentsMargins(8, 4, 8, 4); l2.setSpacing(8)
        g_pipe = QGroupBox("ALGORITHM STAGES")
        g_pipe.setProperty("class", "cad-ribbon-group")
        l_pipe = QHBoxLayout(g_pipe); l_pipe.setContentsMargins(4, 2, 4, 2)
        b_det = QToolButton(); b_det.setText("DETECTOR"); b_det.setProperty("class", "cad-ribbon-btn"); b_det.clicked.connect(lambda: self.inspector.select("Detector"))
        b_loc = QToolButton(); b_loc.setText("LOCALIZATION"); b_loc.setProperty("class", "cad-ribbon-btn"); b_loc.clicked.connect(lambda: self.inspector.select("Localization"))
        b_kf = QToolButton(); b_kf.setText("KALMAN ESTIMATOR"); b_kf.setProperty("class", "cad-ribbon-btn"); b_kf.clicked.connect(lambda: self.inspector.select("Kalman Filter"))
        b_search = QToolButton(); b_search.setText("ADAPTIVE SEARCH"); b_search.setProperty("class", "cad-ribbon-btn"); b_search.clicked.connect(lambda: self.inspector.select("Adaptive Search"))
        l_pipe.addWidget(b_det); l_pipe.addWidget(b_loc); l_pipe.addWidget(b_kf); l_pipe.addWidget(b_search)
        l2.addWidget(g_pipe); l2.addStretch(); self.ribbon_stack.addWidget(p2)

        # Panel 3: Analytics
        p3 = QWidget(); l3 = QHBoxLayout(p3); l3.setContentsMargins(8, 4, 8, 4); l3.setSpacing(8)
        g_ana = QGroupBox("SESSION ANALYTICS")
        g_ana.setProperty("class", "cad-ribbon-group")
        l_ana = QHBoxLayout(g_ana); l_ana.setContentsMargins(4, 2, 4, 2)
        b_dash = QToolButton(); b_dash.setText("PERFORMANCE DASHBOARD"); b_dash.setProperty("class", "cad-ribbon-btn"); b_dash.clicked.connect(lambda: self._switch_workspace(WS_ANALYTICS))
        l_ana.addWidget(b_dash)
        l3.addWidget(g_ana); l3.addStretch(); self.ribbon_stack.addWidget(p3)

        # Panel 4: Diagnostics
        p4 = QWidget(); l4 = QHBoxLayout(p4); l4.setContentsMargins(8, 4, 8, 4); l4.setSpacing(8)
        g_bm = QGroupBox("DIAGNOSTIC TOOLS")
        g_bm.setProperty("class", "cad-ribbon-group")
        l_bm = QHBoxLayout(g_bm); l_bm.setContentsMargins(4, 2, 4, 2)
        b_vid = QToolButton(); b_vid.setText("VIDEO REPLAY"); b_vid.setProperty("class", "cad-ribbon-btn"); b_vid.clicked.connect(lambda: self._switch_workspace(WS_BENCHMARK))
        b_log = QToolButton(); b_log.setText("DEBUG CONSOLE"); b_log.setProperty("class", "cad-ribbon-btn"); b_log.clicked.connect(lambda: self._switch_workspace(WS_DEBUG))
        l_bm.addWidget(b_vid); l_bm.addWidget(b_log)
        l4.addWidget(g_bm); l4.addStretch(); self.ribbon_stack.addWidget(p4)

        # Panel 5: Research
        p5 = QWidget(); l5 = QHBoxLayout(p5); l5.setContentsMargins(8, 4, 8, 4); l5.setSpacing(8)
        g_res = QGroupBox("RESEARCH EXPERIMENTS")
        g_res.setProperty("class", "cad-ribbon-group")
        l_res = QHBoxLayout(g_res); l_res.setContentsMargins(4, 2, 4, 2)
        b_lab = QToolButton(); b_lab.setText("RESEARCH LAB (EXP 00-23)"); b_lab.setProperty("class", "cad-ribbon-btn"); b_lab.clicked.connect(lambda: self._switch_workspace(WS_RESEARCH))
        b_mc = QToolButton(); b_mc.setText("MONTE CARLO VALIDATION"); b_mc.setProperty("class", "cad-ribbon-btn"); b_mc.clicked.connect(lambda: self._switch_workspace(WS_MONTE))
        l_res.addWidget(b_lab); l_res.addWidget(b_mc)
        l5.addWidget(g_res); l5.addStretch(); self.ribbon_stack.addWidget(p5)

        layout.addWidget(self.ribbon_stack)
        return container

    def _build_scene_explorer(self) -> QFrame:
        """Project / Scene Explorer Tree Panel."""
        panel = QFrame()
        panel.setProperty("class", "cad-panel")
        panel.setObjectName("scene-panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("PROJECT / SCENE EXPLORER")
        title.setProperty("class", "cad-panel-header")
        layout.addWidget(title)

        self.scene_tree = QTreeWidget()
        self.scene_tree.setHeaderHidden(True)

        # Root scenario node
        root_item = QTreeWidgetItem(self.scene_tree, ["▼ OrvessPat_Demo_Scenario"])
        root_item.setData(0, Qt.UserRole, "Scenario")

        # Environment sub-tree
        env_item = QTreeWidgetItem(root_item, ["▼ Environment"])
        env_item.setData(0, Qt.UserRole, "Environment")
        for sub in ["Background", "Noise", "Atmosphere", "Platform Motion", "Camera Jitter"]:
            child = QTreeWidgetItem(env_item, [f"  • {sub}"])
            child.setData(0, Qt.UserRole, sub)

        # Camera sub-tree
        cam_item = QTreeWidgetItem(root_item, ["▼ Camera Subsystem"])
        cam_item.setData(0, Qt.UserRole, "Camera")
        for sub in ["Virtual Camera", "Optics", "PSF", "Actuator"]:
            child = QTreeWidgetItem(cam_item, [f"  • {sub}"])
            child.setData(0, Qt.UserRole, sub)

        # Target sub-tree
        target_item = QTreeWidgetItem(root_item, ["▼ Target & Beacon"])
        target_item.setData(0, Qt.UserRole, "Targets")
        for sub, key in [("Beacon_01 (Optical Beacon)", "Beacon_01"), ("Motion Model", "Motion")]:
            child = QTreeWidgetItem(target_item, [f"  • {sub}"])
            child.setData(0, Qt.UserRole, key)

        # Tracking sub-tree
        track_item = QTreeWidgetItem(root_item, ["▼ Tracking System"])
        track_item.setData(0, Qt.UserRole, "Tracking System")
        for sub in ["Preprocessing", "Detector", "Candidate Filter", "Localization", "ROI", "Kalman Filter", "Prediction", "Adaptive Search"]:
            child = QTreeWidgetItem(track_item, [f"  • {sub}"])
            child.setData(0, Qt.UserRole, sub)

        # Analysis node
        analysis_item = QTreeWidgetItem(root_item, ["▼ Analysis & Research"])
        analysis_item.setData(0, Qt.UserRole, "Analysis")
        for sub in ["Analytics Dashboard", "Research Lab (EXP 00-23)", "Monte Carlo Validation", "Debug Logs"]:
            key_map = {
                "Analytics Dashboard": "Analytics Dashboard",
                "Research Lab (EXP 00-23)": "Research Lab",
                "Monte Carlo Validation": "Monte Carlo",
                "Debug Logs": "Debug Logs",
            }
            child = QTreeWidgetItem(analysis_item, [f"  • {sub}"])
            child.setData(0, Qt.UserRole, key_map[sub])

        self.scene_tree.expandAll()
        self.scene_tree.itemClicked.connect(self._on_scene_item_clicked)
        layout.addWidget(self.scene_tree, 1)

        return panel

    def _build_workspaces(self):
        self.pages = {}

        # 0. Home: Live Debug Cockpit (viewport + state vector + live plots)
        self.pages["Live Tracking"] = live(self.sim)
        self.workspace_stack.addWidget(self.pages["Live Tracking"])

        # 1. Configuration Hub (sidebar over all settings modules)
        self.pages["Configuration"] = configuration_hub()
        self.workspace_stack.addWidget(self.pages["Configuration"])

        # 2. Tracking Pipeline Inspector
        self.pages["Tracking Pipeline"] = TrackingWorkspace()
        self.workspace_stack.addWidget(self.pages["Tracking Pipeline"])

        # 3. Analytics Dashboard (session accumulation + performance analysis)
        self.pages["Analytics"] = AnalyticsWorkspace()
        self.workspace_stack.addWidget(self.pages["Analytics"])

        # 4. Video Benchmark
        self.pages["Video Benchmark"] = BenchmarkWorkspace()
        self.workspace_stack.addWidget(self.pages["Video Benchmark"])

        # 5. Debug Console / Technical Logs
        self.pages["Debug Logs"] = DebugWorkspace()
        self.workspace_stack.addWidget(self.pages["Debug Logs"])

        # 6. Research Lab Experiments
        self.pages["Research Lab"] = research()
        self.workspace_stack.addWidget(self.pages["Research Lab"])

        # 7. Monte Carlo Statistical Validation
        self.pages["Monte Carlo"] = monte_carlo()
        self.workspace_stack.addWidget(self.pages["Monte Carlo"])

        # Wire Scenario execution buttons inside the Configuration hub
        for b in self.pages["Configuration"].findChildren(QPushButton):
            if b.text() == "START SIMULATION":
                b.clicked.connect(self.start_simulation)
            elif b.text() == "STOP":
                b.clicked.connect(self.stop_simulation)
            elif b.text() == "RESET":
                b.clicked.connect(self.reset_simulation)

    def _open_configuration(self, module: str):
        """Switch to the Configuration hub and open the given settings module."""
        self._switch_workspace(WS_CONFIG)
        self.pages["Configuration"].select_page(module)

    def _build_inspector_panel(self) -> QFrame:
        panel = QFrame()
        panel.setProperty("class", "cad-panel")
        panel.setObjectName("inspector-panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("PARAMETER INSPECTOR")
        title.setProperty("class", "cad-panel-header")
        layout.addWidget(title)

        self.inspector = Inspector(self.store)
        self.inspector.openRequested.connect(self._on_inspector_open_requested)
        layout.addWidget(self.inspector, 1)

        return panel

    def _build_timeline_panel(self) -> QFrame:
        self.timeline_panel = QFrame()
        self.timeline_panel.setProperty("class", "cad-panel")
        self.timeline_panel.setObjectName("timeline-panel")
        self.timeline_panel.setFixedHeight(46)
        layout = QHBoxLayout(self.timeline_panel)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(10)

        # Controls
        play_btn = QToolButton()
        play_btn.setText("▶ PLAY")
        play_btn.clicked.connect(self.start_simulation)
        layout.addWidget(play_btn)

        pause_btn = QToolButton()
        pause_btn.setText("⏸ PAUSE")
        pause_btn.clicked.connect(lambda: self.timer.stop())
        layout.addWidget(pause_btn)

        step_btn = QToolButton()
        step_btn.setText("STEP")
        step_btn.clicked.connect(lambda: self.tick())
        layout.addWidget(step_btn)

        # Timeline playhead
        time_start = QLabel("0.0s")
        time_start.setStyleSheet("color:#858585; font-family:Consolas;")
        layout.addWidget(time_start)

        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setRange(0, 1200)
        self.timeline_slider.setValue(0)
        layout.addWidget(self.timeline_slider, 1)

        time_end = QLabel("60.0s")
        time_end.setStyleSheet("color:#858585; font-family:Consolas;")
        layout.addWidget(time_end)

        # Time Scale Combo
        layout.addWidget(QLabel("SPEED:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5×", "1.0×", "2.0×", "5.0×"])
        self.speed_combo.setCurrentText("1.0×")
        layout.addWidget(self.speed_combo)

        # Event Badges
        events = [("ACQ ≤2s ✓", "#0e3a2f", "#4ec9b0"), ("ERR ≤10px ✓", "#0e3a2f", "#4ec9b0"), ("LOSS <5% ✓", "#0e3a2f", "#4ec9b0")]
        for ev, bg, fg in events:
            lbl = QLabel(ev)
            lbl.setStyleSheet(f"background:{bg}; color:{fg}; border:1px solid {fg}; padding:2px 6px; font-weight:700; font-size:9px;")
            layout.addWidget(lbl)

        return self.timeline_panel

    def _build_statusbar(self) -> QStatusBar:
        sb = QStatusBar()
        sb.showMessage("OrvessPat Sim Nominal  |  Simulation: RUNNING  |  Camera: 640×480 @ 60 FPS  |  Lock: LOCKED  |  FPS: 60.0  |  Latency: 18.2 ms")
        return sb

    def _on_ribbon_tab_changed(self, index: int):
        self.ribbon_stack.setCurrentIndex(index)
        tab_to_workspace = {
            0: WS_LIVE,        # Home / Live Debug
            1: WS_CONFIG,      # Configuration
            2: WS_PIPELINE,    # Tracking Pipeline
            3: WS_ANALYTICS,   # Analytics
            4: WS_BENCHMARK,   # Diagnostics (video replay default)
            5: WS_RESEARCH,    # Research
        }
        if index in tab_to_workspace:
            self._switch_workspace(tab_to_workspace[index])

    def _switch_workspace(self, index: int):
        if index < 0 or index >= self.workspace_stack.count():
            return
        self.workspace_stack.setCurrentIndex(index)

    def _on_scene_item_clicked(self, item: QTreeWidgetItem, column: int):
        component_key = item.data(0, Qt.UserRole)
        if component_key:
            if component_key in ("Scenario", "Environment", "Camera", "Optics", "Targets", "Beacon_01", "Motion"):
                module_map = {
                    "Scenario": "Scenario",
                    "Environment": "Environment",
                    "Camera": "Camera & Optics",
                    "Optics": "Camera & Optics",
                    "Targets": "Target & Beacon",
                    "Beacon_01": "Target & Beacon",
                    "Motion": "Target & Beacon",
                }
                self.inspector.select(component_key)
                self._open_configuration(module_map[component_key])
                return
            self.inspector.select(component_key)
            tab_map = {
                "Tracking System": WS_PIPELINE,
                "Detector": WS_PIPELINE,
                "Localization": WS_PIPELINE,
                "Kalman Filter": WS_PIPELINE,
                "Prediction": WS_PIPELINE,
                "Adaptive Search": WS_PIPELINE,
                "Analysis": WS_ANALYTICS,
                "Analytics Dashboard": WS_ANALYTICS,
                "Research Lab": WS_RESEARCH,
                "Monte Carlo": WS_MONTE,
                "Debug Logs": WS_DEBUG,
            }
            if component_key in tab_map:
                self._switch_workspace(tab_map[component_key])

    def _on_inspector_open_requested(self, component: str):
        self.inspector.select(component)

    def _on_property_changed(self, component: str, field: str, value: object):
        if component == "Motion" and field == "Primary Model":
            self.sim.set_motion_model(str(value))
        self._toast(f"Configuration Updated: {component} / {field} = {value}")

    def _trigger_loss_demo(self):
        self._switch_workspace(0)
        self.sim.trigger_loss_demo()
        self._toast("State Transition Triggered: LOCKED ➔ TARGET LOST ➔ SEARCHING ➔ REACQUIRING ➔ LOCKED")

    def tick(self):
        d = self.sim.tick()

        # Update Live Tracking page
        w = self.pages.get("Live Tracking")
        if w:
            w.camera.set_telemetry(d)
            for m, val, unit in zip(
                w.metrics,
                [
                    f"{d.fps:.1f}",
                    f"{d.track_error:.2f}",
                    "3.14",
                    "98.4",
                    f"{d.nis:.2f}",
                    f"{d.latency:.1f}",
                    f"{d.acq_time:.2f}",
                    f"{d.reacq_time:.2f}",
                ],
                ["", "px", "px", "%", "", "ms", "s", "s"],
            ):
                m.set_value(val, unit)

            debug_map = {
                "STATE": d.lock,
                "FRAME": f"{d.frame:05d}",
                "MODE": d.motion_model,
                "TARGET U,V": f"{d.u:.1f}, {d.v:.1f}",
                "EST U,V": f"{d.est_u:.1f}, {d.est_v:.1f}",
                "PRED U,V": f"{d.pred_u:.1f}, {d.pred_v:.1f}",
                "SEARCH U,V": f"{d.search_u:.1f}, {d.search_v:.1f}",
                "SIGMA U,V": f"{d.sigma_u:.1f} / {d.sigma_v:.1f}",
                "NIS": f"{d.nis:.2f}",
                "FPS": f"{d.fps:.1f}",
                "LATENCY": f"{d.latency:.1f} ms",
            }
            for key, label in w.debug_labels.items():
                label.setText(f"{key}  ▸  {debug_map[key]}")

            for p, history, value in zip(w.plots, self.history, [d.u, d.track_error, d.nis]):
                history.append(value)
                p.update_values(history)

        # Analytics dashboard accumulates session statistics on every tick
        analytics = self.pages.get("Analytics")
        if analytics:
            analytics.update_telemetry(d)

        # Update timeline slider
        self.timeline_slider.setValue(d.frame % 1200)

        # Update status bar
        self.statusBar().showMessage(
            f"OrvessPat Sim Nominal  |  Simulation: RUNNING  |  Frame: {d.frame:05d}  |  Lock: {d.lock}  |  FPS: {d.fps:.1f}  |  Latency: {d.latency:.1f} ms"
        )

        # Forward telemetry to the active workspace (Analytics already updated above)
        current_w = self.workspace_stack.currentWidget()
        if hasattr(current_w, "update_telemetry") and current_w is not self.pages.get("Analytics"):
            current_w.update_telemetry(d)

    def start_simulation(self):
        self.sim.running = True
        self.timer.start()
        self.statusBar().showMessage("OrvessPat Sim Nominal  |  Simulation: RUNNING")

    def stop_simulation(self):
        self.sim.running = False
        self.timer.stop()
        self.statusBar().showMessage("OrvessPat Sim Nominal  |  Simulation: PAUSED")

    def reset_simulation(self):
        self.timer.stop()
        self.sim.reset()
        self.store.reset()
        self.timeline_slider.setValue(0)
        self.statusBar().showMessage("Configuration reset  |  Simulation: IDLE")

    def _reset_layout(self):
        self.scene_explorer_panel.show()
        self.inspector_panel.show()
        self.timeline_panel.show()
        self.central_splitter.setSizes([230, 1090, 280])
        self._toast("OrvessPat Sim layout reset")

    def _toast(self, message: str):
        self.statusBar().showMessage(f"{message}  |  OrvessPat Sim Nominal", 3500)
