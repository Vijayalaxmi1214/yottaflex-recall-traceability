
import csv
import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output_frontend"

st.set_page_config(
    page_title="YottaFlex | Recall Traceability",
    page_icon="🔗",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 16px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔗 YottaFlex")
st.subheader("Supply Chain Traceability & Product Recall Dashboard")
st.caption(
    "Generate synthetic supply-chain data, inspect validation findings, "
    "and explore product-recall results."
)


# -------------------- Data loading helpers --------------------

def load_json(filename):
    path = OUTPUT_DIR / filename

    if not path.is_file():
        return None

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        st.warning(f"Could not read {filename}: {exc}")
        return None


def load_csv_preview(filename, limit=100):
    path = OUTPUT_DIR / filename

    if not path.is_file():
        return [], []

    try:
        with path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames or []
            rows = []

            for index, row in enumerate(reader):
                if index >= limit:
                    break
                rows.append(row)

        return columns, rows

    except (OSError, csv.Error) as exc:
        st.warning(f"Could not read {filename}: {exc}")
        return [], []


def display_value(value):
    """Display text, numbers, lists, and dictionaries appropriately."""
    if value is None:
        st.write("Not available")
    elif isinstance(value, (dict, list)):
        st.json(value)
    else:
        # IDs and other ordinary text must not be parsed as JSON.
        st.write(value)


def display_label(key):
    return key.replace("_", " ").title()


# -------------------- Sidebar controls --------------------

with st.sidebar:
    st.header("Dataset Configuration")

    scale = st.selectbox(
        "Dataset size",
        ["small", "full"],
        index=0,
    )

    seed = st.number_input(
        "Random seed",
        min_value=0,
        max_value=2147483647,
        value=20261027,
        step=1,
    )

    inject_anomalies = st.checkbox(
        "Inject four known anomalies",
        value=True,
        help="Adds deliberate issues for validation and recall testing.",
    )

    run_button = st.button(
        "Generate Dataset",
        type="primary",
        use_container_width=True,
    )

    st.divider()
    st.caption("Synthetic demonstration data only.")


# -------------------- Dataset generation --------------------

if run_button:
    command = [
        sys.executable,
        "-m",
        "src.main",
        "--scale",
        scale,
        "--seed",
        str(int(seed)),
        "--output",
        str(OUTPUT_DIR),
    ]

    if inject_anomalies:
        command.append("--inject-anomalies")

    try:
        with st.spinner(
            "Generating data and running validation and recall analysis..."
        ):
            result = subprocess.run(
                command,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=600,
            )

        st.session_state["run_output"] = result.stdout
        st.session_state["run_error"] = result.stderr
        st.session_state["run_returncode"] = result.returncode
        st.session_state["run_scale"] = scale
        st.session_state["run_seed"] = int(seed)
        st.session_state["run_anomalies"] = inject_anomalies

    except subprocess.TimeoutExpired:
        st.error(
            "Generation timed out. Try the small dataset first."
        )
    except OSError as exc:
        st.error(f"Could not start the generator: {exc}")


# -------------------- Generation status --------------------

if "run_returncode" in st.session_state:
    if st.session_state["run_returncode"] == 0:
        st.success(
            "Dataset generated successfully — "
            f"{st.session_state['run_scale']} scale, "
            f"seed {st.session_state['run_seed']}."
        )

        with st.expander("Generator console output"):
            st.code(st.session_state.get("run_output", ""))

    else:
        st.error("The generator returned an error.")

        error_text = st.session_state.get("run_error", "")
        output_text = st.session_state.get("run_output", "")

        st.code(error_text or output_text or "No error details available.")


# -------------------- Load generated reports --------------------

metrics = load_json("metrics.json")
validation = load_json("validation_report.json")
recall = load_json("recall_report.json")
manifest = load_json("manifest.json")


# -------------------- Empty state --------------------

if not metrics:
    st.info(
        "Choose your settings in the sidebar and click "
        "**Generate Dataset** to begin."
    )

    st.markdown("### Dashboard overview")

    col1, col2, col3 = st.columns(3)
    col1.markdown(
        "**Data generation**\n\nCreate repeatable synthetic records."
    )
    col2.markdown(
        "**Validation**\n\nInspect errors and warnings."
    )
    col3.markdown(
        "**Recall analysis**\n\nExplore downstream impact."
    )


# -------------------- Dashboard --------------------

else:
    counts = metrics.get("table_row_counts", {})
    total_rows = metrics.get(
        "total_entities_and_relationship_rows", 0
    )
    issue_count = metrics.get("ground_truth_issue_count", 0)

    st.markdown("### Dataset overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Entity & relationship rows", f"{total_rows:,}")
    c2.metric("Ground-truth issues", issue_count)

    c3.metric(
        "Validation errors",
        validation.get("error_count", 0) if validation else "N/A",
    )

    c4.metric(
        "Validation warnings",
        validation.get("warning_count", 0) if validation else "N/A",
    )

    st.markdown("### Generated table sizes")

    if counts:
        st.dataframe(
            [
                {"Table": name, "Rows": value}
                for name, value in counts.items()
            ],
            use_container_width=True,
            hide_index=True,
        )

    overview_tab, validation_tab, recall_tab, data_tab = st.tabs(
        [
            "Overview",
            "Validation",
            "Recall analysis",
            "Data explorer",
        ]
    )

    # -------------------- Overview tab --------------------

    with overview_tab:
        st.markdown("#### Run details")

        st.write(
            "**Scale:**",
            st.session_state.get("run_scale", "Existing output"),
        )
        st.write(
            "**Seed:**",
            st.session_state.get("run_seed", "Not recorded"),
        )
        st.write("**Output folder:**", str(OUTPUT_DIR))

        if manifest:
            st.markdown("#### Output manifest")
            st.json(manifest)

            st.download_button(
                "Download manifest.json",
                data=json.dumps(
                    manifest, indent=2
                ).encode("utf-8"),
                file_name="manifest.json",
                mime="application/json",
            )

    # -------------------- Validation tab --------------------

    with validation_tab:
        if validation:
            if validation.get("valid", False):
                st.success(
                    "Validation passed: no validation errors were reported."
                )
            else:
                st.warning(
                    "Validation found issues. This is expected when "
                    "deliberate anomalies are enabled."
                )

            errors = validation.get("errors", [])
            warnings = validation.get("warnings", [])

            st.markdown(f"#### Errors ({len(errors)})")

            if errors:
                st.dataframe(
                    errors,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success("No validation errors.")

            st.markdown(f"#### Warnings ({len(warnings)})")

            if warnings:
                st.dataframe(
                    warnings,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.write("No validation warnings.")

        else:
            st.info("No validation report found. Generate a dataset first.")

        ground_truth_columns, ground_truth_rows = load_csv_preview(
            "ground_truth.csv"
        )

        if ground_truth_rows:
            st.markdown("#### Ground-truth anomaly labels")

            st.dataframe(
                ground_truth_rows,
                use_container_width=True,
                hide_index=True,
            )

    # -------------------- Recall analysis tab --------------------

    with recall_tab:
        if recall:
            r1, r2, r3 = st.columns(3)

            r1.metric(
                "Affected customers",
                recall.get("affected_customer_count", 0),
            )
            r2.metric(
                "Affected deliveries",
                recall.get("affected_delivery_count", 0),
            )
            r3.metric(
                "Unrecovered quantity",
                recall.get("unrecovered_delivered_quantity", 0),
            )

            st.markdown("#### Recall details")

            # Display scalar fields as normal text.
            # Use JSON only for actual lists and dictionaries.
            scalar_fields = [
                "recall_id",
                "trigger_type",
                "trigger_lot_id",
                "affected_delivered_quantity",
                "recovered_quantity",
                "unrecovered_delivered_quantity",
            ]

            for key in scalar_fields:
                if key in recall:
                    st.markdown(f"**{display_label(key)}**")
                    display_value(recall[key])

            list_fields = [
                "affected_finished_lots",
                "affected_customers",
                "affected_deliveries",
                "recall_actions",
            ]

            for key in list_fields:
                if key in recall:
                    st.markdown(f"#### {display_label(key)}")

                    value = recall[key]

                    if isinstance(value, list) and value:
                        if all(
                            isinstance(item, dict) for item in value
                        ):
                            st.dataframe(
                                value,
                                use_container_width=True,
                                hide_index=True,
                            )
                        else:
                            st.write(value)

                    elif isinstance(value, list):
                        st.write("No records.")

                    else:
                        display_value(value)

            st.download_button(
                "Download recall_report.json",
                data=json.dumps(
                    recall, indent=2
                ).encode("utf-8"),
                file_name="recall_report.json",
                mime="application/json",
            )

        else:
            st.info(
                "No recall report found. Generate a dataset first."
            )

    # -------------------- Data explorer tab --------------------

    with data_tab:
        csv_files = sorted(OUTPUT_DIR.glob("*.csv"))

        if not csv_files:
            st.info("No CSV files are available yet.")

        else:
            selected_file = st.selectbox(
                "Choose a CSV file",
                [file.name for file in csv_files],
            )

            columns, rows = load_csv_preview(selected_file)

            if rows:
                st.caption("Showing up to 100 rows.")

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

            elif columns:
                st.caption(
                    "The CSV contains headers but no data rows."
                )
                st.write(columns)

            else:
                st.warning("Could not read this CSV file.")

            selected_path = OUTPUT_DIR / selected_file

            if selected_path.is_file():
                try:
                    with selected_path.open("rb") as file:
                        csv_bytes = file.read()

                    st.download_button(
                        "Download selected CSV",
                        data=csv_bytes,
                        file_name=selected_file,
                        mime="text/csv",
                    )

                except OSError as exc:
                    st.error(f"Could not prepare CSV download: {exc}")


# -------------------- Footer --------------------

st.divider()

st.caption(
    "YottaFlex Recall Traceability System · "
    "Synthetic data for demonstration"
)
