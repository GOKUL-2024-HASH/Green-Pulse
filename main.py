"""
GreenPulse — main.py
Entry point for the real-time PM2.5 compliance monitoring pipeline.
Requires Linux / macOS / WSL2 with the genuine Pathway package installed.
"""
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(__file__))

# ── Pathway availability check ─────────────────────────────────────────────
try:
    import pathway as pw
    _has_pathway = hasattr(pw, "io") and hasattr(pw, "run")
except ImportError:
    _has_pathway = False

if not _has_pathway:
    print(
        "\n⚠  GreenPulse requires the genuine Pathway package (Linux / WSL2).\n"
        "   On Windows, run inside WSL2:\n"
        "     wsl -d Ubuntu\n"
        "     cd '/mnt/c/Users/keert/OneDrive/Desktop/project/Green Bharath'\n"
        "     pip install -r requirements.txt\n"
        "     python3 src/data_generator.py\n"
        "     python3 main.py\n"
        "\n   For a Windows demo, run:  python demo.py\n"
    )
    sys.exit(0)

# ── Import pipeline modules ────────────────────────────────────────────────
from src.stream        import get_sensor_stream
from src.normalization import normalize_stream
from src.windowing     import compute_window_metrics
from src.rules         import load_config_tables, apply_rules
from src.compliance    import detect_violations
from src.explanation   import add_explanations
from src.cli           import configure_cli_output


# ── Output sink callback ───────────────────────────────────────────────────
def _print_report(key, row: dict, time: int, is_addition: bool) -> None:
    """
    Called by Pathway's subscribe connector on every row change.
    Only prints additions (is_addition=True) — deletions are Pathway's
    internal retraction events and must be suppressed to avoid duplicates.
    Prints the raw log_entry string produced by configure_cli_output.
    """
    if is_addition:
        print(row.get("log_entry", ""), flush=True)


def main() -> None:
    print("GreenPulse: Initializing pipeline…")

    data_csv = "./data/sensor_stream.csv"
    if not os.path.exists(data_csv):
        print(f"✗  Data file not found: {data_csv}")
        print("   Run:  python3 src/data_generator.py")
        sys.exit(1)

    # ── Build computation graph ────────────────────────────────────────────
    stream     = get_sensor_stream("./data")
    normed     = normalize_stream(stream)
    windowed   = compute_window_metrics(normed)
    rules      = load_config_tables("./config")
    enriched   = apply_rules(windowed, rules)
    compliance = detect_violations(enriched)
    explained  = add_explanations(compliance)
    formatted  = configure_cli_output(explained)

    # ── Attach SOLE output sink ────────────────────────────────────────────
    # pw.io.subscribe is the only active sink.
    # It calls _print_report for every row change, printing the raw
    # formatted log_entry string — not JSON or CSV.
    # No other print(), .print(), logging, or jsonlines.write exists.
    pw.io.subscribe(
        table=formatted,
        on_change=_print_report,
    )

    # ── Execute graph ──────────────────────────────────────────────────────
    print(
        "\n=== GREENPULSE LIVE MONITOR ===\n"
        "Press Ctrl-C to stop.\n"
        "══════════════════════════════\n"
    )
    pw.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGreenPulse: Stopped by user.")
