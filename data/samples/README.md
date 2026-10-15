# DataTripwire Sample Datasets Catalog

This directory houses curated synthetic datasets used for benchmarking, demonstration, and automated verification of the **DataTripwire Data-Pipeline Reliability & Mutation Testing Engine**.

All datasets in this catalog are **100% synthetic baseline fixtures**. They contain zero company-confidential or proprietary data, and their clean baselines have not been deliberately corrupted; synthetic faults (mutations) are injected on-the-fly into isolated copies during evaluation.

---

## Dataset Inventory

| Dataset File | Domain Profile | Records | Columns | Size | Primary Key | Synthetic Baseline | Compatible Workflow |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :--- |
| **[`ecommerce_showcase_2500.csv`](./ecommerce_showcase_2500.csv)** | `sales` (E-Commerce) | **2,500** | **10** | 226 KB | `transaction_id` | Yes | High-scale sales mutation testing & revenue drift |
| **[`manufacturing_iot_sensor_readings_5040.csv`](./manufacturing_iot_sensor_readings_5040.csv)** | `manufacturing` (IoT Telemetry) | **5,040** | **18** | 824 KB | `reading_id` | Yes | Multi-machine telemetry frames & composite uniqueness |
| **[`realistic_sales_test.csv`](./realistic_sales_test.csv)** | `sales` (E-Commerce) | **60** | **5** | 2.7 KB | `transaction_id` | Yes | Compact deterministic sales testing fixture |

> [!NOTE]
> The repository also includes two lightweight bundled sample fixtures embedded directly in the backend runtime for instantaneous one-click demonstration without uploading files:
> - `backend/src/datatripwire/data/sample_sales.csv` (15 rows, 5 columns)
> - `backend/src/datatripwire/data/sample_manufacturing.csv` (20 rows, 18 columns)

---

## Schema Specifications

### 1. E-Commerce Sales Showcase (`ecommerce_showcase_2500.csv`)
- **Domain Identifier**: `sales`
- **Total Records**: 2,500 clean transactional records
- **Total Columns**: 10
- **Canonical Schema Columns**:
  1. `transaction_id` (string, e.g., `TXN-0000001`): Mandatory unique order identifier.
  2. `customer_id` (string, e.g., `CUST-1024`): Customer reference account.
  3. `product_id` (string, e.g., `PROD-0042`): Catalog product SKU.
  4. `product_category` (string, e.g., `Electronics`, `Apparel`): Department categorization.
  5. `quantity` (integer, e.g., `1`, `4`): Item purchase volume (strictly positive).
  6. `unit_price` (float, e.g., `249.0`, `1250.0`): Price per unit in INR (non-negative).
  7. `transaction_date` (string, ISO-8601 `YYYY-MM-DD`): Transaction timestamp.
  8. `payment_method` (string, e.g., `UPI`, `Credit Card`): Payment gateway method.
  9. `city` (string, e.g., `Jaipur`, `Chennai`): Fulfillment city.
  10. `sales_channel` (string, e.g., `iOS App`, `Marketplace`): Channel attribution.
- **Intended Testing Purpose**:
  - Validates high-volume ingestion and statistical profiling.
  - Tests transaction replay (`duplicate_row`) and silent revenue inflation across thousands of records.
  - Evaluates corrupt price/quantity mutations (`invalid_quantity`, `invalid_unit_price`) and missing values.

---

### 2. Manufacturing & Industrial IoT Showcase (`manufacturing_iot_sensor_readings_5040.csv`)
- **Domain Identifier**: `manufacturing`
- **Total Records**: 5,040 industrial telemetry frames
- **Total Columns**: 18
- **Canonical Schema Columns**:
  1. `reading_id` (string, e.g., `RDG-01-0001`): Primary sensor frame identifier.
  2. `timestamp` (string, ISO-8601 `2026-10-08T00:00:00`): Telemetry event timestamp.
  3. `facility_id` (string, e.g., `FAC-01`, `FAC-02`): Factory or plant site.
  4. `machine_id` (string, e.g., `MCH-01`, `MCH-02`): Industrial machinery asset ID.
  5. `production_line` (string, e.g., `LINE-A`, `LINE-B`): Factory production line.
  6. `product_family` (string, e.g., `GEARBOX`, `PUMP`): Product being fabricated.
  7. `batch_id` (string, e.g., `BATCH-2026-10`): Manufacturing batch number.
  8. `shift` (string, e.g., `SHIFT-1`, `SHIFT-2`): Operating shift.
  9. `temperature_c` (float, e.g., `68.4`): Operating temperature (°C).
  10. `pressure_bar` (float, e.g., `5.2`): Hydraulic/pneumatic pressure (bar).
  11. `vibration_mm_s` (float, e.g., `0.72`): Tri-axial vibration velocity (mm/s).
  12. `motor_current_a` (float, e.g., `8.5`): Motor electrical current (amperes).
  13. `power_kw` (float, e.g., `7.1`): Active power draw (kilowatts).
  14. `energy_kwh_20min` (float, e.g., `2.37`): Energy consumption per 20-minute interval (kWh).
  15. `units_produced` (integer, e.g., `12`): Good units produced in this interval.
  16. `defect_count` (integer, e.g., `0`): Rejected or defective units.
  17. `machine_status` (string, e.g., `RUNNING`, `MAINTENANCE`): Operating state.
  18. `quality_pass_rate_pct` (float, e.g., `98.5`): Calculated quality yield percentage (0–100%).
- **Intended Testing Purpose**:
  - Tests multi-machine timestamp ingestion where multiple machines report at the exact same timestamp.
  - Verifies the **Composite Machine & Timestamp Uniqueness Safeguard** (`check_machine_timestamp_unique`).
  - Evaluates equipment telemetry mutations: `duplicate_sensor_reading`, `missing_sensor_value`, `invalid_sensor_value`, `dropped_sensor_reading`, `invalid_production_value`.
  - Assesses distortion in operational metrics: total energy consumed (kWh), total defect counts, average vibration, and yield pass rate.

---

### 3. Realistic Sales Benchmark (`realistic_sales_test.csv`)
- **Domain Identifier**: `sales`
- **Total Records**: 60 transactional records
- **Total Columns**: 5
- **Canonical Schema Columns**:
  1. `transaction_id` (string, e.g., `TXN-2026-0010`)
  2. `customer_id` (string, e.g., `CUST-018`)
  3. `quantity` (integer)
  4. `unit_price` (float)
  5. `transaction_date` (string, `YYYY-MM-DD`)
- **Intended Testing Purpose**:
  - Compact determinism fixture for rapid integration and edge-case testing.

---

## How to Test the Datasets with DataTripwire

### Via Web Interface (The Mutation Lab)
1. Launch DataTripwire via `start_datatripwire.bat` or `py scripts/dev.py`.
2. Open `http://127.0.0.1:5173`.
3. In **01 Overview & Ingest**, drag-and-drop or select any of the sample CSVs from `data/samples/`.
4. In **02 Dataset Profile**, the platform automatically detects the domain (`sales` or `manufacturing`), renders column profiles, null distributions, and unlocks the Mutation Lab.
5. In **03 Mutation Lab**, configure synthetic faults (duplicate rows, negative sensor values, dropped records), toggle validation safeguards, and click **Execute Evaluation**.
6. In **04 Investigation**, inspect the mutation score, forensic rule evidence, and signature business/operational metric deltas.

### Via Automated Test Suite
Run the automated pytest integration test that exercises the full 5,040-record manufacturing dataset:
```bash
py -3 -m pytest backend/tests/integration/test_manufacturing_workflow.py -k "test_full_5040_row_manufacturing_dataset_verification" -v
```
