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

    st.subheader("📋 Extracted Key Specs")
    df = pd.DataFrame(specs.items(), columns=["Field", "Value"])
    st.table(df)

    # --- Export Section ---
    st.markdown("### 📥 Export Extracted Data")

    # --- Build dynamic export filename ---
    quote_id = specs.get("Quotation No", "quote").replace(" ", "_").strip()
    project_id_raw = specs.get("Project ID", "").strip()

    # Normalize project_id
    project_id = project_id_raw.replace(" ", "_")
    if project_id_raw.lower() in ["not found", "", "none"]:
        filename_base = quote_id
    else:
        filename_base = f"{quote_id}_{project_id}"

    # CSV Download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv,
        file_name=f"{filename_base}.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("🔍 Full Raw Text (for reference)")
    st.text_area("PDF Text", full_text, height=400)
