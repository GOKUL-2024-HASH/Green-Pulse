
import os
import yaml
import pathway as pw

def load_zone_map(config_dir: str = "./config") -> pw.Table:
    """
    Loads logical station-to-zone mapping from a YAML file.
    Returns a Pathway Table with columns: [station_id, zone]
    """
    with open(f"{config_dir}/zone_map.yaml", "r") as f:
        data = yaml.safe_load(f)
    
    # Create a static table (no streaming needed for config usually)
    # But for Pathway joins, we treat everything as a Table.
    table = pw.debug.table_from_markdown(
        """
        | station_id | zone |
        |---|---|
        """ + "\n".join([f"| {row['station_id']} | {row['zone']} |" for row in data])
    )
    return table

def load_rules(config_dir: str = "./config") -> pw.Table:
    """
    Loads PM2.5 rules from a YAML file.
    Returns a Pathway Table with columns: [zone, limit, min_duration, severity]
    """
    with open(f"{config_dir}/pm25_rules.yaml", "r") as f:
        data = yaml.safe_load(f)

    # Create a static table with schema inferred or explicit
    # Using table_from_markdown for easy static data creation in this demo context
    markdown_str = """
    | zone | limit | min_duration | severity |
    |---|---|---|---|
    """
    for row in data:
        markdown_str += f"\n| {row['zone']} | {float(row['limit'])} | {int(row['min_duration'])} | {row['severity']} |"
        
    table = pw.debug.table_from_markdown(markdown_str)
    return table
