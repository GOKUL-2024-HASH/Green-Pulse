# GreenPulse — Completion Report
> Real-Time PM2.5 Environmental Compliance Monitoring

---

## System Status: ✅ COMPLETE

All modules implemented, debugged, and verified.

---

## Architecture Overview

```
data/sensor_stream.csv  ←── stream/live_append.py (live feed, 5s intervals)
        │
        ▼
src/stream.py           Schema: station_id:str, timestamp:DateTimeNaive, pm25:float
        │
src/normalization.py    Filter: pm25 in [0,1000], station_id non-empty
        │
src/windowing.py        15-min sliding window (timedelta), avg/min/max/range per station
        │
src/rules.py            Join with config → adds zone, limit, min_duration,
        │               severity, rule_reference, health_context
        │
src/compliance.py       30-min sliding window, classify: OK / TRANSIENT / VIOLATION
        │
src/explanation.py      LLM (gemini-2.0-flash) or deterministic template explanation
        │
src/cli.py              Two-tier formatter: single-line OK/TRANSIENT,
        │               full regulatory block for VIOLATION
        │
pw.io.subscribe()       Sole output sink — prints raw log_entry string
        │
pw.run()                Single execution entrypoint
```

---

## Module Inventory

| File | Purpose | Status |
|---|---|---|
| `main.py` | Pipeline orchestration + pw.io.subscribe sink | ✅ |
| `src/stream.py` | CSV ingestion, pw.DateTimeNaive schema | ✅ |
| `src/normalization.py` | Validation filter | ✅ |
| `src/windowing.py` | 15-min sliding window metrics | ✅ |
| `src/rules.py` | Zone/rule join via table_from_pandas | ✅ |
| `src/compliance.py` | 30-min violation detection, UDF classify | ✅ |
| `src/explanation.py` | LLM + template explanation UDF | ✅ |
| `src/cli.py` | Two-tier compliance report formatter | ✅ |
| `src/data_generator.py` | Deterministic seed data (ISO 8601 timestamps) | ✅ |
| `stream/live_append.py` | Append-only live sensor feed | ✅ |
| `demo.py` | Windows-native full pipeline simulation | ✅ |

---

## Configuration

| File | Purpose |
|---|---|
| `config/zone_map.yaml` | station_id → zone mapping |
| `config/pm25_rules.yaml` | Zone limits, duration thresholds, CPCB rule references |
| `.env` | `GEMINI_API_KEY` (optional) |

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| `pw.DateTimeNaive` in schema | Pathway rejects `datetime.datetime` in schema; CamelCase type is correct |
| `timedelta()` for window sizes | `pw.temporal.duration()` doesn't exist; Python stdlib timedelta works |
| `pw.debug.table_from_pandas` | `table_from_markdown` without separator row causes `NaN` key errors |
| `pw.io.subscribe` as sink | `jsonlines.write` wraps output in JSON envelope; subscribe prints raw strings |
| Top-level `@pw.udf` functions | Nested/lambda functions fail Pathway's pickling; named top-level UDFs are safe |
| `google.genai.Client(api_key=)` | Replaces deprecated `google.generativeai`; no module-level `configure()` |

---

## Regulatory Coverage

| Zone | Limit | Duration Threshold | Rule Reference |
|---|---|---|---|
| Residential | 60 µg/m³ | 10 min | CPCB PM2.5 Residential Standard |
| Industrial | 120 µg/m³ | 20 min | CPCB PM2.5 Industrial Zone Standard |

---

## Demo Sequence (via live_append.py)

```
NORMAL → TRANSIENT SPIKE → RECOVERY → SUSTAINED VIOLATION → COOLDOWN
```

Total demo runtime: ~20 minutes for full cycle.
Ctrl-C at any point to stop cleanly.

---

*Generated: 2026-02-21 | GreenPulse v1.0*
