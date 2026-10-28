"""Export data tables and summary files with deterministic checksums."""
import csv, hashlib, json
from pathlib import Path
from .models import ENTITY_FIELDS

def export_data(data: dict, output_dir: str) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"files":{}}
    for table, rows in data.items():
        path = out / f"{table}.csv"
        if not rows:
            columns = ENTITY_FIELDS.get(table, [])
            if columns:
                path.write_text(",".join(columns) + "\n", encoding="utf-8")
            else:
                path.write_text("", encoding="utf-8")
        else:
            path = out / f"{table}.csv"
            columns = list(rows[0].keys())
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
        raw = path.read_bytes()
        manifest["files"][path.name] = {
            "rows":len(rows), "sha256":hashlib.sha256(raw).hexdigest()
        }
    return manifest

def write_json(path: str, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

def export_validation_error_files(validation: dict, output_dir: str) -> dict:
    """Generate yottaflex_validation_errors_report.txt, .csv, and .json."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    def normalize_issue(idx: int, item: dict, severity: str) -> dict:
        err_type = item.get("type", "unknown")
        prefix = "ERR" if severity == "ERROR" else "WARN"
        issue_id = f"{prefix}-{idx:04d}"
        table = item.get("table", "")
        entity_id = item.get("id") or item.get("finished_lot_id") or item.get("production_order_id") or item.get("recall_id") or ""
        category = "general"

        if err_type == "missing_input_lot":
            table = "production_inputs"
            category = "foreign_key_violation"
            entity_id = item.get("production_order_id", entity_id)
            details = f"Referenced raw lot '{item.get('id')}' does not exist in material_lots (Production Order: {item.get('production_order_id')})"
        elif err_type == "quarantine_violation":
            table = "recall_actions"
            category = "quarantine_violation"
            details = f"Action {item.get('id')}: target '{item.get('target_id')}' marked violation_available_for_sale under active recall"
        elif err_type == "delivered_quantity_exceeds_production":
            table = "deliveries"
            category = "quantity_reconciliation_failure"
            entity_id = item.get("finished_lot_id", entity_id)
            details = f"Finished lot {item.get('finished_lot_id')} delivered {item.get('delivered')} units, exceeding produced {item.get('produced')} units"
        elif err_type == "report_missing_customer_relationship":
            table = "recall_cases"
            category = "missing_relationship"
            entity_id = item.get("recall_id", entity_id)
            details = f"Recall case {item.get('recall_id')} has affected deliveries but lacks downstream customer recall actions"
        elif err_type == "negative_quantity":
            category = "value_constraint_violation"
            details = f"Table {table} field '{item.get('field')}' has negative quantity ({item.get('id')})"
        elif err_type == "duplicate_primary_key":
            category = "primary_key_violation"
            details = f"Duplicate primary key in {table} on field '{item.get('field')}'"
        elif err_type.startswith("invalid_"):
            category = "foreign_key_violation"
            details = f"Foreign key violation in {table} for identifier '{item.get('id')}'"
        else:
            details = str(item)

        return {
            "issue_id": issue_id,
            "severity": severity,
            "error_type": err_type,
            "category": category,
            "table": table,
            "entity_id": str(entity_id),
            "details": details
        }

    errors_list = [normalize_issue(i + 1, e, "ERROR") for i, e in enumerate(validation.get("errors", []))]
    warnings_list = [normalize_issue(i + 1, w, "WARNING") for i, w in enumerate(validation.get("warnings", []))]
    all_issues = errors_list + warnings_list

    # 1. JSON Export
    json_payload = {
        "summary": {
            "valid": validation.get("valid", False),
            "total_issues": len(all_issues),
            "error_count": len(errors_list),
            "warning_count": len(warnings_list)
        },
        "errors": errors_list,
        "warnings": warnings_list,
        "issues": all_issues
    }
    json_path = out / "yottaflex_validation_errors.json"
    write_json(str(json_path), json_payload)

    # 2. CSV Export
    csv_path = out / "yottaflex_validation_errors.csv"
    fieldnames = ["issue_id", "severity", "error_type", "category", "table", "entity_id", "details"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_issues)

    # 3. Text Report Export
    txt_path = out / "yottaflex_validation_errors_report.txt"
    lines = [
        "=" * 80,
        "                    YOTTAFLEX VALIDATION ERRORS REPORT",
        "=" * 80,
        f"Validation Result : {'PASSED (Clean)' if validation.get('valid') else 'FAILED (Issues Detected)'}",
        f"Total Issues      : {len(all_issues)}",
        f"  - Errors        : {len(errors_list)}",
        f"  - Warnings      : {len(warnings_list)}",
        "-" * 80,
        "SUMMARY BY CATEGORY:",
    ]
    cat_counts = {}
    for issue in all_issues:
        cat_counts[issue["category"]] = cat_counts.get(issue["category"], 0) + 1
    for cat, count in sorted(cat_counts.items()):
        lines.append(f"  * {cat.replace('_', ' ').title():<35}: {count}")

    lines.extend([
        "-" * 80,
        "DETAILED ERROR LIST:",
        "-" * 80
    ])
    if not errors_list:
        lines.append("  (No validation errors detected)")
    else:
        for err in errors_list:
            lines.append(f"[{err['issue_id']}] {err['error_type'].upper()}")
            lines.append(f"  Severity : {err['severity']}")
            lines.append(f"  Category : {err['category']}")
            lines.append(f"  Table    : {err['table']}")
            lines.append(f"  Entity ID: {err['entity_id']}")
            lines.append(f"  Details  : {err['details']}")
            lines.append("")

    lines.extend([
        "-" * 80,
        "DETAILED WARNING LIST:",
        "-" * 80
    ])
    if not warnings_list:
        lines.append("  (No validation warnings detected)")
    else:
        for warn in warnings_list:
            lines.append(f"[{warn['issue_id']}] {warn['error_type'].upper()}")
            lines.append(f"  Severity : {warn['severity']}")
            lines.append(f"  Category : {warn['category']}")
            lines.append(f"  Table    : {warn['table']}")
            lines.append(f"  Entity ID: {warn['entity_id']}")
            lines.append(f"  Details  : {warn['details']}")
            lines.append("")

    lines.extend([
        "=" * 80,
        "                              END OF REPORT",
        "=" * 80
    ])
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Also copy to root directory if output_dir is not root
    root = Path(".")
    if out.resolve() != root.resolve():
        (root / "yottaflex_validation_errors.json").write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
        (root / "yottaflex_validation_errors.csv").write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
        (root / "yottaflex_validation_errors_report.txt").write_text(txt_path.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "txt": str(txt_path)
    }
