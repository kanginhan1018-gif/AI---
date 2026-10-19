"""Checks for accounting signs, units, missing evidence and double counting."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("carbon_measurement", ROOT / "notebooks/21_carbon_measurement.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CarbonMeasurementTests(unittest.TestCase):
    def setUp(self):
        with (ROOT / "examples/carbon/scenario_inputs.csv").open() as stream:
            self.rows = list(csv.DictReader(stream))
        self.factors = json.loads((ROOT / "examples/carbon/illustrative_factors.json").read_text())

    def test_reproduces_all_prior_scenarios_and_occupancy(self):
        expected = [-14.2710947225, -3.739693227083334, .9485705285]
        for row, value, occupancy in zip(self.rows, expected, [1, 2, 3]):
            result = module.calculate(row, self.factors, "scenario")
            self.assertAlmostEqual(result["net_reduction_tco2eq_negative_is_increase"], value)
            self.assertAlmostEqual(result["distance_weighted_target_occupancy"], occupancy)
            self.assertFalse(result["causal_reduction_verified"])

    def test_rejects_nonfinite_negative_and_inconsistent_distances(self):
        for field, value in [("drt_energy_amount", "nan"), ("drt_empty_vehicle_km", "-1"),
                             ("car_replaced_reference_km", "999999"), ("drt_loaded_vehicle_km", "0")]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                module.calculate(dict(self.rows[0], **{field: value}), self.factors, "scenario")

    def test_rejects_energy_unit_mismatch(self):
        with self.assertRaises(ValueError):
            module.calculate(dict(self.rows[0], drt_energy_unit="kWh"), self.factors, "scenario")

    def test_operational_requires_evidence_but_does_not_certify_causality(self):
        with self.assertRaises(ValueError):
            module.calculate(self.rows[0], self.factors, "operational")
        row = dict(self.rows[0], substitution_evidence_ref="operator-reviewed counterfactual",
                   baseline_energy_evidence_ref="baseline allocation document", drt_energy_evidence_ref="receipts")
        self.assertFalse(module.calculate(row, self.factors, "operational")["causal_reduction_verified"])

    def test_empty_template_is_not_zero_emissions(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
            module.run(ROOT / "examples/carbon/operational_measurement_template.csv",
                       ROOT / "examples/carbon/illustrative_factors.json", tmp, "operational")

    def test_duplicate_measurements_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.csv"
            with path.open("w") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(self.rows[0]))
                writer.writeheader()
                writer.writerows([self.rows[0], self.rows[0]])
            with self.assertRaises(ValueError):
                module.run(path, ROOT / "examples/carbon/illustrative_factors.json", Path(tmp) / "out", "scenario")


if __name__ == "__main__":
    unittest.main()
