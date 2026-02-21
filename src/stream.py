import pathway as pw


class SensorSchema(pw.Schema):
    """
    Schema for PM2.5 sensor stream.
    Uses pw.DateTimeNaive for timestamp (timezone-unaware).
    Pathway's CSV connector will parse ISO-format strings automatically.
    """
    station_id: str
    timestamp: pw.DateTimeNaive   # Correct Pathway type (CamelCase, not DATE_TIME_NAIVE)
    pm25: float


def get_sensor_stream(data_dir: str = "./data") -> pw.Table:
    """Reads sensor data from CSV in streaming mode."""
    return pw.io.csv.read(
        f"{data_dir}/sensor_stream.csv",
        schema=SensorSchema,
        mode="streaming",
        autocommit_duration_ms=1000,
    )
