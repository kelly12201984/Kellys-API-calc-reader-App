import streamlit as st
import pdfplumber
import re
import pandas as pd

st.set_page_config(page_title="Tank Spec Reader")

st.title("📄 API-650 Tank Spec Reader")
st.markdown(
    "Toss in your tank calculation PDF and I'll get those key details you need."
)

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])


def extract_specs(text):
    specs = {}

    # --- Ordered Key Fields from mapping table ---
    ordered_fields = [
        ("Quotation No", r"Tag ID\s*[:=]?\s*([\w-]+)"),
        ("Project ID", r"Project\s*=\s*([^\n]+)"),
        ("Design Standard", r"Design Basis\s*[:=]?\s*([^\n]+)"),
        ("Annexes Used", r"Annexes Used\s*[:=]?\s*([^\n]+)"),
        ("Internal Pressure", r"Design Internal Pressure\s*[:=]?\s*([^\n]+)"),
        ("External Pressure", r"Design External Pressure\s*[:=]?\s*([^\n]+)"),
        ("Tank Diameter", r"D of Tank\s*=\s*([\d.]+)"),
        ("Outside Diameter", r"OD of Tank\s*[:=]?\s*([\d.]+)"),
        ("Inside Diameter", r"ID of Tank\s*[:=]?\s*([\d.]+)"),
        ("Shell Height", r"Shell Height\s*=\s*([\d.]+)"),
        ("Standard Gravity (SG)", r"S\.G of Contents\s*[:=]?\s*([\d.]+)"),
        ("Liquid Level", r"Max Design Liq\. Level\s*[:=]?\s*([\d.]+)"),
        ("Design Temperature", r"Design Temperature\s*[:=]?\s*([^\n]+)"),
        ("MDMT", r"\bMDMT\s*[:=]?\s*([^\n]+)"),
        ("Roof Live Load", r"Roof Live Load\s*[:=]?\s*([^\n]+)"),
        ("Wind Speed", r"Design Wind Speed.*?=\s*([\d.]+\s*mph)"),
    ]

    for field, pattern in ordered_fields:
        match = re.search(pattern, text, re.IGNORECASE)
        specs[field] = match.group(1).strip() if match else "Not found"

    # --- Extract all Shell Course Thicknesses dynamically ---
    shell_matches = re.findall(
        r"Shell\s*\((\d+)\)\s*[A-Z0-9\-]+\s*:\s*([\d.]+)\s*in", text
    )
    for course_num, thickness in shell_matches:
        specs[f"Shell Course {course_num} Thickness"] = f"{thickness} in"

    # --- Seismic Design (combined from Ss and S1) ---
    match_ss = re.search(r"Ss\s*\(g\)\s*=\s*([\d.]+)", text)
    match_s1 = re.search(r"S1\s*\(g\)\s*=\s*([\d.]+)", text)
    if match_ss and match_s1:
        specs["Seismic Design"] = f"{match_ss.group(1)}, {match_s1.group(1)}"
    else:
        specs["Seismic Design"] = "Not found"

    # --- Shell - Size: Extract widths from broken multi-line table ---
    shell_widths = []
    capture = False

    for line in text.splitlines():
        if "Shell Width" in line:
            capture = True
            continue
        if capture:
            if "Shell Weight" in line or "Weight CA" in line:
                break  # Stop capturing — we've entered the second table

            line = line.strip()
            if re.match(r"^\d+\s+\d+", line):
                try:
                    width = int(re.findall(r"^\d+\s+(\d+)", line)[0])
                    if 30 <= width <= 120:  # Extra safety: ignore bogus values like 982
                        shell_widths.append(str(width))
                except:
                    continue

    specs["Shell - Size"] = ", ".join(shell_widths) if shell_widths else "Not found"

    # --- Shell - Quantity: Find the highest Shell (#) mentioned ---
    shell_course_numbers = re.findall(r"Shell\s*\((\d+)\)", text)
    if shell_course_numbers:
        max_course = max(map(int, shell_course_numbers))
        specs["Shell - Quantity"] = str(max_course)
    else:
        specs["Shell - Quantity"] = "Not found"

    # --- Roof Type ---
    match = re.search(r"Roof\s*Type\s*[:=]\s*(.+)", text, re.IGNORECASE)
    specs["Roof Type"] = match.group(1).strip() if match else "Not found"

    # --- Roof Material ---
    match = re.search(r"Plates Material\s*=\s*(.+)", text)
    specs["Roof Material"] = match.group(1).strip() if match else "Not found"

    # --- Roof Thickness (from Roof section's t.actual) ---
    match = re.search(
        r"Roof.*?\bt\.actual\s*=\s*([\d.]+)\s*in", text, re.IGNORECASE | re.DOTALL
    )
    specs["Roof Thickness"] = match.group(1) + " in" if match else "Not found"

    # --- Bottom Material ---
    match = re.search(r"Bottom Material\s*[:=]?\s*(.+)", text)
    specs["Bottom Material"] = match.group(1).strip() if match else "Not found"

    # --- Bottom Thickness (from Bottom section's t.actual) ---
    match = re.search(
        r"Bottom.*?\bt\.actual\s*=\s*([\d.]+)\s*in", text, re.IGNORECASE | re.DOTALL
    )
    specs["Bottom Thickness"] = match.group(1) + " in" if match else "Not found"

    # --- Rim Angle Material (from Top Member section's Material) ---
    match = re.search(
        r"Top Member.*?Material\s*=\s*([^\n]+)", text, re.IGNORECASE | re.DOTALL
    )
    specs["Rim Angle Material"] = match.group(1).strip() if match else "Not found"

    # --- Rim Angle Size (from Top Member section's Size) ---
    match = re.search(
        r"Top Member.*?Size\s*=\s*([^\n]+)", text, re.IGNORECASE | re.DOTALL
    )
    specs["Rim Angle Size"] = match.group(1).strip() if match else "Not found"

    # --- Anchors Quantity (scoped to Anchors section) ---
    match = re.search(
        r"Anchors.*?Quantity\s*=\s*(\d+)", text, re.IGNORECASE | re.DOTALL
    )
    specs["Anchors Quantity"] = match.group(1) if match else "Not found"

    # --- Anchors Size ---
    match = re.search(r"Size\s*=\s*([\d.]+\s*in)", text, re.IGNORECASE)
    specs["Anchors Size"] = match.group(1).strip() if match else "Not found"

    # --- Anchors Material ---
    match = re.search(r"Material\s*=\s*([A-Z0-9\-]+)", text, re.IGNORECASE)
    specs["Anchors Material"] = match.group(1).strip() if match else "Not found"

    # --- Top Plate Thickness (c) ---
    match = re.search(r"c\s*=\s*([\d.]+)\s*in", text)
    specs["Top Plate Thickness (in)"] = match.group(1) if match else "Not found"

    # --- Top Plate Size (a, b) formatted as "__, __" ---
    a = re.search(r"a\s*=\s*([\d.]+)\s*in", text)
    b = re.search(r"b\s*=\s*([\d.]+)\s*in", text)
    specs["Top Plate Size"] = f"{a.group(1)}, {b.group(1)}" if a and b else "Not found"

    # --- Anchor Chair Quantity (duplicate of Anchors Quantity) ---
    specs["Anchor Chair Quantity"] = specs.get("Anchors Quantity", "Not found")

    # --- Vertical Plate Quantity (2x Anchors Quantity) ---
    try:
        quantity = int(specs["Anchors Quantity"])
        specs["Vertical Plate Quantity"] = str(quantity * 2)
    except:
        specs["Vertical Plate Quantity"] = "Not found"

    # --- Vertical Plate Size (h, b) formatted as "__, __" ---
    h = re.search(r"h\s*=\s*([\d.]+)\s*in", text)
    specs["Vertical Plate Size"] = (
        f"{b.group(1)}, {h.group(1)}" if b and h else "Not found"
    )

    # --- Vertical Plate Thickness (j) ---
    match = re.search(r"j\s*=\s*([\d.]+)\s*in", text)
    specs["Vertical Plate Thickness"] = match.group(1) if match else "Not found"

    return specs


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
