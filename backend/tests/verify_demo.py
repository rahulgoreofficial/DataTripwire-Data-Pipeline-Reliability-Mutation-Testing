"""Section 28 End-to-End Demonstration Verification Script.

Executes and verifies steps 1 through 14 against real backend services and files.
"""

from decimal import Decimal
from fastapi.testclient import TestClient

from datatripwire.api.main import app


def run_e2e_demonstration():
    print("=== STARTING DATATRIPWIRE SECTION 28 END-TO-END DEMONSTRATION ===")
    client = TestClient(app)

    # STEP 1: Load the actual bundled sample dataset
    print("\n[STEP 1] Loading bundled sample dataset...")
    res = client.post("/api/v1/datasets/sample")
    assert res.status_code == 201, f"Failed to load sample dataset: {res.text}"
    sample_data = res.json()
    dataset_id = sample_data["dataset_id"]
    print(f"-> Dataset loaded with ID: '{dataset_id}', filename: '{sample_data['filename']}'")

    # STEP 2: Retrieve its dataset profile and calculated business metrics
    print("\n[STEP 2] Retrieving dataset profile and verifying baseline metrics...")
    profile_res = client.get(f"/api/v1/datasets/{dataset_id}/profile")
    assert profile_res.status_code == 200
    profile = profile_res.json()
    assert profile["row_count"] == 15, f"Expected 15 rows, got {profile['row_count']}"
    assert profile["column_count"] == 5
    assert profile["is_sales_compatible"] is True
    print(f"-> Profile verified: {profile['row_count']} rows, {profile['column_count']} columns, sales_compatible={profile['is_sales_compatible']}")

    # STEP 3: Create an evaluation with uniqueness validation disabled
    # Request a duplicate-row mutation targeting existing unique transaction ORD-102
    print("\n[STEP 3] Creating evaluation with uniqueness validation DISABLED (Baseline)...")
    eval_payload_1 = {
        "mutations": [
            {
                "mutation_type": "duplicate_row",
                "target_transaction_id": "ORD-102",
                "description": "Controlled duplication of transaction ORD-102",
            }
        ],
        "rules": {
            "check_required_values": True,
            "check_quantity_positive": True,
            "check_unit_price_nonnegative": True,
            "check_valid_transaction_date": True,
            "check_unique_transaction_id": False,  # DISABLED
            "check_expected_row_count": False,
        },
    }
    eval_res_1 = client.post(f"/api/v1/datasets/{dataset_id}/evaluations", json=eval_payload_1)
    assert eval_res_1.status_code == 201, f"Evaluation 1 failed: {eval_res_1.text}"
    report_1 = eval_res_1.json()
    eval_1 = report_1["evaluations"][0]

    # STEP 4: Verify that the backend actually duplicates the selected row
    print("\n[STEP 4] Verifying backend actually duplicated the row...")
    assert eval_1["applied"] is True
    mutated_metrics_1 = eval_1["mutated_metrics"]
    baseline_metrics_1 = eval_1["baseline_metrics"]
    assert mutated_metrics_1["transaction_count"] == baseline_metrics_1["transaction_count"] + 1
    print(f"-> Mutated transaction count: {mutated_metrics_1['transaction_count']} (Baseline: {baseline_metrics_1['transaction_count']})")

    # STEP 5: Verify that the backend recalculates revenue and transaction count from mutated dataset
    print("\n[STEP 5] Verifying recalculated revenue and transaction count...")
    # Baseline was ₹19,000.00; ORD-102 is 1 qty * ₹800 = ₹800.00; Mutated should be ₹19,800.00
    assert mutated_metrics_1["total_revenue"] == "19800.00"
    assert eval_1["metric_deltas"]["revenue_delta_abs"] == "800.00"
    assert eval_1["metric_deltas"]["transaction_count_delta"] == 1
    print(f"-> Baseline revenue: INR {baseline_metrics_1['total_revenue']} -> Mutated revenue: INR {mutated_metrics_1['total_revenue']} (Delta: +INR {eval_1['metric_deltas']['revenue_delta_abs']})")

    # STEP 6: Verify that no relevant duplicate-validation finding exists
    print("\n[STEP 6] Verifying no duplicate-validation finding exists in baseline run...")
    dup_findings_1 = [f for f in eval_1["findings"] if f["rule_id"] == "TRANSACTION_ID_DUPLICATE"]
    assert len(dup_findings_1) == 0
    print(f"-> Duplicate findings count: {len(dup_findings_1)} (Expected: 0)")

    # STEP 7: Verify that the mutation is reported as surviving
    print("\n[STEP 7] Verifying mutation is reported as SURVIVING...")
    assert eval_1["detected"] is False
    assert report_1["surviving_mutations"] == 1
    assert report_1["detected_mutations"] == 0
    assert report_1["mutation_score"] == 0.0
    print(f"-> Mutation detection status: {eval_1['detected']} (Surviving), Score: {report_1['mutation_score']}%")

    # STEP 8: Verify that a uniqueness-rule recommendation is returned
    print("\n[STEP 8] Verifying uniqueness-rule recommendation is returned...")
    assert len(report_1["recommendations"]) == 1
    rec = report_1["recommendations"][0]
    assert rec["rule_type"] == "uniqueness"
    assert rec["target_column"] == "transaction_id"
    assert rec["suggested_rule_config"]["check_unique_transaction_id"] is True
    print(f"-> Recommended Rule: {rec['description']} for column '{rec['target_column']}'")

    # STEP 9: Create second evaluation from the ORIGINAL dataset with uniqueness ENABLED
    print("\n[STEP 9] Creating evaluation with uniqueness validation ENABLED (Hardened)...")
    eval_payload_2 = {
        "mutations": [
            {
                "mutation_type": "duplicate_row",
                "target_transaction_id": "ORD-102",
                "description": "Re-test duplicate transaction ORD-102 with hardened rules",
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
    eval_res_2 = client.post(f"/api/v1/datasets/{dataset_id}/evaluations", json=eval_payload_2)
    assert eval_res_2.status_code == 201
    report_2 = eval_res_2.json()
    eval_2 = report_2["evaluations"][0]

    # STEP 10: Verify that the uniqueness rule generates a relevant finding for the injected duplicate
    print("\n[STEP 10] Verifying uniqueness rule generated relevant finding for ORD-102...")
    dup_findings_2 = [f for f in eval_2["findings"] if f["rule_id"] == "TRANSACTION_ID_DUPLICATE"]
    assert len(dup_findings_2) == 1
    assert "ORD-102" in dup_findings_2[0]["affected_record_ids"]
    print(f"-> Duplicate finding captured: {dup_findings_2[0]['explanation']}")

    # STEP 11: Verify that the mutation is now reported as DETECTED
    print("\n[STEP 11] Verifying mutation is now reported as DETECTED...")
    assert eval_2["detected"] is True
    assert report_2["detected_mutations"] == 1
    assert report_2["surviving_mutations"] == 0
    assert report_2["mutation_score"] == 100.0
    assert len(report_2["recommendations"]) == 0
    print(f"-> Mutation detection status: {eval_2['detected']} (Detected), Score: {report_2['mutation_score']}%")

    # STEP 12: Verify that the source dataset has not changed after either evaluation
    print("\n[STEP 12] Verifying source dataset immutability...")
    dataset_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert dataset_res.status_code == 200
    assert dataset_res.json()["profile"]["row_count"] == 15
    print("-> Source dataset remains completely immutable (15 rows preserved)")

    # STEP 13: Retrieve the saved evaluation report through the API
    print("\n[STEP 13] Retrieving persisted evaluation report from API...")
    report_id_1 = report_1["report_id"]
    get_rep_res = client.get(f"/api/v1/evaluations/{report_id_1}")
    assert get_rep_res.status_code == 200
    retrieved_rep_1 = get_rep_res.json()
    print(f"-> Successfully retrieved report '{report_id_1}'")

    # STEP 14: Verify that the returned report matches the actual completed evaluation
    print("\n[STEP 14] Verifying retrieved report matches completed evaluation...")
    assert retrieved_rep_1["report_id"] == report_1["report_id"]
    assert retrieved_rep_1["mutation_score"] == report_1["mutation_score"]
    assert len(retrieved_rep_1["evaluations"]) == 1
    assert retrieved_rep_1["evaluations"][0]["detected"] is False
    print("-> Retrieved report matches evaluation run perfectly!")

    print("\n==================================================================")
    print("ALL 14 SECTION 28 DEMONSTRATION STEPS VERIFIED AND PASSED!")
    print("==================================================================")


if __name__ == "__main__":
    run_e2e_demonstration()
