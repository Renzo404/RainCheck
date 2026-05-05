import simpy
import pandas as pd
import numpy as np
# import parameters as p

class DeliveryEnvironment:
    """
    The core SimPy environment that handles system-wide states, 
    such as the stochastic shifting of weather based on the Meteoblue CSV.
    """
    def __init__(self, env, simulation_month="Aug"):
        self.env = env
        self.simulation_month = simulation_month
        
        # System States
        self.current_weather_state = "Dry"  # Default starting state
        
        # Load the empirical data from the CSV
        # (Assumes script is run from the root directory of the repository)
        self.weather_data = pd.read_csv('data/raw/meteoblue_pagasa_probabilities.csv')
        
        # Extract the specific probability weights for the chosen month
        self.month_probabilities = self._load_month_probs(self.simulation_month)
        
        # Start the continuous SimPy weather process
        self.env.process(self.weather_controller())

    def _load_month_probs(self, month):
        """Filters the DataFrame to extract the probabilities for the given month."""
        df_indexed = self.weather_data.set_index('Month')
        if month in df_indexed.index:
            # Returns a dictionary: {'Dry': 0.0, 'Light Rains': 0.3226, ...}
            return df_indexed.loc[month].to_dict()
        else:
            raise ValueError(f"Month '{month}' not found in the empirical CSV.")

    def weather_controller(self):
        while True:
            states = ["Dry", "Light Rains", "Moderate Rains", "Heavy Rains"]
            weights = [
                self.month_probabilities["Dry"],
                self.month_probabilities["Light Rains"],
                self.month_probabilities["Moderate Rains"],
                self.month_probabilities["Heavy Rains"]
            ]
            
            # Normalize the weights to sum to exactly 1.0
            weights = np.array(weights)
            weights /= weights.sum()
            
            self.current_weather_state = np.random.choice(states, p=weights)
            yield self.env.timeout(1)
            
    # Add other system-wide queues here later (e.g., simpy.Resource for the Riders)