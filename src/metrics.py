import statistics

import pandas as pd


def summarize_replication(config, replication, weather_log, order_results):
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
        "p95_total_latency": round(
            pd.Series(latencies).quantile(0.95),
            4
        ),
        "max_total_latency": round(max(latencies), 4),
        "avg_rider_queue_time": round(
            statistics.mean(rider_queues),
            4
        ),
        "max_rider_queue_time": round(max(rider_queues), 4),
        "sla_violations": sla_violations,
        "sla_violation_rate": round(
            sla_violations / len(order_results),
            4
        ),
        "degraded": avg_latency > config.target_latency_minutes,
    }


def summarize_weather(raw_orders_df):
    if raw_orders_df.empty:
        return pd.DataFrame()

    weather_summary = (
        raw_orders_df
        .groupby(["weather_state", "weather_label"])
        .agg(
            completed_orders=("order_id", "count"),
            mean_total_latency=("total_latency", "mean"),
            p95_total_latency=(
                "total_latency",
                lambda x: x.quantile(0.95)
            ),
            max_total_latency=("total_latency", "max"),
            mean_rider_queue_time=("rider_queue_time", "mean"),
            sla_violation_rate=(
                "met_sla",
                lambda x: 1 - x.mean()
            ),
        )
        .reset_index()
    )

    numeric_columns = weather_summary.select_dtypes(
        include="number"
    ).columns

    weather_summary[numeric_columns] = (
        weather_summary[numeric_columns].round(4)
    )

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


def build_arena_style_report(
    config,
    replication_summary_df,
    weather_summary_df
):
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
    lines.append(
        "SLA THRESHOLD: " +
        str(config.target_latency_minutes) +
        " minutes"
    )
    lines.append(
        "WEATHER ASSUMPTION: One sampled weather state is fixed per replication."
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
            lines.append(
                "Weather Condition: " +
                str(row["weather_label"])
            )
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
    output_dir
):
    output_dir.mkdir(parents=True, exist_ok=True)

    report = build_arena_style_report(
        config=config,
        replication_summary_df=replication_summary_df,
        weather_summary_df=weather_summary_df
    )

    print(report)

    report_path = output_dir / "arena_style_report.txt"
    report_path.write_text(report, encoding="utf-8")

    return report_path