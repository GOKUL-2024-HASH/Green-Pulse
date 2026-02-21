import pathway as pw
from datetime import timedelta


@pw.udf
def classify_status(avg: float, limit: float, exceeded_mins: int, req_mins: int) -> str:
    """Classify row as VIOLATION / TRANSIENT / OK. Never returns None."""
    if avg is None or limit is None:
        return "OK"
    if avg > limit:
        return "VIOLATION" if exceeded_mins >= req_mins else "TRANSIENT"
    return "OK"


def detect_violations(enriched: pw.Table) -> pw.Table:
    """
    Secondary 30-minute sliding window counts duration of exceedance per station.
    Classifies each row as OK / TRANSIENT / VIOLATION.
    Uses standard Python timedelta — NOT pw.temporal.duration.
    """
    eval_win = enriched.windowby(
        enriched.window_end,
        window=pw.temporal.sliding(
            hop=timedelta(minutes=1),
            duration=timedelta(minutes=30),
        ),
        instance=enriched.station_id,
        behavior=pw.temporal.common_behavior(
            delay=timedelta(seconds=0),
        ),
    )

    stats = eval_win.reduce(
        station_id=pw.this._pw_instance,
        timestamp=pw.this._pw_window_end,
        exceed_minutes=pw.reducers.sum(pw.cast(int, pw.this.is_exceeding)),
        current_avg_pm25=pw.reducers.max(pw.this.avg_pm25),
        limit=pw.reducers.max(pw.this.limit),
        min_duration_req=pw.reducers.max(pw.this.min_duration),
        severity=pw.reducers.max(pw.this.severity),
        zone=pw.reducers.max(pw.this.zone),
        pm25_range=pw.reducers.max(pw.this.pm25_range),
        # NEW enrichment fields — use max() as safe aggregation for static strings
        rule_reference=pw.reducers.max(pw.this.rule_reference),
        health_context=pw.reducers.max(pw.this.health_context),
    )

    result = stats.select(
        stats.station_id,
        stats.timestamp,
        stats.current_avg_pm25,
        stats.limit,
        stats.exceed_minutes,
        stats.min_duration_req,
        stats.severity,
        stats.zone,
        stats.pm25_range,
        # NEW enrichment fields
        stats.rule_reference,
        stats.health_context,
        status=classify_status(
            stats.current_avg_pm25,
            stats.limit,
            stats.exceed_minutes,
            stats.min_duration_req,
        ),
    )

    return result
