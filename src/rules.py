import os
import yaml
import pandas as pd
import pathway as pw


def load_config_tables(config_dir: str = "./config") -> pw.Table:
    """
    Loads zone_map.yaml + pm25_rules.yaml and returns a joined
    static Pathway table:
      [station_id, zone, limit, min_duration, severity, rule_reference, health_context]
    Uses pw.debug.table_from_pandas — avoids markdown parsing NaN issues.
    """
    with open(os.path.join(config_dir, "zone_map.yaml")) as f:
        zones = yaml.safe_load(f) or []

    with open(os.path.join(config_dir, "pm25_rules.yaml")) as f:
        rules = yaml.safe_load(f) or []

    # Build lookup dict: zone -> rule
    rule_map = {r["zone"]: r for r in rules}

    records = []
    for z in zones:
        sid  = z["station_id"]
        zone = z["zone"]
        rule = rule_map.get(zone, {
            "limit": 999,
            "min_duration": 99,
            "severity": "Unknown",
            "rule_reference": "No rule defined",
            "health_context": "No health context available.",
        })
        records.append({
            "station_id":    sid,
            "zone":          zone,
            "limit":         float(rule["limit"]),
            "min_duration":  int(rule["min_duration"]),
            "severity":      str(rule["severity"]),
            # NEW enrichment fields
            "rule_reference": str(rule.get("rule_reference", "N/A")),
            "health_context": str(rule.get("health_context", "N/A")),
        })

    df = pd.DataFrame(records)

    table = pw.debug.table_from_pandas(
        df,
        schema=pw.schema_from_dict({
            "station_id":    str,
            "zone":          str,
            "limit":         float,
            "min_duration":  int,
            "severity":      str,
            "rule_reference": str,
            "health_context": str,
        }),
    )
    return table


def apply_rules(windowed: pw.Table, rules: pw.Table) -> pw.Table:
    """
    Joins windowed stream with static rule table on station_id.
    Adds: zone, limit, min_duration, severity, is_exceeding,
          rule_reference, health_context (NEW).
    """
    enriched = windowed.join(
        rules,
        pw.left.station_id == pw.right.station_id,
    ).select(
        pw.left.station_id,
        pw.left.window_end,
        pw.left.avg_pm25,
        pw.left.pm25_range,
        pw.right.zone,
        pw.right.limit,
        pw.right.min_duration,
        pw.right.severity,
        # NEW enrichment fields passed downstream
        pw.right.rule_reference,
        pw.right.health_context,
        is_exceeding=pw.left.avg_pm25 > pw.right.limit,
    )
    return enriched
