import re
from collections import defaultdict


# Part 1
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


# PART 2
def parse_nozzle_table(text):
    lines = text.splitlines()
    nozzle_lines = [line for line in lines if re.search(r"\bNozzle-\b", line)]
    blind_map = {}

    for line in nozzle_lines:
        parts = line.split()
        if len(parts) >= 3:
            size = parts[1].replace('"', "")
            with_blind = "W/ BLIND" in line.upper()
            blind_map[line] = (size, with_blind)
    return blind_map


def extract_repad_details(text):
    pattern = re.compile(
        r"NOZZLE Description\s*:\s*(\d+)\s+in\s+SCH\s+([^\s]+)\s+TYPE\s+([^\n]+).*?"
        r"Repad Size.*?=\s*([\d.]+)\s*in.*?"
        r"t_rpr\s*=\s*([\d.]+)\s*in",
        re.DOTALL | re.IGNORECASE,
    )

    matches = pattern.findall(text)
    repads = {}
    for size, sch, typ, repad_od, t_rpr in matches:
        key = f"{size}in_{sch}_{typ}"
        t_rpr_val = float(t_rpr)
        if t_rpr_val == 0:
            t_rpr_val = 0.1875
        repads[key] = {
            "Repad Required?": "1",
            "Repad OD": float(repad_od),
            "Repad Thickness": t_rpr_val,
        }
    return repads


def group_nozzles_by_size_sch_type(nozzle_entries, full_text):
    grouped = defaultdict(lambda: {"QTY": 0, "With Blind?": 0})
    repad_info = extract_repad_details(full_text)

    for entry in nozzle_entries:
        size = entry["Size"].replace('"', "").strip()
        sch = entry.get("SCH", "").strip()
        typ = entry.get("Type", "").strip()
        has_blind = entry.get("With Blind?", "No") == "Yes"
        key = f"{size}in_{sch}_{typ}"

        grouped[key]["QTY"] += 1
        if has_blind:
            grouped[key]["With Blind?"] += 1

    results = []
    for key, group in grouped.items():
        size, sch, typ = key.split("_")
        base = {
            "Size": f'{size}"',
            "SCH": sch,
            "Type": typ,
            "QTY": group["QTY"],
            "With Blind?": group["With Blind?"],
        }
        base.update(
            repad_info.get(
                key, {"Repad Required?": "0", "Repad OD": "", "Repad Thickness": ""}
            )
        )
        results.append(base)

    return results


def extract_nozzles(text):
    nozzle_blocks = re.findall(
        r"Nozzle-[^\n]+\n.+?NOZZLE", text, re.DOTALL | re.IGNORECASE
    )
    nozzle_table_blinds = parse_nozzle_table(text)
    nozzles = []

    for line in text.splitlines():
        if "NOZZLE" in line.upper():
            parts = line.split()
            if not parts or len(parts) < 3:
                continue
            try:
                size = parts[1].replace('"', "")
                has_blind = "W/ BLIND" in line.upper()
                desc_match = re.search(
                    r"NOZZLE Description\s*:\s*(\d+)\s+in\s+SCH\s+([^\s]+)\s+TYPE\s+([^\n]+)",
                    text,
                    re.IGNORECASE,
                )
                sch = desc_match.group(2) if desc_match else "UNKNOWN"
                typ = desc_match.group(3) if desc_match else "UNKNOWN"

                nozzles.append(
                    {
                        "Size": f'{size}"',
                        "SCH": sch,
                        "Type": typ,
                        "With Blind?": "Yes" if has_blind else "No",
                    }
                )
            except Exception:
                continue

    return group_nozzles_by_size_sch_type(nozzles, text)


def extract_manways(text):
    manway_pattern = re.compile(
        r"MANWAY Description\s*:\s*(\d+)\s+in.*?t_rpr\s*=\s*([\d.]+)\s*in.*?"
        r"Repad Size.*?=\s*([\d.]+)\s*in",
        re.DOTALL | re.IGNORECASE,
    )

    matches = manway_pattern.findall(text)
    result = []

    for size, t_rpr, repad_od in matches:
        t_rpr_val = float(t_rpr)
        if t_rpr_val == 0:
            t_rpr_val = 0.1875
        result.append(
            {
                "Size": f'{size}"',
                "QTY": 1,
                "Repad Required?": "1",
                "Repad OD": float(repad_od),
                "Repad Thickness": t_rpr_val,
            }
        )

    return result
