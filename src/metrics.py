"""Simple, measurable output metrics."""
def summarize(data: dict) -> dict:
    return {
        "table_row_counts": {name:len(rows) for name, rows in data.items()},
        "total_entities_and_relationship_rows": sum(len(rows) for rows in data.values()),
        "ground_truth_issue_count": len(data.get("ground_truth", []))
    }
