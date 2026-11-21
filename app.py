"""
Building Energy Usage Analysis Dashboard - Flask Application
"""

import os
import io
import csv
from flask import Flask, jsonify, render_template, request, Response
from data_generator import BUILDINGS, generate_building_telemetry, TARIFF_RATES
import analytics

app = Flask(__name__, template_folder="templates", static_folder="static")

# In-memory cache for generated telemetry
_TELEMETRY_CACHE = {}

def get_cached_telemetry(building_id: str, days: int = 14):
    cache_key = f"{building_id}_{days}"
    if cache_key not in _TELEMETRY_CACHE:
        bldg = next((b for b in BUILDINGS if b["id"] == building_id), BUILDINGS[0])
        records = generate_building_telemetry(bldg, days=days)
        _TELEMETRY_CACHE[cache_key] = records
    return _TELEMETRY_CACHE[cache_key]

@app.route("/")
def index():
    return render_template("index.html", buildings=BUILDINGS, rates=TARIFF_RATES)

@app.route("/api/buildings")
def api_buildings():
    return jsonify({"status": "success", "data": BUILDINGS})

@app.route("/api/dashboard")
def api_dashboard():
    building_id = request.args.get("building_id", BUILDINGS[0]["id"])
    days = int(request.args.get("days", 7))
    days = max(1, min(60, days))

    bldg = next((b for b in BUILDINGS if b["id"] == building_id), BUILDINGS[0])
    records = get_cached_telemetry(building_id, days=days)
    
    summary = analytics.calculate_summary_metrics(records, bldg)
    anomalies = analytics.detect_anomalies(records, bldg)

    # Subsample for frontend charts if days > 7 to keep response snappy
    stride = 1 if days <= 7 else (2 if days <= 14 else 4)
    chart_series = records[::stride]

    return jsonify({
        "status": "success",
        "building": bldg,
        "summary": summary,
        "anomalies": anomalies,
        "timeseries": chart_series,
        "tariff_rates": TARIFF_RATES
    })

@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.get_json() or {}
    building_id = data.get("building_id", BUILDINGS[0]["id"])
    days = int(data.get("days", 14))
    
    bldg = next((b for b in BUILDINGS if b["id"] == building_id), BUILDINGS[0])
    records = get_cached_telemetry(building_id, days=days)

    measures = {
        "hvac_setpoint_offset": float(data.get("hvac_setpoint_offset", 0.0)),
        "led_retrofit": bool(data.get("led_retrofit", False)),
        "plug_load_control": bool(data.get("plug_load_control", False)),
        "add_solar_kwp": float(data.get("add_solar_kwp", 0.0))
    }

    result = analytics.simulate_conservation_measures(records, bldg, measures)
    return jsonify({"status": "success", "simulation": result})

@app.route("/api/export")
def api_export():
    building_id = request.args.get("building_id", BUILDINGS[0]["id"])
    days = int(request.args.get("days", 14))
    bldg = next((b for b in BUILDINGS if b["id"] == building_id), BUILDINGS[0])
    records = get_cached_telemetry(building_id, days=days)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Timestamp", "Hour", "Temperature_C", "Solar_W_m2", "Occupancy_Pct",
        "HVAC_kW", "Lighting_kW", "Plug_kW", "EV_kW", "Elev_kW",
        "Solar_Gen_kW", "Gross_kW", "Net_kW", "Tariff_Rate", "Cost_USD", "Carbon_kg"
    ])
    for r in records:
        writer.writerow([
            r["timestamp"], r["hour"], r["temperature_c"], r["solar_irr_w_m2"], r["occupancy_pct"],
            r["hvac_kw"], r["lighting_kw"], r["plug_kw"], r["ev_kw"], r["elev_kw"],
            r["solar_gen_kw"], r["gross_kw"], r["net_kw"], r["tariff_rate"], r["cost"], r["carbon_kg"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={bldg['id']}_energy_telemetry.csv"}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Building Energy Usage Analysis Dashboard on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
