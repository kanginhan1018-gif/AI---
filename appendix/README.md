# 분석 부록 안내

제출 기준은 [본문 PDF](../outputs/reports/망젤이네_분석보고서.pdf)입니다. 부록은 별도 열람 자료이며 본문과 합친 제출 파일이 아닙니다.

- [분석 부록 PDF](research_appendix.pdf): A1~A14, 15쪽
- [편집 가능한 부록 원문](분석부록.md)
- [파일별 역할·실행 코드·SHA-256 인덱스](evidence_index.csv)

관측 결과, 미검증 계획 가정, 설명용 탄소 시나리오를 구분합니다. 0.95톤은 정책의 예상 감축량이 아닙니다. 원자료와 개인 식별정보는 포함하지 않았습니다.

## A2 원자료 선별

자료 성격: 관측 집계. 관련 코드: 10·12·15번.

- [outputs/tables/public_service_necessity/purpose_burden_annual.csv](../outputs/tables/public_service_necessity/purpose_burden_annual.csv)
- [outputs/tables/public_service_necessity/purpose_burden_monthly.csv](../outputs/tables/public_service_necessity/purpose_burden_monthly.csv)
- [outputs/tables/public_service_necessity/purpose_label_audit.csv](../outputs/tables/public_service_necessity/purpose_label_audit.csv)
- [outputs/tables/public_service_necessity/analysis_manifest.json](../outputs/tables/public_service_necessity/analysis_manifest.json)
- [outputs/tables/seoul_drt_policy/treatment_timeband_burden.csv](../outputs/tables/seoul_drt_policy/treatment_timeband_burden.csv)

## A3 추가 검증

자료 성격: 조건별 기술 비교. 관련 코드: 22번.

- [outputs/tables/treatment_robustness/sensitivity_checks.csv](../outputs/tables/treatment_robustness/sensitivity_checks.csv)
- [outputs/tables/treatment_robustness/independent_weekpart_check.json](../outputs/tables/treatment_robustness/independent_weekpart_check.json)
- [outputs/tables/treatment_robustness/scope.json](../outputs/tables/treatment_robustness/scope.json)

## A4 비용

자료 성격: 미검증 계획 가정·과거 비교값. 관련 코드: 13·16번.

- [outputs/tables/vehicle_budget_screen/assumptions.json](../outputs/tables/vehicle_budget_screen/assumptions.json)
- [outputs/tables/vehicle_budget_screen/budget_scenarios.csv](../outputs/tables/vehicle_budget_screen/budget_scenarios.csv)
- [outputs/tables/vehicle_budget_screen/supplemental_service_capacity_scenarios.csv](../outputs/tables/vehicle_budget_screen/supplemental_service_capacity_scenarios.csv)
- [outputs/tables/seoul_cost_verification/central_case.csv](../outputs/tables/seoul_cost_verification/central_case.csv)
- [outputs/tables/seoul_cost_verification/scenario_grid.csv](../outputs/tables/seoul_cost_verification/scenario_grid.csv)
- [outputs/tables/seoul_cost_verification/verification_manifest.json](../outputs/tables/seoul_cost_verification/verification_manifest.json)
- [data/raw/drt_cost_evidence/seoul_2025_budget_review.pdf](../data/raw/drt_cost_evidence/seoul_2025_budget_review.pdf)
- [data/raw/drt_cost_evidence/seoul_bus_2024_settlement.pdf](../data/raw/drt_cost_evidence/seoul_bus_2024_settlement.pdf)

## A5 예산·정책 검증

자료 성격: 제출 예산안·공식 전체 평균·조건부 계산. 관련 코드: 24·공식 문서번.

- [outputs/tables/policy_environment_verification/official_citywide_outcomes.csv](../outputs/tables/policy_environment_verification/official_citywide_outcomes.csv)
- [outputs/tables/policy_environment_verification/official_outcome_scope.json](../outputs/tables/policy_environment_verification/official_outcome_scope.json)
- [outputs/tables/policy_environment_verification/dispatch_shortening_CONDITIONAL.csv](../outputs/tables/policy_environment_verification/dispatch_shortening_CONDITIONAL.csv)
- [outputs/tables/policy_environment_verification/dispatch_only_boundary.json](../outputs/tables/policy_environment_verification/dispatch_only_boundary.json)
- [outputs/tables/policy_environment_verification/independent_10min_check.json](../outputs/tables/policy_environment_verification/independent_10min_check.json)
- [outputs/tables/policy_environment_verification/verification_status.json](../outputs/tables/policy_environment_verification/verification_status.json)
- [outputs/tables/seoul_budget_feasibility/budget_scale_scenarios.csv](../outputs/tables/seoul_budget_feasibility/budget_scale_scenarios.csv)
- [outputs/tables/seoul_budget_feasibility/assessment_manifest.json](../outputs/tables/seoul_budget_feasibility/assessment_manifest.json)
- [data/raw/drt_cost_evidence/seoul_2026_transport_budget_proposal.pdf](../data/raw/drt_cost_evidence/seoul_2026_transport_budget_proposal.pdf)
- [data/raw/drt_cost_evidence/seoul_2026_february_transport_workplan.pdf](../data/raw/drt_cost_evidence/seoul_2026_february_transport_workplan.pdf)

## A6 탄소 관측 자료

자료 성격: 관측 거리·결측과 해석. 관련 코드: 19번.

- [outputs/tables/carbon_audit/distance_audit.csv](../outputs/tables/carbon_audit/distance_audit.csv)
- [outputs/tables/carbon_audit/monthly_recorded_distance.csv](../outputs/tables/carbon_audit/monthly_recorded_distance.csv)
- [outputs/tables/carbon_audit/field_availability.csv](../outputs/tables/carbon_audit/field_availability.csv)
- [outputs/tables/carbon_audit/independent_distance_check.json](../outputs/tables/carbon_audit/independent_distance_check.json)
- [outputs/tables/carbon_audit/carbon_identification_audit.json](../outputs/tables/carbon_audit/carbon_identification_audit.json)

## A7 탄소 보조 시나리오

자료 성격: 가정 계산·실측 아님. 관련 코드: 20·21번.

- [outputs/tables/carbon_audit/assumption_evidence_register.csv](../outputs/tables/carbon_audit/assumption_evidence_register.csv)
- [outputs/tables/carbon_audit/conditional_car_substitution_projection_NOT_EMPIRICAL.csv](../outputs/tables/carbon_audit/conditional_car_substitution_projection_NOT_EMPIRICAL.csv)
- [outputs/tables/carbon_audit/private_car_substitution_break_even_ASSUMPTIONS.csv](../outputs/tables/carbon_audit/private_car_substitution_break_even_ASSUMPTIONS.csv)
- [examples/carbon/README.md](../examples/carbon/README.md)
- [examples/carbon/scenario_inputs.csv](../examples/carbon/scenario_inputs.csv)
- [examples/carbon/operational_measurement_template.csv](../examples/carbon/operational_measurement_template.csv)
- [examples/carbon/illustrative_factors.json](../examples/carbon/illustrative_factors.json)
- [outputs/tables/carbon_measurement_demo/carbon_measurements.json](../outputs/tables/carbon_measurement_demo/carbon_measurements.json)

## A9 서울 비교와 위험 모형

자료 성격: 관측 비교·후향적 예측 검증. 관련 코드: 25번.

- [notebooks/25_citywide_predictive_validation.py](../notebooks/25_citywide_predictive_validation.py)
- [outputs/tables/citywide_predictive_validation/citywide_same_cohort.csv](../outputs/tables/citywide_predictive_validation/citywide_same_cohort.csv)
- [outputs/tables/citywide_predictive_validation/retrospective_temporal_metrics.csv](../outputs/tables/citywide_predictive_validation/retrospective_temporal_metrics.csv)
- [outputs/tables/citywide_predictive_validation/logistic_calibration.csv](../outputs/tables/citywide_predictive_validation/logistic_calibration.csv)
- [outputs/tables/citywide_predictive_validation/subgroup_metrics.csv](../outputs/tables/citywide_predictive_validation/subgroup_metrics.csv)
- [outputs/tables/citywide_predictive_validation/validation_scope.json](../outputs/tables/citywide_predictive_validation/validation_scope.json)

## A11 OD·버스 노선 연결

자료 성격: 통신 통행 평균·대표정류장·노선ID 화면검사. 관련 코드: 30·31번.

- [notebooks/30_transit_corridor_overlay.py](../notebooks/30_transit_corridor_overlay.py)
- [notebooks/31_build_transit_corridor_report.py](../notebooks/31_build_transit_corridor_report.py)
- [docs/2026-10-19-transit-corridor-overlay.md](../docs/2026-10-19-transit-corridor-overlay.md)
- [outputs/reports/망젤이네_서울_OD_버스연결_검토.pdf](../outputs/reports/망젤이네_서울_OD_버스연결_검토.pdf)
- [outputs/tables/open_pooling_verification/pilot_morning_OD_INPUT.csv](../outputs/tables/open_pooling_verification/pilot_morning_OD_INPUT.csv)
- [outputs/tables/open_pooling_verification/pilot_morning_OD_bus_overlay.csv](../outputs/tables/open_pooling_verification/pilot_morning_OD_bus_overlay.csv)
- [outputs/tables/open_pooling_verification/pilot_candidate_OD_no_shared_representative_route.csv](../outputs/tables/open_pooling_verification/pilot_candidate_OD_no_shared_representative_route.csv)
- [outputs/tables/open_pooling_verification/pilot_OD_bus_connectivity_screen_summary.csv](../outputs/tables/open_pooling_verification/pilot_OD_bus_connectivity_screen_summary.csv)
- [outputs/tables/open_pooling_verification/pilot_OD_bus_distance_screen.csv](../outputs/tables/open_pooling_verification/pilot_OD_bus_distance_screen.csv)
- [outputs/tables/open_pooling_verification/pilot_dong_representative_bus_supply.csv](../outputs/tables/open_pooling_verification/pilot_dong_representative_bus_supply.csv)
- [outputs/tables/open_pooling_verification/transit_overlay_scope.json](../outputs/tables/open_pooling_verification/transit_overlay_scope.json)
- [outputs/tables/telecom_12weeks/official_pilot_codes.csv](../outputs/tables/telecom_12weeks/official_pilot_codes.csv)
- [outputs/tables/telecom_12weeks/source_manifest.json](../outputs/tables/telecom_12weeks/source_manifest.json)
- [outputs/tables/telecom_12weeks/project_code_crosswalk_review.csv](../outputs/tables/telecom_12weeks/project_code_crosswalk_review.csv)
- [data/raw/telecom/admdong_codes.zip](../data/raw/telecom/admdong_codes.zip)
- [data/raw/headway_11010.csv](../data/raw/headway_11010.csv)
- [data/raw/dong_centroids_11010.csv](../data/raw/dong_centroids_11010.csv)
- [data/raw/dong_walk_input_11010.csv](../data/raw/dong_walk_input_11010.csv)
- [data/raw/headway_11020.csv](../data/raw/headway_11020.csv)
- [data/raw/dong_centroids_11020.csv](../data/raw/dong_centroids_11020.csv)
- [data/raw/dong_walk_input_11020.csv](../data/raw/dong_walk_input_11020.csv)
- [data/raw/headway_11030.csv](../data/raw/headway_11030.csv)
- [data/raw/dong_centroids_11030.csv](../data/raw/dong_centroids_11030.csv)
- [data/raw/dong_walk_input_11030.csv](../data/raw/dong_walk_input_11030.csv)
- [data/raw/headway_11040.csv](../data/raw/headway_11040.csv)
- [data/raw/dong_centroids_11040.csv](../data/raw/dong_centroids_11040.csv)
- [data/raw/dong_walk_input_11040.csv](../data/raw/dong_walk_input_11040.csv)
- [data/raw/headway_11050.csv](../data/raw/headway_11050.csv)
- [data/raw/dong_centroids_11050.csv](../data/raw/dong_centroids_11050.csv)
- [data/raw/dong_walk_input_11050.csv](../data/raw/dong_walk_input_11050.csv)
- [data/raw/headway_11060.csv](../data/raw/headway_11060.csv)
- [data/raw/dong_centroids_11060.csv](../data/raw/dong_centroids_11060.csv)
- [data/raw/dong_walk_input_11060.csv](../data/raw/dong_walk_input_11060.csv)
- [data/raw/headway_11070.csv](../data/raw/headway_11070.csv)
- [data/raw/dong_centroids_11070.csv](../data/raw/dong_centroids_11070.csv)
- [data/raw/dong_walk_input_11070.csv](../data/raw/dong_walk_input_11070.csv)
- [data/raw/headway_11080.csv](../data/raw/headway_11080.csv)
- [data/raw/dong_centroids_11080.csv](../data/raw/dong_centroids_11080.csv)
- [data/raw/dong_walk_input_11080.csv](../data/raw/dong_walk_input_11080.csv)
- [data/raw/headway_11090.csv](../data/raw/headway_11090.csv)
- [data/raw/dong_centroids_11090.csv](../data/raw/dong_centroids_11090.csv)
- [data/raw/dong_walk_input_11090.csv](../data/raw/dong_walk_input_11090.csv)
- [data/raw/headway_11100.csv](../data/raw/headway_11100.csv)
- [data/raw/dong_centroids_11100.csv](../data/raw/dong_centroids_11100.csv)
- [data/raw/dong_walk_input_11100.csv](../data/raw/dong_walk_input_11100.csv)
- [data/raw/headway_11110.csv](../data/raw/headway_11110.csv)
- [data/raw/dong_centroids_11110.csv](../data/raw/dong_centroids_11110.csv)
- [data/raw/dong_walk_input_11110.csv](../data/raw/dong_walk_input_11110.csv)
- [data/raw/headway_11120.csv](../data/raw/headway_11120.csv)
- [data/raw/dong_centroids_11120.csv](../data/raw/dong_centroids_11120.csv)
- [data/raw/dong_walk_input_11120.csv](../data/raw/dong_walk_input_11120.csv)
- [data/raw/headway_11130.csv](../data/raw/headway_11130.csv)
- [data/raw/dong_centroids_11130.csv](../data/raw/dong_centroids_11130.csv)
- [data/raw/dong_walk_input_11130.csv](../data/raw/dong_walk_input_11130.csv)
- [data/raw/headway_11140.csv](../data/raw/headway_11140.csv)
- [data/raw/dong_centroids_11140.csv](../data/raw/dong_centroids_11140.csv)
- [data/raw/dong_walk_input_11140.csv](../data/raw/dong_walk_input_11140.csv)
- [data/raw/headway_11150.csv](../data/raw/headway_11150.csv)
- [data/raw/dong_centroids_11150.csv](../data/raw/dong_centroids_11150.csv)
- [data/raw/dong_walk_input_11150.csv](../data/raw/dong_walk_input_11150.csv)
- [data/raw/headway_11160.csv](../data/raw/headway_11160.csv)
- [data/raw/dong_centroids_11160.csv](../data/raw/dong_centroids_11160.csv)
- [data/raw/dong_walk_input_11160.csv](../data/raw/dong_walk_input_11160.csv)
- [data/raw/headway_11170.csv](../data/raw/headway_11170.csv)
- [data/raw/dong_centroids_11170.csv](../data/raw/dong_centroids_11170.csv)
- [data/raw/dong_walk_input_11170.csv](../data/raw/dong_walk_input_11170.csv)
- [data/raw/headway_11180.csv](../data/raw/headway_11180.csv)
- [data/raw/dong_centroids_11180.csv](../data/raw/dong_centroids_11180.csv)
- [data/raw/dong_walk_input_11180.csv](../data/raw/dong_walk_input_11180.csv)
- [data/raw/headway_11190.csv](../data/raw/headway_11190.csv)
- [data/raw/dong_centroids_11190.csv](../data/raw/dong_centroids_11190.csv)
- [data/raw/dong_walk_input_11190.csv](../data/raw/dong_walk_input_11190.csv)
- [data/raw/headway_11200.csv](../data/raw/headway_11200.csv)
- [data/raw/dong_centroids_11200.csv](../data/raw/dong_centroids_11200.csv)
- [data/raw/dong_walk_input_11200.csv](../data/raw/dong_walk_input_11200.csv)
- [data/raw/headway_11210.csv](../data/raw/headway_11210.csv)
- [data/raw/dong_centroids_11210.csv](../data/raw/dong_centroids_11210.csv)
- [data/raw/dong_walk_input_11210.csv](../data/raw/dong_walk_input_11210.csv)
- [data/raw/headway_11220.csv](../data/raw/headway_11220.csv)
- [data/raw/dong_centroids_11220.csv](../data/raw/dong_centroids_11220.csv)
- [data/raw/dong_walk_input_11220.csv](../data/raw/dong_walk_input_11220.csv)
- [data/raw/headway_11230.csv](../data/raw/headway_11230.csv)
- [data/raw/dong_centroids_11230.csv](../data/raw/dong_centroids_11230.csv)
- [data/raw/dong_walk_input_11230.csv](../data/raw/dong_walk_input_11230.csv)
- [data/raw/headway_11240.csv](../data/raw/headway_11240.csv)
- [data/raw/dong_centroids_11240.csv](../data/raw/dong_centroids_11240.csv)
- [data/raw/dong_walk_input_11240.csv](../data/raw/dong_walk_input_11240.csv)
- [data/raw/headway_11250.csv](../data/raw/headway_11250.csv)
- [data/raw/dong_centroids_11250.csv](../data/raw/dong_centroids_11250.csv)
- [data/raw/dong_walk_input_11250.csv](../data/raw/dong_walk_input_11250.csv)

## A12 장거리 OD와 실제 버스 노선 순번 검증

자료 성격: 정적 버스망의 최소 환승 수 전수 선별. 관련 코드: 34·35번.

- [notebooks/34_exhaustive_bus_transfer_screen.py](../notebooks/34_exhaustive_bus_transfer_screen.py)
- [notebooks/35_minimum_bus_transfers_all_OD.py](../notebooks/35_minimum_bus_transfers_all_OD.py)
- [outputs/tables/non_drt_policy_comparison/all_15012_OD_bus_0_1_transfer_screen.csv](../outputs/tables/non_drt_policy_comparison/all_15012_OD_bus_0_1_transfer_screen.csv)
- [outputs/tables/non_drt_policy_comparison/all_15012_OD_bus_path_class_summary.csv](../outputs/tables/non_drt_policy_comparison/all_15012_OD_bus_path_class_summary.csv)
- [outputs/tables/non_drt_policy_comparison/all_15012_OD_minimum_bus_transfers.csv](../outputs/tables/non_drt_policy_comparison/all_15012_OD_minimum_bus_transfers.csv)
- [outputs/tables/non_drt_policy_comparison/all_15012_OD_minimum_bus_transfers_summary.csv](../outputs/tables/non_drt_policy_comparison/all_15012_OD_minimum_bus_transfers_summary.csv)
- [outputs/tables/non_drt_policy_comparison/all_15012_OD_minimum_bus_transfers_scope.json](../outputs/tables/non_drt_policy_comparison/all_15012_OD_minimum_bus_transfers_scope.json)
- [data/raw/bus_routes_seoul_20260902.xlsx](../data/raw/bus_routes_seoul_20260902.xlsx)

## A13 서울 버스·철도 접근 공백 후보

자료 성격: 427개 행정동 중심점의 버스·철도 직선거리 보조 선별. 관련 코드: 37번.

- [notebooks/37_seoul_bus_stop_desert_screen.py](../notebooks/37_seoul_bus_stop_desert_screen.py)
- [docs/2026-10-19-seoul-transit-access-gap-screen.md](../docs/2026-10-19-seoul-transit-access-gap-screen.md)
- [outputs/tables/non_drt_policy_comparison/seoul_dong_bus_stop_sparse_screen.csv](../outputs/tables/non_drt_policy_comparison/seoul_dong_bus_stop_sparse_screen.csv)
- [outputs/tables/non_drt_policy_comparison/seoul_dong_bus_stop_sparse_summary.csv](../outputs/tables/non_drt_policy_comparison/seoul_dong_bus_stop_sparse_summary.csv)
- [data/raw/subway_station_coords_derived_20260630.csv](../data/raw/subway_station_coords_derived_20260630.csv)

## A14 AI 수요예측·공동배차 최적화 설계

자료 성격: 운영 설계안·효과 미실증. 관련 코드: 25·후속 실증번.

- [docs/2026-10-19-ai-dispatch-optimization-design.md](../docs/2026-10-19-ai-dispatch-optimization-design.md)

## A10 일반 이용형 공동승차 검증

자료 성격: 관측·조건부 계산·정책효과 미입증. 관련 코드: 26·27·28·29번.

- [notebooks/26_shared_destination_screen.py](../notebooks/26_shared_destination_screen.py)
- [notebooks/27_open_pooling_verification.py](../notebooks/27_open_pooling_verification.py)
- [notebooks/28_open_pooling_independent_check.py](../notebooks/28_open_pooling_independent_check.py)
- [notebooks/29_build_open_pooling_report.py](../notebooks/29_build_open_pooling_report.py)
- [docs/2026-10-19-open-pooling-verification.md](../docs/2026-10-19-open-pooling-verification.md)
- [outputs/tables/shared_destination_screen/coarse_cooccurrence_NOT_FEASIBLE_POOLING.csv](../outputs/tables/shared_destination_screen/coarse_cooccurrence_NOT_FEASIBLE_POOLING.csv)
- [outputs/tables/shared_destination_screen/scope.json](../outputs/tables/shared_destination_screen/scope.json)
- [outputs/tables/open_pooling_verification/service_cooccurrence.csv](../outputs/tables/open_pooling_verification/service_cooccurrence.csv)
- [outputs/tables/open_pooling_verification/general_population_top10_OD_NOT_DRT_DEMAND.csv](../outputs/tables/open_pooling_verification/general_population_top10_OD_NOT_DRT_DEMAND.csv)
- [outputs/tables/open_pooling_verification/general_population_OD_INPUT_ALL_ELIGIBLE.csv](../outputs/tables/open_pooling_verification/general_population_OD_INPUT_ALL_ELIGIBLE.csv)
- [outputs/tables/open_pooling_verification/conditional_unit_cost.csv](../outputs/tables/open_pooling_verification/conditional_unit_cost.csv)
- [outputs/tables/open_pooling_verification/cost_thresholds.json](../outputs/tables/open_pooling_verification/cost_thresholds.json)
- [outputs/tables/open_pooling_verification/vehicle_km_sensitivity_NOT_CONGESTION_IMPACT.csv](../outputs/tables/open_pooling_verification/vehicle_km_sensitivity_NOT_CONGESTION_IMPACT.csv)
- [outputs/tables/open_pooling_verification/verification_scope.json](../outputs/tables/open_pooling_verification/verification_scope.json)
- [outputs/tables/open_pooling_verification/independent_check.json](../outputs/tables/open_pooling_verification/independent_check.json)
- [outputs/reports/망젤이네_일반이용형_DRT_검증.pdf](../outputs/reports/망젤이네_일반이용형_DRT_검증.pdf)
- [data/raw/drt_cost_evidence/uk_rmf_phase1_evaluation_2025.pdf](../data/raw/drt_cost_evidence/uk_rmf_phase1_evaluation_2025.pdf)

## A8 재현 코드와 검사

자료 성격: 실행 코드·검사. 관련 코드: 18·21·23번.

- [notebooks/18_build_contest_submission.py](../notebooks/18_build_contest_submission.py)
- [notebooks/19_carbon_feasibility_audit.py](../notebooks/19_carbon_feasibility_audit.py)
- [notebooks/20_carbon_substitution_break_even.py](../notebooks/20_carbon_substitution_break_even.py)
- [notebooks/21_carbon_measurement.py](../notebooks/21_carbon_measurement.py)
- [notebooks/22_treatment_robustness.py](../notebooks/22_treatment_robustness.py)
- [notebooks/23_build_appendix.py](../notebooks/23_build_appendix.py)
- [notebooks/24_policy_environment_verification.py](../notebooks/24_policy_environment_verification.py)
- [tests/test_carbon_measurement.py](../tests/test_carbon_measurement.py)
