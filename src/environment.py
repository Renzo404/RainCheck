import random

import pandas as pd

from parameters import (
    BASELINE_ORDERS_PER_HOUR,
    BASELINE_SPEED_KMH,
    DISTANCE_KM_TRIANGULAR,
    PREP_TIME_TRIANGULAR,
    WEATHER_EFFECTS,
    WEATHER_PROBABILITY_CSV,
)


class DeliveryEnvironment:
    """
    Handles weather loading, validation, sampling, and weather-adjusted parameters.

    Paper-aligned rule:
    One weather state is sampled at the start of each 4-hour replication.
    That weather state remains fixed for the whole replication.
    """

    def __init__(self, simulation_month="Aug", replication=1):
        self.simulation_month = simulation_month
        self.replication = replication

        self.weather_data = self.load_weather_data()
        self.month_probabilities = self.load_month_probabilities(simulation_month)

        self.current_weather_state = self.sample_weather_state()
        self.current_parameters = self.build_weather_parameters()

    def load_weather_data(self):
        """Loads and validates the weather probability CSV file."""
        if not WEATHER_PROBABILITY_CSV.exists():
            raise FileNotFoundError(
                "Weather probability CSV not found: {}".format(
                    WEATHER_PROBABILITY_CSV
                )
            )

        weather_data = pd.read_csv(WEATHER_PROBABILITY_CSV)

        if "Month" not in weather_data.columns:
            raise ValueError("Weather CSV must contain a 'Month' column.")

        csv_weather_states = set(weather_data.columns) - {"Month"}
        expected_weather_states = set(WEATHER_EFFECTS.keys())

        missing_states = expected_weather_states - csv_weather_states
        extra_states = csv_weather_states - expected_weather_states

        if missing_states:
            raise ValueError(
                "Weather CSV is missing required states: {}".format(
                    sorted(missing_states)
                )
            )

        if extra_states:
            raise ValueError(
                "Weather CSV contains states not defined in WEATHER_EFFECTS: {}".format(
                    sorted(extra_states)
                )
            )

        return weather_data

    def load_month_probabilities(self, month):
        """Extracts and normalizes weather probabilities for the selected month."""
        df_indexed = self.weather_data.set_index("Month")

        if month not in df_indexed.index:
            available_months = ", ".join(df_indexed.index.astype(str))
            raise ValueError(
                "Month '{}' not found. Available months: {}".format(
                    month,
                    available_months
                )
            )

        probabilities = df_indexed.loc[month].to_dict()

        cleaned = {}
        for state, value in probabilities.items():
            probability = float(value)

            if probability < 0:
                raise ValueError(
                    "Weather probability for '{}' cannot be negative.".format(
                        state
                    )
                )

            cleaned[state] = probability

        total = sum(cleaned.values())

        if total <= 0:
            raise ValueError(
                "Weather probabilities for '{}' must sum to more than 0.".format(
                    month
                )
            )

        return {
            state: probability / total
            for state, probability in cleaned.items()
        }

    def sample_weather_state(self):
        """Arena Assign equivalent: samples one weather state for the replication."""
        states = list(self.month_probabilities.keys())
        weights = list(self.month_probabilities.values())

        return random.choices(
            states,
            weights=weights,
            k=1
        )[0]

    def build_weather_parameters(self):
        """Builds weather-adjusted demand and speed parameters."""
        effect = WEATHER_EFFECTS[self.current_weather_state]

        prep_min, prep_mode, prep_max = PREP_TIME_TRIANGULAR
        dist_min, dist_mode, dist_max = DISTANCE_KM_TRIANGULAR

        return {
            "weather_state": self.current_weather_state,
            "weather_label": effect["display_name"],
            "monthly_probability": self.month_probabilities[self.current_weather_state],
            "orders_per_hour": BASELINE_ORDERS_PER_HOUR * effect["demand_multiplier"],
            "speed_kmh": BASELINE_SPEED_KMH * effect["speed_multiplier"],
            "prep_min": prep_min,
            "prep_mode": prep_mode,
            "prep_max": prep_max,
            "distance_min": dist_min,
            "distance_mode": dist_mode,
            "distance_max": dist_max,
        }

    def get_replication_weather_log(self):
        """Returns one weather log row for the completed replication."""
        return {
            "replication": self.replication,
            "weather_state": self.current_weather_state,
            "weather_label": self.current_parameters["weather_label"],
            "monthly_probability": round(
                self.current_parameters["monthly_probability"],
                6
            ),
            "orders_per_hour": round(
                self.current_parameters["orders_per_hour"],
                4
            ),
            "speed_kmh": round(
                self.current_parameters["speed_kmh"],
                4
            ),
        }