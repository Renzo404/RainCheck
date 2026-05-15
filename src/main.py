import random
from dataclasses import asdict

import pandas as pd
import simpy

from entities import OrderResult, SimulationConfig
from environment import DeliveryEnvironment
from metrics import (
    print_and_save_arena_report,
    summarize_replication,
    summarize_weather,
)
from parameters import (
    BASELINE_ACTIVE_RIDERS,
    OUTPUT_DIR,
    RANDOM_SEED,
    REPLICATION_LENGTH_MINUTES,
    REPLICATIONS,
    REPOSITION_TIME_TRIANGULAR,
    SIMULATION_MONTH,
    TARGET_LATENCY_MINUTES,
)


class RainCheckSimulation:
    """
    Main discrete-event simulation model.

    Arena equivalents:
    Create  -> stochastic customer order arrivals
    Assign  -> weather state and order start time
    Process -> restaurant preparation and rider delivery
    Record  -> total delivery latency
    Decide  -> SLA compliance
    Dispose -> completed order result
    """

    def __init__(self, config, replication):
        self.config = config
        self.replication = replication

        random.seed(config.random_seed + replication)

        self.env = simpy.Environment()

        self.delivery_environment = DeliveryEnvironment(
            simulation_month=config.simulation_month,
            replication=replication
        )

        self.delivery_rider = simpy.Resource(
            self.env,
            capacity=BASELINE_ACTIVE_RIDERS
        )

        self.generated_orders = 0
        self.results = []

    def order_generator(self):
        params = self.delivery_environment.current_parameters

        mean_interarrival_minutes = (
            60.0 / params["orders_per_hour"]
        )

        while self.env.now < self.config.replication_length_minutes:
            interarrival = random.expovariate(
                1.0 / mean_interarrival_minutes
            )

            yield self.env.timeout(interarrival)

            if self.env.now > self.config.replication_length_minutes:
                break

            self.generated_orders += 1

            self.env.process(
                self.order_process(self.generated_orders)
            )

    def order_process(self, order_id):
        arrival_time = self.env.now
        params = self.delivery_environment.current_parameters

        prep_time = random.triangular(
            params["prep_min"],
            params["prep_max"],
            params["prep_mode"]
        )

        yield self.env.timeout(prep_time)

        rider_queue_start = self.env.now

        with self.delivery_rider.request() as rider_request:
            yield rider_request

            rider_queue_time = (
                self.env.now - rider_queue_start
            )

            distance_km = random.triangular(
                params["distance_min"],
                params["distance_max"],
                params["distance_mode"]
            )

            travel_time = (
                distance_km / params["speed_kmh"]
            ) * 60.0

            reposition_min, reposition_mode, reposition_max = (
                REPOSITION_TIME_TRIANGULAR
            )

            reposition_time = random.triangular(
                reposition_min,
                reposition_max,
                reposition_mode
            )

            yield self.env.timeout(
                travel_time + reposition_time
            )

        total_latency = (
            self.env.now - arrival_time
        )

        met_sla = (
            total_latency <=
            self.config.target_latency_minutes
        )

        self.results.append(
            OrderResult(
                replication=self.replication,
                order_id=order_id,
                weather_state=params["weather_state"],
                weather_label=params["weather_label"],
                arrival_time=round(arrival_time, 4),
                prep_time=round(prep_time, 4),
                rider_queue_time=round(rider_queue_time, 4),
                travel_time=round(travel_time, 4),
                reposition_time=round(reposition_time, 4),
                total_latency=round(total_latency, 4),
                met_sla=met_sla
            )
        )

    def run(self):
        self.env.process(self.order_generator())

        self.env.run(
            until=self.config.replication_length_minutes
        )

        return (
            self.results,
            self.delivery_environment.get_replication_weather_log()
        )


def run_all_replications(config):
    raw_order_rows = []
    weather_log_rows = []
    replication_summary_rows = []

    for replication in range(1, config.replications + 1):
        model = RainCheckSimulation(
            config=config,
            replication=replication
        )

        order_results, weather_log = model.run()

        raw_order_rows.extend(
            asdict(order)
            for order in order_results
        )

        weather_log_rows.append(weather_log)

        replication_summary_rows.append(
            summarize_replication(
                config=config,
                replication=replication,
                weather_log=weather_log,
                order_results=order_results
            )
        )

    raw_orders_df = pd.DataFrame(raw_order_rows)
    weather_log_df = pd.DataFrame(weather_log_rows)
    replication_summary_df = pd.DataFrame(replication_summary_rows)
    weather_summary_df = summarize_weather(raw_orders_df)

    return (
        raw_orders_df,
        weather_log_df,
        replication_summary_df,
        weather_summary_df
    )


def main():
    config = SimulationConfig(
        simulation_month=SIMULATION_MONTH,
        replication_length_minutes=REPLICATION_LENGTH_MINUTES,
        replications=REPLICATIONS,
        target_latency_minutes=TARGET_LATENCY_MINUTES,
        random_seed=RANDOM_SEED
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    (
        raw_orders_df,
        weather_log_df,
        replication_summary_df,
        weather_summary_df
    ) = run_all_replications(config)

    raw_orders_path = OUTPUT_DIR / "raincheck_raw_orders.csv"
    weather_log_path = OUTPUT_DIR / "raincheck_replication_weather_log.csv"
    replication_summary_path = OUTPUT_DIR / "raincheck_replication_summary.csv"
    weather_summary_path = OUTPUT_DIR / "raincheck_weather_summary.csv"

    raw_orders_df.to_csv(raw_orders_path, index=False)
    weather_log_df.to_csv(weather_log_path, index=False)
    replication_summary_df.to_csv(
        replication_summary_path,
        index=False
    )
    weather_summary_df.to_csv(
        weather_summary_path,
        index=False
    )

    report_path = print_and_save_arena_report(
        config=config,
        replication_summary_df=replication_summary_df,
        weather_summary_df=weather_summary_df,
        output_dir=OUTPUT_DIR
    )

    print("\nSaved output files:")
    print("- " + str(raw_orders_path))
    print("- " + str(weather_log_path))
    print("- " + str(replication_summary_path))
    print("- " + str(weather_summary_path))
    print("- " + str(report_path))


if __name__ == "__main__":
    main()