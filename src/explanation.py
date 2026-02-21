import os
import pathway as pw

# --- Environment setup ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

try:
    import google.genai as genai
    _genai_available = bool(GEMINI_KEY)  # Only usable if key exists
except Exception:
    genai = None
    _genai_available = False


# ─── Deterministic template fallback ─────────────────────────────────────────

def _template_explanation(
    station_id: str,
    zone: str,
    avg: float,
    limit: float,
    duration: int,
    status: str,
    rule_reference: str,
    health_context: str,
) -> str:
    """Build a structured, human-readable explanation from template. Never hallucinate."""
    if status == "OK":
        return (
            f"Station {station_id} ({zone}) is operating within regulatory limits. "
            f"Current PM2.5: {avg:.1f} µg/m³ (Limit: {limit:.0f} µg/m³). No action required."
        )
    if status == "TRANSIENT":
        return (
            f"Station {station_id} ({zone}) recorded a short-duration PM2.5 spike "
            f"of {avg:.1f} µg/m³ (Limit: {limit:.0f} µg/m³) for {duration} minute(s). "
            f"Duration is below the {rule_reference} enforcement threshold. "
            f"Monitoring continues."
        )
    # VIOLATION
    return (
        f"Station {station_id} ({zone}) has exceeded the {rule_reference} limit. "
        f"Observed: {avg:.1f} µg/m³  |  Limit: {limit:.0f} µg/m³  |  "
        f"Duration: {duration} min. "
        f"{health_context} "
        f"Immediate officer review is required."
    )


# ─── UDFs ────────────────────────────────────────────────────────────────────

@pw.udf
def build_explanation(
    station_id: str,
    zone: str,
    avg: float,
    limit: float,
    duration: int,
    status: str,
    pm25_range: float,
    severity: str,
    rule_reference: str,      # NEW
    health_context: str,      # NEW
) -> str:
    """Generate structured explanation text. Falls back gracefully if LLM unavailable."""
    fallback = _template_explanation(
        station_id, zone, avg, limit, duration, status, rule_reference, health_context
    )

    if not _genai_available or genai is None:
        return fallback

    prompt = (
        f"Environmental compliance event — write one professional log entry sentence only.\n"
        f"Station: {station_id} ({zone})\n"
        f"PM2.5: {avg:.1f} µg/m³  Limit: {limit:.0f} µg/m³\n"
        f"Duration above limit: {duration} min\n"
        f"Status: {status} | Severity: {severity}\n"
        f"Rule: {rule_reference}\n"
        f"Health context: {health_context}\n"
        f"No markdown. No bullet points. One sentence only."
    )
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = (resp.text or "").strip()
        return text[:300] if text else fallback
    except Exception as exc:
        return fallback + f" [LLM unavailable: {exc}]"


@pw.udf
def set_review_status(_: str) -> str:
    """Always returns PENDING_OFFICER_REVIEW. Named UDF — no lambda serialisation issues."""
    return "PENDING_OFFICER_REVIEW"


def add_explanations(stream: pw.Table) -> pw.Table:
    return stream.select(
        *pw.this.without(),
        explanation=build_explanation(
            pw.this.station_id,
            pw.this.zone,
            pw.this.current_avg_pm25,
            pw.this.limit,
            pw.this.exceed_minutes,
            pw.this.status,
            pw.this.pm25_range,
            pw.this.severity,
            pw.this.rule_reference,     # NEW
            pw.this.health_context,     # NEW
        ),
        review_status=set_review_status(pw.this.status),
    )
