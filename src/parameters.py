from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
OUTPUT_DIR = ROOT_DIR / "data" / "outputs"

WEATHER_PROBABILITY_CSV = RAW_DATA_DIR / "meteoblue_pagasa_probabilities.csv"

RAW_ORDERS_OUTPUT = OUTPUT_DIR / "raincheck_raw_orders.csv"
WEATHER_LOG_OUTPUT = OUTPUT_DIR / "raincheck_replication_weather_log.csv"
REPLICATION_SUMMARY_OUTPUT = OUTPUT_DIR / "raincheck_replication_summary.csv"
WEATHER_SUMMARY_OUTPUT = OUTPUT_DIR / "raincheck_weather_summary.csv"
ARENA_REPORT_OUTPUT = OUTPUT_DIR / "arena_style_report.txt"
VALIDATION_REPORT_OUTPUT = OUTPUT_DIR / "validation_report.txt"

SIMULATION_MONTH = "Aug"
REPLICATION_LENGTH_MINUTES = 240.0
REPLICATIONS = 30
RANDOM_SEED = 10000

TARGET_LATENCY_MINUTES = 45.0

BASELINE_ORDERS_PER_HOUR = 50.0
BASELINE_ACTIVE_RIDERS = 30
BASELINE_SPEED_KMH = 16.0

PREP_TIME_TRIANGULAR = (8.0, 12.0, 20.0)
DISTANCE_KM_TRIANGULAR = (1.0, 2.0, 4.0)
REPOSITION_TIME_TRIANGULAR = (2.0, 5.0, 10.0)

WEATHER_EFFECTS = {
    "Dry": {
        "display_name": "Dry Conditions",
        "demand_multiplier": 1.0000,
        "speed_multiplier": 1.00,
    },
    "Light Rains": {
        "display_name": "Light Rains",
        "demand_multiplier": 1.1767,
        "speed_multiplier": 0.90,
    },
    "Moderate Rains": {
        "display_name": "Moderate Rains",
        "demand_multiplier": 1.3933,
        "speed_multiplier": 0.85,
    },
    "Heavy Rains": {
        "display_name": "Heavy Rains",
        "demand_multiplier": 1.4467,
        "speed_multiplier": 0.80,
    },
}