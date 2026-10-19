"""Find conditional car-substitution thresholds without inventing observed mode shift."""
from pathlib import Path
import csv
import itertools
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/tables/carbon_audit"
OUT.mkdir(parents=True, exist_ok=True)


def threshold(intensity_ratio, empty_to_loaded_km, detour, target_occupancy):
    if not all(math.isfinite(x) for x in [intensity_ratio, empty_to_loaded_km, detour, target_occupancy]):
        raise ValueError("Finite parameters required")
    if intensity_ratio <= 0 or empty_to_loaded_km < 0 or detour < 0 or target_occupancy <= 0:
        raise ValueError("Positive intensity and occupancy; nonnegative empty/detour ratios required")
    return intensity_ratio*(1+empty_to_loaded_km)*(1+detour)/target_occupancy


assert threshold(1,0,0,1)==1
assert threshold(1,0,0,2)==.5
assert math.isclose(threshold(1.5,.25,.1,3),.6875)
assert threshold(1.5,.25,.1,2)>1
try:
    threshold(1,0,0,0)
except ValueError:
    pass
else:
    raise AssertionError("Zero occupancy must be rejected")

rows=[]
for s,e,d,n in itertools.product([1,1.5,2],[0,.25,.5],[0,.1,.2],[1,2,3,4]):
    p=threshold(s,e,d,n)
    rows.append({"assumed_drt_to_car_kg_per_vehicle_km_ratio":s,"assumed_empty_to_loaded_km_ratio":e,
                 "assumed_passenger_detour_ratio":d,"assumed_distance_weighted_target_riders":n,
                 "minimum_car_substitution_direct_distance_share_pct":100*p,
                 "strict_reduction_requires_share_above_threshold":True,"possible_with_share_at_most100":p<1,
                 "status":"illustrative conditional model; neither target occupancy nor mode substitution measured"})
assert len(rows)==108
with (OUT/"private_car_substitution_break_even_ASSUMPTIONS.csv").open("w") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
central=[r for r in rows if r["assumed_drt_to_car_kg_per_vehicle_km_ratio"]==1.5 and r["assumed_empty_to_loaded_km_ratio"]==.25 and r["assumed_passenger_detour_ratio"]==.1]
print(central)

# shortcut: the historical distance is only a reference scale, not forecast DRT demand or observed car substitution.
import json
baseline = next(r for r in csv.DictReader((OUT/"distance_audit.csv").open()) if r["cohort"]=="three_district_treatment_main")
reference_km=float(baseline["recorded_passenger_km"])
assert math.isclose(reference_km,42536.795)
car_kg_km=2.18/12  # Assumed petrol car efficiency; historical educational conversion factor.
drt_kg_km=2.6/10  # Assumed diesel service efficiency; same conversion boundary.
forecasts=[]
for name,p,n,e,d in [("one_target_rider",.3,1,.5,0),("two_target_riders",.5,2,.25,.1),("three_target_riders",.7,3,.1,.1)]:
    assert 0<=p<=1
    drt_km=reference_km*(1+d)*(1+e)/n
    avoided_car_km=reference_km*p
    saved=avoided_car_km*car_kg_km
    added=drt_km*drt_kg_km
    net=(saved-added)/1000
    assert math.isclose(net*1000,saved-added)
    forecasts.append({"scenario":name,"reference_trip_distance_km_not_forecast_demand":reference_km,
                      "assumed_car_substitution_distance_share":p,"assumed_target_riders":n,
                      "assumed_empty_to_loaded_km":e,"assumed_extra_detour":d,
                      "assumed_car_km_per_l":12,"assumed_drt_km_per_l":10,
                      "hypothetical_avoided_car_km":avoided_car_km,"hypothetical_total_drt_km":drt_km,
                      "conditional_avoided_car_tco2eq":saved/1000,"conditional_added_drt_tco2eq":added/1000,
                      "conditional_net_reduction_tco2eq_negative_is_increase":net,
                      "minimum_car_substitution_distance_share":threshold(drt_kg_km/car_kg_km,e,d,n),
                      "status":"scenario arithmetic at one historical-year reference scale; not actual riders changing mode, not measured savings, not probabilistic forecast"})
assert forecasts[0]["conditional_net_reduction_tco2eq_negative_is_increase"]<0
assert forecasts[1]["conditional_net_reduction_tco2eq_negative_is_increase"]<0
assert forecasts[2]["conditional_net_reduction_tco2eq_negative_is_increase"]>0
with (OUT/"conditional_car_substitution_projection_NOT_EMPIRICAL.csv").open("w") as f:
    w=csv.DictWriter(f,fieldnames=list(forecasts[0]));w.writeheader();w.writerows(forecasts)
print(json.dumps(forecasts,ensure_ascii=False,indent=2))
