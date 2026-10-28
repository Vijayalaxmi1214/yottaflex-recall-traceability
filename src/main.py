
"""Command-line entry point for the YottaFlex recall system."""

import argparse
import json
from pathlib import Path

from .data_generator import generate_data
from .validators import validate
from .recall_engine import simulate_recall
from .exporter import export_data, write_json
from .metrics import summarize


def main():
    parser = argparse.ArgumentParser(
        description="YottaFlex synthetic traceability and recall system"
    )

    parser.add_argument(
        "--scale",
        choices=["small", "full"],
        default="small",
        help="Dataset size: small for testing, full for the challenge",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=20261027,
        help="Random seed for reproducible data generation",
    )

    parser.add_argument(
        "--output",
        default="output",
        help="Directory where generated files will be saved",
    )

    parser.add_argument(
        "--inject-anomalies",
        action="store_true",
        help="Inject four labeled data-quality and recall anomalies",
    )

    args = parser.parse_args()

    # Resolve the configuration from the project root.
    config_path = Path("config.json")

    if not config_path.exists():
        raise FileNotFoundError(
            "config.json was not found. Run this command from F:\\yottaflex."
        )

    config = json.loads(config_path.read_text(encoding="utf-8"))

    if args.scale not in config.get("scales", {}):
        raise ValueError(
            f"Scale '{args.scale}' is missing from config.json."
        )

    scale = config["scales"][args.scale]

    # Generate the requested dataset.
    # The flag explicitly controls whether labeled anomalies are injected.
    data = generate_data(
        scale=scale,
        seed=args.seed,
        inject_anomalies=args.inject_anomalies,
    )

    # Validate the generated data and calculate recall impact.
    validation = validate(data)
    recall = simulate_recall(data)

    # Export CSV tables and deterministic file checksums.
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = export_data(data, str(output_dir))

    write_json(
        str(output_dir / "validation_report.json"),
        validation,
    )

    write_json(
        str(output_dir / "recall_report.json"),
        recall,
    )

    write_json(
        str(output_dir / "metrics.json"),
        summarize(data),
    )

    write_json(
        str(output_dir / "manifest.json"),
        manifest,
    )

    # Print a concise execution summary.
    print("=" * 55)
    print("YottaFlex Synthetic Traceability and Recall System")
    print("=" * 55)
    print(f"Scale: {args.scale}")
    print(f"Seed: {args.seed}")
    print(f"Anomalies injected: {args.inject_anomalies}")
    print(f"Output directory: {output_dir.resolve()}")
    print(f"Validation errors: {validation.get('error_count', 0)}")
    print(f"Validation warnings: {validation.get('warning_count', 0)}")
    print(f"Ground-truth issues: {len(data.get('ground_truth', []))}")
    print(f"Recall case: {recall.get('recall_id', 'not available')}")
    print(
        "Affected customers: "
        f"{recall.get('affected_customer_count', 0)}"
    )
    print(
        "Affected deliveries: "
        f"{recall.get('affected_delivery_count', 0)}"
    )
    print("=" * 55)


if __name__ == "__main__":
    main()
