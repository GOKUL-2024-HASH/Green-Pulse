import pathway as pw
from datetime import timedelta


def compute_window_metrics(table: pw.Table) -> pw.Table:
    """
    Computes 15-minute sliding window statistics grouped by station_id.
    Returns: station_id, window_end, avg_pm25, pm25_range, count
    Uses standard Python timedelta for window sizes — NOT pw.temporal.duration.
    """
    windowed = table.windowby(
        table.timestamp,
        window=pw.temporal.sliding(
            hop=timedelta(minutes=1),
            duration=timedelta(minutes=15),
        ),
        instance=table.station_id,
        behavior=pw.temporal.common_behavior(
            delay=timedelta(seconds=0),
        ),
    )

    metrics = windowed.reduce(
        station_id=pw.this._pw_instance,
        window_end=pw.this._pw_window_end,
        avg_pm25=pw.reducers.avg(pw.this.pm25),
        min_pm25=pw.reducers.min(pw.this.pm25),
        max_pm25=pw.reducers.max(pw.this.pm25),
        count=pw.reducers.count(pw.this.pm25),
    )

    result = metrics.select(
        metrics.station_id,
        metrics.window_end,
        metrics.avg_pm25,
        metrics.count,
        pm25_range=metrics.max_pm25 - metrics.min_pm25,
    )

    return result
