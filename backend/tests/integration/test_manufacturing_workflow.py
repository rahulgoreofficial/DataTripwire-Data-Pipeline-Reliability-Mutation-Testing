"""Integration tests for the manufacturing workflow and multi-domain evaluation engine.

Tests end-to-end API ingestion, domain compatibility detection,
baseline fault escape, hardened detection, recommendations, and
the uploaded 5,040-row manufacturing telemetry dataset.
"""

import io
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from datatripwire.api.main import create_app
from datatripwire.config import settings, WORKSPACE_ROOT


@pytest.fixture
def client(tmp_path: Path):
    """TestClient configured with isolated runtime storage."""
    settings.runtime_data_dir = tmp_path
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


class TestManufacturingAPIWorkflow:
    """Verifies API endpoints with manufacturing datasets."""

    def test_domains_discovery_endpoint(self, client: TestClient):
        res = client.get("/api/v1/domains")
        assert res.status_code == 200
        domains = res.json()
        assert len(domains) >= 3
        domain_ids = [d["domain_id"] for d in domains]
        assert "sales" in domain_ids
        assert "manufacturing" in domain_ids
        assert "general" in domain_ids

    def test_load_sample_manufacturing_dataset(self, client: TestClient):
        res = client.post("/api/v1/datasets/sample-manufacturing")
        assert res.status_code == 201
        data = res.json()
        assert data["is_manufacturing_compatible"] is True
        assert data["is_sales_compatible"] is False
        assert data["detected_domain"] == "manufacturing"
        assert data["profile"]["row_count"] == 20
        assert data["profile"]["column_count"] == 18

    def test_dataset_domains_endpoint(self, client: TestClient):
        res = client.post("/api/v1/datasets/sample-manufacturing")
        dataset_id = res.json()["dataset_id"]

        dom_res = client.get(f"/api/v1/datasets/{dataset_id}/domains")
        assert dom_res.status_code == 200
        dom_data = dom_res.json()
        assert dom_data["detected_domain"] == "manufacturing"
        mfg_meta = next(d for d in dom_data["domains"] if d["domain_id"] == "manufacturing")
        assert mfg_meta["is_compatible"] is True

    def test_manufacturing_evaluation_survival_and_hardening_loop(self, client: TestClient):
        # 1. Ingest sample manufacturing dataset
        ingest_res = client.post("/api/v1/datasets/sample-manufacturing")
        assert ingest_res.status_code == 201
        dataset_id = ingest_res.json()["dataset_id"]

        # 2. Run evaluation with baseline safeguards (check_machine_timestamp_unique=False)
        baseline_eval_payload = {
            "mutations": [
                {
                    "mutation_type": "duplicate_sensor_reading",
                    "target_record_id": "RDG-02-0001",
                    "description": "Injected duplicate sensor reading RDG-02-0001",
                }
            ],
            "rules": {
                "check_machine_timestamp_unique": False,
                "check_reading_id_unique": False,
                "check_sensor_numeric": True,
            },
        }
        res_baseline = client.post(f"/api/v1/datasets/{dataset_id}/evaluations", json=baseline_eval_payload)
        assert res_baseline.status_code == 201
        report_baseline = res_baseline.json()

        assert report_baseline["total_attempted"] == 1
        assert report_baseline["successfully_applied"] == 1
        assert report_baseline["surviving_mutations"] == 1
        assert report_baseline["detected_mutations"] == 0
        assert report_baseline["mutation_score"] == 0.0

        # Verify recommendation is generated proposing uniqueness check
        assert len(report_baseline["recommendations"]) >= 1
        reco = report_baseline["recommendations"][0]
        assert reco["rule_type"] == "uniqueness"
        assert "check_machine_timestamp_unique" in reco["suggested_rule_config"]

        # 3. Retest with hardened uniqueness safeguard enabled
        hardened_eval_payload = {
            "mutations": [
                {
                    "mutation_type": "duplicate_sensor_reading",
                    "target_record_id": "RDG-02-0001",
                    "description": "Injected duplicate sensor reading RDG-02-0001",
                }
            ],
            "rules": {
                "check_machine_timestamp_unique": True,
                "check_reading_id_unique": True,
            },
        }
        res_hardened = client.post(f"/api/v1/datasets/{dataset_id}/evaluations", json=hardened_eval_payload)
        assert res_hardened.status_code == 201
        report_hardened = res_hardened.json()

        assert report_hardened["total_attempted"] == 1
        assert report_hardened["successfully_applied"] == 1
        assert report_hardened["detected_mutations"] == 1
        assert report_hardened["surviving_mutations"] == 0
        assert report_hardened["mutation_score"] == 100.0


class TestFull5040RowManufacturingDataset:
    """End-to-end verification against the uploaded 5,040-record manufacturing telemetry file."""

    def test_full_5040_row_manufacturing_workflow(self, client: TestClient):
        full_csv_path = WORKSPACE_ROOT / "data" / "runtime" / "datasets" / "ds-43cf8f39.csv"
        if not full_csv_path.is_file():
            pytest.skip("Full 5,040-row manufacturing file not present at expected path")

        with open(full_csv_path, "rb") as f:
            csv_bytes = f.read()

        # Step 1: Upload the manufacturing CSV
        files = {"file": ("datatripwire_manufacturing_iot_sensor_readings_5040.csv", io.BytesIO(csv_bytes), "text/csv")}
        res = client.post("/api/v1/datasets", files=files)
        assert res.status_code == 201
        data = res.json()
        dataset_id = data["dataset_id"]

        # Step 2: Confirm generic profiling succeeds
        assert data["profile"]["row_count"] == 5040
        assert data["profile"]["column_count"] == 18

        # Step 3: Confirm Manufacturing compatibility
        assert data["is_manufacturing_compatible"] is True
        assert data["detected_domain"] == "manufacturing"

        # Step 4: Confirm required fields are recognized
        for col in ["reading_id", "timestamp", "machine_id", "temperature_c", "vibration_mm_s"]:
            assert col in data["profile"]["column_names"]

        # Step 5 & 6: Inject duplicate sensor reading with baseline rules
        eval_payload_survive = {
            "mutations": [
                {
                    "mutation_type": "duplicate_sensor_reading",
                    "target_record_id": "RDG-01-0001",
                    "description": "Duplicate telemetry reading RDG-01-0001",
                }
            ],
            "rules": {
                "check_machine_timestamp_unique": False,
                "check_reading_id_unique": False,
            },
        }
        res_survive = client.post(f"/api/v1/datasets/{dataset_id}/evaluations", json=eval_payload_survive)
        assert res_survive.status_code == 201
        rep_survive = res_survive.json()

        # Step 7 & 8: Confirm mutation survives without uniqueness safeguard
        assert rep_survive["surviving_mutations"] == 1
        assert rep_survive["detected_mutations"] == 0

        # Step 9 & 10: Repeat with uniqueness safeguard enabled
        eval_payload_detect = {
            "mutations": [
                {
                    "mutation_type": "duplicate_sensor_reading",
                    "target_record_id": "RDG-01-0001",
                    "description": "Duplicate telemetry reading RDG-01-0001",
                }
            ],
            "rules": {
                "check_machine_timestamp_unique": True,
                "check_reading_id_unique": True,
            },
        }
        res_detect = client.post(f"/api/v1/datasets/{dataset_id}/evaluations", json=eval_payload_detect)
        assert res_detect.status_code == 201
        rep_detect = res_detect.json()

        # Step 11: Confirm relevant validation finding detects it
        assert rep_detect["detected_mutations"] == 1
        assert rep_detect["surviving_mutations"] == 0
        assert rep_detect["mutation_score"] == 100.0

        # Step 12: Compare metric changes
        eval_item = rep_detect["evaluations"][0]
        assert eval_item["metric_deltas"]["readings_delta"] == 1

        # Step 13: Immutability verification - Original dataset remains exactly 5040 rows
        ds_check = client.get(f"/api/v1/datasets/{dataset_id}")
        assert ds_check.status_code == 200
        assert ds_check.json()["profile"]["row_count"] == 5040
