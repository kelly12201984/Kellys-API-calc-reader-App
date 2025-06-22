import re
from collections import defaultdict
import pandas as pd


def extract_specs(text):
    specs = {}

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

    shell_matches = re.findall(
        r"Shell\s*\((\d+)\)\s*[A-Z0-9\-]+\s*:\s*([\d.]+)\s*in", text
    )
    for course_num, thickness in shell_matches:
        specs[f"Shell Course {course_num} Thickness"] = f"{thickness} in"

    match_ss = re.search(r"Ss\s*\(g\)\s*=\s*([\d.]+)", text)
    match_s1 = re.search(r"S1\s*\(g\)\s*=\s*([\d.]+)", text)
    specs["Seismic Design"] = (
        f"{match_ss.group(1)}, {match_s1.group(1)}"
        if match_ss and match_s1
        else "Not found"
    )

    shell_widths = []
    capture = False
    for line in text.splitlines():
        if "Shell Width" in line:
            capture = True
            continue
        if capture:
            if "Shell Weight" in line or "Weight CA" in line:
                break
            line = line.strip()
            if re.match(r"^\d+\s+\d+", line):
                try:
                    width = int(re.findall(r"^\d+\s+(\d+)", line)[0])
                    if 30 <= width <= 120:
                        shell_widths.append(str(width))
                except:
                    continue

    specs["Shell - Size"] = ", ".join(shell_widths) if shell_widths else "Not found"

    shell_course_numbers = re.findall(r"Shell\s*\((\d+)\)", text)
    specs["Shell - Quantity"] = (
        str(max(map(int, shell_course_numbers)))
        if shell_course_numbers
        else "Not found"
    )

    match = re.search(r"Roof\s*Type\s*[:=]\s*(.+)", text, re.IGNORECASE)
    specs["Roof Type"] = match.group(1).strip() if match else "Not found"

    match = re.search(r"Plates Material\s*=\s*(.+)", text)
    specs["Roof Material"] = match.group(1).strip() if match else "Not found"

    match = re.search(
        r"Roof.*?\bt\.actual\s*=\s*([\d.]+)\s*in", text, re.IGNORECASE | re.DOTALL
    )
    specs["Roof Thickness"] = match.group(1) + " in" if match else "Not found"

    match = re.search(r"Bottom Material\s*[:=]?\s*(.+)", text)
    specs["Bottom Material"] = match.group(1).strip() if match else "Not found"

    match = re.search(
        r"Bottom.*?\bt\.actual\s*=\s*([\d.]+)\s*in", text, re.IGNORECASE | re.DOTALL
    )
    specs["Bottom Thickness"] = match.group(1) + " in" if match else "Not found"

    match = re.search(
        r"Top Member.*?Material\s*=\s*([^\n]+)", text, re.IGNORECASE | re.DOTALL
    )
    specs["Rim Angle Material"] = match.group(1).strip() if match else "Not found"

    match = re.search(
        r"Top Member.*?Size\s*=\s*([^\n]+)", text, re.IGNORECASE | re.DOTALL
    )
    specs["Rim Angle Size"] = match.group(1).strip() if match else "Not found"

    match = re.search(
        r"Anchors.*?Quantity\s*=\s*(\d+)", text, re.IGNORECASE | re.DOTALL
    )
    specs["Anchors Quantity"] = match.group(1) if match else "Not found"

    match = re.search(r"Size\s*=\s*([\d.]+\s*in)", text, re.IGNORECASE)
    specs["Anchors Size"] = match.group(1).strip() if match else "Not found"

    match = re.search(r"Material\s*=\s*([A-Z0-9\-]+)", text, re.IGNORECASE)
    specs["Anchors Material"] = match.group(1).strip() if match else "Not found"

    match = re.search(r"c\s*=\s*([\d.]+)\s*in", text)
    specs["Top Plate Thickness (in)"] = match.group(1) if match else "Not found"

    a = re.search(r"a\s*=\s*([\d.]+)\s*in", text)
    b = re.search(r"b\s*=\s*([\d.]+)\s*in", text)
    specs["Top Plate Size"] = f"{a.group(1)}, {b.group(1)}" if a and b else "Not found"

    specs["Anchor Chair Quantity"] = specs.get("Anchors Quantity", "Not found")

    try:
        quantity = int(specs["Anchors Quantity"])
        specs["Vertical Plate Quantity"] = str(quantity * 2)
    except:
        specs["Vertical Plate Quantity"] = "Not found"

    h = re.search(r"h\s*=\s*([\d.]+)\s*in", text)
    specs["Vertical Plate Size"] = (
        f"{b.group(1)}, {h.group(1)}" if b and h else "Not found"
    )

    match = re.search(r"j\s*=\s*([\d.]+)\s*in", text)
    specs["Vertical Plate Thickness"] = match.group(1) if match else "Not found"

    return specs


def get_nozzle_blind_flags(text):
    import re

    lines = text.splitlines()
    blind_map = {}
    current_block = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        current_block.append(stripped)

        # Match line like: 0002 NOZZLE
        nozzle_label_match = re.match(r"^(\d{4})\s+NOZZLE$", stripped.upper())
        if nozzle_label_match:
            nozzle_number = nozzle_label_match.group(1)
            nozzle_id = f"Nozzle-{nozzle_number}"

            block_text = " ".join(current_block).upper()
            has_blind = "W/ BLIND" in block_text

            # ✅ This is the correct debug line
            print(f"[BLIND DETECT] {nozzle_id}: {'Yes' if has_blind else 'No'}")

            blind_map[nozzle_id] = "Yes" if has_blind else "No"
            current_block = []

    return blind_map


def extract_nozzles(text):
    nozzle_pattern = re.compile(
        r"NOZZLE Description\s*:\s*(\d+) in SCH ?(\d+)[A-Z]* TYPE ([A-Z]+)",
        re.IGNORECASE,
    )
    repad_required_pattern = re.compile(r"No Reinforcement Pad required", re.IGNORECASE)
    repad_od_pattern = re.compile(r"Repad\s+OD\s*=\s*(\d+)", re.IGNORECASE)
    repad_thk_pattern = re.compile(r"t_rpr\s*=\s*(0?\.\d+)\s*in", re.IGNORECASE)

    lines = text.splitlines()
    nozzle_blocks = []
    current_block = []
    in_nozzle_block = False

    for line in lines:
        if "Shell Nozzle: Nozzle-" in line:
            if current_block:
                nozzle_blocks.append(current_block)
                current_block = []
            in_nozzle_block = True
        if in_nozzle_block:
            current_block.append(line.strip())
            if line.strip() == "":
                nozzle_blocks.append(current_block)
                current_block = []
                in_nozzle_block = False
    if current_block:
        nozzle_blocks.append(current_block)

    # Get blind flags from plan/elevation views
    blind_flags = get_nozzle_blind_flags(text)

    nozzle_counts = defaultdict(
        lambda: {"qty": 0, "blind": 0, "repads": [], "repad_thk": []}
    )

    for block in nozzle_blocks:
        block_text = " ".join(block)
        desc_match = nozzle_pattern.search(block_text)
        if not desc_match:
            continue

        size, sch, nozzle_type = desc_match.groups()
        size += '"'  # Format like 2"
        repad_required = "No" if repad_required_pattern.search(block_text) else "Yes"

        # Determine which nozzle ID this is (e.g., Nozzle-0002)
        nozzle_id_match = re.search(r"Nozzle-(\d{4})", block_text)
        nozzle_id = f"Nozzle-{nozzle_id_match.group(1)}" if nozzle_id_match else None
        has_blind = blind_flags.get(nozzle_id, "No") if nozzle_id else "No"

        key = (size, sch, nozzle_type)

        nozzle_counts[key]["qty"] += 1
        if has_blind == "Yes":
            nozzle_counts[key]["blind"] += 1
        if repad_required == "Yes":
            repad_od_match = repad_od_pattern.search(block_text)
            repad_thk_match = repad_thk_pattern.search(block_text)
            repad_od = repad_od_match.group(1) if repad_od_match else "0"
            repad_thk = repad_thk_match.group(1) if repad_thk_match else "0"
            nozzle_counts[key]["repads"].append(repad_od)
            nozzle_counts[key]["repad_thk"].append(repad_thk)

    output = []
    for (size, sch, nozzle_type), data in nozzle_counts.items():
        repad_required = "Yes" if data["repads"] else "No"
        repad_od = max(map(int, data["repads"])) if data["repads"] else ""
        repad_thk = max(map(float, data["repad_thk"])) if data["repad_thk"] else ""

        output.append(
            {
                "QTY": data["qty"],
                "Size": size,
                "SCH": sch,
                "Type": nozzle_type,
                "With Blind": data["blind"],
                "Repad Required": repad_required,
                "Repad OD (in)": repad_od,
                "Repad Thickness (in)": repad_thk,
            }
        )

    return output


def extract_manways(text):
    # Grab the block starting at "Roof Manway:" through the next blank line or EOF
    manway_match = re.search(r"(Roof Manway:.*?)(?=\n\s*\n|$)", text, re.DOTALL)
    if not manway_match:
        return []

    block = manway_match.group(1)

    # Extract size and neck thickness
    size_match = re.search(r"MANWAY Description\s*:\s*(\d+)", block)
    neck_match = re.search(r"Neck Thickness\s*([\d.]+)", block)

    size = size_match.group(1) if size_match else "Unknown"
    neck_thk = neck_match.group(1) if neck_match else "Unknown"

    # Repad logic (same structure as nozzle fix)
    has_repad_text = "Reinforcement Pad is required" in block
    t_rpr_match = re.search(r"t_rpr\s*=\s*([\d.]+)\s*in", block)
    t_rpr_val = float(t_rpr_match.group(1)) if t_rpr_match else 0
    repad_required = has_repad_text and t_rpr_val > 0

    repad_od = re.search(r"Repad Size \(OD\) Must be = (\d+\.?\d*) in", block)

    return [
        {
            "QTY": 1,
            "Size": f'{size}"',
            "Neck Thickness (in)": neck_thk,
            "Type": "",  # Not in PDF
            "Repad Required": "Yes" if repad_required else "No",
            "Repad OD (in)": repad_od.group(1) if repad_od else "",
            "Repad Thickness (in)": f"{t_rpr_val:.4f}" if repad_required else "",
        }
    ]
