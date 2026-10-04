from dataclasses import dataclass
import math
import random


@dataclass
class Telemetry:
    frame: int = 1842
    fps: float = 60.0
    u: float = 321.42
    v: float = 219.18
    est_u: float = 319.11
    est_v: float = 220.24
    pred_u: float = 328.45
    pred_v: float = 215.30
    sigma_u: float = 18.4
    sigma_v: float = 7.2
    ellipse_angle: float = 32.0
    nis: float = 2.17
    latency: float = 18.2
    lock: str = "LOCKED"
    motion_model: str = "Figure-8"
    search_u: float = 321.42
    search_v: float = 219.18
    # Baseline vs Achieved targets
    acq_time: float = 0.82  # Target <= 2.0s
    reacq_time: float = 0.41  # Target <= 1.0s
    track_error: float = 2.31  # Target <= 10.0px
    loss_rate: float = 1.6  # Target < 5.0%
    target_acq_req: str = "≤ 2.0 s"
    target_error_req: str = "≤ 10.0 px"
    target_loss_req: str = "< 5.0 %"
    target_reacq_req: str = "≤ 1.0 s"
    target_fps_req: str = "≥ 20 FPS"


class MockSimulation:
    """Rich simulation engine with motion models, target loss demo triggers, prediction, and adaptive search."""
    def __init__(self):
        self.t = 0.0
        self.data = Telemetry()
        self.running = False
        self.rng = random.Random(42)
        self.motion_model = "Figure-8"
        self.loss_timer = 0
        self.force_loss = False

    def reset(self):
        self.t = 0.0
        self.data = Telemetry()
        self.loss_timer = 0
        self.force_loss = False

    def trigger_loss_demo(self):
        """Trigger an explicit state transition demo: LOCKED -> TARGET LOST -> SEARCHING -> REACQUIRING -> LOCKED."""
        self.force_loss = True
        self.loss_timer = 30
        self.data.lock = "TARGET LOST"

    def set_motion_model(self, model: str):
        self.motion_model = model
        self.data.motion_model = model

    def tick(self):
        self.t += 0.05
        d = self.data
        d.frame += 1

        # Target motion trajectories
        if self.motion_model == "Circular":
            d.u = 320 + 85 * math.cos(self.t * 0.9)
            d.v = 240 + 85 * math.sin(self.t * 0.9)
        elif self.motion_model == "Straight":
            d.u = 120 + ((d.frame * 2.2) % 400)
            d.v = 180 + ((d.frame * 1.1) % 160)
        elif self.motion_model == "Sinusoidal":
            d.u = 150 + ((d.frame * 2.5) % 340)
            d.v = 240 + 55 * math.sin(self.t * 1.4)
        elif self.motion_model == "Spiral":
            r = min(120, 10 + (self.t * 8) % 110)
            d.u = 320 + r * math.cos(self.t * 1.2)
            d.v = 240 + r * math.sin(self.t * 1.2)
        elif self.motion_model == "Random":
            d.u = max(60, min(580, d.u + self.rng.uniform(-4, 4)))
            d.v = max(60, min(420, d.v + self.rng.uniform(-3, 3)))
        else:  # Figure-8 default
            d.u = 320 + 68 * math.sin(self.t * 0.8) * math.cos(self.t * 0.31)
            d.v = 240 + 42 * math.sin(self.t * 1.15)

        # Estimate & 5s prediction
        d.est_u = d.u + self.rng.uniform(-2.2, 2.2)
        d.est_v = d.v + self.rng.uniform(-2.2, 2.2)
        d.pred_u = d.est_u + 14 * math.cos(self.t * 0.5)
        d.pred_v = d.est_v + 10 * math.sin(self.t * 0.5)

        # Uncertainty bounds
        d.sigma_u = 16.0 + 4.0 * math.sin(self.t * 0.3)
        d.sigma_v = 7.0 + 2.0 * math.cos(self.t * 0.4)
        d.ellipse_angle = (30.0 + self.t * 5.0) % 360.0

        # Adaptive Lissajous search trajectory offset
        d.search_u = d.pred_u + d.sigma_u * 1.2 * math.sin(self.t * 2.4)
        d.search_v = d.pred_v + d.sigma_v * 1.2 * math.cos(self.t * 1.8 + 0.4)

        # Performance metrics
        d.fps = 59.5 + self.rng.uniform(-1.2, 1.2)
        d.nis = max(0.4, 2.15 + self.rng.uniform(-0.5, 0.5))
        d.latency = 18.0 + self.rng.uniform(-2.0, 2.5)
        d.track_error = math.hypot(d.u - d.est_u, d.v - d.est_v)

        # State machine transition demo logic
        if self.force_loss:
            self.loss_timer -= 1
            if self.loss_timer > 20:
                d.lock = "TARGET LOST"
            elif self.loss_timer > 10:
                d.lock = "SEARCHING"
            elif self.loss_timer > 0:
                d.lock = "REACQUIRING"
            else:
                d.lock = "LOCKED"
                self.force_loss = False
        else:
            if self.rng.random() < 0.008:
                d.lock = self.rng.choice(["LOCKED", "SEARCHING", "REACQUIRING"])
            elif d.lock != "LOCKED" and self.rng.random() < 0.15:
                d.lock = "LOCKED"

        return d
