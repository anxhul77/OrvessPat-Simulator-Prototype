"""Compact property storage and inspector widgets for the FSOC prototype.

The inspector is deliberately a presentation layer.  It owns no simulation
logic; it only edits the values kept by :class:`PropertyStore` and reports
those edits to the host application.
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class FieldSpec:
    """Description of one editable property in the inspector."""

    key: str
    kind: str = "number"
    default: Any = 0
    label: str = ""
    options: tuple[str, ...] = ()
    unit: str = ""
    decimals: int = 2
    minimum: float = -999999.0
    maximum: float = 999999.0
    tooltip: str = ""


def _number(
    key: str,
    default: float,
    unit: str = "",
    decimals: int = 2,
    minimum: float = -999999.0,
    maximum: float = 999999.0,
    label: str = "",
    tooltip: str = "",
) -> FieldSpec:
    return FieldSpec(
        key,
        "number",
        default,
        label or key,
        (),
        unit,
        decimals,
        minimum,
        maximum,
        tooltip,
    )


def _integer(
    key: str,
    default: int,
    unit: str = "",
    minimum: int = -999999,
    maximum: int = 999999,
    label: str = "",
    tooltip: str = "",
) -> FieldSpec:
    return FieldSpec(
        key,
        "integer",
        default,
        label or key,
        (),
        unit,
        0,
        minimum,
        maximum,
        tooltip,
    )


def _choice(
    key: str,
    default: str,
    options: Iterable[str],
    label: str = "",
    tooltip: str = "",
) -> FieldSpec:
    return FieldSpec(
        key,
        "choice",
        default,
        label or key,
        tuple(options),
        "",
        0,
        0,
        0,
        tooltip,
    )


def _text(key: str, default: str, label: str = "", tooltip: str = "") -> FieldSpec:
    return FieldSpec(key, "text", default, label or key, (), "", 0, 0, 0, tooltip)


def _check(key: str, default: bool, label: str = "", tooltip: str = "") -> FieldSpec:
    return FieldSpec(key, "check", default, label or key, (), "", 0, 0, 0, tooltip)


# The order here is also the order exposed by Inspector.components.  These
# names are the stable keys used by preview consumers.
_COMPONENT_FIELDS: dict[str, tuple[FieldSpec, ...]] = {
    "Scenario": (
        _text("Scenario Name", "FSOC Demo — Moving Beacon"),
        _text("Scenario ID", "FSOC-DEMO-001"),
        _integer("Random Seed", 42, minimum=0),
        _integer("Duration", 120, "s", minimum=0),
        _choice("Time Scale", "1×", ("Real Time", "0.5×", "1×", "2×", "5×", "10×", "Custom")),
        _text("Start Time", "2026-09-30 08:42:12"),
        _text("Description", "Coarse alignment and beacon tracking demonstration for a mobile FSOC terminal."),
        _number("Custom Time Scale", 1, "×", minimum=0.01),
        _choice("Execution Mode", "Interactive", ("Interactive", "Benchmark", "Headless", "Video Input")),
        _check("Record Simulation", True),
        _check("Record Frames", True),
        _check("Record Metrics", True),
        _check("Record Video", False),
        _text("Video File", "/data/demo_beacon_sequence.mp4"),
        _text("Video Resolution", "1920 × 1080"),
        _integer("Video FPS", 30, "Hz", minimum=1),
        _integer("Video Frames", 18000, "frames", minimum=0),
        _text("Video Duration", "10:00"),
        _check("Bypass Virtual PTZ", False),
        _check("Run Detection", True),
        _check("Run Localization", True),
        _check("Generate Performance Log", True),
    ),
    "Environment": (
        _choice("Profile", "Nominal", ("Nominal", "Clear Sky", "Degraded", "Custom")),
        _check("Enabled", True),
    ),
    "Background": (
        _choice(
            "Background Type",
            "Uniform",
            (
                "Uniform",
                "Horizontal Gradient",
                "Vertical Gradient",
                "2D Gradient",
                "Radial Gradient",
                "Gaussian Illumination",
                "Random",
                "Structured",
                "Time Varying",
            ),
        ),
        _number("Background Intensity", 0.12, minimum=0, maximum=1),
        _number("Gradient Strength", 0.15, minimum=0, maximum=1),
        _number("Gradient Direction", 0, "°", 1, -360, 360),
        _number("Temporal Variation", 0.02, decimals=3, minimum=0, maximum=1),
        _number("Drift", 0.01, decimals=3, minimum=0),
    ),
    "Noise": (
        _check("Enabled", True, label="Enable Noise"),
        _choice(
            "Noise Type",
            "Gaussian",
            (
                "Gaussian",
                "Salt & Pepper",
                "Poisson",
                "Read Noise",
                "Dark Current",
                "Quantization",
                "Fixed Pattern Noise",
                "Hot Pixels",
                "Dead Pixels",
                "Saturation",
                "Dropout",
            ),
        ),
        _number("Mean", 0, decimals=2),
        _number("Standard Deviation", 0.08, decimals=3, minimum=0),
        _number("SNR", 20, "dB", 1, minimum=-60, maximum=120),
        _integer("Photon Count", 1200, minimum=0),
        _number("Intensity Scaling", 1, minimum=0),
        _number("Density", 0.01, decimals=3, minimum=0, maximum=1),
        _number("Salt Probability", 0.5, minimum=0, maximum=1),
        _number("Pepper Probability", 0.5, minimum=0, maximum=1),
    ),
    "Atmosphere": (
        _choice("Condition", "Clear", ("Clear", "Haze", "Fog", "Rain", "Low Light")),
        _number("Attenuation", 0.08, decimals=3, minimum=0, maximum=1),
        _number("Range", 2.5, "km", minimum=0),
        _number("Visibility", 18, "km", minimum=0),
        _number("Dust / Aerosol", 0.12, minimum=0, maximum=1),
        _number("Smoke", 0, minimum=0, maximum=1),
        _number("Turbulence", 0.15, minimum=0, maximum=1),
        _number("Scintillation", 0.06, minimum=0, maximum=1),
        _number("Beam Wander", 0.1, minimum=0, maximum=1),
        _number("Contrast Reduction", 0.08, minimum=0, maximum=1),
        _number("Intensity Fluctuation", 0.05, minimum=0, maximum=1),
        _number("PSF Broadening", 0.12, minimum=0, maximum=1),
        FieldSpec("Cn²", "scientific", 1e-14, "Cn² (m⁻²/³)", decimals=20, minimum=0, maximum=1),
        _number("Coherence Length", 0.12, "m", minimum=0),
        _number("Turbulence Strength", 0.2, minimum=0, maximum=1),
        _number("Temporal Correlation", 0.35, "s", minimum=0),
    ),
    "Platform Motion": (
        _choice("Model", "Linear", ("Linear", "Circular", "Random", "Spiral", "Figure-8", "Sinusoidal", "Custom")),
        _number("Velocity", 1.2, "m/s", minimum=0),
        _number("Acceleration", 0.2, "m/s²", minimum=0),
        _number("Angular Velocity", 2, "°/s", 1),
        _number("Frequency", 0.4, "Hz", minimum=0),
        _number("Amplitude", 0.8, "m", minimum=0),
    ),
    "Camera Jitter": (
        _choice("Model", "Gaussian", ("Gaussian", "Bounded", "Periodic", "Random", "User Defined")),
        _number("X Jitter", 0.4, "px", minimum=0),
        _number("Y Jitter", 0.4, "px", minimum=0),
        _number("Angular Jitter", 0.02, "°", 3, minimum=0),
        _number("Standard Deviation", 0.2, "px", minimum=0),
        _number("Maximum Jitter", 1, "px", minimum=0),
        _number("Frequency", 2, "Hz", 1, minimum=0),
    ),
    "Camera": (
        _integer("Screen Width", 2000, "px", minimum=1, maximum=16384),
        _integer("Screen Height", 2000, "px", minimum=1, maximum=16384),
        _choice("Sensor Type", "Monochrome", ("Monochrome", "Color")),
        _choice("Resolution Preset", "640 × 480", ("640 × 480", "1280 × 720", "1920 × 1080", "Custom")),
        _integer("Resolution Width", 640, "px", minimum=1, maximum=16384),
        _integer("Resolution Height", 480, "px", minimum=1, maximum=16384),
        _integer("Frame Rate", 60, "Hz", minimum=1, maximum=10000),
        _choice("Bit Depth", "8-bit", ("8-bit", "10-bit", "12-bit", "16-bit")),
        _number("FOV Control", 50, "%", 0, 0, 100),
    ),
    "Virtual Camera": (
        _number("Initial Pan", 0, "°"),
        _number("Initial Tilt", 0, "°"),
        _number("Initial Roll", 0, "°"),
        _number("Initial Pointing Error", 1.2, "°", minimum=0),
    ),
    "Optics": (
        _number("FOV H", 4, "°", 2, 0.01, 180, label="Horizontal FOV", tooltip="Horizontal field of view of the optical train, in degrees."),
        _number("FOV V", 3, "°", 2, 0.01, 180, label="Vertical FOV", tooltip="Vertical field of view of the optical train, in degrees."),
        _number("fx", 14200, "px", 2, minimum=0),
        _number("fy", 14200, "px", 2, minimum=0),
        _number("cx", 320, "px", 2, minimum=0),
        _number("cy", 240, "px", 2, minimum=0),
        _number("Focal Length", 12.5, "mm", minimum=0),
        _number("Pixel Pitch", 5.2, "μm", minimum=0),
        _number("Aperture", 2.8, "f/", minimum=0),
        _number("Magnification", 1, "×", minimum=0),
        _number("Optical Gain", 1, "×", minimum=0),
    ),
    "PSF": (
        _choice("PSF Model", "Gaussian", ("Gaussian", "Elliptical Gaussian", "Custom")),
        _number("Sigma X", 1.8, "px", minimum=0, tooltip="Gaussian standard deviation σ along image X; this controls blur width."),
        _number("Sigma Y", 1.8, "px", minimum=0, tooltip="Gaussian standard deviation σ along image Y; this controls blur width."),
        _number("Rotation", 0, "°", 1, -360, 360),
        _number("Amplitude", 1, minimum=0),
        _number("PSF Mismatch", 0.05, minimum=0, maximum=1),
        _choice("ROI / Truncation", "11 × 11", ("11 × 11", "21 × 21", "31 × 31")),
        _choice("Calibration Mode", "Nominal", ("Nominal", "Measured", "Off")),
    ),
    "Actuator": (
        _number("Max Pan Speed", 12, "°/s", minimum=0),
        _number("Max Tilt Speed", 12, "°/s", minimum=0),
        _number("Pan Acceleration", 8, "°/s²", minimum=0),
        _number("Tilt Acceleration", 8, "°/s²", minimum=0),
        _number("Deceleration", 10, "°/s²", minimum=0),
        _number("Actuator Response", 12, "ms", 1, minimum=0),
        _number("Command Delay", 18, "ms", 1, minimum=0),
        _number("Position Resolution", 0.01, "°", 2, minimum=0),
        _integer("Command Update Rate", 60, "Hz", minimum=1),
    ),
    "Targets": (
        _choice("Target Type", "Optical Beacon", ("Optical Beacon", "Custom Target")),
        _choice("Target Count", "1", ("1", "Multiple")),
        _integer("Count", 1, minimum=1, maximum=10000, label="Multiple Count"),
        _choice("Active Target", "Beacon_01", ("Beacon_01",)),
    ),
    "Beacon_01": (
        _choice("Shape", "Square", ("Square", "Circle", "Gaussian Spot", "Ellipse", "Custom")),
        _choice("Size", "10 px", ("5 px", "10 px", "20 px", "Custom"), label="Target Size"),
        _number("Custom Size", 10, "px", 1, minimum=0.1),
        _number("Peak Intensity", 0.92, minimum=0, maximum=1),
        _number("Total Energy", 14.8, "μJ", minimum=0),
        _number("Signal Power", -38, "dBm", 1),
        _number("Brightness", 82, "%", 0, 0, 100),
        _number("Beacon / Background Ratio", 20, "dB", 1),
        _choice("Position Mode", "Center", ("Center", "Random", "User Defined", "Edge", "Corner", "Outside FOV")),
        _number("X Coordinate", 320, "px", 1),
        _number("Y Coordinate", 240, "px", 1),
    ),
    "Motion": (
        _choice(
            "Primary Model",
            "Figure-8",
            (
                "Straight",
                "Circular",
                "Figure-8",
                "Random",
                "Sinusoidal",
                "Spiral",
                "Constant Velocity",
                "Constant Acceleration",
                "Random Acceleration",
                "Piecewise Maneuver",
                "Abrupt Direction Change",
                "Stop-Go",
                "Oscillatory",
                "User Defined",
                "Recorded Trajectory",
            ),
        ),
        _number("Velocity", 3.2, "px/s", minimum=0),
        _number("Acceleration", 0.8, "px/s²", minimum=0),
        _number("Angular Velocity", 12, "°/s", 1),
        _number("Radius", 90, "px", 1, minimum=0),
        _number("Frequency", 0.45, "Hz", 2, minimum=0),
        _number("Amplitude", 60, "px", 1, minimum=0),
        _number("Phase", 0, "°", 1, -360, 360),
        _choice("Direction", "North-East", ("North-East", "East", "South-East", "Custom")),
        _number("Maneuver Time", 20, "s", 1, minimum=0),
        _integer("Random Seed", 42, minimum=0),
    ),
    "Tracking System": (
        _choice("Mode", "Coarse Alignment", ("Coarse Alignment", "Beacon Tracking", "Validation")),
        _check("Enabled", True),
        _integer("Frame Rate", 60, "Hz", minimum=1),
    ),
    "Detector": (
        _choice(
            "Algorithm",
            "Fixed Threshold",
            ("Fixed Threshold", "Otsu", "Adaptive Threshold", "Statistical μ + kσ", "Hybrid Threshold", "AI Detector", "Hybrid CV + AI"),
        ),
        _number("k value", 3, "σ", 2, minimum=0),
        _number("Minimum Threshold", 0.2, minimum=0, maximum=1),
        _number("Maximum Threshold", 0.95, minimum=0, maximum=1),
        _choice("AI Model", "YOLO", ("YOLO", "RF-DETR", "Custom CNN")),
        _number("Confidence Threshold", 0.65, minimum=0, maximum=1),
        _choice("Inference Resolution", "640", ("320", "640", "1280")),
        _choice("Compute", "GPU", ("GPU", "CPU")),
    ),
    "Preprocessing": (
        _choice(
            "Pipeline",
            "Gaussian Filter",
            ("None", "Gaussian Filter", "Median Filter", "Bilateral Filter", "Background Subtraction", "Contrast Normalization", "CLAHE", "Temporal Filtering"),
        ),
        _choice("Kernel Size", "3 × 3", ("3 × 3", "5 × 5", "7 × 7")),
        _number("Sigma", 1.2, "px", minimum=0, tooltip="Spatial filter scale σ in pixels; larger values smooth a wider neighborhood."),
        _number("Clip Limit", 2, decimals=1, minimum=0),
        _choice("Tile Grid Size", "8 × 8", ("8 × 8", "16 × 16")),
        _number("Color Sigma", 0.1, minimum=0, tooltip="Bilateral range sigma in normalized intensity units; limits smoothing across intensity edges."),
        _integer("History", 500, "frames", minimum=1),
        _number("Learning Rate", 0.01, decimals=3, minimum=0, maximum=1),
        _number("Foreground Threshold", 0.1, minimum=0, maximum=1),
        _number("Lower Percentile", 1, "%", 1, 0, 100),
        _number("Upper Percentile", 99, "%", 1, 0, 100),
        _number("Temporal Alpha", 0.25, minimum=0, maximum=1),
        _integer("Temporal Window", 5, "frames", minimum=1),
    ),
    "Candidate Filter": (
        _number("Minimum Area", 4, "px²", 0, minimum=0),
        _number("Maximum Area", 900, "px²", 0, minimum=0),
        _number("Minimum Intensity", 0.2, minimum=0, maximum=1),
        _number("Maximum Intensity", 1, minimum=0, maximum=1),
        _number("Aspect Ratio", 1, minimum=0),
        _number("Circularity", 0.65, minimum=0, maximum=1),
        _choice("Bounding Box", "Unconstrained", ("Unconstrained", "ROI bounded", "Square only")),
        _choice("Ranking", "Intensity", ("Intensity", "Area", "Compactness", "Distance From Prediction", "PSF Similarity", "Temporal Consistency", "Combined Score")),
    ),
    "Localization": (
        _choice(
            "Method",
            "Intensity Weighted Centroid",
            ("Bounding Box Center", "Binary Centroid", "Intensity Weighted Centroid", "Gaussian Fitting", "PSF Fitting", "Image Moments", "Template Matching", "Learned Localization"),
        ),
    ),
    "ROI": (
        _choice("ROI Mode", "Predicted ROI", ("Full Frame", "Fixed ROI", "Predicted ROI", "Adaptive ROI")),
        _choice("ROI Size", "21 × 21", ("11 × 11", "15 × 15", "21 × 21", "31 × 31", "41 × 41", "Custom")),
        _integer("Custom Width", 21, "px", minimum=1),
        _integer("Custom Height", 21, "px", minimum=1),
        _integer("Margin", 4, "px", minimum=0),
        _integer("Update Rate", 10, "Hz", minimum=1),
    ),
    "Kalman Filter": (
        _choice("Estimator", "Adaptive Kalman Filter", ("None", "Kalman Filter", "Adaptive Kalman Filter", "EKF", "UKF")),
        _choice("State", "Position + Velocity + Acceleration", ("Position", "Position + Velocity", "Position + Velocity + Acceleration")),
        _number("Q", 0.02, decimals=3, minimum=0, tooltip="Process-noise covariance Q used to model state uncertainty."),
        _number("R", 0.8, minimum=0, tooltip="Measurement-noise covariance R used to weight observations."),
        _number("Initial Covariance", 4, minimum=0),
        _number("Process Noise", 0.02, decimals=3, minimum=0),
        _number("Measurement Noise", 0.8, minimum=0),
        _number("Gating Threshold", 9.21, decimals=2, minimum=0, tooltip="NIS/Mahalanobis gate: reject measurements whose covariance-scaled innovation exceeds this threshold."),
    ),
    "Prediction": (
        _choice("Prediction Horizon", "5 s", ("0.5 s", "1 s", "2 s", "3 s", "4 s", "5 s", "10 s", "Custom")),
        _number("Custom Horizon", 5, "s", 2, minimum=0),
        _text("Predicted Position", "321.42, 219.18 px"),
        _text("Predicted Velocity", "+1.42, −0.36 px/s"),
        _text("Covariance", "Σu 1.4 / Σv 1.1 px"),
        _choice("Uncertainty Ellipse", "2σ", ("1σ", "2σ", "3σ")),
    ),
    "Adaptive Search": (
        _choice("Search Algorithm", "Adaptive EAL", ("None", "Fixed EAL", "Adaptive EAL", "Spiral", "Raster", "Circular", "Custom")),
        _number("X Amplitude", 24, "px", 1, minimum=0),
        _number("Y Amplitude", 18, "px", 1, minimum=0),
        _number("Frequency X", 1.2, "Hz", 2, minimum=0),
        _number("Frequency Y", 1, "Hz", 2, minimum=0),
        _number("Phase", 0, "°", 1, -360, 360),
        _number("Duration", 2, "s", 1, minimum=0),
        _number("Orientation", 18, "°", 1, -360, 360),
        _number("Covariance Scaling γ", 1.4, minimum=0, tooltip="Scale factor γ applied to the predicted covariance before search planning."),
        _number("Eigenvalue Scaling", 1.2, minimum=0),
        _number("Confidence Level", 0.95, minimum=0, maximum=1),
        _number("Safety Margin", 4, "px", 1, minimum=0),
        _number("Velocity Constraint", 12, "px/s", 1, minimum=0),
        _check("NIS Feedback", True, tooltip="Use normalized innovation squared (NIS) feedback to adapt the search envelope."),
        _integer("Window", 12, "frames", minimum=1),
        _number("Threshold", 5.99, decimals=2, minimum=0, tooltip="NIS threshold for feedback decisions."),
        _number("Amplitude Gain", 1.2, minimum=0),
        _number("Expansion Gain", 1.15, minimum=0),
    ),
    "Analysis": (
        _choice(
            "View",
            "Performance Summary",
            (
                "Performance Summary", "Error Timeline", "Error Histogram", "Error CDF",
                "RMSE vs SNR", "Background vs RMSE", "PSF Width vs RMSE",
                "Detection vs SNR", "False Alarm vs SNR", "FPS vs Resolution",
                "FPS vs Noise", "Prediction Error vs Horizon", "Lock Retention vs Velocity",
                "Acquisition vs Uncertainty", "Fixed EAL vs Adaptive EAL",
            ),
        ),
    ),
}


_DEMO_VALUES: dict[str, dict[str, Any]] = {
    component: {field.key: deepcopy(field.default) for field in fields}
    for component, fields in _COMPONENT_FIELDS.items()
}


def _normalise_component(value: object) -> str:
    """Return a forgiving lookup token for a component name."""

    return " ".join(str(value).strip().replace("_", " ").replace("-", " ").split()).casefold()


_COMPONENT_ALIASES = {
    _normalise_component(component): component for component in _COMPONENT_FIELDS
}
_COMPONENT_ALIASES.update(
    {
        "target": "Targets",
        "targets": "Targets",
        "target and beacon": "Beacon_01",
        "beacon": "Beacon_01",
        "beacon 1": "Beacon_01",
        "target motion": "Motion",
        "beacon motion": "Motion",
        "camera sensor": "Camera",
        "sensor": "Camera",
        "transform": "Virtual Camera",
        "detection": "Detector",
        "tracking": "Tracking System",
        "tracking system": "Tracking System",
        "candidate filtering": "Candidate Filter",
        "estimator": "Kalman Filter",
        "filter": "Kalman Filter",
        "adaptive eal": "Adaptive Search",
        "search": "Adaptive Search",
        "performance analysis": "Analysis",
        "scenario control": "Scenario",
    }
)


_FIELD_ALIASES = {
    ("Optics", "Horizontal FOV"): "FOV H",
    ("Optics", "Vertical FOV"): "FOV V",
    ("Beacon_01", "Target Size"): "Size",
    ("Beacon_01", "Beacon Size"): "Size",
    ("Noise", "Enable Noise"): "Enabled",
}


def _canonical_component(component: object) -> str:
    token = _normalise_component(component)
    return _COMPONENT_ALIASES.get(token, str(component).strip())


def _canonical_field(component: str, field: object) -> str:
    text = str(field).strip()
    return _FIELD_ALIASES.get((component, text), text)


_UMBRELLA_COMPONENTS = {
    "Environment": ("Background", "Noise", "Atmosphere", "Camera Jitter", "Platform Motion"),
    "Camera": ("Virtual Camera", "Optics", "PSF", "Actuator"),
    "Virtual Camera": ("Camera", "Optics", "PSF", "Actuator"),
    "Targets": ("Beacon_01", "Motion"),
    "Beacon_01": ("Targets", "Motion"),
    "Tracking System": (
        "Preprocessing", "Detector", "Candidate Filter", "Localization", "ROI",
        "Kalman Filter", "Prediction", "Adaptive Search",
    ),
}


def _canonical_path(component: object, field: object) -> tuple[str, str]:
    """Resolve scene aliases and unambiguous properties of collection nodes."""

    canonical = _canonical_component(component)
    key = _canonical_field(canonical, field)
    own_keys = {spec.key for spec in _COMPONENT_FIELDS.get(canonical, ())}
    if key in own_keys:
        return canonical, key
    matches = []
    for child in _UMBRELLA_COMPONENTS.get(canonical, ()):
        child_key = _canonical_field(child, field)
        if any(spec.key == child_key for spec in _COMPONENT_FIELDS[child]):
            matches.append((child, child_key))
    return matches[0] if len(matches) == 1 else (canonical, key)


class PropertyStore(QObject):
    """Qt-owned configuration values shared by the property inspector.

    Values are intentionally ordinary Python values.  The store does not
    validate or interpret them, which keeps it useful to preview-only hosts as
    well as to a future simulation backend.
    """

    changed = Signal(str, str, object)

    COMPONENTS = (
        "Scenario", "Environment", "Background", "Noise", "Atmosphere",
        "Platform Motion", "Camera Jitter", "Camera", "Virtual Camera",
        "Optics", "PSF", "Actuator", "Targets", "Beacon_01", "Motion",
        "Tracking System", "Preprocessing", "Detector", "Candidate Filter",
        "Localization", "ROI", "Kalman Filter", "Prediction", "Adaptive Search",
        "Analysis",
    )
    PREVIEW_KEYS = (
        "Optics/FOV H",
        "Optics/FOV V",
        "PSF/Sigma X",
        "PSF/Sigma Y",
        "Beacon_01/Size",
        "Beacon_01/X Coordinate",
        "Beacon_01/Y Coordinate",
        "Noise/SNR",
    )
    DEFAULT_VALUES = deepcopy(_DEMO_VALUES)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._defaults: dict[str, dict[str, Any]] = deepcopy(_DEMO_VALUES)
        self._values: dict[str, dict[str, Any]] = deepcopy(self._defaults)

    def get(self, component: str, field: str, default: Any = None) -> Any:
        """Read a value, returning *default* when the path is not present."""

        canonical, key = _canonical_path(component, field)
        return deepcopy(self._values.get(canonical, {}).get(key, default))

    def set(self, component: str, field: str, value: Any) -> Any:
        """Set a value and emit its canonical component/field path.

        Unknown paths are retained so an embedding application can add a
        small preview-only property without changing this module.
        """

        canonical, key = _canonical_path(component, field)
        values = self._values.setdefault(canonical, {})
        previous = values.get(key, object())
        if previous == value:
            return value
        values[key] = deepcopy(value)
        self.changed.emit(canonical, key, deepcopy(value))
        return value

    def reset(self) -> dict[str, dict[str, Any]]:
        """Restore demo values and notify listeners for changed paths."""

        before = self.dump()
        self._values = deepcopy(self._defaults)
        components = dict.fromkeys((*before, *self._values))
        for component in components:
            fields = dict.fromkeys((*before.get(component, {}), *self._values.get(component, {})))
            for field in fields:
                old = before.get(component, {}).get(field, object())
                new = self._values.get(component, {}).get(field, None)
                if old != new:
                    self.changed.emit(component, field, new)
        return self.dump()

    def dump(self) -> dict[str, dict[str, Any]]:
        """Return a detached nested snapshot keyed by canonical components."""

        return deepcopy(self._values)


def _group(
    title: str,
    subtitle: str,
    fields: Iterable[object],
    collapsed: bool = False,
) -> tuple[str, str, tuple[object, ...], bool]:
    return title, subtitle, tuple(fields), collapsed


_SUBTITLES = {
    "Scenario": "Mission setup and recording preferences",
    "Environment": "Global disturbance stack",
    "Background": "Illumination model",
    "Noise": "Sensor and photon noise",
    "Atmosphere": "Propagation and turbulence",
    "Platform Motion": "Terminal platform dynamics",
    "Camera Jitter": "Pointing disturbance model",
    "Camera": "Virtual camera sensor and optical chain",
    "Virtual Camera": "Transform and initial pointing",
    "Optics": "Field of view and camera intrinsics",
    "PSF": "Point-spread function model",
    "Actuator": "Virtual gimbal response",
    "Targets": "Scene target collection",
    "Beacon_01": "Primary optical beacon signature",
    "Motion": "Target trajectory model",
    "Tracking System": "Tracking pipeline overview",
    "Detector": "Candidate detection policy",
    "Preprocessing": "Image conditioning pipeline",
    "Candidate Filter": "Candidate screening and ranking",
    "Localization": "Sub-pixel position estimate",
    "ROI": "Region of interest policy",
    "Kalman Filter": "State estimator and gating",
    "Prediction": "Predicted state and uncertainty",
    "Adaptive Search": "Uncertainty-guided search policy",
    "Analysis": "Performance views · illustrative demo results",
}


_GROUP_LAYOUTS: dict[str, tuple[tuple[str, str, tuple[object, ...], bool], ...]] = {
    "Scenario": (
        _group("Simulation Setup", "Identity and run timing", ("Scenario Name", "Scenario ID", "Random Seed", "Duration", "Time Scale", "Custom Time Scale", "Start Time")),
        _group("Mission Brief", "Short operator description", ("Description",)),
        _group("Execution & Recording", "Session capture preferences", ("Execution Mode", "Record Simulation", "Record Frames", "Record Metrics", "Record Video")),
        _group("Video Input", "Replay source and processing preferences", ("Video File", "Video Resolution", "Video FPS", "Video Frames", "Video Duration", "Bypass Virtual PTZ", "Run Detection", "Run Localization", "Generate Performance Log"), True),
    ),
    "Environment": (
        _group("Environment Profile", _SUBTITLES["Environment"], ("Profile", "Enabled")),
    ),
    "Background": (
        _group("Background Model", _SUBTITLES["Background"], tuple(field.key for field in _COMPONENT_FIELDS["Background"])),
    ),
    "Noise": (
        _group("Signal Noise", "Primary signal and sensor noise", ("Enabled", "Noise Type", "Mean", "Standard Deviation", "SNR", "Photon Count", "Intensity Scaling")),
        _group("Impulse & Defects", "Sparse noise probabilities", ("Density", "Salt Probability", "Pepper Probability"), True),
    ),
    "Atmosphere": (
        _group("Atmosphere", "Range and visibility conditions", ("Condition", "Attenuation", "Range", "Visibility", "Dust / Aerosol", "Smoke", "Turbulence", "Scintillation", "Beam Wander", "Contrast Reduction", "Intensity Fluctuation", "PSF Broadening")),
        _group("Advanced Turbulence", "Cn² and temporal correlation", ("Cn²", "Coherence Length", "Turbulence Strength", "Temporal Correlation"), True),
    ),
    "Platform Motion": (
        _group("Platform Motion", _SUBTITLES["Platform Motion"], tuple(field.key for field in _COMPONENT_FIELDS["Platform Motion"])),
    ),
    "Camera Jitter": (
        _group("Jitter Model", _SUBTITLES["Camera Jitter"], ("Model", "X Jitter", "Y Jitter", "Angular Jitter", "Standard Deviation", "Maximum Jitter", "Frequency")),
    ),
    "Virtual Camera": (
        _group("Transform", _SUBTITLES["Virtual Camera"], tuple(field.key for field in _COMPONENT_FIELDS["Virtual Camera"])),
    ),
    "Optics": (
        _group("Optical Model", _SUBTITLES["Optics"], tuple(field.key for field in _COMPONENT_FIELDS["Optics"])),
    ),
    "PSF": (
        _group("PSF", _SUBTITLES["PSF"], tuple(field.key for field in _COMPONENT_FIELDS["PSF"])),
    ),
    "Actuator": (
        _group("Actuator", _SUBTITLES["Actuator"], tuple(field.key for field in _COMPONENT_FIELDS["Actuator"])),
    ),
    "Targets": (
        _group("Target Collection", _SUBTITLES["Targets"], tuple(field.key for field in _COMPONENT_FIELDS["Targets"])),
    ),
    "Beacon_01": (
        _group("Beacon Signature", "Shape, energy, and brightness", ("Shape", "Size", "Custom Size", "Peak Intensity", "Total Energy", "Signal Power", "Brightness", "Beacon / Background Ratio")),
        _group("Initial Position", "Scene placement", ("Position Mode", "X Coordinate", "Y Coordinate")),
    ),
    "Motion": (
        _group("Motion Model", _SUBTITLES["Motion"], tuple(field.key for field in _COMPONENT_FIELDS["Motion"])),
    ),
    "Tracking System": (
        _group("Tracking System", _SUBTITLES["Tracking System"], tuple(field.key for field in _COMPONENT_FIELDS["Tracking System"])),
    ),
    "Detector": (
        _group("Detection", "Threshold and candidate generation", ("Algorithm", "k value", "Minimum Threshold", "Maximum Threshold")),
        _group("AI Detector", "Optional inference stage", ("AI Model", "Confidence Threshold", "Inference Resolution", "Compute"), True),
    ),
    "Preprocessing": (
        _group("Pipeline", _SUBTITLES["Preprocessing"], tuple(field.key for field in _COMPONENT_FIELDS["Preprocessing"])),
    ),
    "Candidate Filter": (
        _group("Candidate Filtering", _SUBTITLES["Candidate Filter"], tuple(field.key for field in _COMPONENT_FIELDS["Candidate Filter"])),
    ),
    "Localization": (
        _group("Localization", _SUBTITLES["Localization"], ("Method",)),
    ),
    "ROI": (
        _group("ROI Configuration", _SUBTITLES["ROI"], tuple(field.key for field in _COMPONENT_FIELDS["ROI"])),
    ),
    "Kalman Filter": (
        _group("Estimator", "State model and covariance", ("Estimator", "State", "Q", "R", "Initial Covariance", "Process Noise", "Measurement Noise")),
        _group("Gating", "Innovation consistency check", ("Gating Threshold",), True),
    ),
    "Prediction": (
        _group("Prediction", _SUBTITLES["Prediction"], tuple(field.key for field in _COMPONENT_FIELDS["Prediction"])),
    ),
    "Adaptive Search": (
        _group("Search Geometry", "Envelope and trajectory", ("Search Algorithm", "X Amplitude", "Y Amplitude", "Frequency X", "Frequency Y", "Phase", "Duration", "Orientation")),
        _group("Uncertainty & Feedback", "Covariance-aware control", ("Covariance Scaling γ", "Eigenvalue Scaling", "Confidence Level", "Safety Margin", "Velocity Constraint", "NIS Feedback", "Window", "Threshold", "Amplitude Gain", "Expansion Gain"), True),
    ),
    "Analysis": (
        _group("Analysis View", _SUBTITLES["Analysis"], ("View",)),
    ),
}


_CAMERA_GROUPS = (
    _group("Transform", "Virtual camera pose", tuple(("Virtual Camera", field.key) for field in _COMPONENT_FIELDS["Virtual Camera"])),
    _group("Optics", "Field of view and intrinsics", tuple(("Optics", field.key) for field in _COMPONENT_FIELDS["Optics"])),
    _group("Sensor", "Resolution and readout", tuple(("Camera", field.key) for field in _COMPONENT_FIELDS["Camera"])),
    _group("PSF", "Point-spread function model", tuple(("PSF", field.key) for field in _COMPONENT_FIELDS["PSF"]), True),
    _group("Actuator", "Virtual gimbal response", tuple(("Actuator", field.key) for field in _COMPONENT_FIELDS["Actuator"]), True),
)


def _qualified_groups(component: str, collapsed: bool | None = None) -> tuple:
    """Reuse a component's groups in its parent scene-node inspector."""

    return tuple(
        _group(
            title,
            subtitle,
            ((component, field) for field in fields),
            default_collapsed if collapsed is None else collapsed,
        )
        for title, subtitle, fields, default_collapsed in _GROUP_LAYOUTS[component]
    )


_SCENE_GROUPS = {
    "Camera": _CAMERA_GROUPS,
    "Virtual Camera": _CAMERA_GROUPS,
    "Environment": (
        *_qualified_groups("Environment"),
        *_qualified_groups("Background"),
        *_qualified_groups("Noise", True),
        *_qualified_groups("Atmosphere", True),
        *_qualified_groups("Camera Jitter", True),
        *_qualified_groups("Platform Motion", True),
    ),
    "Targets": (
        *_qualified_groups("Targets"),
        *_qualified_groups("Beacon_01"),
        *_qualified_groups("Motion", True),
    ),
    "Beacon_01": (*_qualified_groups("Beacon_01"), *_qualified_groups("Motion", True)),
    "Tracking System": (
        *_qualified_groups("Tracking System"),
        *_qualified_groups("Preprocessing"),
        *_qualified_groups("Detector", True),
        *_qualified_groups("Candidate Filter", True),
        *_qualified_groups("Localization", True),
        *_qualified_groups("ROI", True),
        *_qualified_groups("Kalman Filter", True),
        *_qualified_groups("Prediction", True),
        *_qualified_groups("Adaptive Search", True),
    ),
}


class _CollapsibleGroup(QWidget):
    """Small group container with a native, stylesheet-friendly header."""

    def __init__(self, title: str, subtitle: str, collapsed: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "property-group")
        self.setMinimumWidth(0)
        self.default_expanded = not collapsed
        self.rows: list[_PropertyRow] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(0)

        header = QWidget(self)
        header.setProperty("class", "property-group-header")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(6, 4, 6, 3)
        header_layout.setSpacing(1)
        self.toggle = QToolButton(header)
        self.toggle.setText(title)
        self.toggle.setCheckable(True)
        self.toggle.setChecked(not collapsed)
        self.toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle.setProperty("class", "property-group-toggle")
        self.toggle.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.toggle.setToolTip(f"Expand or collapse {title.lower()} properties.")
        header_layout.addWidget(self.toggle)
        subtitle_label = QLabel(subtitle, header)
        subtitle_label.setWordWrap(True)
        subtitle_label.setProperty("class", "property-group-subtitle")
        subtitle_label.setToolTip(subtitle)
        header_layout.addWidget(subtitle_label)
        outer.addWidget(header)

        self.body = QWidget(self)
        self.body.setProperty("class", "property-group-body")
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(6, 2, 6, 4)
        body_layout.setSpacing(3)
        outer.addWidget(self.body)
        self._body_layout = body_layout
        self.toggle.toggled.connect(self.set_expanded)
        self.set_expanded(not collapsed)

    @property
    def title(self) -> str:
        return self.toggle.text()

    def add_row(self, row: "_PropertyRow") -> None:
        self.rows.append(row)
        self._body_layout.addWidget(row)

    def set_expanded(self, expanded: bool) -> None:
        self.toggle.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.body.setVisible(expanded)
        if self.toggle.isChecked() != expanded:
            self.toggle.setChecked(expanded)

    def set_group_visible(self, visible: bool) -> None:
        self.setVisible(visible)


class _PropertyRow(QWidget):
    def __init__(
        self,
        component: str,
        spec: FieldSpec,
        control: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.component = component
        self.field = spec.key
        self.spec = spec
        self.control = control
        self.dynamic_visible = True
        self.setProperty("class", "property-row")
        self.setMinimumWidth(0)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(spec.label or spec.key, self)
        label.setWordWrap(True)
        tooltip = _field_tooltip(spec)
        label.setToolTip(tooltip)
        label.setBuddy(control)
        label.setProperty("class", "property-label")
        label.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        label.setMinimumWidth(64)
        label.setMaximumWidth(126)
        self.label = label
        control.setToolTip(tooltip)
        control.setAccessibleName(f"{component}: {spec.label or spec.key}")
        control.setAccessibleDescription(tooltip)
        control.setProperty("class", "property-control")
        control.setProperty("component", component)
        control.setProperty("field", spec.key)
        control.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        layout.addWidget(label)
        layout.addWidget(control)
        self._search_blob = " ".join((spec.key, spec.label or spec.key, tooltip, component)).casefold()

    def matches(self, query: str) -> bool:
        return all(word in self._search_blob for word in query.casefold().split())


_PREPROCESSING_PARAMETERS = {
    "None": set(),
    "Gaussian Filter": {"Kernel Size", "Sigma"},
    "Median Filter": {"Kernel Size"},
    "Bilateral Filter": {"Kernel Size", "Sigma", "Color Sigma"},
    "Background Subtraction": {"History", "Learning Rate", "Foreground Threshold"},
    "Contrast Normalization": {"Lower Percentile", "Upper Percentile"},
    "CLAHE": {"Clip Limit", "Tile Grid Size"},
    "Temporal Filtering": {"Temporal Alpha", "Temporal Window"},
}


_CONDITIONAL_FIELDS = {
    ("Scenario", "Custom Time Scale"): ("Time Scale", "Custom"),
    ("Camera", "Resolution Width"): ("Resolution Preset", "Custom"),
    ("Camera", "Resolution Height"): ("Resolution Preset", "Custom"),
    ("Targets", "Count"): ("Target Count", "Multiple"),
    ("Beacon_01", "Custom Size"): ("Size", "Custom"),
    ("ROI", "Custom Width"): ("ROI Size", "Custom"),
    ("ROI", "Custom Height"): ("ROI Size", "Custom"),
    ("Prediction", "Custom Horizon"): ("Prediction Horizon", "Custom"),
}


_ENGINEERING_TIPS = {
    "SNR": "Signal-to-noise ratio: 10 log₁₀(signal power / noise power), in dB. Higher values indicate cleaner observations; negative values are valid.",
    "Standard Deviation": "Standard deviation σ, a nonnegative measure of spread. For Gaussian noise, about 68% of values lie within one σ of the mean.",
    "Cn²": "Refractive-index structure parameter Cn² in m⁻²/³. Use scientific notation, for example 1e-14; larger values describe stronger atmospheric turbulence.",
    "Coherence Length": "Atmospheric coherence length r₀ in metres: the transverse scale over which wavefront phase remains correlated.",
    "Scintillation": "Normalized intensity variation caused by propagation through turbulent air; this is a UI model setting.",
    "Beam Wander": "Normalized beam-centroid wander setting caused by low-frequency turbulence.",
    "PSF Broadening": "Relative broadening of the optical point-spread function due to the atmospheric model.",
    "PSF Model": "Point-spread function (PSF): the image of an ideal point source. Elliptical Gaussian permits different X and Y widths.",
    "PSF Mismatch": "Relative mismatch between the nominal PSF and the localization template; zero represents an exact nominal match.",
    "ROI / Truncation": "Width × height of the PSF support in pixels. Truncation limits the portion of the PSF represented by the model.",
    "fx": "Horizontal focal length in pixel coordinates, the fx entry of the camera intrinsic matrix.",
    "fy": "Vertical focal length in pixel coordinates, the fy entry of the camera intrinsic matrix.",
    "cx": "Horizontal principal-point coordinate in pixels, measured from the image origin.",
    "cy": "Vertical principal-point coordinate in pixels, measured from the image origin.",
    "Aperture": "Dimensionless f-number: focal length divided by entrance-pupil diameter. Smaller f-numbers admit more light.",
    "FOV Control": "Normalized field-of-view control position in percent; retained independently of the optical FOV values.",
    "Screen Width": "Virtual display width in pixels. Sensor resolution is configured separately with Resolution Preset.",
    "Screen Height": "Virtual display height in pixels. Sensor resolution is configured separately with Resolution Preset.",
    "Signal Power": "Optical signal power in dBm: 10 log₁₀(power / 1 mW). Negative values are normal for weak received signals.",
    "Peak Intensity": "Normalized peak beacon intensity; 0 is dark and 1 is the nominal sensor ceiling.",
    "Beacon / Background Ratio": "Beacon-to-background power ratio in decibels, independent of the noise SNR setting.",
    "k value": "Statistical detection multiplier k in μ + kσ, where μ and σ are the local background mean and standard deviation.",
    "Circularity": "Shape score 4πA/P². A perfect circle has circularity 1; elongated or irregular regions have lower scores.",
    "Aspect Ratio": "Dimensionless candidate bounding-box width divided by height.",
    "Ranking": "Candidate ranking criterion; distance from prediction can use covariance-aware Mahalanobis distance in a connected backend.",
    "Clip Limit": "CLAHE histogram contrast-clipping limit. Larger values permit stronger local contrast enhancement.",
    "Tile Grid Size": "CLAHE grid dimensions in tiles; this is a tile count, not an image-pixel size.",
    "History": "Number of frames retained by the background model.",
    "Learning Rate": "Background-model update weight from 0 to 1; a smaller weight adapts more slowly.",
    "Foreground Threshold": "Normalized intensity difference required to mark a pixel as foreground.",
    "Lower Percentile": "Lower intensity percentile used as the contrast-normalization black point.",
    "Upper Percentile": "Upper intensity percentile used as the contrast-normalization white point.",
    "Temporal Alpha": "Temporal smoothing weight for the newest frame, from 0 to 1. Larger values retain more of the new observation.",
    "Temporal Window": "Maximum number of frames in the temporal filtering window.",
    "Initial Covariance": "Initial state-uncertainty covariance scale; units follow the selected state coordinates.",
    "Process Noise": "Process-noise covariance scale. Larger values allow the state estimate to respond to unmodeled motion.",
    "Measurement Noise": "Measurement-noise covariance scale. Larger values reduce the relative influence of noisy observations.",
    "Uncertainty Ellipse": "Ellipse scale in standard deviations σ. In two dimensions, 1σ, 2σ, and 3σ enclose approximately 39%, 86%, and 99% of an ideal Gaussian distribution.",
    "Predicted Position": "Illustrative predicted image position in pixels; this editable demo value is not a computed tracking result.",
    "Predicted Velocity": "Illustrative predicted image velocity in pixels per second.",
    "Covariance": "Illustrative covariance summary. Mahalanobis distance scales a residual by its covariance rather than measuring raw pixel distance.",
    "Eigenvalue Scaling": "Multiplier applied to covariance eigenvalues when sizing the uncertainty-aligned search envelope.",
    "Confidence Level": "Probability mass targeted by the covariance-based search envelope, between 0 and 1.",
    "Window": "Number of recent frames used for normalized innovation squared (NIS) feedback.",
    "Threshold": "NIS decision threshold. NIS is the squared Mahalanobis innovation νᵀS⁻¹ν; 5.99 is approximately the 95% chi-square threshold for a two-dimensional observation.",
    "View": "Choose an existing performance-analysis view. Results in this prototype are illustrative.",
}


def _field_spec(component: str, field: str) -> FieldSpec | None:
    for spec in _COMPONENT_FIELDS.get(component, ()):
        if spec.key == field:
            return spec
    return None


def _field_tooltip(spec: FieldSpec) -> str:
    if spec.tooltip:
        return spec.tooltip
    if spec.key in _ENGINEERING_TIPS:
        return _ENGINEERING_TIPS[spec.key]
    key = spec.key.casefold()
    if key == "snr":
        return "Signal-to-noise ratio in dB; higher values indicate a cleaner observation."
    if "sigma" in key:
        return "Standard deviation σ controlling the width of the blur or filter response."
    if "nis" in key:
        return "Normalized innovation squared (NIS), a covariance-aware measurement consistency statistic."
    if "mahalanobis" in key or "gating" in key:
        return "Mahalanobis-distance gate in covariance-scaled units; larger values accept more outliers."
    if key in {"q", "r"}:
        return "Covariance term used by the state estimator; it controls uncertainty weighting."
    return ""


def _object_name(component: str, field: str) -> str:
    safe = "".join(char if char.isalnum() else "_" for char in f"{component}_{field}")
    return f"property_{safe}"


class Inspector(QWidget):
    """A narrow, searchable, collapsible property inspector."""

    edited = Signal(str, str, object)
    openRequested = Signal(str)

    components = PropertyStore.COMPONENTS

    def __init__(self, store: PropertyStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store
        self.controls: dict[tuple[str, str], QWidget] = {}
        self._rows: list[_PropertyRow] = []
        self._groups: list[_CollapsibleGroup] = []
        self._syncing = False
        self._selected_component = "Scenario"

        self.setObjectName("property-inspector")
        self.setProperty("class", "property-inspector")
        self.setMinimumWidth(250)
        self.setMaximumWidth(320)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title = QLabel("PROPERTIES", self)
        title.setProperty("class", "property-title")
        title_row.addWidget(title)
        title_row.addStretch(1)
        self.open_button = QPushButton("Open workspace", self)
        self.open_button.setObjectName("property-open-workspace")
        self.open_button.setProperty("class", "property-open")
        self.open_button.setToolTip("Open the selected component in its full workspace.")
        self.open_button.setFixedWidth(112)
        self.open_button.clicked.connect(self._open_selected)
        title_row.addWidget(self.open_button)
        outer.addLayout(title_row)

        self.component_label = QLabel(self._selected_component, self)
        self.component_label.setProperty("class", "property-component")
        outer.addWidget(self.component_label)
        self.subtitle_label = QLabel(_SUBTITLES[self._selected_component], self)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setProperty("class", "property-subtitle")
        outer.addWidget(self.subtitle_label)

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search properties…")
        self.search.setClearButtonEnabled(True)
        self.search.setObjectName("property-search")
        self.search.setProperty("class", "property-search")
        self.search.setToolTip("Filter by property label, component, or engineering term.")
        self.search.textChanged.connect(self._apply_filter)
        outer.addWidget(self.search)

        self.scroll = QScrollArea(self)
        self.scroll.setObjectName("property-scroll")
        self.scroll.setProperty("class", "property-scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content = QWidget(self.scroll)
        self.content.setProperty("class", "property-content")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(5)
        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll, 1)

        self.store.changed.connect(self._store_changed)
        self.select(self._selected_component)

    @property
    def selected_component(self) -> str:
        return self._selected_component

    def select(self, component: str) -> str:
        """Show *component* and return its canonical component key."""

        canonical = _canonical_component(component)
        if canonical not in _COMPONENT_FIELDS:
            supported = ", ".join(self.components)
            raise ValueError(f"Unknown component {component!r}; expected one of: {supported}")
        self._selected_component = canonical
        self.component_label.setText(canonical)
        self.subtitle_label.setText(_SUBTITLES.get(canonical, "Configuration properties"))
        self._clear_content()
        layouts = _SCENE_GROUPS[canonical] if canonical in _SCENE_GROUPS else _GROUP_LAYOUTS[canonical]
        for title, subtitle, refs, collapsed in layouts:
            group = _CollapsibleGroup(title, subtitle, collapsed, self.content)
            self._groups.append(group)
            self.content_layout.addWidget(group)
            for ref in refs:
                if isinstance(ref, tuple):
                    field_component, field = ref
                else:
                    field_component, field = canonical, ref
                spec = _field_spec(field_component, field)
                if spec is None:
                    continue
                control = self._make_control(field_component, spec)
                row = _PropertyRow(field_component, spec, control, group.body)
                group.add_row(row)
                self._rows.append(row)
                self.controls[(field_component, spec.key)] = control
                self._connect_control(field_component, spec.key, control)
        self.content_layout.addStretch(1)
        self._update_preprocessing_rows()
        self._apply_filter()
        return canonical

    def _clear_content(self) -> None:
        self.controls.clear()
        self._rows.clear()
        self._groups.clear()
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _make_control(self, component: str, spec: FieldSpec) -> QWidget:
        value = self.store.get(component, spec.key, spec.default)
        tooltip = _field_tooltip(spec)
        if spec.kind == "choice":
            control = QComboBox(self.content)
            control.addItems(list(spec.options))
            control.setCurrentText(str(value))
            control.setFixedWidth(132)
        elif spec.kind == "text":
            control = QLineEdit(str(value), self.content)
            control.setFixedWidth(132)
        elif spec.kind == "check":
            control = QCheckBox(self.content)
            control.setChecked(bool(value))
            control.setFixedWidth(24)
        elif spec.kind == "integer":
            control = QSpinBox(self.content)
            control.setRange(int(spec.minimum), int(spec.maximum))
            control.setValue(int(value))
            if spec.unit:
                control.setSuffix(f" {spec.unit}")
            control.setFixedWidth(112)
        else:
            control = QDoubleSpinBox(self.content)
            control.setRange(float(spec.minimum), float(spec.maximum))
            control.setDecimals(spec.decimals)
            control.setValue(float(value))
            if spec.unit:
                control.setSuffix(f" {spec.unit}")
            control.setFixedWidth(112)
        control.setObjectName(_object_name(component, spec.key))
        if tooltip:
            control.setToolTip(tooltip)
        return control

    def _connect_control(self, component: str, field: str, control: QWidget) -> None:
        callback = lambda *_args, c=component, f=field, w=control: self._control_edited(c, f, w)
        if isinstance(control, QComboBox):
            control.currentTextChanged.connect(callback)
        elif isinstance(control, QLineEdit):
            control.textChanged.connect(callback)
        elif isinstance(control, QCheckBox):
            control.toggled.connect(callback)
        elif isinstance(control, (QSpinBox, QDoubleSpinBox)):
            control.valueChanged.connect(callback)

    @staticmethod
    def _control_value(control: QWidget) -> Any:
        if isinstance(control, QComboBox):
            return control.currentText()
        if isinstance(control, QLineEdit):
            return control.text()
        if isinstance(control, QCheckBox):
            return control.isChecked()
        if isinstance(control, (QSpinBox, QDoubleSpinBox)):
            return control.value()
        return None

    def _control_edited(self, component: str, field: str, control: QWidget) -> None:
        if self._syncing:
            return
        value = self._control_value(control)
        previous = self.store.get(component, field, object())
        self.store.set(component, field, value)
        if previous != value:
            self.edited.emit(component, field, value)
        self._update_preprocessing_rows()

    def _store_changed(self, component: str, field: str, value: Any) -> None:
        control = self.controls.get((component, field))
        if control is not None:
            self._set_control_value(control, value)
        self._update_preprocessing_rows()

    def _set_control_value(self, control: QWidget, value: Any) -> None:
        self._syncing = True
        try:
            if isinstance(control, QComboBox):
                control.setCurrentText(str(value))
            elif isinstance(control, QLineEdit):
                control.setText(str(value))
            elif isinstance(control, QCheckBox):
                control.setChecked(bool(value))
            elif isinstance(control, (QSpinBox, QDoubleSpinBox)):
                control.setValue(value)
        finally:
            self._syncing = False

    def _update_preprocessing_rows(self) -> None:
        pipeline = self.store.get("Preprocessing", "Pipeline", "None")
        allowed = _PREPROCESSING_PARAMETERS.get(str(pipeline), set())
        for row in self._rows:
            conditional = _CONDITIONAL_FIELDS.get((row.component, row.field))
            if conditional is not None:
                controlling_field, expected = conditional
                row.dynamic_visible = self.store.get(row.component, controlling_field, "") == expected
            elif row.component == "Preprocessing":
                row.dynamic_visible = row.field == "Pipeline" or row.field in allowed
        self._apply_filter()

    def _apply_filter(self, *_args: object) -> None:
        query = self.search.text().strip()
        for group in self._groups:
            matching = []
            for row in group.rows:
                visible = row.dynamic_visible and row.matches(query)
                row.setVisible(visible)
                if visible:
                    matching.append(row)
            group.set_group_visible(bool(matching))
            if query and matching and not group.body.isVisible():
                group.set_expanded(True)

    def _open_selected(self) -> None:
        self.openRequested.emit(self._selected_component)
