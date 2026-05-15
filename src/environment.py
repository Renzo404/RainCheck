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
    Handles weather-state selection and weather-adjusted parameters.

    Paper-aligned rule:
    One weather state is sampled at the start of each 4-hour replication.
    That weather state remains constant for the whole replication.
    """

    def __init__(self, simulation_month="Aug", replication=1):
        self.simulation_month = simulation_month
        self.replication = replication

        self.weather_data = pd.read_csv(WEATHER_PROBABILITY_CSV)
        self.month_probabilities = self._load_month_probabilities(simulation_month)

        self.current_weather_state = self.sample_weather_state()
        self.current_parameters = self.build_weather_parameters()

    def _load_month_probabilities(self, month):
        if "Month" not in self.weather_data.columns:
            raise ValueError("Weather CSV must contain a Month column.")

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

            if state not in WEATHER_EFFECTS:
                raise ValueError(
                    "Weather state '{}' exists in CSV but not in WEATHER_EFFECTS.".format(
                        state
                    )
                )

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
        states = list(self.month_probabilities.keys())
        weights = list(self.month_probabilities.values())

        return random.choices(
            states,
            weights=weights,
            k=1
        )[0]

    def build_weather_parameters(self):
        effect = WEATHER_EFFECTS[self.current_weather_state]

        prep_min, prep_mode, prep_max = PREP_TIME_TRIANGULAR
        dist_min, dist_mode, dist_max = DISTANCE_KM_TRIANGULAR

        orders_per_hour = (
            BASELINE_ORDERS_PER_HOUR *
            effect["demand_multiplier"]
        )

        speed_kmh = (
            BASELINE_SPEED_KMH *
            effect["speed_multiplier"]
        )

        return {
            "weather_state": self.current_weather_state,
            "weather_label": effect["display_name"],
            "monthly_probability": self.month_probabilities[self.current_weather_state],
            "orders_per_hour": orders_per_hour,
            "speed_kmh": speed_kmh,
            "prep_min": prep_min,
            "prep_mode": prep_mode,
            "prep_max": prep_max,
            "distance_min": dist_min,
            "distance_mode": dist_mode,
            "distance_max": dist_max,
        }

    def get_replication_weather_log(self):
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