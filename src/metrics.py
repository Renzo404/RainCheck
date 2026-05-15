import statistics

import pandas as pd

from parameters import (
    ARENA_REPORT_OUTPUT,
    BASELINE_ACTIVE_RIDERS,
    BASELINE_ORDERS_PER_HOUR,
    BASELINE_SPEED_KMH,
    RANDOM_SEED,
    TARGET_LATENCY_MINUTES,
    VALIDATION_REPORT_OUTPUT,
)


def summarize_replication(config, replication, weather_log, order_results):
    """Creates one KPI row per replication."""
    if not order_results:
        return {
            "replication": replication,
            "weather_state": weather_log["weather_state"],
            "weather_label": weather_log["weather_label"],
            "monthly_probability": weather_log["monthly_probability"],
            "orders_per_hour": weather_log["orders_per_hour"],
            "speed_kmh": weather_log["speed_kmh"],
            "completed_orders": 0,
            "avg_total_latency": 0.0,
            "p95_total_latency": 0.0,
            "max_total_latency": 0.0,
            "avg_rider_queue_time": 0.0,
            "max_rider_queue_time": 0.0,
            "sla_violations": 0,
            "sla_violation_rate": 0.0,
            "degraded": False,
        }

    latencies = [order.total_latency for order in order_results]
    rider_queues = [order.rider_queue_time for order in order_results]
    sla_violations = sum(
        1 for order in order_results
        if not order.met_sla
    )

    avg_latency = statistics.mean(latencies)

    return {
        "replication": replication,
        "weather_state": weather_log["weather_state"],
        "weather_label": weather_log["weather_label"],
        "monthly_probability": weather_log["monthly_probability"],
        "orders_per_hour": weather_log["orders_per_hour"],
        "speed_kmh": weather_log["speed_kmh"],
        "completed_orders": len(order_results),
        "avg_total_latency": round(avg_latency, 4),
        "p95_total_latency": round(pd.Series(latencies).quantile(0.95), 4),
        "max_total_latency": round(max(latencies), 4),
        "avg_rider_queue_time": round(statistics.mean(rider_queues), 4),
        "max_rider_queue_time": round(max(rider_queues), 4),
        "sla_violations": sla_violations,
        "sla_violation_rate": round(sla_violations / len(order_results), 4),
        "degraded": avg_latency > config.target_latency_minutes,
    }


def summarize_weather(raw_orders_df):
    """Aggregates order-level results by weather condition."""
    if raw_orders_df.empty:
        return pd.DataFrame()

    weather_summary = (
        raw_orders_df
        .groupby(["weather_state", "weather_label"])
        .agg(
            completed_orders=("order_id", "count"),
            mean_total_latency=("total_latency", "mean"),
            p95_total_latency=("total_latency", lambda x: x.quantile(0.95)),
            max_total_latency=("total_latency", "max"),
            mean_rider_queue_time=("rider_queue_time", "mean"),
            sla_violation_rate=("met_sla", lambda x: 1 - x.mean()),
        )
        .reset_index()
    )

    numeric_columns = weather_summary.select_dtypes(include="number").columns
    weather_summary[numeric_columns] = weather_summary[numeric_columns].round(4)

    weather_order = {
        "Dry": 0,
        "Light Rains": 1,
        "Moderate Rains": 2,
        "Heavy Rains": 3,
    }

    weather_summary["weather_order"] = (
        weather_summary["weather_state"].map(weather_order)
    )

    weather_summary = (
        weather_summary
        .sort_values("weather_order")
        .drop(columns=["weather_order"])
    )

    return weather_summary


def build_weather_distribution_check(weather_log_df):
    """Compares expected monthly weather probabilities against observed replications."""
    rows = []

    total_replications = len(weather_log_df)

    if total_replications == 0:
        return rows

    grouped = (
        weather_log_df
        .groupby(["weather_state", "weather_label", "monthly_probability"])
        .size()
        .reset_index(name="observed_count")
    )

    for _, row in grouped.iterrows():
        observed_percent = row["observed_count"] / total_replications
        expected_count = row["monthly_probability"] * total_replications

        rows.append({
            "weather_state": row["weather_state"],
            "weather_label": row["weather_label"],
            "expected_probability": row["monthly_probability"],
            "expected_count": expected_count,
            "observed_count": int(row["observed_count"]),
            "observed_probability": observed_percent,
        })

    return rows


def build_arena_style_report(
    config,
    replication_summary_df,
    weather_summary_df,
    weather_distribution_rows
):
    """Builds a human-readable Arena-style output report."""
    lines = []

    lines.append("=" * 78)
    lines.append("ARENA-STYLE SIMULATION OUTPUT REPORT")
    lines.append("=" * 78)
    lines.append("")
    lines.append("MODEL NAME: RainCheck Baguio Food Delivery Logistics DES")
    lines.append("SIMULATION MONTH: " + str(config.simulation_month))
    lines.append(
        "REPLICATION LENGTH: " +
        str(config.replication_length_minutes) +
        " minutes"
    )
    lines.append("NUMBER OF REPLICATIONS: " + str(config.replications))
    lines.append("BASE TIME UNITS: Minutes")
    lines.append("SLA THRESHOLD: " + str(config.target_latency_minutes) + " minutes")
    lines.append(
        "WEATHER ASSUMPTION: One sampled weather state is fixed per replication."
    )

    lines.append("")
    lines.append("-" * 78)
    lines.append("REPRODUCIBILITY AND BASELINE METADATA")
    lines.append("-" * 78)
    lines.append("Random Seed                  : " + str(RANDOM_SEED))
    lines.append("Baseline Orders per Hour     : " + str(BASELINE_ORDERS_PER_HOUR))
    lines.append("Baseline Active Riders       : " + str(BASELINE_ACTIVE_RIDERS))
    lines.append("Baseline Speed               : " + str(BASELINE_SPEED_KMH) + " km/h")
    lines.append("Target SLA                   : " + str(TARGET_LATENCY_MINUTES) + " minutes")

    lines.append("")
    lines.append("-" * 78)
    lines.append("WEATHER DISTRIBUTION CHECK")
    lines.append("-" * 78)

    if not weather_distribution_rows:
        lines.append("No weather distribution data available.")
    else:
        lines.append(
            "Weather        | Expected % | Expected Count | Observed Count | Observed %"
        )
        lines.append("-" * 78)

        for row in weather_distribution_rows:
            lines.append(
                "{:<14} | {:>9.2f}% | {:>14.2f} | {:>14} | {:>9.2f}%".format(
                    row["weather_label"][:14],
                    row["expected_probability"] * 100,
                    row["expected_count"],
                    row["observed_count"],
                    row["observed_probability"] * 100,
                )
            )

    lines.append("")
    lines.append("-" * 78)
    lines.append("WEATHER SUMMARY")
    lines.append("-" * 78)

    if weather_summary_df.empty:
        lines.append("No completed orders were recorded.")
    else:
        for _, row in weather_summary_df.iterrows():
            lines.append("")
            lines.append("Weather Condition: " + str(row["weather_label"]))
            lines.append(
                "  Completed Orders          : " +
                str(int(row["completed_orders"]))
            )
            lines.append(
                "  Mean Total Latency        : {:.2f} minutes".format(
                    row["mean_total_latency"]
                )
            )
            lines.append(
                "  95th Percentile Latency   : {:.2f} minutes".format(
                    row["p95_total_latency"]
                )
            )
            lines.append(
                "  Maximum Latency           : {:.2f} minutes".format(
                    row["max_total_latency"]
                )
            )
            lines.append(
                "  Mean Rider Queue Time     : {:.2f} minutes".format(
                    row["mean_rider_queue_time"]
                )
            )
            lines.append(
                "  SLA Violation Rate        : {:.2f}%".format(
                    row["sla_violation_rate"] * 100
                )
            )

    lines.append("")
    lines.append("-" * 78)
    lines.append("REPLICATION SUMMARY")
    lines.append("-" * 78)
    lines.append(
        "Replication | Weather        | Completed | Avg Latency | "
        "P95 Latency | SLA Viol. | Degraded"
    )
    lines.append("-" * 78)

    for _, row in replication_summary_df.iterrows():
        lines.append(
            "{:>11} | {:<14} | {:>9} | {:>11.2f} | {:>11.2f} | {:>8.2f}% | {:>8}".format(
                int(row["replication"]),
                str(row["weather_label"])[:14],
                int(row["completed_orders"]),
                row["avg_total_latency"],
                row["p95_total_latency"],
                row["sla_violation_rate"] * 100,
                str(row["degraded"])
            )
        )

    lines.append("")
    lines.append("=" * 78)
    lines.append("END OF ARENA-STYLE REPORT")
    lines.append("=" * 78)

    return "\n".join(lines)


def print_and_save_arena_report(
    config,
    replication_summary_df,
    weather_summary_df,
    weather_log_df,
    output_dir
):
    """Prints and saves the Arena-style report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    weather_distribution_rows = build_weather_distribution_check(weather_log_df)

    report = build_arena_style_report(
        config=config,
        replication_summary_df=replication_summary_df,
        weather_summary_df=weather_summary_df,
        weather_distribution_rows=weather_distribution_rows
    )

    print(report)

    ARENA_REPORT_OUTPUT.write_text(report, encoding="utf-8")

    return ARENA_REPORT_OUTPUT


def validate_outputs(raw_orders_df, replication_summary_df, weather_summary_df):
    """
    Validates simulation outputs without changing any values.

    Checks:
    - no negative durations
    - total latency consistency
    - SLA flag consistency
    - raw order count equals replication summary count
    - raw order count equals weather summary count
    """
    issues = []

    if raw_orders_df.empty:
        issues.append("Raw orders dataframe is empty.")

    time_columns = [
        "arrival_time",
        "prep_time",
        "rider_queue_time",
        "travel_time",
        "reposition_time",
        "total_latency",
    ]

    for column in time_columns:
        if column in raw_orders_df.columns:
            negative_count = (raw_orders_df[column] < 0).sum()
            if negative_count > 0:
                issues.append(
                    "{} has {} negative values.".format(column, negative_count)
                )

    if not raw_orders_df.empty:
        recomputed_latency = (
            raw_orders_df["prep_time"] +
            raw_orders_df["rider_queue_time"] +
            raw_orders_df["travel_time"] +
            raw_orders_df["reposition_time"]
        )

        recorded_latency = raw_orders_df["total_latency"]

        tolerance = 0.01

        mismatches = (
            (recomputed_latency - recorded_latency).abs() > tolerance
        ).sum()

        if mismatches > 0:
            issues.append(
                "{} rows have total latency mismatches.".format(mismatches)
            )

        expected_sla = raw_orders_df["total_latency"] <= TARGET_LATENCY_MINUTES
        sla_mismatches = (expected_sla != raw_orders_df["met_sla"]).sum()

        if sla_mismatches > 0:
            issues.append(
                "{} rows have incorrect SLA flags.".format(sla_mismatches)
            )

    raw_count = len(raw_orders_df)

    if "completed_orders" in replication_summary_df.columns:
        replication_count = int(replication_summary_df["completed_orders"].sum())
        if raw_count != replication_count:
            issues.append(
                "Raw order count ({}) does not match replication summary count ({}).".format(
                    raw_count,
                    replication_count
                )
            )

    if "completed_orders" in weather_summary_df.columns:
        weather_count = int(weather_summary_df["completed_orders"].sum())
        if raw_count != weather_count:
            issues.append(
                "Raw order count ({}) does not match weather summary count ({}).".format(
                    raw_count,
                    weather_count
                )
            )

    lines = []
    lines.append("=" * 78)
    lines.append("RAINCHECK OUTPUT VALIDATION REPORT")
    lines.append("=" * 78)

    if issues:
        lines.append("Validation Status: FAILED")
        lines.append("")
        for issue in issues:
            lines.append("- " + issue)
    else:
        lines.append("Validation Status: PASSED")
        lines.append("")
        lines.append("All output consistency checks passed.")

    lines.append("")
    lines.append("Total Raw Orders: " + str(raw_count))
    lines.append("=" * 78)

    validation_report = "\n".join(lines)

    VALIDATION_REPORT_OUTPUT.write_text(validation_report, encoding="utf-8")
    print("\n" + validation_report)

    return issues