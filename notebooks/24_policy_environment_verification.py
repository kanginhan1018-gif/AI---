"""Verify official outcomes, conditional delay response, and environmental evidence gaps."""
from pathlib import Path
import hashlib
import json
import re
import runpy
import subprocess
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/tables/policy_environment_verification"
OUT.mkdir(parents=True,exist_ok=True)
PDF=ROOT/"data/raw/drt_cost_evidence/seoul_2026_february_transport_workplan.pdf"
text=subprocess.run(["pdftotext","-layout",str(PDF),"-"],check=True,capture_output=True).stdout.decode()
line=next(s for s in text.splitlines() if "33.8" in s and "40.8" in s and "대기시간" in s)
values={year:float(re.search(fr"{str(year)[-2:]}년\)\s*([0-9.]+)",line).group(1)) for year in [2023,2024,2025]}
assert values=={2023:47.0,2024:40.8,2025:33.8}
pd.DataFrame([{"year":y,"official_citywide_wait_minutes":v,"scope":"official administrative aggregate, not the selected treatment cohort or a causal estimate"} for y,v in values.items()]).to_csv(OUT/"official_citywide_outcomes.csv",index=False)
change={"2024_minutes":values[2024],"2025_minutes":values[2025],"difference_minutes":values[2025]-values[2024],"relative_decrease_pct":100*(values[2024]-values[2025])/values[2024],
        "source_pdf":str(PDF.relative_to(ROOT)),"source_sha256":hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "pdf_page":next(i for i,p in enumerate(text.split("\f"),1) if line in p),
        "policy_attribution_verified":False,"metric_comparability_to_our_cohort_verified":False}
(OUT/"official_outcome_scope.json").write_text(json.dumps(change,ensure_ascii=False,indent=2))


def shortened_wait(wait,queue,target,minutes):
    if not np.isfinite(minutes) or minutes<0:raise ValueError("Nonnegative finite shortening required")
    if (queue<0).any() or (wait<queue).any():raise ValueError("Invalid interval decomposition")
    return wait-np.where(target,np.minimum(queue,minutes),0)


sample=shortened_wait(np.array([70.,80.,50.]),np.array([15.,5.,5.]),np.array([True,True,False]),10)
assert np.array_equal(sample,np.array([60.,75.,50.]))
data=runpy.run_path(str(ROOT/"notebooks/22_treatment_robustness.py"))
main=data["main"]
target=main.weekday.lt(5)&main.scheduled_hour.between(7,9)
assert int(target.sum())==2992 and int((target&main.wait.gt(60)).sum())==1145
results=[]
for minutes in [0,5,10,15,20]:
    after=shortened_wait(main.wait,main.queue,target,minutes)
    assert (after>=0).all() and np.all(after[~target]==main.wait[~target])
    before_late=int(main.wait.gt(60).sum());after_late=int(after.gt(60).sum())
    results.append({"assumed_dispatch_queue_shortening_min":minutes,"affected_scope":"Mon-Fri including holidays, scheduled 07:00-09:59",
                    "target_records":int(target.sum()),"target_over60_before":1145,"target_over60_after_conditional":int(after[target].gt(60).sum()),
                    "target_over60_pct_after_conditional":100*after[target].gt(60).mean(),
                    "all_main_over60_before":before_late,"all_main_over60_after_conditional":after_late,
                    "over60_records_no_longer_over60_conditional":before_late-after_late,
                    "all_main_over60_pct_after_conditional":100*after.gt(60).mean(),"all_main_p90_after_conditional_min":float(after.quantile(.9)),
                    "interpretation":"Fixed-record arithmetic only, not observed effect or feasible fleet/queueing simulation"})
assert results[0]["all_main_over60_after_conditional"]==1374
assert all(a["all_main_over60_after_conditional"]>=b["all_main_over60_after_conditional"] for a,b in zip(results,results[1:]))
pd.DataFrame(results).to_csv(OUT/"dispatch_shortening_CONDITIONAL.csv",index=False)
unreachable=int((target&main.pickup.gt(60)).sum())
envelope={"target_over60_records":1145,"target_records_with_pickup_alone_over60":unreachable,
          "maximum_over60_records_fixable_by_zero_queue_mathematical_bound":1145-unreachable,
          "interpretation":"Zero queue is not an operationally feasible plan or a forecast"}
(OUT/"dispatch_only_boundary.json").write_text(json.dumps(envelope,ensure_ascii=False,indent=2))
carbon=pd.read_csv(ROOT/"outputs/tables/carbon_audit/conditional_car_substitution_projection_NOT_EMPIRICAL.csv")
assert carbon["conditional_net_reduction_tco2eq_negative_is_increase"].min()<0<carbon["conditional_net_reduction_tco2eq_negative_is_increase"].max()
status={"policy_causal_effect_verified":False,"official_citywide_change_verified":True,
        "conditional_policy_sensitivity_computed":True,"environmental_causal_reduction_verified":False,
        "positive_environmental_result_robust_across_three_illustrations":False,
        "actual_policy_effect_minutes":None,"actual_carbon_reduction_tonnes":None,
        "missing_for_policy_effect":["actual intervention dates and exposure","post-intervention comparable records","valid comparison group","support requirements and full requests incl unserved"],
        "missing_for_environment":["actual total/deadhead distance and energy by comparison scope","verified substitution or complete prior-service baseline","consistent verified emissions factors","post-intervention service equivalence"],
        "source_year":2025,"workplan_year":2026,
        "decision":"Reported citywide change confirmed; our proposed policy effect and net carbon benefit are not identified. Conditional arithmetic is supplementary evidence only."}
(OUT/"verification_status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2))
print(pd.DataFrame(results).to_string(index=False))
print(json.dumps(change,ensure_ascii=False))
print(json.dumps(envelope,ensure_ascii=False))
