# TSapp.py

import streamlit as st
import pdfplumber
import pandas as pd
from TSutils import extract_specs, extract_nozzles, extract_manways

st.set_page_config(page_title="Tank Spec Reader")

st.title("📄 API-650 Tank Spec Reader")
st.markdown(
    "Toss in your tank calculation PDF and I'll get those key details you need."
)

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

# --- Streamlit UI Output ---
if uploaded_file:
    st.success("PDF uploaded! Extracting text...")

    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    specs = extract_specs(full_text)

    # --- Filename base from extracted specs ---
    quote_id = specs.get("Quotation No", "quote").replace(" ", "_").strip()
    project_id_raw = specs.get("Project ID", "").strip()
    project_id = project_id_raw.replace(" ", "_")
    if project_id_raw.lower() in ["not found", "", "none"]:
        filename_base = quote_id
    else:
        filename_base = f"{quote_id}_{project_id}"

    # --- Display Spec Table ---
    st.subheader("📋 Extracted Key Specs")
    df = pd.DataFrame(specs.items(), columns=["Field", "Value"])
    st.table(df)

    # --- Nozzles Table ---
    nozzles = extract_nozzles(full_text)
    if nozzles:
        st.subheader("🛠️ Nozzles (Roof & Shell)")
        nozzle_df = pd.DataFrame(nozzles)
        st.table(nozzle_df)
        csv_nozzles = nozzle_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Nozzles CSV",
            data=csv_nozzles,
            file_name=f"{filename_base}_nozzles.csv",
            mime="text/csv",
        )
    else:
        st.info("No nozzles found.")

    # --- Manway Table ---
    manways = extract_manways(full_text)
    if manways:
        st.subheader("🛠️ Manway Nozzles")
        manway_df = pd.DataFrame(manways)
        st.table(manway_df)
        csv_manways = manway_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Manways CSV",
            data=csv_manways,
            file_name=f"{filename_base}_manways.csv",
            mime="text/csv",
        )
    else:
        st.info("No manway nozzles found.")

    # --- Combined Export Function ---
    def create_combined_csv(specs_df, nozzle_df=None, manway_df=None):
        parts = []
        parts.append("=== TANK SPECS ===")
        parts.append(specs_df.to_csv(index=False))

        if nozzle_df is not None and not nozzle_df.empty:
            parts.append("\n=== NOZZLES (Roof & Shell) ===")
            parts.append(nozzle_df.to_csv(index=False))

        if manway_df is not None and not manway_df.empty:
            parts.append("\n=== MANWAYS ===")
            parts.append(manway_df.to_csv(index=False))

        return "\n".join(parts).encode("utf-8")

    # --- Combined CSV Export ---
    combined_csv = create_combined_csv(
        df,
        nozzle_df if "nozzle_df" in locals() else None,
        manway_df if "manway_df" in locals() else None,
    )

    st.download_button(
        label="⬇️ Download All Data",
        data=combined_csv,
        file_name=f"{filename_base}.csv",
        mime="text/csv",
    )

    # --- Full Raw PDF Text Viewer ---
    st.markdown("---")
    st.subheader("🔍 Full Raw Text (for reference)")
    st.text_area("PDF Text", full_text, height=400)
