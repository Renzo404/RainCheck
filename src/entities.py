from dataclasses import dataclass


@dataclass
class SimulationConfig:
    simulation_month: str
    replication_length_minutes: float
    replications: int
    target_latency_minutes: float
    random_seed: int


@dataclass
class OrderResult:
    replication: int
    order_id: int
    weather_state: str
    weather_label: str
    arrival_time: float
    prep_time: float
    rider_queue_time: float
    travel_time: float
    reposition_time: float
    total_latency: float
    met_sla: bool