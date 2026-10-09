# SIH Problem Statement — UI Coverage Checklist (Prototype Scope)

Scope note: this is a **UI prototype with hardcoded mock values** — that is by design and is
NOT counted as a gap. An item is only "missing" if the spec setting has **no UI element at all**
(no config field, no panel, no display widget) anywhere in the app.

Status legend:
- ✅ **In UI** — a config field / panel / metric display exists for it
- ❌ **Not in UI** — no UI element for this spec item

---

## A. Camera Parameters

| # | Parameter (Spec) | Status | Where in UI |
|---|------------------|--------|-------------|
| 1 | Screen Size ≥ 2000×2000, user-defined | ✅ | Camera Config → "Screen Width / Screen Height" (2000 px defaults) |
| 2 | Camera Type: Monochrome FPA, optional Colour | ✅ | Camera Config → "Sensor Type" combo (Monochrome / Color) |
| 3 | Camera Resolution 640×480, user-defined | ✅ | Camera Config → "Resolution Preset" + custom width/height |
| 4 | Camera FOV user-defined, default 4°×3° | ✅ | Camera Config → "Horizontal FOV" 4° / "Vertical FOV" 3° |
| 5 | Camera update Rate 30 Hz (min.) | ✅ | Inspector → Sensor → "Frame Rate" (60 Hz) |
| 6 | Initial Camera Position = screen centre | ✅ | Camera Config → "Initial Pan / Tilt / Roll" = 0° |

## B. Target Parameters

| # | Parameter (Spec) | Status | Where in UI |
|---|------------------|--------|-------------|
| 7 | Target Type: Beacon Spot | ✅ | Target Config → "Target Type" combo |
| 8 | Number of Targets: 1 mandatory, multiple optional | ❌ **Partial** | Only a "Target Count: 1 / Multiple" combo — there is **no UI to add or configure a 2nd/3rd target** (no target list, no Beacon_02 in the scene explorer, no per-target shape/size/motion settings) |
| 9 | Target Shape user-defined, default Square | ✅ | Target Config → "Shape" combo (Square / Circle / Gaussian Spot / Ellipse / Custom) |
| 10 | Target Size 5–20 px, default 10×10 | ✅ | Target Config → "Target Size" combo (5 / 10 / 20 / Custom px) |
| 11 | Initial Target Location user-defined, default Random | ✅ | Target Config → "Position Mode" (Center / Random / User Defined / Edge / Corner / Outside FOV) + X/Y Coordinate |
| 12 | Motion: ≥4 selectable (Straight, Circular, Figure-8, Random; opt. Spiral, Sinusoidal, User-defined) | ✅ | Target Config → "Primary Model" combo — all six spec motions plus extras (Stop-Go, Oscillatory, Recorded Trajectory, …) |

## C. Camera Motion Constraints

| # | Parameter (Spec) | Status | Where in UI |
|---|------------------|--------|-------------|
| 13 | Max. Pan Speed 5–10 °/s, user-defined | ✅ | Camera Config → "Max Pan Speed" (°/s) |
| 14 | Max. Tilt Speed 5–10 °/s, user-defined | ✅ | Camera Config → "Max Tilt Speed" (°/s) |
| 15 | Update Interval ≥ 20 Hz | ✅ | Camera Config → "Command Update Rate" (60 Hz) |

## D. Performance Specifications (as real-time metric displays)

| # | Parameter (Spec) | Status | Where in UI |
|---|------------------|--------|-------------|
| 16 | Acquisition Time ≤ 2 s | ✅ | Live Tracking metrics + Performance Analysis ("Acquisition Time") |
| 17 | Tracking Error ≤ 10 px | ✅ | Live Tracking metrics + Analysis ("Centroid RMSE", "Max Tracking Error") |
| 18 | Target Loss < 5 % | ✅ | Analysis ("Target Loss Rate", "Lock Retention") |
| 19 | Re-acquisition Time ≤ 1 s | ✅ | Live Tracking metrics + Analysis ("Reacquisition") |
| 20 | Processing Speed ≥ 20 FPS | ✅ | Live Tracking metrics + Analysis ("FPS", "Mean/P95 Latency") |

## E. Disturbances & Noise

| # | Parameter (Spec) | Status | Where in UI |
|---|------------------|--------|-------------|
| 21.1 | Image Noise: Salt & Pepper (~10%), Gaussian, Poisson — selectable | ✅ | Environment Config → "Noise Type" combo (all three + extras), Enable checkbox, Density / Salt / Pepper probability fields |
| 21.2 | Max. std. deviation of noise = 20 px | ✅ | Environment Config → Noise "Standard Deviation" |
| 21.3 | Max. Camera Jitter ± 20 px / frame | ✅ | Environment Config → "Camera Jitter" section (Model, X/Y/Angular, Standard Deviation, Maximum Jitter) |
| 21.4 | Atmospheric: Clear / Haze / Fog / Rain / Low light (contrast & brightness reduction) | ✅ | Environment Config → "Atmosphere" section ("Condition" combo + "Contrast Reduction" + attenuation/turbulence fields) |
| 21.5 | Platform Motion ± 20 px/frame (Linear mandatory; Circular/Random/Spiral/Figure-8 optional) | ✅ | Environment Config → "Platform Motion" section (all six model options) |

## F. Expected-Solution Capabilities (as UI surfaces)

| Capability | Status | Where in UI |
|------------|--------|-------------|
| Configurable virtual environment | ✅ | Environment Config page (Background / Noise / Atmosphere / Jitter / Platform Motion) |
| One or more moving targets | ❌ **Partial** | Same gap as B-8: single target config only, no add-target UI |
| Movable virtual camera | ✅ (as config + viewport) | Camera Config page + Live Tracking viewport with PTZ lock box |
| Automatic target detection / CV tracking | ✅ (as pipeline UI) | Tracking Pipeline workspace (Preprocessing, Detection, Candidate Filtering, Localization, ROI, Estimator, Prediction, Adaptive Search tabs) + AI Detector inspector group |
| Camera control / repositioning | ✅ (as actuator UI) | Inspector → Actuator group (speeds, accelerations, response, delay) |
| Disturbance generation in feed | ✅ (as config UI) | Environment Config page |
| Real-time performance & statistics display | ✅ | Live Tracking metrics cards + live plots + Performance Analysis dashboard |
| Benchmark video input (.mp4 @30fps, bypass PTZ) | ✅ | Video Benchmark workspace (Video File, FPS, Frames, "Bypass Virtual PTZ" checkbox) |
| Auto-generated performance log | ✅ | "Generate Performance Log" checkbox + Export CSV / Export Figure / Generate Report buttons + Technical Logs console |
| Live Tracking status (lock state machine) | ✅ | Live Tracking viewport (LOCKED / SEARCHING / REACQUIRING) + Simulation menu → Trigger Target Loss Demo |

---

## Summary — what is genuinely NOT in the UI

Only **one** spec item has no real UI element:

1. **Multi-target management** (Spec B-8): "Target Count: 1 / Multiple" exists as a combo, but there is no way to actually add a second beacon and give it its own shape, size, position, and motion model. No target list anywhere in the UI (scene explorer, inspector, or target config page all reference a single `Beacon_01`).

Everything else in the SIH parameter table (rows 1–21 and sub-items), all six performance
criteria, and all expected-solution capabilities have a corresponding UI surface somewhere in
the app (with hardcoded mock defaults, as intended for the prototype).
