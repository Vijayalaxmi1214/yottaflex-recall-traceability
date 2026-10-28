# YottaFlex — Supply Chain Traceability and Product Recall Dashboard

A Python-based synthetic supply chain traceability system that generates linked supply chain data, validates data integrity, traces affected customers and deliveries, and supports product recall analysis through a Streamlit dashboard.

## Features

- **Synthetic data generation:** Generates linked suppliers, material lots, products, bills of materials (BOMs), production orders, finished lots, customers, shipments, and deliveries.
- **Traceability:** Connects production inputs to finished lots and downstream shipments and deliveries.
- **Data validation:** Detects foreign-key violations, quantity reconciliation failures, missing customer relationships, and quarantine violations.
- **Recall analysis:** Identifies affected customers and deliveries and calculates unrecovered delivered quantities.
- **Anomaly injection:** Adds controlled data anomalies to test validation and recall workflows.
- **Streamlit dashboard:** Provides an interactive interface for overview metrics, validation results, recall analysis, and data exploration.
- **Reproducibility:** Supports seeded data generation for repeatable results.
- **Automated tests:** Includes unit tests for identifiers, data generation, recall logic, and validation.

## Project Structure

```text
yottaflex/
├── app.py
├── config.json
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── id_generator.py
│   ├── models.py
│   ├── data_generator.py
│   ├── validators.py
│   ├── recall_engine.py
│   ├── exporter.py
│   ├── metrics.py
│   └── main.py
└── tests/
    ├── test_ids.py
    ├── test_generator.py
    ├── test_recall.py
    └── test_validation.py
```

## Requirements

- Python 3.9 or later
- pip
- Git
- Streamlit for the dashboard

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Run the Application

### 1. Launch the Streamlit dashboard

From the project root directory, run:

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal.

### 2. Generate the full synthetic dataset

```bash
python -m src.main --scale full --seed 20261027 --inject-anomalies --output output_full
```

The command generates the full dataset with controlled anomalies for testing validation and recall functionality.

### 3. Run the automated tests

```bash
python -m unittest discover -s tests -v
```

## Full Dataset Summary

The verified full-scale run generated the following records:

| Entity or relationship | Record count |
|---|---:|
| Suppliers | 500 |
| Material lots | 10,000 |
| Products | 3 |
| Bills of materials | 3 |
| BOM materials | 7 |
| Production orders | 5,000 |
| Production inputs | 10,001 |
| Finished lots | 8,000 |
| Customers | 1,000 |
| Shipments | 20,000 |
| Shipment items | 20,000 |
| Deliveries | 20,001 |
| Recall cases | 1 |
| Recall actions | 2 |
| Ground-truth anomaly labels | 4 |

The entity and relationship tables contain **94,522 total rows**.

## Validation and Anomaly Testing

The anomaly-injected dataset was tested for the following conditions:

1. **Foreign-key violation:** A production input references a missing material lot.
2. **Quantity reconciliation failure:** Delivered quantity exceeds the associated production quantity.
3. **Missing customer relationship:** A recall report omits a downstream customer relationship.
4. **Quarantine violation:** Recalled inventory remains available for sale.

The full anomaly-injected validation run reported **3 errors and 1 warning**.

## Recall Analysis Results

The verified full-scale recall analysis reported:

- **Affected customers:** 4
- **Affected deliveries:** 4
- **Unrecovered delivered quantity:** 16

These values describe the recorded full-scale test run and its generated synthetic data.

## Reproducibility

Use a fixed random seed to reproduce the generated dataset:

```bash
python -m src.main --scale full --seed 20261027 --inject-anomalies --output output_full
```

The reproducibility check compared 19 generated files and found no mismatches or unexpected extra files.

## Testing

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

The verified test run passed **10 out of 10 tests**.

## Notes

- This project uses synthetic data; it does not represent real suppliers, customers, or shipments.
- Anomaly injection is intended for testing data validation and recall workflows.
- Generated output folders and the Python virtual environment should not be committed to Git.

## License

Add the license details here if a license is selected for this project.
