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
    nis: float = 2.17
    latency: float = 18.2
    lock: str = "LOCKED"


class MockSimulation:
    """Tiny deterministic telemetry source. No vision, physics, or filter math."""
    def __init__(self):
        self.t = 0.0
        self.data = Telemetry()
        self.running = False
        self.rng = random.Random(42)

    def reset(self):
        self.t = 0.0
        self.data = Telemetry()

    def tick(self):
        self.t += 0.05
        d = self.data
        d.frame += 1
        d.u = 320 + 62 * math.sin(self.t * .8) * math.cos(self.t * .31)
        d.v = 240 + 38 * math.sin(self.t * 1.15)
        d.est_u = d.u + self.rng.uniform(-2.8, 2.8)
        d.est_v = d.v + self.rng.uniform(-2.8, 2.8)
        d.fps = 59.5 + self.rng.uniform(-1.4, 1.4)
        d.nis = max(.4, 2.2 + self.rng.uniform(-.65, .65))
        d.latency = 18 + self.rng.uniform(-2.8, 3.2)
        if self.rng.random() < .012:
            d.lock = self.rng.choice(["LOCKED", "SEARCHING", "REACQUIRING"])
        elif d.lock != "LOCKED" and self.rng.random() < .18:
            d.lock = "LOCKED"
        return d
