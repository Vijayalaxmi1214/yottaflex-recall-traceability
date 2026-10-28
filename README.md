
# YottaFlex Recall Traceability System

A deterministic synthetic-data generator and product-recall simulation built for the YottaFlex.ai coding challenge.

The project generates supply-chain traceability records, validates entity relationships and quantities, injects known anomalies, and simulates downstream product-recall analysis.

## Features

- Reproducible synthetic supply-chain data using a configurable random seed.
- Supplier, material-lot, product, bill-of-materials, production, finished-lot, customer, shipment, and delivery records.
- Validation of foreign-key relationships, quantities, and recall-related constraints.
- Four deliberately injected anomalies with corresponding ground-truth labels.
- Recall analysis identifying affected finished lots, deliveries, and customers.
- CSV and JSON output files with a manifest containing row counts and SHA-256 checksums.
- Automated unit tests for generation, identifiers, validation, and recall calculations.

## Requirements

- Python 3.9 or later, as tested in the development environment.
- No third-party packages are required for the core project.

## Quick Start — Windows

Open a terminal in the project directory:

```powershell
cd F:\yottaflex
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Generate a small dataset:

```powershell
python -m src.main --scale small --seed 20261027
```

If PowerShell blocks environment activation, run the project using the virtual environment's Python executable or your installed Python interpreter.

## Generate the Full Dataset

Run the challenge-scale generator with the fixed seed and four deliberate anomalies:

```powershell
python -m src.main --scale full --seed 20261027 --inject-anomalies --output output_full
```

The output directory contains CSV files for generated entities and relationships, along with JSON reports.

## Dataset Size

The verified full-scale run produced the following counts:

| Dataset | Rows |
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
| Ground-truth issues | 4 |
| **Total entity and relationship rows** | **94,522** |

## Injected Anomalies

The challenge run injects four known issues:

1. **Missing input lot:** a production input references a material lot that does not exist.
2. **Quantity reconciliation failure:** delivered quantity exceeds the quantity produced for the affected finished lot.
3. **Missing downstream customer relationship:** the recall report is missing a required customer relationship.
4. **Quarantine violation:** an action indicates that recalled inventory is available for sale.

The ground-truth labels are exported separately in `ground_truth.csv`. Validation findings are written to `validation_report.json`.

An invalid validation report is expected when deliberate anomalies are enabled.

## Recall Simulation

The recall simulation follows the generated traceability relationships to identify affected finished lots, deliveries, and customers.

The verified full-scale run reported:

- Affected customers: 4
- Affected deliveries: 4
- Unrecovered delivered quantity: 16

These figures correspond to the run using seed `20261027` and the current dataset configuration.

## Generated Outputs

The output directory includes:

- Entity and relationship CSV files.
- `ground_truth.csv` — labels for injected anomalies.
- `validation_report.json` — validation errors, warnings, and overall validity.
- `recall_report.json` — recall findings and affected downstream records.
- `metrics.json` — generated table counts and aggregate metrics.
- `manifest.json` — file metadata, row counts, and SHA-256 checksums, as implemented by the exporter.

## Run Tests

Run the complete unit-test suite:

```powershell
python -m unittest discover -s tests -v
```

The verified test run passed all 10 tests, covering:

- Baseline dataset counts.
- Fixed-seed reproducibility.
- Identifier formats.
- Recall report fields.
- Unrecovered-quantity calculations.
- Detection of injected anomalies.
- Clean-data validation.
- Invalid foreign-key detection.
- Negative-quantity detection.
- Ground-truth anomaly detection.

## Reproducibility

Use the same seed, scale, anomaly setting, and configuration to reproduce the same output.

The full-scale output generated with seed `20261027` was compared against a second run. All 19 output files matched byte-for-byte, with zero mismatches and zero extra files.

## Design Notes

- IDs are deterministic for a fixed seed and generation order.
- Relationships reference entity IDs rather than comma-separated lists.
- Derived totals are calculated from generated source records.
- Baseline records are generated before deliberate anomalies are injected.
- Ground-truth labels are stored separately from ordinary entity data.
- The dataset is synthetic and is not real company data.

## Important

The full dataset contains many records and may take longer to generate. Start with the small scale to inspect the output and reports before generating the full dataset.
=======
# yottaflex-recall-traceability
Synthetic Supply Chain Traceability and Product Recall Dashboard
>>>>>>> 8d40355db70d4ac6b565d2f68bfe17d84522ed3d
