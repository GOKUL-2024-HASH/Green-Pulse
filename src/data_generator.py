
import csv
import random
from datetime import datetime, timedelta

# Constants
STATIONS = ["Alandur", "Manali", "Velachery"]
# Fixed SEED ensures every demo run is identical (Requirement: Deterministic demo behavior)
RANDOM_SEED = 42  
START_TIME = datetime.now()
DURATION_MINUTES = 60  
INTERVAL_SECONDS = 60  

def generate_data():
    """Generates deterministic PM2.5 data for the demo."""
    
    # Set the seed for reproducibility
    random.seed(RANDOM_SEED)
    
    data = []
    
    # Base values for stations
    base_pm25 = {
        "Alandur": 45.0,   # Residential (Limit 60) - Usually OK
        "Manali": 110.0,   # Industrial (Limit 120) - Borderline
        "Velachery": 50.0  # Residential (Limit 60) - Usually OK
    }

    current_time = START_TIME

    for i in range(DURATION_MINUTES):
        timestamp_str = current_time.strftime("%Y-%m-%dT%H:%M:%S")

        for station in STATIONS:
            val = base_pm25[station]
            
            # Add some random noise
            noise = random.uniform(-5, 5)
            val += noise

            # Scenario 1: Transient Spike in Velachery (Minutes 10-15)
            if station == "Velachery" and 10 <= i <= 15:
                val += 40.0 # Spikes to ~90 (Violation is >60) - Duration 5 mins (Transient)

            # Scenario 2: Sustained Violation in Alandur (Minutes 30-50)
            if station == "Alandur" and 30 <= i <= 50:
                val += 50.0 # Spikes to ~95 (Violation is >60) - Duration 20 mins (sustained > 15m)

            # Scenario 3: Manali stays high but under limit mostly, maybe slight breach
            if station == "Manali" and 40 <= i <= 45:
                val += 20.0 # Spikes to ~130 (Violation is >120) - Duration 5 mins (Transient)

            data.append({
                "station_id": station,
                "timestamp": timestamp_str,
                "pm25": round(val, 2)
            })

        current_time += timedelta(seconds=INTERVAL_SECONDS)

    return data

def write_csv(filename, data):
    try:
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=["station_id", "timestamp", "pm25"])
            writer.writeheader()
            writer.writerows(data)
        print(f"Generated {len(data)} records to {filename}")
    except IOError as e:
        print(f"Error writing to {filename}: {e}")

if __name__ == "__main__":
    data = generate_data()
    write_csv("data/sensor_stream.csv", data)
