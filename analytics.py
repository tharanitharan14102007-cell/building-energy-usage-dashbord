"""
Building Energy Analytics Engine
Provides professional ASHRAE 90.1 energy metrics, EUI calculations,
Time-of-Use tariff cost analysis, automated fault/anomaly detection, and ECM simulations.
"""

from typing import Dict, List, Any
import statistics

def calculate_summary_metrics(records: List[Dict[str, Any]], building: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate key performance indicators (KPIs) over the given telemetry window."""
    if not records:
        return {}

    total_net_kwh = sum(r["net_kw"] for r in records)
    total_gross_kwh = sum(r["gross_kw"] for r in records)
    total_solar_kwh = sum(r["solar_gen_kw"] for r in records)
    total_energy_cost = sum(r["cost"] for r in records)
    total_carbon_kg = sum(r["carbon_kg"] for r in records)

    # Peak demand
    peak_record = max(records, key=lambda r: r["net_kw"])
    peak_demand_kw = peak_record["net_kw"]
    peak_timestamp = peak_record["timestamp"]

    # Average load and load factor
    hours = len(records)
    avg_load_kw = total_net_kwh / hours if hours > 0 else 0
    # Load Factor = (Total kWh) / (Peak kW * Total Hours)
    load_factor = (total_net_kwh / (peak_demand_kw * hours)) if (peak_demand_kw > 0 and hours > 0) else 0

    # Demand charges (applied to monthly peak)
    from data_generator import TARIFF_RATES
    demand_charge = round(peak_demand_kw * TARIFF_RATES["demand_charge_per_kw"], 2)
    total_utility_bill = round(total_energy_cost + demand_charge, 2)

    # Annualized EUI calculation (Energy Use Intensity: kWh/m²/year)
    area_sqm = building["area_sqm"]
    annual_factor = (8760 / hours) if hours > 0 else 1
    annualized_net_kwh = total_net_kwh * annual_factor
    calculated_eui = round(annualized_net_kwh / area_sqm, 1) if area_sqm > 0 else 0
    benchmark_eui = building.get("benchmark_eui_kwh_sqm", 120.0)
    eui_performance_pct = round(((calculated_eui - benchmark_eui) / benchmark_eui) * 100, 1)

    # Subsystem energy breakdown (kWh and %)
    hvac_total = sum(r["hvac_kw"] for r in records)
    lighting_total = sum(r["lighting_kw"] for r in records)
    plug_total = sum(r["plug_kw"] for r in records)
    ev_total = sum(r["ev_kw"] for r in records)
    elev_total = sum(r["elev_kw"] for r in records)

    breakdown = [
        {"name": "HVAC (Cooling/Heating)", "kwh": round(hvac_total, 1), "pct": round(hvac_total / total_gross_kwh * 100, 1) if total_gross_kwh > 0 else 0, "color": "#3B82F6"},
        {"name": "Equipment & Plug Loads", "kwh": round(plug_total, 1), "pct": round(plug_total / total_gross_kwh * 100, 1) if total_gross_kwh > 0 else 0, "color": "#10B981"},
        {"name": "Lighting Systems", "kwh": round(lighting_total, 1), "pct": round(lighting_total / total_gross_kwh * 100, 1) if total_gross_kwh > 0 else 0, "color": "#F59E0B"},
        {"name": "EV Fleet Chargers", "kwh": round(ev_total, 1), "pct": round(ev_total / total_gross_kwh * 100, 1) if total_gross_kwh > 0 else 0, "color": "#8B5CF6"},
        {"name": "Elevators & Vertical Transport", "kwh": round(elev_total, 1), "pct": round(elev_total / total_gross_kwh * 100, 1) if total_gross_kwh > 0 else 0, "color": "#EC4899"}
    ]

    # Solar self-consumption / self-sufficiency
    solar_offset_pct = round((total_solar_kwh / total_gross_kwh) * 100, 1) if total_gross_kwh > 0 else 0

    return {
        "building_id": building["id"],
        "building_name": building["name"],
        "building_type": building["type"],
        "area_sqm": area_sqm,
        "hours_analyzed": hours,
        "total_net_mwh": round(total_net_kwh / 1000, 2),
        "total_net_kwh": round(total_net_kwh, 1),
        "total_gross_mwh": round(total_gross_kwh / 1000, 2),
        "total_solar_mwh": round(total_solar_kwh / 1000, 2),
        "solar_offset_pct": solar_offset_pct,
        "peak_demand_kw": round(peak_demand_kw, 1),
        "peak_timestamp": peak_timestamp,
        "avg_load_kw": round(avg_load_kw, 1),
        "load_factor_pct": round(load_factor * 100, 1),
        "energy_cost": round(total_energy_cost, 2),
        "demand_charge": demand_charge,
        "total_bill": total_utility_bill,
        "carbon_metric_tons": round(total_carbon_kg / 1000, 2),
        "eui_kwh_sqm": calculated_eui,
        "benchmark_eui": benchmark_eui,
        "eui_performance_pct": eui_performance_pct, # negative is better than benchmark
        "breakdown": breakdown
    }

def detect_anomalies(records: List[Dict[str, Any]], building: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scan hourly records for energy waste, schedule overrides, and operational faults."""
    anomalies = []
    
    # 1. Baseload Creep Check: 01:00 - 04:00 consumption should be near base_load_kw
    expected_base = building["base_load_kw"]
    night_records = [r for r in records if 1 <= r["hour"] <= 4]
    
    for r in night_records:
        if r["net_kw"] > expected_base * 1.45:
            anomalies.append({
                "type": "Baseload Overconsumption",
                "severity": "Warning",
                "timestamp": r["timestamp"],
                "observed_kw": r["net_kw"],
                "expected_kw": expected_base,
                "impact_kwh": round(r["net_kw"] - expected_base, 1),
                "message": f"Nighttime baseload ({r['net_kw']} kW) exceeds expected idle capacity ({expected_base} kW) by {round((r['net_kw']/expected_base - 1)*100)}%. Check HVAC setback schedule and unpowered server/lighting circuits."
            })
            if len(anomalies) >= 3:
                break

    # 2. On-Peak Demand Spike Alert (14:00 - 18:00)
    on_peak_records = [r for r in records if 14 <= r["hour"] <= 18]
    if on_peak_records:
        avg_on_peak = statistics.mean([r["net_kw"] for r in on_peak_records])
        max_on_peak = max(on_peak_records, key=lambda r: r["net_kw"])
        if max_on_peak["net_kw"] > avg_on_peak * 1.35 and max_on_peak["net_kw"] > building["peak_capacity_kw"] * 0.8:
            anomalies.append({
                "type": "Peak Demand Surcharge Risk",
                "severity": "High",
                "timestamp": max_on_peak["timestamp"],
                "observed_kw": max_on_peak["net_kw"],
                "expected_kw": round(avg_on_peak, 1),
                "impact_kwh": round(max_on_peak["net_kw"] - avg_on_peak, 1),
                "message": f"Critical peak of {max_on_peak['net_kw']} kW occurred during high-tariff utility window. Adds up to ${round((max_on_peak['net_kw'] - avg_on_peak) * 18.50, 2)} in monthly demand charges."
            })

    # 3. Solar Generation Anomaly (Irradiance high but solar generation near zero)
    for r in records:
        if r["solar_irr_w_m2"] > 550 and r["solar_gen_kw"] < (building["solar_pv_kwp"] * 0.15):
            anomalies.append({
                "type": "Solar PV Inverter Fault / Soiling",
                "severity": "Medium",
                "timestamp": r["timestamp"],
                "observed_kw": r["solar_gen_kw"],
                "expected_kw": round(building["solar_pv_kwp"] * 0.55, 1),
                "impact_kwh": round(building["solar_pv_kwp"] * 0.55 - r["solar_gen_kw"], 1),
                "message": f"Solar PV generated only {r['solar_gen_kw']} kW despite high solar irradiance ({r['solar_irr_w_m2']} W/m²). Potential inverter tripping or heavy panel soiling."
            })
            break

    # 4. Weekend After-Hours HVAC Override
    weekend_records = [r for r in records if r["is_weekend"]]
    for r in weekend_records:
        if r["hvac_kw"] > (building["peak_capacity_kw"] * 0.3) and r["occupancy_pct"] < 10:
            anomalies.append({
                "type": "Unscheduled Weekend HVAC Run",
                "severity": "Warning",
                "timestamp": r["timestamp"],
                "observed_kw": r["hvac_kw"],
                "expected_kw": round(building["base_load_kw"] * 0.25, 1),
                "impact_kwh": round(r["hvac_kw"] - building["base_load_kw"] * 0.25, 1),
                "message": f"Central chiller plant operated at {r['hvac_kw']} kW during weekend with only {r['occupancy_pct']}% building occupancy. Review BMS manual overrides."
            })
            break

    return anomalies

def simulate_conservation_measures(records: List[Dict[str, Any]], building: Dict[str, Any], measures: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate impact of Energy Conservation Measures (ECMs):
    - hvac_setpoint_offset: +1 or +2 degrees C in cooling season (reduces HVAC load by ~6% per degree)
    - led_retrofit: boolean (reduces lighting energy by 32%)
    - plug_load_control: boolean (smart occupancy plugs reduce plug load by 16%)
    - add_solar_kwp: additional solar PV capacity in kWp
    """
    hvac_offset = measures.get("hvac_setpoint_offset", 0.0)
    led_retrofit = measures.get("led_retrofit", False)
    plug_control = measures.get("plug_load_control", False)
    add_solar_kwp = measures.get("add_solar_kwp", 0.0)

    hvac_savings_factor = max(0.0, 1.0 - (hvac_offset * 0.065))
    lighting_savings_factor = 0.68 if led_retrofit else 1.0
    plug_savings_factor = 0.84 if plug_control else 1.0

    original_net_kwh = sum(r["net_kw"] for r in records)
    original_cost = sum(r["cost"] for r in records)
    from data_generator import get_tariff_rate, TARIFF_RATES

    simulated_net_kwh = 0.0
    simulated_cost = 0.0
    simulated_peak_kw = 0.0

    for r in records:
        hvac_new = r["hvac_kw"] * hvac_savings_factor
        lighting_new = r["lighting_kw"] * lighting_savings_factor
        plug_new = r["plug_kw"] * plug_savings_factor
        ev_new = r["ev_kw"]
        elev_new = r["elev_kw"]
        
        # New solar generation
        extra_solar_kw = (add_solar_kwp * (r["solar_irr_w_m2"] / 1000.0) * 0.95) if r["solar_irr_w_m2"] > 0 else 0.0
        solar_new = r["solar_gen_kw"] + extra_solar_kw
        
        gross_new = hvac_new + lighting_new + plug_new + ev_new + elev_new
        net_new = max(0.0, gross_new - solar_new)
        
        simulated_net_kwh += net_new
        simulated_cost += net_new * r["tariff_rate"]
        if net_new > simulated_peak_kw:
            simulated_peak_kw = net_new

    # Annualized projections
    hours = len(records)
    annual_factor = (8760 / hours) if hours > 0 else 1
    
    kwh_saved = round((original_net_kwh - simulated_net_kwh) * annual_factor, 1)
    cost_saved = round((original_cost - simulated_cost) * annual_factor, 2)
    co2_saved_tons = round((kwh_saved * TARIFF_RATES["grid_carbon_factor"]) / 1000, 2)
    
    # Capital cost estimate
    capex = 0
    if led_retrofit:
        capex += building["area_sqm"] * 3.5  # $3.5 per sqm for LED upgrade
    if plug_control:
        capex += building["occupancy_capacity"] * 45  # $45 per workstation for smart plugs
    if add_solar_kwp > 0:
        capex += add_solar_kwp * 950  # $950 per kWp installed
        
    payback_years = round(capex / cost_saved, 1) if cost_saved > 0 and capex > 0 else 0.0

    return {
        "annual_kwh_saved": kwh_saved,
        "annual_cost_saved": cost_saved,
        "annual_co2_abated_tons": co2_saved_tons,
        "pct_reduction": round(((original_net_kwh - simulated_net_kwh) / original_net_kwh) * 100, 1) if original_net_kwh > 0 else 0,
        "estimated_capex": capex,
        "simple_payback_years": payback_years,
        "simulated_peak_kw": round(simulated_peak_kw, 1)
    }
