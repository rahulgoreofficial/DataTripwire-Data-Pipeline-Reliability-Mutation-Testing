# DataTripwire: Backend API Specification & Contract Reference

**Base URL (Local Development)**: `http://127.0.0.1:8000`  
**Interactive API Documentation (Swagger)**: `http://127.0.0.1:8000/docs`  
**Alternative Documentation (ReDoc)**: `http://127.0.0.1:8000/redoc`

---

## 1. System Limits & Configuration

| Parameter | Default Value | Environment Variable | Description |
| :--- | :--- | :--- | :--- |
| **Max Upload Size** | `5,242,880 bytes` (5 MB) | `DATATRIPWIRE_MAX_UPLOAD_SIZE` | Hard byte limit for CSV uploads |
| **Max Accepted Rows** | `50,000` | `DATATRIPWIRE_MAX_ROWS` | Row threshold to preserve local bounded memory |
| **Max Accepted Columns** | `100` | `DATATRIPWIRE_MAX_COLUMNS` | Maximum allowable CSV columns |
| **Max Mutations per Batch** | `10` | `DATATRIPWIRE_MAX_MUTATIONS` | Maximum mutations per evaluation request |
| **Runtime Storage Dir** | `data/runtime/` | `DATATRIPWIRE_RUNTIME_DIR` | Local directory for datasets and reports |
| **CORS Allowed Origins** | `http://localhost:5173,http://127.0.0.1:5173` | `DATATRIPWIRE_CORS_ORIGINS` | Permitted browser origins |

---

## 2. API Endpoints Reference

### Health Endpoints

#### `GET /health`
Unversioned liveness check.

**Response `200 OK`**:
```json
{
  "status": "ok",
  "app": "DataTripwire",
  "version": "0.1.0",
  "environment": "development"
}
```

#### `GET /api/v1/health`
Versioned v1 API health check.

**Response `200 OK`**: Same format as `/health`.

---

### Dataset Endpoints

#### `POST /api/v1/datasets/sample`
Loads and profiles the bundled deterministic 15-record e-commerce sales dataset (`sample_sales.csv`). Reuses or creates dataset ID `sample-sales`.

**Response `201 Created`**:
```json
{
  "dataset_id": "sample-sales",
  "filename": "sample_sales.csv",
  "uploaded_at": "2026-10-15T16:39:18.756209Z",
  "profile": {
    "dataset_id": "sample-sales",
    "filename": "sample_sales.csv",
    "row_count": 15,
    "column_count": 5,
    "column_names": ["transaction_id", "customer_id", "quantity", "unit_price", "transaction_date"],
    "column_types": {
      "transaction_id": "string",
      "customer_id": "string",
      "quantity": "integer",
      "unit_price": "float",
      "transaction_date": "date"
    },
    "null_counts": {
      "transaction_id": 0,
      "customer_id": 0,
      "quantity": 0,
      "unit_price": 0,
      "transaction_date": 0
    },
    "null_percentages": {
      "transaction_id": 0.0,
      "customer_id": 0.0,
      "quantity": 0.0,
      "unit_price": 0.0,
      "transaction_date": 0.0
    },
    "duplicate_row_count": 0,
    "created_at": "2026-10-15T16:39:18.756195Z",
    "null_percentages": {},
    "numeric_summaries": {
      "quantity": { "min": 1.0, "max": 10.0, "mean": 2.93, "sum": 44.0 },
      "unit_price": { "min": 80.0, "max": 2500.0, "mean": 758.67, "sum": 11380.0 }
    },
    "is_sales_compatible": true,
    "warnings": []
  },
  "is_sales_compatible": true,
  "warnings": []
}
```

#### `POST /api/v1/datasets`
Uploads a custom tabular CSV dataset via `multipart/form-data`.

**Request**:
- `file`: Multipart file with `.csv` extension.

**Response `201 Created`**: Same structure as `POST /api/v1/datasets/sample` with generated UUID `ds-<hex>`.

#### `GET /api/v1/datasets`
Lists all persisted datasets.

**Response `200 OK`**: Array of `DatasetResponse` objects.

#### `GET /api/v1/datasets/{dataset_id}`
Retrieves metadata and profile for a specific dataset.

**Response `200 OK`**: `DatasetResponse` object.  
**Response `404 Not Found`**: Dataset does not exist.

#### `GET /api/v1/datasets/{dataset_id}/profile`
Returns the `DatasetProfile` model directly for quick inspection.

**Response `200 OK`**: `DatasetProfile` JSON.

#### `GET /api/v1/datasets/{dataset_id}/evaluations`
Retrieves the history of evaluation runs conducted against this dataset.

**Response `200 OK`**: Array of `EvaluationSummaryItem` records.

---

### Evaluation Endpoints

#### `POST /api/v1/datasets/{dataset_id}/evaluations`
Executes an evaluation batch of 1 to 10 mutations against independent copies of the dataset.

**Request Body**:
```json
{
  "mutations": [
    {
      "mutation_type": "duplicate_row",
      "target_transaction_id": "ORD-102",
      "description": "Evaluate duplicate ORD-102"
    }
  ],
  "rules": {
    "check_required_columns": true,
    "check_required_values": true,
    "check_quantity_positive": true,
    "check_unit_price_nonnegative": true,
    "check_valid_transaction_date": true,
    "check_unique_transaction_id": false,
    "check_expected_row_count": false
  }
}
```

**Response `201 Created`**: Returns a full `EvaluationReport`.

#### `GET /api/v1/evaluations/{evaluation_id}`
Retrieves a previously persisted evaluation report.

**Response `200 OK`**: Full `EvaluationReport` JSON.

---

## 3. End-to-End Duplicate Transaction Workflow

This walkthrough demonstrates DataTripwire's primary technical capability: detecting that a duplicate transaction fault escapes baseline validation, measuring its financial impact, recommending a rule, and proving the hardened rule catches the fault.

### Step 1: Baseline Evaluation (Uniqueness Disabled)

**Endpoint**: `POST /api/v1/datasets/sample-sales/evaluations`

**Request Payload**:
```json
{
  "mutations": [
    {
      "mutation_type": "duplicate_row",
      "target_transaction_id": "ORD-102",
      "description": "Test duplicate transaction ORD-102 under baseline rules"
    }
  ],
  "rules": {
    "check_required_values": true,
    "check_quantity_positive": true,
    "check_unit_price_nonnegative": true,
    "check_valid_transaction_date": true,
    "check_unique_transaction_id": false,
    "check_expected_row_count": false
  }
}
```

**Actual Response (`201 Created`)**:
```json
{
  "report_id": "REP-C1186D9E",
  "dataset_id": "sample-sales",
  "created_at": "2026-10-15T16:39:18.775Z",
  "total_attempted": 1,
  "successfully_applied": 1,
  "detected_mutations": 0,
  "surviving_mutations": 1,
  "failed_evaluations": 0,
  "mutation_score": 0.0,
  "evaluations": [
    {
      "mutation_spec": {
        "mutation_id": "MUT-001",
        "mutation_type": "duplicate_row",
        "target_column": null,
        "target_record_id": "ORD-102",
        "params": { "target_transaction_id": "ORD-102" },
        "description": "Test duplicate transaction ORD-102 under baseline rules",
        "reproducibility_seed": null
      },
      "applied": true,
      "detected": false,
      "findings": [],
      "baseline_metrics": {
        "total_revenue": "19000.00",
        "transaction_count": 15,
        "customer_count": 10,
        "average_order_value": "1266.67",
        "additional_metrics": { "completeness": "complete", "excluded_rows": 0 }
      },
      "mutated_metrics": {
        "total_revenue": "19800.00",
        "transaction_count": 16,
        "customer_count": 10,
        "average_order_value": "1237.50",
        "additional_metrics": { "completeness": "complete", "excluded_rows": 0 }
      },
      "metric_deltas": {
        "revenue_baseline": "19000.00",
        "revenue_mutated": "19800.00",
        "revenue_delta_abs": "800.00",
        "revenue_delta_pct": 4.21,
        "transaction_count_delta": 1,
        "customer_count_delta": 0
      },
      "failure_reason": null
    }
  ],
  "recommendations": [
    {
      "recommendation_id": "REC-001",
      "rule_type": "uniqueness",
      "target_column": "transaction_id",
      "description": "Enforce unique constraint on primary key column 'transaction_id'",
      "rationale": "Mutation 'MUT-001' duplicated a transaction without being caught, silently inflating revenue and transaction counts. Enabling uniqueness verification on 'transaction_id' prevents duplicate ingestion.",
      "suggested_rule_config": {
        "check_unique_transaction_id": true
      },
      "code_snippet": "df['transaction_id'].duplicated().any() == False",
      "status": "suggested"
    }
  ],
  "baseline_metrics": {
    "total_revenue": "19000.00",
    "transaction_count": 15,
    "customer_count": 10,
    "average_order_value": "1266.67"
  },
  "summary_deltas": {
    "baseline_revenue": "19000.00",
    "baseline_transaction_count": 15,
    "max_revenue_impact_abs": "800.00",
    "total_surviving": 1,
    "total_detected": 0
  }
}
```

---

### Step 2: Hardened Evaluation (Uniqueness Enabled)

**Endpoint**: `POST /api/v1/datasets/sample-sales/evaluations`

**Request Payload**:
```json
{
  "mutations": [
    {
      "mutation_type": "duplicate_row",
      "target_transaction_id": "ORD-102",
      "description": "Re-test duplicate transaction ORD-102 with uniqueness enabled"
    }
  ],
  "rules": {
    "check_required_values": true,
    "check_quantity_positive": true,
    "check_unit_price_nonnegative": true,
    "check_valid_transaction_date": true,
    "check_unique_transaction_id": true,
    "check_expected_row_count": false
  }
}
```

**Actual Response (`201 Created`)**:
```json
{
  "report_id": "REP-9C4B2E01",
  "dataset_id": "sample-sales",
  "total_attempted": 1,
  "successfully_applied": 1,
  "detected_mutations": 1,
  "surviving_mutations": 0,
  "failed_evaluations": 0,
  "mutation_score": 100.0,
  "evaluations": [
    {
      "mutation_spec": {
        "mutation_id": "MUT-001",
        "mutation_type": "duplicate_row",
        "target_record_id": "ORD-102"
      },
      "applied": true,
      "detected": true,
      "findings": [
        {
          "finding_id": "FIND-DUP-1",
          "rule_id": "TRANSACTION_ID_DUPLICATE",
          "rule_type": "uniqueness",
          "severity": "critical",
          "affected_column": "transaction_id",
          "affected_record_ids": ["ORD-102"],
          "explanation": "Duplicate transaction_id values detected for 1 distinct identifier(s): ['ORD-102']",
          "detected": true
        }
      ]
    }
  ],
  "recommendations": []
}
```

---

## 4. Standard Error Codes and Responses

All error responses return a structured JSON body with `error`, `detail`, and machine-readable `code`:

```json
{
  "error": "Dataset Not Found",
  "detail": "Dataset with ID 'ds-missing' not found.",
  "code": "DATASET_NOT_FOUND"
}
```

| HTTP Status | Code | Cause |
| :--- | :--- | :--- |
| `400 Bad Request` | `INVALID_CSV` | Malformed CSV, empty file, empty column headers, duplicate column names |
| `404 Not Found` | `DATASET_NOT_FOUND` | Dataset ID does not exist in local repository |
| `404 Not Found` | `EVALUATION_NOT_FOUND` | Evaluation ID does not exist in local repository |
| `413 Payload Too Large` | `FILE_TOO_LARGE` | Uploaded file exceeds 5 MB (`settings.max_upload_size_bytes`) |
| `422 Unprocessable` | `LIMIT_EXCEEDED` | Dataset exceeds 50,000 rows or 100 columns |
| `422 Unprocessable` | `INCOMPATIBLE_SALES_SCHEMA`| Attempting sales evaluation on non-sales dataset lacking canonical columns |
| `422 Unprocessable` | `REQUEST_VALIDATION_ERROR` | Schema validation error (e.g., > 10 mutations in request) |
| `500 Server Error` | `INTERNAL_SERVER_ERROR` | Unexpected runtime error. Traceback logged server-side; safe message returned. |
