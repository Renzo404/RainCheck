# RainCheck

SimPy-based discrete-event simulation analyzing food delivery Service Level Agreement (SLA) performance under rainfall conditions in Baguio City. The model integrates **Meteoblue ERA5T historical climate data**, **DOST-PAGASA precipitation intensity standards**, **FHWA weather-related travel speed penalties**, and **behavioral demand shifts from UP NCTS research** to evaluate how adverse weather affects urban delivery logistics.

Built as the computational framework for urban logistics and stochastic simulation research.

---

## Overview

In highly congested, high-altitude urban environments like the **Baguio City Central Business District (CBD)**, adverse weather conditions can significantly degrade on-demand food delivery performance. **RainCheck** quantifies this degradation using a **stochastic SimPy discrete-event simulation (DES)** framework.

The simulation evaluates whether standard **45-minute Service Level Agreements (SLAs)** remain attainable under adverse weather by modeling the interaction between:

### Weather-Induced Demand Surges
Consumers substitute physical dining trips with food delivery during rainfall, increasing delivery demand. Based on **UP National Center for Transportation Studies (NCTS)** findings (Sunga et al., 2017), food delivery demand increases by as much as **44.67% during heavy rainfall conditions**.

### Kinematic Travel Friction
Delivery rider travel speed decreases under adverse road weather conditions. Following **FHWA road weather management guidance**, rider speed is reduced by up to **20% during heavy precipitation**, increasing travel times and delivery latency.

### Stochastic Weather Conditions
Monthly precipitation probabilities are derived from **Meteoblue ERA5T historical climate data** and mapped to **DOST-PAGASA precipitation intensity standards**. These probabilities govern stochastic weather-state selection during simulation execution.

Each simulation replication models a **4-hour peak delivery period (16:00–20:00)** in which **one weather condition remains fixed throughout the replication**, following the assumptions defined in the manuscript methodology.

---

## Simulation Design

The RainCheck simulation follows a **Discrete-Event Simulation (DES)** architecture modeled after Arena simulation logic.

### Simulation Flow

```text
Create  →  Assign  →  Process  →  Record  →  Decide  →  Dispose
```

| Arena Logic | RainCheck Implementation |
|---|---|
| **Create** | Stochastic customer order arrivals using exponential interarrival times |
| **Assign** | Weather state selection and order timestamp assignment |
| **Process** | Restaurant preparation and rider delivery processing |
| **Record** | Delivery latency measurement |
| **Decide** | SLA compliance evaluation |
| **Dispose** | Completed order logging |

### Key Modeling Assumptions

The simulation preserves the assumptions defined in the research manuscript:

- **Baseline rider speed:** `16 km/h`
- **Delivery SLA threshold:** `45 minutes`
- **Peak delivery simulation period:** `240 minutes (16:00–20:00)`
- **Number of replications:** `30`
- **Baseline active riders:** `30`
- **Baseline order rate:** `50 orders/hour`
- **Weather condition:** Fixed throughout each replication
- **Random seed:** Fixed for reproducibility

### Weather Effects

| Weather State | Demand Multiplier | Speed Penalty | Effective Rider Speed |
|---|---:|---:|---:|
| Dry | 1.0000 | 0% | 16.0 km/h |
| Light Rains | 1.1767 | 10% | 14.4 km/h |
| Moderate Rains | 1.3933 | 15% | 13.6 km/h |
| Heavy Rains | 1.4467 | 20% | 12.8 km/h |

---

## Repository Structure

The repository is organized to separate empirical data, simulation logic, and outputs.

```text
RainCheck/
│
├── data/
│   ├── raw/
│   │   └── meteoblue_pagasa_probabilities.csv
│   │
│   └── outputs/
│       ├── raincheck_raw_orders.csv
│       ├── raincheck_replication_weather_log.csv
│       ├── raincheck_replication_summary.csv
│       ├── raincheck_weather_summary.csv
│       └── arena_style_report.txt
│
├── notebooks/
│   └── visualization notebooks
│
├── src/
│   ├── __init__.py
│   ├── entities.py
│   ├── environment.py
│   ├── main.py
│   ├── metrics.py
│   └── parameters.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

### Source Code Description

#### `entities.py`
Contains dataclasses used by the simulation:

- `SimulationConfig`
- `OrderResult`

#### `environment.py`
Handles:

- loading weather probability data
- monthly weather selection
- stochastic weather-state sampling
- weather-adjusted parameter generation

#### `main.py`
Contains the **core SimPy discrete-event simulation engine**, including:

- customer order arrivals
- restaurant preparation
- rider queueing
- travel time simulation
- SLA evaluation
- replication execution

#### `metrics.py`
Generates:

- replication summaries
- weather summaries
- latency calculations
- SLA statistics
- Arena-style simulation reports

#### `parameters.py`
Acts as the **control center** for all simulation assumptions and empirical model parameters.

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Renzo404/RainCheck.git
cd RainCheck
```

### 2. Create a Virtual Environment (Recommended)

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Running the Simulation

Execute the main simulation script:

```bash
python src/main.py
```

The simulation reads configuration values from:

```text
src/parameters.py
```

and automatically saves all outputs to:

```text
data/outputs/
```

---

## Generated Outputs

### `raincheck_raw_orders.csv`

Contains **order-level simulation data**.

Includes:

- order arrival time
- preparation duration
- rider queue time
- travel time
- reposition time
- total latency
- SLA compliance

---

### `raincheck_replication_weather_log.csv`

Contains **one sampled weather condition per replication**.

Example:

```csv
replication,weather_state,monthly_probability
1,Heavy Rains,0.5162
2,Light Rains,0.3226
```

---

### `raincheck_replication_summary.csv`

Contains **replication-level KPIs**:

- average latency
- 95th percentile latency
- maximum latency
- SLA violation rate
- rider queue times
- degradation status

---

### `raincheck_weather_summary.csv`

Aggregated system performance grouped by weather condition.

Useful for:

- comparing weather impacts
- statistical interpretation
- manuscript tables

---

### `arena_style_report.txt`

Human-readable simulation report inspired by **Arena output reports**.

Includes:

- weather summaries
- latency statistics
- replication performance
- SLA outcomes

---

## Modifying Parameters

To test different experimental scenarios, edit:

```text
src/parameters.py
```

Examples:

### Change Simulation Month

```python
SIMULATION_MONTH = "Jul"
```

### Change Rider Capacity

```python
BASELINE_ACTIVE_RIDERS = 40
```

### Change Replication Count

```python
REPLICATIONS = 50
```

The architecture is intentionally modular so parameter changes **do not require rewriting the simulation engine**.

---

## Reproducibility

RainCheck uses a **fixed random seed** to ensure simulation reproducibility.

This guarantees:

- identical results across repeated runs
- reproducible manuscript tables
- experimental consistency
- easier debugging and validation

The random seed can be changed inside:

```python
RANDOM_SEED = 10000
```

in:

```text
src/parameters.py
```

---

## Academic Context

This repository serves as the computational framework for the methodology presented in:

> **“Stochastic Modeling and Discrete Event Simulation of Urban Food Delivery Logistics Under Variable Precipitation: A Case Study of Baguio City”**

The simulation framework operationalizes empirical assumptions described in:

- **Section 2.4 — Data Requirements**
- **Section 2.5 — Modeling Assumptions**
- **Appendix A — Meteoblue Historical Climate Data**
- **Appendix B — Weather State Probability Mapping**

Weather conditions are sampled probabilistically using monthly historical precipitation distributions, while remaining **fixed within each 4-hour replication**, consistent with the study's simulation assumptions.

---

## References

- **Federal Highway Administration (FHWA).** (2023). Road Weather Management Program.
- **Meteoblue ERA5T Historical Climate Model.**
- **DOST-PAGASA Rainfall Intensity Classification Standards.**
- **Sunga et al. (2017).** UP National Center for Transportation Studies (NCTS) behavioral mobility findings.

---

## License

This repository is intended for **academic and research purposes**.