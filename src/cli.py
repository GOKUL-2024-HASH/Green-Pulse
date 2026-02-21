"""
src/cli.py — GreenPulse Two-Tier Compliance Report Formatter
=============================================================
Rule:
  - OK / TRANSIENT  → compact single-line update
  - VIOLATION       → full multi-line regulatory block

Noise control is provided for free by Pathway's incremental model:
  pw.io.jsonlines.write only emits a row when its value changes,
  so the full violation block is only printed when the violation
  metadata itself changes (station, avg, duration, etc.).
"""
import pathway as pw
from datetime import datetime, timezone


@pw.udf
def format_event(
    timestamp: pw.DateTimeNaive,
    station_id: str,
    zone: str,
    avg: float,
    limit: float,
    duration: int,
    min_dur: int,
    status: str,
    severity: str,
    rule_reference: str,
    explanation: str,
    review_status: str,
) -> str:
    """
    Two-tier formatter:
      OK / TRANSIENT  → single compact line
      VIOLATION       → full regulatory block
    """
    # Format the timestamp nicely (UTC)
    try:
        ts_str = timestamp.strftime("%H:%M:%S UTC")
    except Exception:
        ts_str = "??:??:??"

    # ── TIER 1: Compact one-liner for non-violations ──────────────────────
    if status == "OK":
        return (
            f"[{ts_str}] {station_id:10s} | {zone:12s} | "
            f"PM2.5: {avg:6.1f} µg/m³ | ✅ COMPLIANT"
        )

    if status == "TRANSIENT":
        return (
            f"[{ts_str}] {station_id:10s} | {zone:12s} | "
            f"PM2.5: {avg:6.1f} µg/m³ | ⚠️  TRANSIENT  "
            f"({duration} min, threshold {min_dur} min)"
        )

    # ── TIER 2: Full regulatory block for VIOLATION ───────────────────────
    bar = "─" * 48

    return (
        f"\n{bar}\n"
        f"🔴 COMPLIANCE VIOLATION DETECTED\n"
        f"{bar}\n"
        f"Time:        {ts_str}\n"
        f"Station:     {station_id}\n"
        f"Zone:        {zone}\n"
        f"\n"
        f"Observed Data:\n"
        f"  • PM2.5 Average: {avg:.1f} µg/m³\n"
        f"  • Duration:      {duration} minutes\n"
        f"\n"
        f"Applicable Regulation:\n"
        f"  • Rule:          {rule_reference}\n"
        f"  • Limit:         {limit:.0f} µg/m³\n"
        f"  • Max Duration:  {min_dur} minutes\n"
        f"  • Severity:      {severity}\n"
        f"\n"
        f"Interpretation:\n"
        f"  {explanation}\n"
        f"\n"
        f"Status:\n"
        f"  🟡 {review_status}\n"
        f"{bar}"
    )


def configure_cli_output(stream: pw.Table) -> pw.Table:
    """
    Collapses the full compliance stream into a single `log_entry` string column.
    Pathway's incremental engine guarantees that the output connector only writes
    a row when the formatted string itself changes — providing noise control
    without any stateful bookkeeping in user code.
    """
    return stream.select(
        log_entry=format_event(
            pw.this.timestamp,
            pw.this.station_id,
            pw.this.zone,
            pw.this.current_avg_pm25,
            pw.this.limit,
            pw.this.exceed_minutes,
            pw.this.min_duration_req,
            pw.this.status,
            pw.this.severity,
            pw.this.rule_reference,
            pw.this.explanation,
            pw.this.review_status,
        )
    )
