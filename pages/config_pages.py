from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QTabWidget, QLabel, QFrame, QGridLayout, QFormLayout, QPlainTextEdit, QTableWidgetItem, QStackedWidget
from ui.widgets import Section, combo, number, text, check, button, Plot, CameraView, Metric, table, StatusPill


def scroll(widget):
    area=QScrollArea(); area.setWidgetResizable(True); area.setFrameShape(QFrame.NoFrame); area.setWidget(widget); return area


def page(title, kicker, content):
    root=QWidget(); lay=QVBoxLayout(root); lay.setContentsMargins(24,20,24,24); lay.setSpacing(14)
    h=QLabel(title); h.setProperty("class","page-title"); lay.addWidget(h)
    k=QLabel(kicker); k.setProperty("class","page-kicker"); lay.addWidget(k)
    lay.addWidget(content,1); return root


def grid_section(title, fields, cols=2):
    s=Section(title); row=0
    for i,(label,widget) in enumerate(fields): s.add_field(label,widget,i//cols,i%cols)
    return s


def scenario():
    box=QWidget(); lay=QVBoxLayout(box); lay.setSpacing(14)
    lay.addWidget(grid_section("SIMULATION SETUP", [("Scenario Name",text("FSOC Demo — Moving Beacon")),("Scenario ID",text("FSOC-DEMO-001")),("Random Seed",number(42,0)),("Duration",number(120,0," s")),("Time Scale",combo(["Real Time","0.5×","1×","2×","5×","10×","Custom"],"1×")),("Start Time",text("2026-09-30 08:42:12"))]))
    desc=Section("MISSION BRIEF"); desc.body.addWidget(QLabel("Description"),0,0); d=QPlainTextEdit("Coarse alignment and beacon tracking demonstration for a mobile FSOC terminal.\nMock data source — simulation backend not connected."); d.setMaximumHeight(70); desc.body.addWidget(d,0,1,1,3); lay.addWidget(desc)
    ctl=Section("EXECUTION & RECORDING")
    ctl.add_field("Execution Mode",combo(["Interactive","Benchmark","Headless","Monte Carlo","Video Input"]),0,0)
    checks=QHBoxLayout()
    for x in ["Record Simulation","Record Frames","Record Metrics","Record Video"]: checks.addWidget(check(x))
    ctl.body.addLayout(checks,1,0,1,4); actions=QHBoxLayout()
    for x in ["START SIMULATION","PAUSE","RESUME","STOP","RESET","STEP FRAME","STEP 1 SECOND"]: actions.addWidget(button(x,x=="START SIMULATION"))
    ctl.body.addLayout(actions,2,0,1,4); lay.addWidget(ctl)
    man=Section("SCENARIO MANAGEMENT"); a=QHBoxLayout()
    for x in ["NEW SCENARIO","SAVE SCENARIO","LOAD SCENARIO","DUPLICATE","EXPORT CONFIGURATION"]: a.addWidget(button(x))
    man.body.addLayout(a,0,0,1,4); lay.addWidget(man)
    v=Section("VALIDATION"); v.body.addWidget(QLabel("✓  Camera Resolution     ✓  FOV     ✓  Frame Rate     ✓  Target Size     ✓  Motion Parameters     ✓  Tracking Configuration"),0,0); lay.addWidget(v)
    return page("Scenario Control", "MISSION SETUP  /  DEMO SCENARIO LOADED", scroll(box))


def camera():
    box=QWidget(); lay=QVBoxLayout(box); lay.setSpacing(14)
    lay.addWidget(grid_section("CAMERA DISPLAY & SENSOR", [("Screen Width",number(2000,0," px")),("Screen Height",number(2000,0," px")),("Sensor Type",combo(["Monochrome","Color"])),("Resolution Preset",combo(["640 × 480","1280 × 720","1920 × 1080","Custom"],"640 × 480")),("Bit Depth",combo(["8-bit","10-bit","12-bit","16-bit"])),("Horizontal FOV",number(4,2,"°",0,180)),("Vertical FOV",number(3,2,"°",0,180)),("FOV Control",number(50,0," %",0,100))]))
    intr=grid_section("CAMERA INTRINSICS", [(x,number(v,2,u)) for x,v,u in [("fx",14200," px"),("fy",14200," px"),("cx",320," px"),("cy",240," px"),("Focal Length",12.5," mm"),("Pixel Pitch",5.2," μm"),("Aperture",2.8," f/"),("Magnification",1.0," ×"),("Optical Gain",1.0," ×")]], cols=3); lay.addWidget(intr)
    psf=grid_section("PSF CONFIGURATION",[("PSF Model",combo(["Gaussian","Elliptical Gaussian","Custom"])),("Sigma X",number(1.8,2," px")),("Sigma Y",number(1.8,2," px")),("Rotation",number(0,1,"°")),("Amplitude",number(1,2)),("PSF Mismatch",number(0.05,2)),("ROI / Truncation",combo(["11 × 11","21 × 21","31 × 31"])),("Calibration Mode",combo(["Nominal","Measured","Off"]))],cols=2)
    p=Plot("PSF PREVIEW", "#efc95c"); p.update_values([.3,.5,.8,1,.8,.5,.3,.16,.08]); psf.body.addWidget(p,0,4,5,2); lay.addWidget(psf)
    lay.addWidget(grid_section("INITIAL STATE & CAMERA MOTION",[("Initial Pan",number(0,2,"°")),("Initial Tilt",number(0,2,"°")),("Initial Roll",number(0,2,"°")),("Initial Pointing Error",number(1.2,2,"°")),("Max Pan Speed",number(12,2," °/s")),("Max Tilt Speed",number(12,2," °/s")),("Pan Acceleration",number(8,2," °/s²")),("Tilt Acceleration",number(8,2," °/s²")),("Deceleration",number(10,2," °/s²")),("Actuator Response",number(12,1," ms")),("Command Delay",number(18,1," ms")),("Position Resolution",number(.01,2,"°")),("Command Update Rate",number(60,0," Hz"))],cols=3))
    return page("Camera Configuration","OPTICAL SENSOR  /  INTRINSICS  /  ACTUATOR MODEL",scroll(box))


def target():
    box=QWidget(); lay=QVBoxLayout(box); lay.setSpacing(14)
    lay.addWidget(grid_section("TARGET & BEACON",[("Target Type",combo(["Optical Beacon","Custom Target"])),("Target Count",combo(["1","Multiple"])),("Shape",combo(["Square","Circle","Gaussian Spot","Ellipse","Custom"])),("Target Size",combo(["5 px","10 px","20 px","Custom"],"10 px")),("Peak Intensity",number(0.92,2)),("Total Energy",number(14.8,2," μJ")),("Signal Power",number(-38,1," dBm")),("Brightness",number(82,0," %")),("Beacon / Background Ratio",number(20,1," dB"))],cols=3))
    lay.addWidget(grid_section("INITIAL POSITION",[("Position Mode",combo(["Center","Random","User Defined","Edge","Corner","Outside FOV"])),("X Coordinate",number(320,1," px")),("Y Coordinate",number(240,1," px"))],cols=3))
    motion=grid_section("MOTION MODEL",[("Primary Model",combo(["Straight","Circular","Figure-8","Random","Sinusoidal","Spiral","Constant Velocity","Constant Acceleration","Random Acceleration","Piecewise Maneuver","Abrupt Direction Change","Stop-Go","Oscillatory","User Defined","Recorded Trajectory"],"Figure-8")),("Velocity",number(3.2,2," px/s")),("Acceleration",number(.8,2," px/s²")),("Angular Velocity",number(12,1," °/s")),("Radius",number(90,1," px")),("Frequency",number(.45,2," Hz")),("Amplitude",number(60,1," px")),("Phase",number(0,1,"°")),("Direction",combo(["North-East","East","South-East","Custom"])),("Maneuver Time",number(20,1," s")),("Random Seed",number(42,0))],cols=3); lay.addWidget(motion)
    chart=Section("TRAJECTORY PREVIEW"); chart.body.addWidget(Plot("TARGET TRAJECTORY","#ef8c63"),0,0,1,4); lay.addWidget(chart)
    return page("Target Configuration","BEACON SIGNATURE  /  INITIAL STATE  /  TRAJECTORY",scroll(box))


def environment():
    box=QWidget(); lay=QVBoxLayout(box); lay.setSpacing(14)
    lay.addWidget(grid_section("NOISE",[("Enable Noise",check("Enabled",True)),("Noise Type",combo(["Gaussian","Salt & Pepper","Poisson","Read Noise","Dark Current","Quantization","Fixed Pattern Noise","Hot Pixels","Dead Pixels","Saturation","Dropout"])),("Mean",number(0,2)),("Standard Deviation",number(.08,3)),("SNR",number(20,1," dB")),("Photon Count",number(1200,0)),("Intensity Scaling",number(1,2)),("Density",number(.01,3)),("Salt Probability",number(.5,2)),("Pepper Probability",number(.5,2))],cols=3))
    lay.addWidget(grid_section("BACKGROUND",[("Background Type",combo(["Uniform","Horizontal Gradient","Vertical Gradient","2D Gradient","Radial Gradient","Gaussian Illumination","Random","Structured","Time Varying"])),("Background Intensity",number(.12,2)),("Gradient Strength",number(.15,2)),("Gradient Direction",number(0,1,"°")),("Temporal Variation",number(.02,3)),("Drift",number(.01,3))],cols=3))
    atm=grid_section("ATMOSPHERE",[("Condition",combo(["Clear","Haze","Fog","Rain","Low Light"])),("Attenuation",number(.08,3)),("Range",number(2.5,2," km")),("Visibility",number(18,1," km")),("Dust / Aerosol",number(.12,2)),("Smoke",number(0,2)),("Turbulence",number(.15,2)),("Scintillation",number(.06,2)),("Beam Wander",number(.1,2)),("Contrast Reduction",number(.08,2)),("Intensity Fluctuation",number(.05,2)),("PSF Broadening",number(.12,2))],cols=3); lay.addWidget(atm)
    adv=Section("ADVANCED TURBULENCE (COLLAPSED)"); adv.setCheckable(True); adv.setChecked(False)
    for i,(l,v,u) in enumerate([("Cn²",1e-14," m⁻²/³"),("Coherence Length",.12," m"),("Turbulence Strength",.2,""),("Temporal Correlation",.35," s")]): adv.add_field(l,number(v,3,u),0,i)
    lay.addWidget(adv)
    lay.addWidget(grid_section("CAMERA JITTER",[("Model",combo(["Gaussian","Bounded","Periodic","Random","User Defined"])),("X Jitter",number(.4,2," px")),("Y Jitter",number(.4,2," px")),("Angular Jitter",number(.02,3,"°")),("Standard Deviation",number(.2,2)),("Maximum Jitter",number(1,2," px")),("Frequency",number(2,1," Hz"))],cols=3))
    lay.addWidget(grid_section("PLATFORM MOTION",[("Model",combo(["Linear","Circular","Random","Spiral","Figure-8","Sinusoidal","Custom"])),("Velocity",number(1.2,2," m/s")),("Acceleration",number(.2,2," m/s²")),("Angular Velocity",number(2,1," °/s")),("Frequency",number(.4,2," Hz")),("Amplitude",number(.8,2," m"))],cols=3))
    return page("Environment Configuration","DISTURBANCE STACK  /  ATMOSPHERE  /  PLATFORM DYNAMICS",scroll(box))


def tracking():
    tabs=QTabWidget()
    def simple(title, fields, preview=None):
        w=QWidget(); l=QVBoxLayout(w); s=grid_section(title,fields,cols=3); l.addWidget(s)
        if preview: l.addWidget(preview)
        l.addStretch(); return w
    tabs.addTab(simple("DETECTION",[("Algorithm",combo(["Fixed Threshold","Otsu","Adaptive Threshold","Statistical μ + kσ","Hybrid Threshold","AI Detector","Hybrid CV + AI"])),("k value",number(3,2," σ")),("Minimum Threshold",number(.2,2)),("Maximum Threshold",number(.95,2)),("AI Model",combo(["YOLO","RF-DETR","Custom CNN"])),("Confidence Threshold",number(.65,2)),("Inference Resolution",combo(["320","640","1280"])),("Compute",combo(["GPU","CPU"]))]),"Detection")
    tabs.addTab(simple("PREPROCESSING",[("Pipeline",combo(["None","Gaussian Filter","Median Filter","Bilateral Filter","Background Subtraction","Contrast Normalization","CLAHE","Temporal Filtering"])),("Kernel Size",combo(["3 × 3","5 × 5","7 × 7"])),("Sigma",number(1.2,2)),("Clip Limit",number(2,1)),("Tile Grid Size",combo(["8 × 8","16 × 16"]))]),"Preprocessing")
    tabs.addTab(simple("CANDIDATE FILTERING",[("Minimum Area",number(4,0," px²")),("Maximum Area",number(900,0," px²")),("Minimum Intensity",number(.2,2)),("Maximum Intensity",number(1,2)),("Aspect Ratio",number(1,2)),("Circularity",number(.65,2)),("Bounding Box",combo(["Unconstrained","ROI bounded","Square only"])),("Ranking",combo(["Intensity","Area","Compactness","Distance From Prediction","PSF Similarity","Temporal Consistency","Combined Score"]))]),"Candidate Filtering")
    comparison=table(["Method","Accuracy","Runtime"],4)
    for i,(a,b,c) in enumerate([("Binary Centroid","1.82 px","0.4 ms"),("Weighted Centroid","0.74 px","0.7 ms"),("Gaussian Fit","0.46 px","3.2 ms"),("PSF Fit","0.39 px","4.8 ms")]):
        for j,v in enumerate([a,b,c]): comparison.setItem(i,j,QTableWidgetItem(v))
    tabs.addTab(simple("LOCALIZATION",[("Method",combo(["Bounding Box Center","Binary Centroid","Intensity Weighted Centroid","Gaussian Fitting","PSF Fitting","Image Moments","Template Matching","Learned Localization"]))],comparison),"Localization")
    tabs.addTab(simple("ROI CONFIGURATION",[("ROI Mode",combo(["Full Frame","Fixed ROI","Predicted ROI","Adaptive ROI"])),("ROI Size",combo(["11 × 11","15 × 15","21 × 21","31 × 31","41 × 41","Custom"])),("Margin",number(4,0," px")),("Update Rate",number(10,0," Hz"))],Plot("ROI OVERLAY PREVIEW","#42d6c5")),"ROI")
    tabs.addTab(simple("ESTIMATOR",[("Estimator",combo(["None","Kalman Filter","Adaptive Kalman Filter","EKF","UKF"],"Adaptive Kalman Filter")),("State",combo(["Position","Position + Velocity","Position + Velocity + Acceleration"])),("Q",number(.02,3)),("R",number(.8,2)),("Initial Covariance",number(4,1)),("Process Noise",number(.02,3)),("Measurement Noise",number(.8,2)),("Gating Threshold",number(9.21,2))]),"Estimator")
    tabs.addTab(simple("PREDICTION",[("Prediction Horizon",combo(["0.5 s","1 s","2 s","3 s","4 s","5 s","10 s","Custom"],"5 s")),("Predicted Position",text("321.42, 219.18 px")),("Predicted Velocity",text("+1.42, −0.36 px/s")),("Covariance",text("Σu 1.4 / Σv 1.1 px")),("Uncertainty Ellipse",combo(["1σ","2σ","3σ"]))],Plot("CURRENT → PREDICTED / UNCERTAINTY","#ef8c63")),"Prediction")
    tabs.addTab(simple("ADAPTIVE SEARCH",[("Search Algorithm",combo(["None","Fixed EAL","Adaptive EAL","Spiral","Raster","Circular","Custom"],"Adaptive EAL")),("X Amplitude",number(24,1," px")),("Y Amplitude",number(18,1," px")),("Frequency X",number(1.2,2," Hz")),("Frequency Y",number(1,2," Hz")),("Phase",number(0,1,"°")),("Duration",number(2,1," s")),("Orientation",number(18,1,"°")),("Covariance Scaling γ",number(1.4,2)),("Eigenvalue Scaling",number(1.2,2)),("Confidence Level",number(.95,2)),("Safety Margin",number(4,1," px")),("Velocity Constraint",number(12,1," px/s")),("NIS Feedback",check("Enable NIS Feedback",True)),("Window",number(12,0)),("Threshold",number(5.99,2)),("Amplitude Gain",number(1.2,2)),("Expansion Gain",number(1.15,2))],Plot("UNCERTAINTY ELLIPSE / ADAPTIVE SEARCH PATH","#b58cff")),"Adaptive Search")
    return page("Tracking Configuration","DETECTION  /  LOCALIZATION  /  ESTIMATION  /  SEARCH",tabs)


CONFIG_MODULES = [
    ("Scenario", "Execution & recording setup"),
    ("Camera & Optics", "Sensor, intrinsics, actuator"),
    ("Target & Beacon", "Signature, position, motion"),
    ("Environment", "Noise, atmosphere, jitter"),
    ("Tracking Pipeline", "Detection → estimation → search"),
]


def configuration_hub():
    """Sidebar-driven configuration hub grouping every settings module."""
    from PySide6.QtWidgets import QListWidget, QListWidgetItem

    root = QWidget()
    lay = QHBoxLayout(root)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)

    nav = QFrame()
    nav.setProperty("class", "cad-panel")
    nl = QVBoxLayout(nav)
    nl.setContentsMargins(0, 0, 0, 0)
    nl.setSpacing(0)
    header = QLabel("CONFIGURATION MODULES")
    header.setProperty("class", "cad-panel-header")
    nl.addWidget(header)
    nav_list = QListWidget()
    for name, sub in CONFIG_MODULES:
        nav_list.addItem(f"{name}\n  {sub}")
    nav_list.setCurrentRow(0)
    nav_list.setFixedWidth(230)
    nl.addWidget(nav_list, 1)
    lay.addWidget(nav)

    stack = QStackedWidget()
    stack.addWidget(scenario())
    stack.addWidget(camera())
    stack.addWidget(target())
    stack.addWidget(environment())
    stack.addWidget(tracking())
    lay.addWidget(stack, 1)

    def select_page(module: str):
        for i, (name, _) in enumerate(CONFIG_MODULES):
            if name == module:
                nav_list.setCurrentRow(i)
                return

    nav_list.currentRowChanged.connect(stack.setCurrentIndex)
    root.select_page = select_page
    return root


def live(sim):
    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setContentsMargins(16, 12, 16, 16)
    lay.setSpacing(10)

    top = QHBoxLayout()
    title = QLabel("Live Optical Tracking Viewport")
    title.setProperty("class", "page-title")
    title.setStyleSheet("font-size:18px; font-weight:700; color:#ffffff;")
    top.addWidget(title)
    top.addStretch()
    top.addWidget(StatusPill("TARGET LOCKED"))
    lay.addLayout(top)

    body = QHBoxLayout()
    body.setSpacing(10)

    # Left: Runtime Debug / State Vector (updated every tick)
    left = Section("RUNTIME DEBUG  /  STATE VECTOR")
    left.setFixedWidth(210)
    debug_labels = {}
    debug_items = [
        ("STATE", "LOCKED"),
        ("FRAME", "00000"),
        ("MODE", "Figure-8"),
        ("TARGET U,V", "321.4, 219.2"),
        ("EST U,V", "319.1, 220.2"),
        ("PRED U,V", "328.5, 215.3"),
        ("SEARCH U,V", "321.4, 219.2"),
        ("SIGMA U,V", "18.4 / 7.2"),
        ("NIS", "2.17"),
        ("FPS", "60.0"),
        ("LATENCY", "18.2 ms"),
    ]
    for i, (k, v) in enumerate(debug_items):
        q = QLabel(f"{k}  ▸  {v}")
        q.setProperty("class", "telemetry-item")
        left.body.addWidget(q, i, 0, 1, 2)
        debug_labels[k] = q
    body.addWidget(left)

    # Center: Optical Viewport
    center = Section("CAMERA VIEW  /  MONOCHROME SENSOR CANVAS")
    center.body.addWidget(CameraView(), 0, 0, 1, 2)
    body.addWidget(center, 1)

    # Right: Scrollable Live Metrics Stack
    right_box = Section("LIVE TELEMETRY METRICS")
    right_box.setFixedWidth(230)
    
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    scroll_content = QWidget()
    rl = QVBoxLayout(scroll_content)
    rl.setContentsMargins(4, 4, 4, 4)
    rl.setSpacing(8)

    metrics = []
    metric_items = [
        ("FPS", "60.0", ""),
        ("Centroid Error", "2.31", "px"),
        ("RMSE", "3.14", "px"),
        ("Lock Retention", "98.4", "%"),
        ("NIS", "2.17", ""),
        ("Latency", "18.2", "ms"),
        ("Acquisition", "0.83", "s"),
        ("Reacquisition", "0.42", "s"),
    ]
    for a, b, u in metric_items:
        m = Metric(a, b, u)
        metrics.append(m)
        rl.addWidget(m)
    rl.addStretch(1)

    scroll_area.setWidget(scroll_content)
    right_box.body.addWidget(scroll_area, 0, 0, 1, 2)
    body.addWidget(right_box)

    lay.addLayout(body, 3)

    charts = QHBoxLayout()
    charts.setSpacing(10)
    plots = [
        Plot("POSITION / U-V", "#42d6c5"),
        Plot("RADIAL ERROR", "#ef8c63"),
        Plot("NIS vs TIME", "#b58cff"),
    ]
    for p in plots:
        charts.addWidget(p)

    lay.addLayout(charts, 1)

    root.metrics = metrics
    root.camera = center.findChild(CameraView)
    root.plots = plots
    root.debug_labels = debug_labels
    return root


def analysis():
    box=QWidget(); l=QVBoxLayout(box); metrics=[("FPS","60.0"),("Mean Latency","18.2 ms"),("P95 Latency","23.8 ms"),("Acquisition Time","0.83 s"),("Reacquisition","0.42 s"),("Lock Retention","98.4%"),("Detection Probability","97.2%"),("False Alarm Probability","0.8%"),("Centroid RMSE","3.14 px"),("Angular RMSE","0.021°"),("Max Tracking Error","8.7 px"),("5 s Prediction RMSE","6.42 px"),("Target Loss Rate","1.6%")]
    grid=QGridLayout()
    for i,(a,b) in enumerate(metrics): grid.addWidget(Metric(a,b),i//4,i%4)
    l.addLayout(grid); tabs=QTabWidget()
    for title in ["Error Timeline","Error Histogram","Error CDF","RMSE vs SNR","Background vs RMSE","PSF Width vs RMSE","Detection vs SNR","False Alarm vs SNR","FPS vs Resolution","FPS vs Noise","Prediction Error vs Horizon","Lock Retention vs Velocity","Acquisition vs Uncertainty","Fixed EAL vs Adaptive EAL"]: tabs.addTab(Plot(title,"#42d6c5"),title)
    l.addWidget(tabs,1); return page("Performance Analysis","EVALUATION  /  MOCK RESULTS  /  REPORT-READY VIEWS",scroll(box))


EXPERIMENTS=["EXP 00 — Baseline / SNR Calibration","EXP 01 — Noise Robustness","EXP 02 — Denoising Comparison","EXP 03 — Background Suppression","EXP 04 — Threshold Selection","EXP 06 — Classical vs AI","EXP 07 — Localization","EXP 09 — PSF Width","EXP 10 — PSF Mismatch","EXP 11 — Background / PSF Interaction","EXP 12 — Atmospheric Degradation","EXP 13 — Beacon Range","EXP 15 — Beacon Tracking","EXP 16 — Motion / Frame Rate","EXP 17 — Prediction Horizon","EXP 18 — Uncertainty Ellipse","EXP 19 — Fixed vs Adaptive EAL","EXP 22 — Monte Carlo Validation","EXP 23 — Architecture"]

def research():
    root=QWidget(); l=QVBoxLayout(root); l.setContentsMargins(24,20,24,24); head=QHBoxLayout(); head.addWidget(QLabel("Research Lab")); head.addStretch(); head.addWidget(button("RUN SELECTED EXPERIMENT",True)); l.addLayout(head)
    from PySide6.QtWidgets import QListWidget, QListWidgetItem
    split=QHBoxLayout(); listw=QListWidget(); listw.addItems(EXPERIMENTS); listw.setCurrentRow(0); split.addWidget(listw,1)
    detail=QWidget(); dl=QVBoxLayout(detail); dl.addWidget(QLabel("EXP 00  /  BASELINE & SNR CALIBRATION"),0); dl.addWidget(QLabel("Controlled baseline for signal-to-noise calibration and tracker readiness. Prototype results are illustrative.")); dl.addWidget(grid_section("EXPERIMENT CONFIGURATION",[("Random Seed",number(42,0)),("SNR Sweep",combo(["5 — 30 dB","0 — 40 dB","Custom"])),("Algorithm Version",text("tracker-ui-mock-0.1")),("Status",combo(["Ready","Completed","Queued"]))],cols=2)); dl.addWidget(Plot("RESULTS / RMSE BY CONDITION","#efc95c")); res=grid_section("RESULT SUMMARY",[("Mean",number(3.14,2," px")),("Standard Deviation",number(.84,2," px")),("RMSE",number(3.25,2," px")),("Minimum",number(1.1,2," px")),("Maximum",number(8.7,2," px")),("95% Confidence Interval",text("2.91 — 3.62 px"))],cols=3); dl.addWidget(res); a=QHBoxLayout()
    for x in ["RUN","RE-RUN","SAVE","EXPORT CSV","EXPORT FIGURE","GENERATE REPORT"]: a.addWidget(button(x,x=="RUN"))
    dl.addLayout(a); split.addWidget(detail,3); l.addLayout(split,1); return root


def benchmark():
    box=QWidget(); l=QVBoxLayout(box); l.addWidget(grid_section("VIDEO INPUT",[("Video File",text("/data/demo_beacon_sequence.mp4")),("Resolution",text("1920 × 1080")),("FPS",number(30,0," Hz")),("Frames",number(18000,0)),("Duration",text("10:00"))],cols=3));
    s=Section("PROCESSING OPTIONS"); row=QHBoxLayout()
    for x in ["Bypass Virtual PTZ","Run Detection","Run Localization","Generate Performance Log"]: row.addWidget(check(x,x!="Bypass Virtual PTZ"))
    s.body.addLayout(row,0,0,1,4); l.addWidget(s); l.addWidget(grid_section("BENCHMARK RESULTS",[(x,text(v)) for x,v in [("Centroid Error","3.42 px"),("RMSE","4.18 px"),("Maximum Error","11.2 px"),("FPS","29.7"),("Detection Probability","96.4%"),("Target Loss","2.1%"),("Ground Truth","GROUND TRUTH UNAVAILABLE")]],cols=3)); l.addStretch(); return page("Video Benchmark","REPLAY  /  PERFORMANCE LOG  /  GROUND TRUTH STATUS",scroll(box))


def logs():
    root=QWidget(); l=QVBoxLayout(root); top=QHBoxLayout(); top.addWidget(QLabel("Log Stream")); top.addStretch()
    for x in ["Filter","Search","Export CSV","Clear"]: top.addWidget(button(x))
    l.addLayout(top); tabs=QTabWidget(); specs={"Detection":["Timestamp","Frame","Detection","Candidate Count","Confidence","False Alarm","Latency"],"Localization":["Ground Truth U","Ground Truth V","Estimated U","Estimated V","X Error","Y Error","Radial Error","RMSE"],"Tracking":["Lock State","Missed Frames","Loss Duration","Tracking Error","Reacquisition"],"Prediction":["Horizon","Predicted U","Predicted V","Actual U","Actual V","Prediction Error","Sigma U","Sigma V","Mahalanobis Distance"],"Filter":["Innovation","Innovation Covariance","NIS","Covariance Trace","Rejected Measurement","Outlier Count"],"Camera / Control":["Commanded Pan","Actual Pan","Commanded Tilt","Actual Tilt","Pan Error","Tilt Error","Saturation","Delay","FOV Violation"],"Search":["Search Duration","Search Path Length","Amplitude","Orientation","Coverage","Acquisition","Reacquisition"],"Computation":["Frame Latency","Detection Latency","Localization Latency","Filter Latency","Control Latency","CPU","RAM","GPU","Dropped Frames","Deadline Misses"]}
    for name,heads in specs.items(): tabs.addTab(table(heads,6),name)
    l.addWidget(tabs,1); return page("Technical Logs","PER-FRAME TELEMETRY  /  DIAGNOSTICS  /  EXPORT",root)


def monte_carlo():
    box=QWidget(); l=QVBoxLayout(box); l.addWidget(grid_section("MONTE CARLO DESIGN",[("Number of Trials",number(1000,0)),("SNR Distribution",combo(["Uniform","Normal","Log-normal"])),("PSF Width Distribution",combo(["Uniform","Normal"])),("Background Distribution",combo(["Low / Medium / High","Normal"])),("Velocity Distribution",combo(["Uniform","Normal"])),("Acceleration Distribution",combo(["Uniform","Normal"])),("Motion Model",combo(["Figure-8","Random","Circular","Mixed"])),("Random Seed",number(42,0))],cols=4)); l.addWidget(grid_section("OUTPUTS",[(x,text(v)) for x,v in [("Mean","3.42 px"),("Std Dev","0.91 px"),("95% CI","3.36 — 3.48"),("Worst Case","12.8 px"),("Success Rate","96.2%"),("Acquisition Probability","98.1%"),("Tracking Probability","95.7%"),("Reacquisition Probability","93.4%")]],cols=4)); row=QHBoxLayout()
    for title in ["Distribution Histogram","CDF","Box Plot","Success Probability","Parameter Sensitivity"]: row.addWidget(Plot(title,"#42d6c5"))
    l.addLayout(row); l.addWidget(button("RUN MONTE CARLO",True)); return page("Monte Carlo Validation","STATISTICAL STUDY  /  MOCK TRIALS  /  CONFIDENCE INTERVALS",scroll(box))
