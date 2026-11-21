"""
Synthetic Building Energy Telemetry Generator
Generates realistic high-frequency and hourly multi-zone telemetry for commercial and industrial facilities.
Includes weather dependencies (CDD/HDD), occupancy profiles, sub-metering, and anomaly injection.
"""

import math
import random
from datetime import datetime, timedelta

BUILDINGS = [
    {
        "id": "bldg-01",
        "name": "Tower Alpha (Corporate HQ)",
        "type": "Commercial Office",
        "area_sqm": 28500,
        "floors": 18,
        "occupancy_capacity": 2200,
        "base_load_kw": 180,
        "peak_capacity_kw": 1250,
        "solar_pv_kwp": 220,
        "benchmark_eui_kwh_sqm": 135.0,
    },
    {
        "id": "bldg-02",
        "name": "Nexus Research & Innovation Center",
        "type": "R&D / High-Tech Lab",
        "area_sqm": 19200,
        "floors": 6,
        "occupancy_capacity": 850,
        "base_load_kw": 320,  # High constant baseload due to lab equipment & cleanrooms
        "peak_capacity_kw": 1600,
        "solar_pv_kwp": 150,
        "benchmark_eui_kwh_sqm": 220.0,
    },
    {
        "id": "bldg-03",
        "name": "Horizon Logistics Hub & Depot",
        "type": "Warehouse & Cold Storage",
        "area_sqm": 42000,
        "floors": 2,
        "occupancy_capacity": 300,
        "base_load_kw": 250,  # Cold storage baseline
        "peak_capacity_kw": 980,
        "solar_pv_kwp": 450,
        "benchmark_eui_kwh_sqm": 95.0,
    }
]

TARIFF_RATES = {
    "currency": "USD",
    "currency_symbol": "$",
    "off_peak": 0.085,     # $/kWh (22:00 - 06:00)
    "mid_peak": 0.145,     # $/kWh (06:00 - 14:00, 19:00 - 22:00)
    "on_peak": 0.245,      # $/kWh (14:00 - 19:00)
    "demand_charge_per_kw": 18.50, # $/kW of monthly peak demand
    "grid_carbon_factor": 0.412    # kg CO2e per kWh
}

def get_tariff_rate(hour):
    """Return Time-of-Use (TOU) energy rate for a given hour."""
    if 22 <= hour or hour < 6:
        return TARIFF_RATES["off_peak"]
    elif 14 <= hour < 19:
        return TARIFF_RATES["on_peak"]
    else:
        return TARIFF_RATES["mid_peak"]

def generate_weather(date_obj, hour):
    """Simulate realistic ambient temperature and solar irradiance."""
    day_of_year = date_obj.timetuple().tm_yday
    # Seasonal base temp (Northern Hemisphere curve: peak July/Aug, trough Jan/Feb)
    seasonal_temp = 20.0 + 10.0 * math.sin(2 * math.pi * (day_of_year - 105) / 365)
    
    # Diurnal cycle (coolest at 5 AM, warmest at 3 PM)
    diurnal_variation = 6.5 * math.sin(2 * math.pi * (hour - 9) / 24)
    ambient_temp = round(seasonal_temp + diurnal_variation + random.uniform(-1.5, 1.5), 1)

    # Solar irradiance (W/m2)
    if 6 <= hour <= 18:
        solar_peak = math.sin(math.pi * (hour - 6) / 12)
        solar_w_m2 = max(0.0, round(solar_peak * 850.0 + random.uniform(-40, 40), 1))
    else:
        solar_w_m2 = 0.0

    return ambient_temp, solar_w_m2

def generate_building_telemetry(building, days=30, end_date=None):
    """
    Generate hourly telemetry records for a building across past N days.
    Produces sub-metered power (kW), energy (kWh), costs, carbon, and alerts.
    """
    if end_date is None:
        end_date = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    start_date = end_date - timedelta(days=days)
    records = []
    
    current_time = start_date
    while current_time <= end_date:
        hour = current_time.hour
        weekday = current_time.weekday() # 0 = Monday, 6 = Sunday
        is_weekend = weekday >= 5
        
        temp, solar_irr = generate_weather(current_time, hour)
        
        # Occupancy ratio
        if is_weekend:
            occupancy = 0.05 + (0.08 if 10 <= hour <= 16 else 0.01)
        else:
            if 8 <= hour <= 18:
                occupancy = 0.75 + 0.20 * math.sin(math.pi * (hour - 8) / 10)
            elif (6 <= hour < 8) or (18 < hour <= 21):
                occupancy = 0.25
            else:
                occupancy = 0.04
        occupancy = max(0.0, min(1.0, occupancy + random.uniform(-0.03, 0.03)))
        
        # Sub-system load breakdown (kW)
        # 1. HVAC Load: tightly coupled to ambient temperature (CDD cooling above 18°C) + occupancy
        temp_delta = max(0, temp - 18.0) # Cooling degree demand
        heating_delta = max(0, 16.0 - temp) # Heating degree demand
        hvac_capacity = building["peak_capacity_kw"] * 0.48
        hvac_kw = (building["base_load_kw"] * 0.25) + \
                  (temp_delta * 14.5 + heating_delta * 10.0) + \
                  (occupancy * hvac_capacity * 0.6) + \
                  random.uniform(-10, 10)
        hvac_kw = max(20.0, min(hvac_capacity, hvac_kw))
        
        # 2. Lighting Load
        daylight_saving_factor = 0.65 if (solar_irr > 300) else 1.0
        lighting_capacity = building["peak_capacity_kw"] * 0.20
        lighting_kw = (building["base_load_kw"] * 0.1) + \
                      (occupancy * lighting_capacity * daylight_saving_factor) + \
                      random.uniform(-4, 4)
        lighting_kw = max(8.0, min(lighting_capacity, lighting_kw))
        
        # 3. Equipment & Plug Loads
        plug_capacity = building["peak_capacity_kw"] * 0.22
        plug_kw = (building["base_load_kw"] * 0.45) + \
                  (occupancy * plug_capacity * 0.7) + \
                  random.uniform(-8, 8)
        plug_kw = max(15.0, min(plug_capacity, plug_kw))
        
        # 4. EV Charging (active mostly 8:00 - 15:00 weekdays)
        ev_capacity = building["peak_capacity_kw"] * 0.06
        if not is_weekend and (8 <= hour <= 16):
            ev_kw = ev_capacity * random.uniform(0.3, 0.9)
        else:
            ev_kw = ev_capacity * random.uniform(0.0, 0.1)
            
        # 5. Elevators / Mechanical
        elev_capacity = building["peak_capacity_kw"] * 0.04
        elev_kw = elev_capacity * (occupancy * 0.9 + 0.1) + random.uniform(-2, 2)
        elev_kw = max(2.0, elev_kw)
        
        # Solar PV Generation (kW)
        solar_efficiency = 0.18
        solar_gen_kw = (building["solar_pv_kwp"] * (solar_irr / 1000.0) * random.uniform(0.92, 0.98)) if solar_irr > 0 else 0.0
        solar_gen_kw = round(solar_gen_kw, 1)

        # Total Gross & Net Load
        gross_kw = round(hvac_kw + lighting_kw + plug_kw + ev_kw + elev_kw, 1)
        net_kw = max(0.0, round(gross_kw - solar_gen_kw, 1))
        
        # Cost and Carbon for this 1-hour interval (kW * 1 hour = kWh)
        kwh = net_kw
        tariff = get_tariff_rate(hour)
        cost = round(kwh * tariff, 2)
        carbon_kg = round(kwh * TARIFF_RATES["grid_carbon_factor"], 2)

        records.append({
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M"),
            "iso_time": current_time.isoformat(),
            "hour": hour,
            "weekday": weekday,
            "is_weekend": is_weekend,
            "temperature_c": temp,
            "solar_irr_w_m2": solar_irr,
            "occupancy_pct": round(occupancy * 100, 1),
            "hvac_kw": round(hvac_kw, 1),
            "lighting_kw": round(lighting_kw, 1),
            "plug_kw": round(plug_kw, 1),
            "ev_kw": round(ev_kw, 1),
            "elev_kw": round(elev_kw, 1),
            "solar_gen_kw": solar_gen_kw,
            "gross_kw": gross_kw,
            "net_kw": net_kw,
            "tariff_rate": tariff,
            "cost": cost,
            "carbon_kg": carbon_kg
        })
        
        current_time += timedelta(hours=1)
        
    return records
