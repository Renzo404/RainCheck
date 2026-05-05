# RainCheck 🌧️🛵

SimPy discrete-event simulation analyzing food delivery SLA degradation during rain in Baguio City. Integrates Meteoblue climate data, FHWA speed penalties, and UP NCTS behavioral shifts to model the "perfect storm" of delivery bottlenecks where supply-side attrition meets a 44% demand surge. Built for urban logistics research.

---

## 📊 Overview

In highly congested, high-altitude urban environments like the Baguio City Central Business District (CBD), adverse weather severely degrades on-demand logistics. **RainCheck** quantifies this degradation by mapping real-world empirical data into a stochastic SimPy environment.

The simulation tests the breaking point of standard 45-minute Service Level Agreements (SLAs) by modeling the intersection of:
* **Weather-Induced Demand Surges:** Consumers substitute physical dining trips with delivery, peaking at a 44.67% volume surge during intense rain (Sunga et al., 2017).
* **Kinematic Travel Friction:** Vehicular speeds are dynamically reduced by up to 20% based on continuous road weather management guidelines (FHWA, 2023).
* **Supply-Side Attrition:** The delivery fleet capacity diminishes during severe precipitation due to the hazards of Baguio's steep topography and poor visibility.

---

## 📂 Repository Structure

The codebase is organized to strictly separate raw empirical data, core simulation logic, and resulting analysis.

* **`data/`**
  * `raw/`: Unedited empirical data, including historical Meteoblue ERA5T climate data (mm/day).
  * `outputs/`: Generated simulation logs (CSVs). *Note: These are ignored by Git to prevent repository bloat.*
* **`notebooks/`**
  * Jupyter Notebooks used for post-simulation data visualization and generating figures for the final manuscript.
* **`src/`**
  * `__init__.py`: Package initialization.
  * `entities.py`: Class definitions for system actors (Orders, Riders, Restaurants).
  * `environment.py`: The SimPy environment setup, orchestrating weather triggers and queues.
  * `main.py`: The primary execution script to run the simulation.
  * `metrics.py`: Calculation tools for SLA latency tracking and threshold validation.
  * `parameters.py`: **The Control Center.** Contains all Modeling Assumptions (baseline speed, arrival rates, and empirical multipliers).
* **`.gitignore`**: Standard Python ignores plus safeguards for `data/outputs/`.
* **`requirements.txt`**: Required Python dependencies.

---

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/RainCheck.git
   cd RainCheck
   ```

2. **Create a virtual environment (Recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Usage

**Running the Simulation**
Execute the main script to start a simulation run. By default, it will read the configurations set in `parameters.py` and output the timeline logs to the `data/outputs/` directory.

```bash
python src/main.py
```

**Modifying Parameters**
To adjust the simulation (e.g., testing different rider fleet capacities or altering the FHWA speed penalty brackets), edit the variables directly inside `src/parameters.py`. The logic architecture is built so that parameter adjustments do not require rewriting the core SimPy environment.

---

## 📚 Academic Context
This repository serves as the computational framework for the methodology outlined in *Stochastic Modeling and Discrete Event Simulation of Urban Food Delivery Logistics Under Variable Precipitation: A Case Study of Baguio City*. All empirical data, bounding logic, and mode-shifting proxies are thoroughly defended in the manuscript's Data Requirements (Section 2.4) and Modeling Assumptions (Section 2.5).