"""
demo.py — GreenPulse Windows Demonstration Script
================================================
Simulates the FULL pipeline (stream → normalize → window → rules →
compliance → explanation → CLI output) using plain Python.
Runs on native Windows with no Pathway dependency.

Usage:
    python demo.py
"""
import csv
import os
import random
import time
from datetime import datetime, timedelta


# ─── Config ──────────────────────────────────────────────────────────────────

ZONE_MAP = {
    "Alandur":   "Residential",
    "Manali":    "Industrial",
    "Velachery": "Residential",
}

PM25_RULES = {
    "Residential": {"limit": 60,  "min_duration": 10, "severity": "High"},
    "Industrial":  {"limit": 120, "min_duration": 20, "severity": "Medium"},
}

RANDOM_SEED = 42
STATIONS    = list(ZONE_MAP.keys())
DATA_FILE   = "data/sensor_stream.csv"


# ─── Step 1: Generate data (same as data_generator.py) ───────────────────────

def generate_data(n_minutes: int = 60) -> list[dict]:
    random.seed(RANDOM_SEED)
    base = {"Alandur": 45.0, "Manali": 110.0, "Velachery": 50.0}
    rows, t = [], datetime.now()

    for i in range(n_minutes):
        for station in STATIONS:
            val = base[station] + random.uniform(-5, 5)
            if station == "Velachery" and 10 <= i <= 15:  val += 40
            if station == "Alandur"   and 30 <= i <= 50:  val += 50
            if station == "Manali"    and 40 <= i <= 45:  val += 20
            rows.append({
                "station_id": station,
                "timestamp":  t.strftime("%Y-%m-%dT%H:%M:%S"),
                "pm25":       round(val, 2),
            })
        t += timedelta(minutes=1)

    return rows


# ─── Step 2: Simulate normalization ──────────────────────────────────────────

def normalize(rows: list[dict]) -> list[dict]:
    return [
        r for r in rows
        if r["station_id"] and 0.0 <= float(r["pm25"]) <= 1000.0
    ]


# ─── Step 3: Simulate 15-min rolling window ───────────────────────────────────

def window_metrics(rows: list[dict], window_min: int = 15) -> list[dict]:
    from collections import defaultdict
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["station_id"]].append(r)

    results = []
    for station, records in grouped.items():
        records.sort(key=lambda x: x["timestamp"])
        for i in range(len(records)):
            t_end = datetime.strptime(records[i]["timestamp"], "%Y-%m-%d %H:%M:%S")
            t_start = t_end - timedelta(minutes=window_min)
            window = [
                float(r["pm25"]) for r in records
                if t_start <= datetime.strptime(r["timestamp"], "%Y-%m-%dT%H:%M:%S") <= t_end
            ]
            if not window:
                continue
            results.append({
                "station_id": station,
                "window_end": t_end,
                "avg_pm25":   round(sum(window) / len(window), 2),
                "pm25_range": round(max(window) - min(window), 2),
                "count":      len(window),
            })
    return results


# ─── Step 4: Apply zone rules ────────────────────────────────────────────────

def apply_rules(windowed: list[dict]) -> list[dict]:
    enriched = []
    for row in windowed:
        zone  = ZONE_MAP.get(row["station_id"], "Unknown")
        rule  = PM25_RULES.get(zone, {"limit": 999, "min_duration": 99, "severity": "Unknown"})
        enriched.append({
            **row,
            "zone":          zone,
            "limit":         rule["limit"],
            "min_duration":  rule["min_duration"],
            "severity":      rule["severity"],
            "is_exceeding":  row["avg_pm25"] > rule["limit"],
        })
    return enriched


# ─── Step 5: Detect violations (30-min duration check) ────────────────────────

def detect_violations(enriched: list[dict]) -> list[dict]:
    from collections import defaultdict
    by_station = defaultdict(list)
    for r in enriched:
        by_station[r["station_id"]].append(r)

    results = []
    for station, records in by_station.items():
        records.sort(key=lambda x: x["window_end"])
        for i, row in enumerate(records):
            t_end   = row["window_end"]
            t_start = t_end - timedelta(minutes=30)
            window  = [
                r for r in records
                if t_start <= r["window_end"] <= t_end
            ]
            exceeded_mins = sum(1 for r in window if r["is_exceeding"])
            avg           = row["avg_pm25"]
            limit         = row["limit"]
            req           = row["min_duration"]

            if avg > limit:
                status = "VIOLATION" if exceeded_mins >= req else "TRANSIENT"
            else:
                status = "OK"

            results.append({
                **row,
                "exceed_minutes":  exceeded_mins,
                "status":          status,
                "current_avg_pm25": avg,
            })

    return results


# ─── Step 6: Generate explanation ─────────────────────────────────────────────

def explain(row: dict) -> str:
    s = row["station_id"]
    z = row["zone"]
    avg = row["current_avg_pm25"]
    lim = row["limit"]
    dur = row["exceed_minutes"]
    status = row["status"]

    if status == "OK":
        return f"Station {s}: compliant at {avg:.1f} µg/m³ (limit {lim})."
    return (
        f"Station {s} ({z}): PM2.5 {avg:.1f} µg/m³ exceeds limit {lim} "
        f"for {dur} minutes. Status: {status}. Regulatory action may be required."
    )


# ─── Step 7: Format CLI output ────────────────────────────────────────────────

def format_event(row: dict, explanation: str) -> str:
    header = {
        "VIOLATION": "[VIOLATION_CANDIDATE] 🔴",
        "TRANSIENT":  "[TRANSIENT_SPIKE]     ⚠️ ",
        "OK":         "[COMPLIANT]           ✅ ",
    }.get(row["status"], f"[{row['status']}]")

    return (
        f"\n{header}\n"
        f"{'─'*50}\n"
        f"Station:     {row['station_id']} ({row['zone']})\n"
        f"PM2.5 Avg:   {row['current_avg_pm25']:.1f} µg/m³  "
        f"(Limit: {row['limit']:.0f} µg/m³)\n"
        f"Duration:    {row['exceed_minutes']} min  "
        f"(Threshold: {row['min_duration']} min)\n"
        f"Severity:    {row['severity']}\n"
        f"Explanation: {explanation}\n"
        f"Status:      PENDING_OFFICER_REVIEW\n"
        f"{'─'*50}"
    )


# ─── Main demo runner ─────────────────────────────────────────────────────────

def run_demo():
    print("\n" + "═" * 55)
    print("  🌿 GreenPulse — Environmental Compliance Monitor")
    print("     (Windows Demo Mode — Pathway Simulated)")
    print("═" * 55 + "\n")

    # Generate & save data
    print("⟳  Generating sensor data…")
    os.makedirs("data", exist_ok=True)
    rows = generate_data(60)
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["station_id", "timestamp", "pm25"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓  {len(rows)} records written to {DATA_FILE}\n")

    # Pipeline
    print("⟳  Running pipeline…")
    normed    = normalize(rows)
    windowed  = window_metrics(normed, window_min=15)
    enriched  = apply_rules(windowed)
    compliance = detect_violations(enriched)

    # Display — stream events one by one with a short delay
    print("\n=== GREENPULSE LIVE MONITOR (SIMULATED) ===\n")
    time.sleep(0.5)

    seen = set()
    for row in compliance:
        # Only show the last reading per station per status change (de-dup)
        key = (row["station_id"], row["status"], row["exceed_minutes"])
        if key in seen:
            continue
        seen.add(key)

        expl   = explain(row)
        output = format_event(row, expl)
        print(output)
        time.sleep(0.2)

    print("\n✅  Demo complete. Run on WSL2 for the live Pathway stream.")


if __name__ == "__main__":
    run_demo()
