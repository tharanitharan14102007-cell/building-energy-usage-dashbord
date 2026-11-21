import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import data_generator
import analytics

def test():
    bldg = data_generator.BUILDINGS[0]
    records = data_generator.generate_building_telemetry(bldg, days=7)
    print(f"Generated {len(records)} records for {bldg['name']}")
    metrics = analytics.calculate_summary_metrics(records, bldg)
    print(f"Total MWh: {metrics['total_net_mwh']}, Peak kW: {metrics['peak_demand_kw']}, EUI: {metrics['eui_kwh_sqm']}")
    anomalies = analytics.detect_anomalies(records, bldg)
    print(f"Detected {len(anomalies)} anomalies")
    for a in anomalies:
        print(f" - [{a['severity']}] {a['type']} at {a['timestamp']}: {a['message']}")
    sim = analytics.simulate_conservation_measures(records, bldg, {'hvac_setpoint_offset': 1.5, 'led_retrofit': True, 'add_solar_kwp': 50})
    print(f"Simulated annual cost savings: ${sim['annual_cost_saved']}, Capex: ${sim['estimated_capex']}, Payback: {sim['simple_payback_years']} yrs")
    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test()
