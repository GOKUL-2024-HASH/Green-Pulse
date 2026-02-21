# GreenPulse — Run Guide
> Real-Time PM2.5 Compliance Monitoring System

---

## ⚠️ Platform Requirement

Pathway requires **Linux / macOS / WSL2**.  
It does **not** run on native Windows.

---

## Option A — Full Live Pipeline (WSL2 / Ubuntu)

### First-Time Setup (once only)
```bash
# Open Ubuntu/WSL terminal
cd "/mnt/c/Users/keert/OneDrive/Desktop/project/Green Bharath"

# Create virtual environment
python3 -m venv ~/venv
source ~/venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate seed data
python3 src/data_generator.py
```

### Run the Pipeline
```bash
source ~/venv/bin/activate
cd "/mnt/c/Users/keert/OneDrive/Desktop/project/Green Bharath"
python3 main.py
```

### Run the Live Sensor Feed (second terminal — simultaneously)
```bash
source ~/venv/bin/activate
cd "/mnt/c/Users/keert/OneDrive/Desktop/project/Green Bharath"
python3 stream/live_append.py
```

Live sensor rows will be appended every **5 seconds**.  
The pipeline detects them automatically — no restart needed.

---

## Option B — Windows Demo (no Pathway needed)

```bash
python demo.py
```

Simulates the full pipeline in plain Python.  
Produces identical output format. Safe for Windows demo.

---

## Expected CLI Output

### Normal / Transient (compact single line):
```
[08:44:01 UTC] Alandur    | Residential  | PM2.5:   42.3 µg/m³ | ✅ COMPLIANT
[08:45:12 UTC] Manali     | Industrial   | PM2.5:  103.6 µg/m³ | ⚠️  TRANSIENT  (8 min, threshold 20 min)
```

### Sustained Violation (full regulatory block):
```
────────────────────────────────────────────────
🔴 COMPLIANCE VIOLATION DETECTED
────────────────────────────────────────────────
Time:        08:52:14 UTC
Station:     Alandur
Zone:        Residential

Observed Data:
  • PM2.5 Average: 94.5 µg/m³
  • Duration:      12 minutes

Applicable Regulation:
  • Rule:          CPCB PM2.5 Residential Standard - 24hr avg 60 µg/m³
  • Limit:         60 µg/m³
  • Max Duration:  10 minutes
  • Severity:      High

Interpretation:
  Station Alandur (Residential) has exceeded the CPCB PM2.5 Residential
  Standard limit. Observed: 94.5 µg/m³ | Limit: 60 µg/m³ | Duration: 12 min.
  Sustained PM2.5 above 60 µg/m³ increases respiratory illness risk in
  sensitive groups. Immediate officer review is required.

Status:
  🟡 PENDING_OFFICER_REVIEW
────────────────────────────────────────────────
```

---

## Demo Scenario Sequence (live_append.py)

| Phase | Duration | Alandur PM2.5 | Expected Status |
|---|---|---|---|
| NORMAL | 2 min | ~38 µg/m³ | COMPLIANT ✅ |
| TRANSIENT_SPIKE | 90 sec | ~80 µg/m³ | TRANSIENT ⚠️ |
| RECOVERY | 1 min | ~42 µg/m³ | COMPLIANT ✅ |
| SUSTAINED_VIOLATION | 12.5 min | ~92 µg/m³ | VIOLATION 🔴 |
| COOLDOWN | 2 min | ~35 µg/m³ | COMPLIANT ✅ |

---

## Stop the Pipeline
```
Ctrl-C
```

---

## Environment Variables (optional — for LLM explanations)
Create or edit `.env` in the project root:
```
GEMINI_API_KEY=your_key_here
```
If absent, the system falls back to deterministic template explanations.
