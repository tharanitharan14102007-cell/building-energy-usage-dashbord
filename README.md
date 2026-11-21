# Building Energy Usage Analysis Dashboard (EcoPulse BMS)

A commercial building energy management and analytics platform built with Python, Flask, and modern data visualization. Compliant with ASHRAE 90.1 energy benchmarking methodologies, featuring automated fault detection, Time-of-Use (TOU) tariff optimization, and an interactive Energy Conservation Measure (ECM) ROI simulator.

---

## 🌟 Key Features

1. **Multi-Facility Telemetry & Submetering**:
   - High-frequency tracking across critical building subsystems: **HVAC (Chillers/AHU)**, **Lighting**, **Plug Loads/IT**, **EV Fleet Charging**, and **Vertical Transportation**.
   - Solar photovoltaic (PV) generation tracking with real-time solar self-consumption calculations.

2. **ASHRAE 90.1 Benchmarking & EUI Analytics**:
   - Calculates **Energy Use Intensity (EUI)** in $\text{kWh/m}^2/\text{year}$ normalized against building gross floor area.
   - Compares performance vs ASHRAE standard baselines and national building type averages.

3. **Peak Demand & Load Factor Monitoring**:
   - Identifies 15-minute rolling peak demand ($\text{kW}$) to mitigate aggressive utility demand ratchets and surcharges.
   - Computes **Load Factor** ($\frac{\text{Total kWh}}{\text{Peak kW} \times \text{Hours}}$) to evaluate electrical load smoothness.

4. **Automated Anomaly & Energy Waste Detection**:
   - **Nighttime Baseload Creep**: Identifies un-setback HVAC or equipment left running after business hours (01:00 - 04:00).
   - **On-Peak Demand Surcharge Risk**: Flags sudden power surges during utility on-peak pricing windows (14:00 - 18:00).
   - **Solar PV Faults / Soiling**: Correlates solar irradiance ($\text{W/m}^2$) with inverter output to alert on underperforming arrays.
   - **Weekend Override Waste**: Alerts when central chillers operate without corresponding building occupancy.

5. **Interactive Energy Conservation Measure (ECM) Simulator**:
   - Dynamic simulation for summer HVAC setpoint relaxation ($\pm 0.5^\circ\text{C}$ to $3^\circ\text{C}$).
   - LED lighting retrofit with daylight harvesting.
   - Smart plug load auto-cutoff schedules.
   - Rooftop solar PV capacity additions.
   - Real-time estimates for **annual cost savings**, **CO2 abatement**, **capital expenditure (CapEx)**, and **simple payback period**.

6. **Export & Reporting**:
   - Direct CSV export of full multi-variable telemetry data.

---

## 📁 Project Architecture

```
building-energy-dashboard/
├── app.py              # Flask server & REST API endpoints
├── analytics.py        # EUI, peak demand, anomaly detection, & ECM simulation engine
├── data_generator.py   # High-fidelity building energy and weather synthesizer
├── test_backend.py     # Backend verification test suite
├── templates/
│   └── index.html      # Responsive dashboard UI (Tailwind + Chart.js)
├── static/             # Static assets
└── README.md           # Documentation
```

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.8+ (Tested with Python 3.15)
- Flask 3.x (`pip install Flask`)

### 2. Run the Dashboard
Open your terminal in this directory and execute:

```powershell
python app.py
```

The application will start at:
👉 **`http://127.0.0.1:5000`**

### 3. Run Backend Verification Tests
```powershell
python test_backend.py
```

---

## 🔌 REST API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/buildings` | `GET` | Returns list of managed properties and building characteristics |
| `/api/dashboard?building_id={id}&days={n}` | `GET` | Returns summary KPIs, timeseries records, anomalies, and breakdown |
| `/api/simulate` | `POST` | Simulates ECM scenarios (setpoint adjustments, LED, solar) |
| `/api/export?building_id={id}&days={n}` | `GET` | Downloads raw telemetry data in CSV format |

---

## 📊 Energy Formulas & Calculations

- **Load Factor**:
  $$\text{Load Factor} = \frac{\sum \text{Net kWh}}{\text{Peak kW} \times \text{Hours}} \times 100\%$$

- **Annualized EUI**:
  $$\text{EUI} = \frac{\text{Total Net kWh} \times \left(\frac{8760}{\text{Hours}}\right)}{\text{Gross Floor Area (m}^2\text{)}}$$

- **Utility Bill**:
  $$\text{Bill} = \sum (\text{kWh}_t \times \text{TOU Rate}_t) + (\text{Peak kW} \times \text{Demand Charge per kW})$$
"# building-energy-usage-dashbord" 
