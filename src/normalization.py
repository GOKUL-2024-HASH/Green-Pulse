import pathway as pw


def normalize_stream(table: pw.Table) -> pw.Table:
    """
    Validates incoming rows.
    Timestamp is already a datetime column (parsed by pw.io.csv.read via schema).
    No UDF needed — no datetime type annotation issues.

    Filters:
    - pm25 must be in [0, 1000]
    - station_id must be non-empty
    """
    valid = (table.pm25 >= 0.0) & (table.pm25 <= 1000.0) & (table.station_id != "")
    return table.filter(valid)
