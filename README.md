# FSOC Virtual Camera Tracking System

Professional PySide6/PyQtGraph frontend prototype for an AI-based coarse alignment and beacon tracking workstation.

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

The application starts on the Live Tracking cockpit with a loaded demonstration scenario. Select **Scenario → START SIMULATION** to activate the lightweight mock telemetry generator. All algorithms, image processing, filters, search math, and backend processing are intentionally placeholders.

## Structure

- `ui/` — main window and reusable visual widgets
- `pages/` — configuration, live, analysis, research, benchmark, Monte Carlo, and log pages
- `mock/` — replaceable telemetry generator boundary
- `styles/` — styling is currently embedded in `ui/main_window.py` for the standalone prototype

The mock layer is deliberately small so a future simulation service can replace `MockSimulation` without redesigning the UI.
