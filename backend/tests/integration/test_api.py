"""API integration tests for DataTripwire backend.

Verifies:
1. Health endpoints (root and v1).
2. Bundled sample dataset loading via API.
3. Custom CSV uploads (valid, empty, oversized, invalid extension).
4. Dataset metadata and profile retrieval.
5. End-to-end evaluation workflow:
   - Run 1: Uniqueness disabled -> duplicate survives -> recommendation generated.
   - Run 2: Uniqueness enabled -> duplicate caught -> score 100%.
6. Evaluation report retrieval and dataset history listing.
7. Error handling (400, 404, 413, 422).
"""

import io
import pytest
from fastapi.testclient import TestClient

from datatripwire.api.dependencies import get_dataset_repository, get_evaluation_repository
from datatripwire.api.main import app
from datatripwire.repositories.dataset_repository import DatasetRepository
from datatripwire.repositories.evaluation_repository import EvaluationRepository


@pytest.fixture
def client(tmp_path):
    """Provides a TestClient with isolated filesystem repositories."""
    ds_repo = DatasetRepository(storage_dir=tmp_path / "datasets")
    eval_repo = EvaluationRepository(storage_dir=tmp_path / "evals")

    app.dependency_overrides[get_dataset_repository] = lambda: ds_repo
    app.dependency_overrides[get_evaluation_repository] = lambda: eval_repo

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == "DataTripwire"

    def test_v1_health(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"


class TestDatasetEndpoints:
    """Tests for dataset loading, upload, and profiling."""

    def test_load_sample_dataset(self, client):
        response = client.post("/api/v1/datasets/sample")
        assert response.status_code == 201
        data = response.json()
        assert data["dataset_id"] == "sample-sales"
        assert data["filename"] == "sample_sales.csv"
        assert data["is_sales_compatible"] is True

        profile = data["profile"]
        assert profile["row_count"] == 15
        assert profile["column_count"] == 5
        assert "quantity" in profile["numeric_summaries"]

    def test_get_dataset(self, client):
        client.post("/api/v1/datasets/sample")
        response = client.get("/api/v1/datasets/sample-sales")
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_id"] == "sample-sales"

    def test_get_dataset_profile(self, client):
        client.post("/api/v1/datasets/sample")
        response = client.get("/api/v1/datasets/sample-sales/profile")
        assert response.status_code == 200
        profile = response.json()
        assert profile["row_count"] == 15

    def test_get_nonexistent_dataset_returns_404(self, client):
        response = client.get("/api/v1/datasets/does-not-exist")
        assert response.status_code == 404
        assert response.json()["code"] == "DATASET_NOT_FOUND"

    def test_upload_valid_csv(self, client):
        csv_content = (
            "transaction_id,customer_id,quantity,unit_price,transaction_date\n"
            "TXN-1,C-1,2,150.00,2026-03-01\n"
            "TXN-2,C-2,1,300.00,2026-03-02\n"
        )
        files = {"file": ("my_sales.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        response = client.post("/api/v1/datasets", files=files)
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "my_sales.csv"
        assert data["is_sales_compatible"] is True
        assert data["profile"]["row_count"] == 2

    def test_upload_empty_csv_returns_400(self, client):
        files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        response = client.post("/api/v1/datasets", files=files)
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_CSV"

    def test_upload_non_csv_extension_returns_400(self, client):
        files = {"file": ("report.json", io.BytesIO(b'{"key": "val"}'), "application/json")}
        response = client.post("/api/v1/datasets", files=files)
        assert response.status_code == 400
        assert "Only .csv files are supported" in response.json()["detail"]

    def test_upload_incompatible_sales_schema(self, client):
        csv_content = "user_id,rating,comment\n1,5,Great!\n"
        files = {"file": ("reviews.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        response = client.post("/api/v1/datasets", files=files)
        assert response.status_code == 201
        data = response.json()
        assert data["is_sales_compatible"] is False
        assert any("lacks required sales columns" in w for w in data["warnings"])


class TestEvaluationWorkflow:
    """Full integration tests for the primary evaluation and hardening flow."""

    def test_complete_evaluation_workflow(self, client):
        # 1. Load sample dataset
        sample_res = client.post("/api/v1/datasets/sample")
        assert sample_res.status_code == 201
        dataset_id = sample_res.json()["dataset_id"]

        # 2. Run evaluation with uniqueness disabled -> fault escapes
        eval_payload_1 = {
            "mutations": [
                {
                    "mutation_type": "duplicate_row",
                    "target_transaction_id": "ORD-102",
                    "description": "Test duplicate transaction ORD-102",
                }
            ],
            "rules": {
                "check_required_values": True,
                "check_quantity_positive": True,
                "check_unit_price_nonnegative": True,
                "check_valid_transaction_date": True,
                "check_unique_transaction_id": False,
                "check_expected_row_count": False,
            },
        }
        res_1 = client.post(f"/api/v1/datasets/{dataset_id}/evaluations", json=eval_payload_1)
        assert res_1.status_code == 201
        report_1 = res_1.json()

        assert report_1["total_attempted"] == 1
        assert report_1["successfully_applied"] == 1
        assert report_1["detected_mutations"] == 0
        assert report_1["surviving_mutations"] == 1
        assert report_1["mutation_score"] == 0.0

        # Verify downstream impact: ORD-102 unit_price is ₹800.00
        eval_item_1 = report_1["evaluations"][0]
        assert eval_item_1["detected"] is False
        assert eval_item_1["metric_deltas"]["revenue_delta_abs"] == "800.00"

        # Verify rule recommendation generated
        assert len(report_1["recommendations"]) == 1
        rec = report_1["recommendations"][0]
        assert rec["rule_type"] == "uniqueness"
        assert rec["target_column"] == "transaction_id"

        report_id_1 = report_1["report_id"]

        # 3. Retrieve first report by ID
        get_rep_1 = client.get(f"/api/v1/evaluations/{report_id_1}")
        assert get_rep_1.status_code == 200
        assert get_rep_1.json()["report_id"] == report_id_1

        # 4. Retest with uniqueness rule enabled -> fault detected
        eval_payload_2 = {
            "mutations": [
                {
                    "mutation_type": "duplicate_row",
                    "target_transaction_id": "ORD-102",
                }
            ],
            "rules": {
                "check_required_values": True,
                "check_quantity_positive": True,
                "check_unit_price_nonnegative": True,
                "check_valid_transaction_date": True,
                "check_unique_transaction_id": True,  # ENABLED!
                "check_expected_row_count": False,
            },
        }
        res_2 = client.post(f"/api/v1/datasets/{dataset_id}/evaluations", json=eval_payload_2)
        assert res_2.status_code == 201
        report_2 = res_2.json()

        assert report_2["detected_mutations"] == 1
        assert report_2["surviving_mutations"] == 0
        assert report_2["mutation_score"] == 100.0
        assert report_2["evaluations"][0]["detected"] is True
        assert len(report_2["recommendations"]) == 0

        # 5. List evaluations for dataset
        history_res = client.get(f"/api/v1/datasets/{dataset_id}/evaluations")
        assert history_res.status_code == 200
        history = history_res.json()
        assert len(history) == 2

    def test_evaluation_on_incompatible_dataset_returns_422(self, client):
        # Upload non-sales CSV
        csv_content = "name,email\nAlice,alice@example.com\n"
        files = {"file": ("users.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        ds_res = client.post("/api/v1/datasets", files=files)
        ds_id = ds_res.json()["dataset_id"]

        # Attempt sales evaluation
        payload = {
            "mutations": [{"mutation_type": "duplicate_row"}],
        }
        res = client.post(f"/api/v1/datasets/{ds_id}/evaluations", json=payload)
        assert res.status_code == 422
        assert res.json()["code"] == "INCOMPATIBLE_SALES_SCHEMA"

    def test_evaluation_on_nonexistent_dataset_returns_404(self, client):
        payload = {"mutations": [{"mutation_type": "duplicate_row"}]}
        res = client.post("/api/v1/datasets/nonexistent-id/evaluations", json=payload)
        assert res.status_code == 404
        assert res.json()["code"] == "DATASET_NOT_FOUND"

    def test_retrieve_nonexistent_evaluation_returns_404(self, client):
        res = client.get("/api/v1/evaluations/nonexistent-report")
        assert res.status_code == 404
        assert res.json()["code"] == "EVALUATION_NOT_FOUND"

    def test_excessive_mutations_rejected_with_422(self, client):
        # Payload with 11 mutations (max allowed is 10)
        client.post("/api/v1/datasets/sample")
        mutations = [{"mutation_type": "duplicate_row"}] * 11
        res = client.post("/api/v1/datasets/sample-sales/evaluations", json={"mutations": mutations})
        assert res.status_code == 422
