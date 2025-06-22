# 🛢️ TankSnip: API-650 Calc Sheet Extractor

**TankSnip** is a lightweight Streamlit app designed to quickly extract key specs from API-650 tank calculation PDFs. It's built to support early-stage estimating by pulling critical details like dimensions, material specs, and course info — reducing the time spent hunting through long calc reports.

## 🚀 Live App  
👉 [Launch TankSnip](https://tanksnip.streamlit.app)

## 📂 Features

- Upload any API-650 PDF and extract key specs
- Instant display of critical tank data
- Export-ready output for integration with estimating workflows
- Currently supports:
  - Tank dimensions
  - Shell course breakdowns
  - Material types
  - Pressure ratings
  - Partial nozzle data (full nozzle support coming soon!)

## 🔧 Tech Stack

- **Python**
- **Streamlit** – for the interactive front end
- **pdfplumber** – for text extraction from PDF
- **re / pandas** – for parsing and formatting

## 📈 Roadmap

TankSnip is just the beginning. Planned enhancements include:

- Full **nozzle schedule extraction**
- Integration with an **estimation engine** (coming soon)
- Cloud database storage (AWS/GCP)
- Plate optimization and cost projection tools

## 📦 Setup (Dev Version)

```bash
# Clone the repo
git clone https://github.com/kelly12201984/Kellys-API-calc-reader-App.git

cd Kellys-API-calc-reader-App

# (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run API_calc_reader/app.py
```

## 🧠 Inspiration

Born from real-world shop floor frustration and estimating bottlenecks, TankSnip was built in close collaboration with professionals in tank fabrication. It's made to be fast, no-fluff, and built for how estimators actually work.

---

*Made with 💥 by Kelly – because you shouldn't have to scroll through 40-page calc sheets just to find a shell thickness.*
