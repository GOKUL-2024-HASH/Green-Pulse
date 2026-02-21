"""
stream/live_append.py — GreenPulse Live Sensor Feed
=====================================================
Appends live PM2.5 readings to data/sensor_stream.csv every 5 seconds.
The existing Pathway pipeline watches this file in streaming mode and
will process new rows automatically without restart.

DESIGN:
  - Append-only writes (never truncates or rewrites the file)
  - Flush after every row (ensures Pathway's inotify/polling detects it)
  - Fixed emission plan: Normal → Transient Spike → Sustained Violation
  - Pure Python standard library (no new dependencies)

USAGE (in a second terminal, while main.py is already running):
  python3 stream/live_append.py

INTEGRATION:
  Pathway's pw.io.csv.read(..., mode="streaming") watches the file
  for appended rows using OS-level file monitoring.
  Each new row triggers the full pipeline: normalize → window → rules →
  compliance → explanation → CLI output.
"""

import csv
import os
import sys
import time
from datetime import datetime, timezone

# ─── Path setup ──────────────────────────────────────────────────────────────

# Allow running from any working directory
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_FILE    = os.path.join(PROJECT_ROOT, "data", "sensor_stream.csv")

# ─── Emission plan ───────────────────────────────────────────────────────────
# Each entry describes one "phase" of the simulation.
# Fields: station_id, phase_name, n_rows, pm25_base, pm25_noise_range
#
# PM2.5 limits (from config/pm25_rules.yaml):
#   Residential (Alandur):  limit=60,  min_duration=10 min
#   Industrial  (Manali):   limit=120, min_duration=20 min
#
# At 5-second intervals, 12 rows = 1 minute of simulated data.
# To trigger VIOLATION: need > min_duration rows above limit in 30-min window.

EMISSION_PLAN = [
    # Phase 1: Normal — both stations well below limit
    # 24 rows × 5s = 2 minutes
    {
        "phase":   "NORMAL",
        "rows": [
            {"station_id": "Alandur", "pm25_base": 38.0, "noise": 3.0},
            {"station_id": "Manali",  "pm25_base": 95.0, "noise": 5.0},
        ],
        "count":   24,   # emit 24 ticks of this phase
    },

    # Phase 2: Transient spike — Alandur briefly above 60 (< 10 min = TRANSIENT)
    # 18 rows × 5s = 90 seconds → ~2 min spike (will show TRANSIENT)
    {
        "phase":   "TRANSIENT_SPIKE",
        "rows": [
            {"station_id": "Alandur", "pm25_base": 80.0, "noise": 4.0},
            {"station_id": "Manali",  "pm25_base": 98.0, "noise": 4.0},
        ],
        "count":   18,
    },

    # Phase 3: Back to normal briefly
    # 12 rows × 5s = 1 minute
    {
        "phase":   "RECOVERY",
        "rows": [
            {"station_id": "Alandur", "pm25_base": 42.0, "noise": 3.0},
            {"station_id": "Manali",  "pm25_base": 90.0, "noise": 4.0},
        ],
        "count":   12,
    },

    # Phase 4: Sustained violation — Alandur above 60 for > 10 min = VIOLATION
    # 150 rows × 5s = 750 seconds = 12.5 minutes sustained
    # → Pathway's 15-min window will accumulate enough to trigger VIOLATION
    {
        "phase":   "SUSTAINED_VIOLATION",
        "rows": [
            {"station_id": "Alandur", "pm25_base": 92.0, "noise": 5.0},
            {"station_id": "Manali",  "pm25_base": 105.0, "noise": 4.0},
        ],
        "count":   150,
    },

    # Phase 5: Cooldown — drop back below limit
    # 24 rows × 5s = 2 minutes
    {
        "phase":   "COOLDOWN",
        "rows": [
            {"station_id": "Alandur", "pm25_base": 35.0, "noise": 2.0},
            {"station_id": "Manali",  "pm25_base": 88.0, "noise": 4.0},
        ],
        "count":   24,
    },
]

INTERVAL_SECONDS = 5   # emit one "tick" every 5 seconds

# ─── Deterministic noise (no random — fixed seed pattern) ───────────────────
# Using a simple sine-like offset for deterministic "natural" variation
def _noise(tick: int, amplitude: float) -> float:
    """Deterministic pseudo-noise based on tick index. No random module needed."""
    import math
    return amplitude * math.sin(tick * 1.3) * 0.5


# ─── Core writer ─────────────────────────────────────────────────────────────

def _now_iso() -> str:
    """Current time as ISO-8601 string with T separator (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _append_row(writer, f, station_id: str, pm25: float) -> None:
    """Write one row and immediately flush so the OS signals the file change."""
    ts = _now_iso()
    writer.writerow({
        "station_id": station_id,
        "timestamp":  ts,
        "pm25":       round(pm25, 2),
    })
    f.flush()
    os.fsync(f.fileno())   # guarantee the kernel writes to disk


# ─── Main loop ───────────────────────────────────────────────────────────────

def run() -> None:
    print("╔══════════════════════════════════════════════╗")
    print("║   GreenPulse — Live Sensor Feed              ║")
    print("║   Appending to: data/sensor_stream.csv       ║")
    print("║   Interval:     5 seconds per tick           ║")
    print("║   Press Ctrl-C to stop                       ║")
    print("╚══════════════════════════════════════════════╝\n")

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    # Open in append mode — NEVER truncate
    with open(DATA_FILE, mode="a", newline="", buffering=1) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["station_id", "timestamp", "pm25"],
        )

        # Write header only if file is empty (first run)
        if f.tell() == 0:
            writer.writeheader()
            f.flush()

        global_tick = 0

        for phase_def in EMISSION_PLAN:
            phase_name = phase_def["phase"]
            station_rows = phase_def["rows"]
            count = phase_def["count"]

            print(f"► Phase: {phase_name} ({count} ticks × {INTERVAL_SECONDS}s "
                  f"= {count * INTERVAL_SECONDS}s)")

            for tick in range(count):
                for station in station_rows:
                    pm25 = station["pm25_base"] + _noise(global_tick, station["noise"])
                    _append_row(writer, f, station["station_id"], pm25)

                    print(
                        f"  [{_now_iso()}] "
                        f"{station['station_id']:10s}  "
                        f"PM2.5={pm25:6.1f} µg/m³  "
                        f"phase={phase_name}"
                    )

                global_tick += 1
                time.sleep(INTERVAL_SECONDS)

    print("\n✅ Emission plan complete. All phases emitted.")
    print("   GreenPulse pipeline will finalize any remaining window computations.")


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n⛔ Live feed stopped by user.")
        sys.exit(0)
