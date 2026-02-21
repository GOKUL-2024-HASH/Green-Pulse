# 🌿 GreenPulse: Environmental Compliance Monitor

GreenPulse is a real-time PM2.5 monitoring and compliance system powered by **Pathway**. It transforms raw sensor data into actionable regulatory reports, helping environmental officers identify violations and transient spikes instantly.

---

## 🚀 Key Features

- **Real-Time Analysis**: Processes streaming PM2.5 data with low latency.
- **Zone-Aware Logic**: Applies specific limits and thresholds based on station zones (Residential vs. Industrial).
- **Transient vs. Violation Filtering**: Intelligently distinguishes between short spikes and sustained environmental breaches.
- **Human-Readable Reports**: Generates detailed compliance dossiers including health impact context and LLM-powered explanations.
- **Live Feed Simulation**: Includes a streaming sensor simulator for real-time demoing.

---

## 🛠 Tech Stack

- **Engine**: [Pathway](https://pathway.com/) (High-performance streaming logic)
- **Language**: Python 3.10+
- **AI**: Google Gemini (via `google-genai`)
- **Data Handling**: Pandas, YAML

---

## 💻 OS Compatibility & Installation

### 🔴 Critical Runtime Requirement
**Pathway's binary engine requires Linux, macOS, or WSL2 (Windows Subsystem for Linux).** It will *not* run natively on the standard Windows command prompt.

### 1. Prerequisites
- **Linux/macOS**: Python 3.10 or higher.
- **Windows**: [Install WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) and a Linux distribution (e.g., Ubuntu).

### 2. Setup (Run inside Linux/macOS/WSL)
```bash
# Navigate to the project folder
cd Green-Pulse

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initial data generation
python3 src/data_generator.py
```

### 3. Environment Configuration
Create a `.env` file in the root directory for LLM capabilities (optional):
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## ▶️ Execution Guidelines

### Running the Live Pipeline (Linux / macOS / WSL)
To see the full streaming system in action, you should use two terminal windows:

**Terminal 1: The Core Pipeline**
```bash
source venv/bin/activate
python3 main.py
```

**Terminal 2: The Live Sensor Feed (Simultaneous)**
```bash
source venv/bin/activate
python3 stream/live_append.py
```
*The pipeline will automatically detect new rows appended to the data file and update the CLI live.*

---

### Running on Native Windows (Simulation Mode)
If you are unable to use WSL2, you can run a full pipeline simulation natively on Windows. This script replicates the Pathway logic using standard Python:
```powershell
python demo.py
```

---

## 📊 Output Format

### Normal Status (Compact)
`[08:44:01 UTC] Alandur | Residential | PM2.5: 42.3 µg/m³ | ✅ COMPLIANT`

### Violation Detected (Detailed)
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
...
Status:      🟡 PENDING_OFFICER_REVIEW
────────────────────────────────────────────────
```

---

## 📂 Project Structure
- `main.py`: Main entry point and orchestration.
- `src/`: Core logic modules (stream, normalization, windowing, compliance).
- `stream/live_append.py`: Live data simulator.
- `config/`: Regulatory rules and zone mappings (YAML).
- `demo.py`: Logic-identical simulator for systems without Pathway.

---

## ⚖️ License
This project is built for environmental monitoring demonstrations. Rules and limits are based on curated CPCB standards for illustrative purposes.
