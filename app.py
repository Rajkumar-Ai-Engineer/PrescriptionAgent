import json
import logging
import tempfile
from pathlib import Path

import streamlit as st

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
_log = logging.getLogger(__name__)

# ── page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Prescription Agent",
    page_icon="💊",
    layout="wide",
)

# ── helpers ────────────────────────────────────────────────────────────────

SUPPORTED_TYPES = ["png", "jpg", "jpeg", "gif", "webp", "pdf"]

STATUS_COLORS = {
    "true": "🟢",
    "false": "🔴",
    "needs_review": "🟡",
}

SEVERITY_COLORS = {
    "none": "🟢",
    "minor": "🟡",
    "significant": "🔴",
    "unknown": "⚪",
}

ALIGNMENT_LABELS = {
    "consistent": ("✅ Consistent", "green"),
    "inconsistent": ("⚠️ Inconsistent", "red"),
    "unrelated_but_plausible": ("ℹ️ Unrelated but plausible", "orange"),
    "not_applicable": ("— N/A", "gray"),
}


def _parse_coordinator_json(raw: str) -> dict | None:
    """Try to extract a JSON object from the coordinator's raw response."""
    if not raw:
        return None
    raw = raw.strip()
    # strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _run_graph(img_path: str, disease_name: str) -> dict:
    """Import and invoke the compiled LangGraph graph."""
    from src.core.agents.orchestrator import graph_builder

    initial_state = {
        "upload_img_path": img_path,
        "disease_name": disease_name,
        "sub_agent_response": "",
        "agent_response": "",
        "verified": False,
        "messages": [],
    }
    return graph_builder.invoke(initial_state)


# ── sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/color/96/pill.png", width=64)
    st.title("Prescription Agent")
    st.caption("Upload a prescription image and let the AI pipeline transcribe and verify it.")

    st.divider()
    st.markdown("**Pipeline**")
    st.markdown(
        """
        1. 🔍 **Sub-agent** (Claude) — OCR transcription  
        2. ✅ **Coordinator** (Groq + Tavily) — fact verification  
        """
    )
    st.divider()
    st.markdown("**Supported formats**")
    st.code("PNG · JPG · JPEG · GIF · WEBP · PDF")


# ── main layout ────────────────────────────────────────────────────────────

st.title("💊 Prescription Analyser")
st.markdown(
    "Upload a prescription image and optionally enter the patient's reported condition. "
    "The agent will transcribe the prescription and verify each medication against medical literature."
)

col_upload, col_form = st.columns([1, 1], gap="large")

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload prescription",
        type=SUPPORTED_TYPES,
        help="Supports PNG, JPG, JPEG, GIF, WEBP, PDF",
    )
    if uploaded_file:
        if uploaded_file.type.startswith("image/"):
            st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
        else:
            st.info(f"📄 PDF uploaded: **{uploaded_file.name}**")

with col_form:
    disease_name = st.text_input(
        "Patient-reported condition (optional)",
        placeholder="e.g. Throat infection, Hypertension, Diabetes…",
        help="Used as context to help disambiguate illegible handwriting. Does not override legible text.",
    )
    st.markdown("")
    run_btn = st.button(
        "🚀 Analyse Prescription",
        type="primary",
        use_container_width=True,
    )

st.divider()

# ── run pipeline ───────────────────────────────────────────────────────────

if run_btn:
    if not uploaded_file:
        st.warning("Please upload a prescription image first.")
        st.stop()

if run_btn and uploaded_file:
    if uploaded_file.size > MAX_UPLOAD_BYTES:
        st.error(f"File exceeds the {MAX_UPLOAD_BYTES // (1024*1024)} MB limit. Please upload a smaller file.")
        st.stop()

    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    with st.status("Running prescription pipeline…", expanded=True) as status:
        st.write("🔍 Sub-agent: transcribing prescription image…")
        try:
            final_state = _run_graph(tmp_path, disease_name)
            st.write("✅ Coordinator: verifying medications…")
            status.update(label="Pipeline complete!", state="complete", expanded=False)
        except Exception as exc:
            _log.exception("Pipeline failed for file %s", uploaded_file.name)
            status.update(label="Pipeline failed", state="error", expanded=True)
            st.error("An error occurred while processing the prescription. Please try again.")
            st.stop()

    # ── results ────────────────────────────────────────────────────────────

    tab_ocr, tab_verify, tab_raw = st.tabs(
        ["📋 Transcription", "🔬 Verification", "🗂️ Raw State"]
    )

    # ── tab 1: OCR transcription ───────────────────────────────────────────
    with tab_ocr:
        st.subheader("Prescription Transcription")
        ocr_output = final_state.get("sub_agent_response", "")
        if ocr_output:
            st.markdown(ocr_output)
        else:
            st.warning("No transcription output received from the sub-agent.")

    # ── tab 2: coordinator verification ───────────────────────────────────
    with tab_verify:
        st.subheader("Medication Verification Report")

        raw_agent = final_state.get("agent_response", "")
        coordinator_data = _parse_coordinator_json(raw_agent)

        if coordinator_data is None:
            # coordinator returned plain text (e.g. no tool call needed)
            st.info("Coordinator response (plain text):")
            st.markdown(raw_agent or "_No response_")
        else:
            medications = coordinator_data.get("medications", [])
            interactions = coordinator_data.get("interaction_flags", [])
            unverifiable = coordinator_data.get("unverifiable_fields", [])

            # ── overall badge ──────────────────────────────────────────────
            needs_review = any(
                m.get("verified") in ("false", "needs_review") for m in medications
            ) or any(
                f.get("severity") in ("significant",) for f in interactions
            ) or bool(unverifiable)

            if needs_review:
                st.error("⚠️ **Manual review required** — one or more items need attention.")
            else:
                st.success("✅ **All medications verified** — no issues found.")

            # ── medications ────────────────────────────────────────────────
            if medications:
                st.markdown("#### Medications")
                for med in medications:
                    status_icon = STATUS_COLORS.get(str(med.get("verified", "")).lower(), "⚪")
                    confidence = med.get("confidence", 0)
                    alignment_val = med.get("diagnosis_alignment", "not_applicable")
                    align_label, align_color = ALIGNMENT_LABELS.get(
                        alignment_val, ("—", "gray")
                    )

                    with st.expander(
                        f"{status_icon} **{med.get('drug_name_as_written', 'Unknown')}** "
                        f"— confidence: {confidence:.0%}",
                        expanded=needs_review,
                    ):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**Status:** {status_icon} `{med.get('verified')}`")
                            st.markdown(f"**Confidence:** {confidence:.0%}")
                        with c2:
                            st.markdown(
                                f"**Diagnosis alignment:** :{align_color}[{align_label}]"
                            )

                        st.markdown(f"**Notes:** {med.get('notes', '—')}")

                        sources = med.get("sources", [])
                        if sources:
                            st.markdown("**Sources:**")
                            for src in sources:
                                st.markdown(f"- [{src}]({src})")

            # ── interactions ───────────────────────────────────────────────
            if interactions:
                st.markdown("#### Drug Interactions")
                for flag in interactions:
                    sev = flag.get("severity", "unknown")
                    sev_icon = SEVERITY_COLORS.get(sev, "⚪")
                    drugs = " + ".join(flag.get("drugs_involved", []))
                    with st.expander(f"{sev_icon} {drugs} — severity: `{sev}`"):
                        st.markdown(f"**Notes:** {flag.get('notes', '—')}")
                        sources = flag.get("sources", [])
                        if sources:
                            st.markdown("**Sources:**")
                            for src in sources:
                                st.markdown(f"- [{src}]({src})")

            # ── unverifiable fields ────────────────────────────────────────
            if unverifiable:
                st.markdown("#### Unverifiable Fields")
                st.warning(
                    "The following fields were marked as **Not specified**, **Illegible**, "
                    "or context-assisted and could not be verified:"
                )
                for field in unverifiable:
                    st.markdown(f"- `{field}`")

    # ── tab 3: raw state ───────────────────────────────────────────────────
    with tab_raw:
        st.subheader("Full Agent State")
        display_state = {
            k: v for k, v in final_state.items()
            if k not in ("upload_img_path", "messages")
        }
        display_state["upload_img_path"] = tmp_path
        st.json(display_state)
