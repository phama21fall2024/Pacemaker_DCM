from fpdf import FPDF
from datetime import datetime
import matplotlib
matplotlib.use("Agg")  # render without opening a window
import matplotlib.pyplot as plt
import tempfile
import os


def _make_egram_plot(egram_data, out_png):

    if not egram_data:
        return False

    a_vals = [s.get("A", 0.0) for s in egram_data]
    v_vals = [s.get("V", 0.0) for s in egram_data]

    plt.figure(figsize=(8, 4))

    plt.subplot(2, 1, 1)
    plt.plot(a_vals)
    plt.ylim(0, 5)
    plt.title("Atrial")
    plt.ylabel("V")
    plt.xticks([])

    plt.subplot(2, 1, 2)
    plt.plot(v_vals)
    plt.ylim(0, 5)
    plt.title("Ventricular")
    plt.ylabel("V")
    plt.xlabel("Samples")

    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    return True


def generate_report(device_model: str,
                    device_serial: str,
                    application_model: str,
                    application_version: str,
                    dcm_serial: str,
                    report_name: str,
                    labels: list[str],
                    parameters: list[float],
                    egram_data: list[dict] = None,
                    output_filename: str = "report.pdf"):

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "McMaster University", ln=True, align="C")

    pdf.set_font("Arial", size=12)
    pdf.ln(5)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(0, 8, f"Report Generated: {timestamp}", ln=True)

    pdf.cell(0, 8, f"Device Model: {device_model}", ln=True)
    pdf.cell(0, 8, f"Device Serial Number: {device_serial}", ln=True)
    pdf.cell(0, 8, f"DCM Serial Number: {dcm_serial}", ln=True)
    pdf.cell(0, 8, f"Application Model: {application_model}", ln=True)
    pdf.cell(0, 8, f"Application Version: {application_version}", ln=True)
    pdf.cell(0, 8, f"Report Name: {report_name}", ln=True)

    pdf.ln(8)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Report Parameters", ln=True)
    pdf.set_font("Arial", size=12)

    for label, value in zip(labels, parameters):
        pdf.cell(0, 8, f"{label}: {value}", ln=True)

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Egram Graph", ln=True)

    # Create temp PNG for the plot
    tmp_png = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            tmp_png = f.name

        ok = _make_egram_plot(egram_data, tmp_png)

        if ok and os.path.exists(tmp_png):
            # fit nicely on page
            pdf.image(tmp_png, x=15, y=30, w=180)
        else:
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            pdf.cell(0, 8, "No egram data recorded.", ln=True)

    finally:
        if tmp_png and os.path.exists(tmp_png):
            os.remove(tmp_png)

    if egram_data:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Egram Data (Table)", ln=True)
        pdf.set_font("Arial", "B", 11)

        pdf.cell(20, 8, "Idx", 1, 0, "C")
        pdf.cell(40, 8, "Atrial (V)", 1, 0, "C")
        pdf.cell(40, 8, "Ventricular (V)", 1, 1, "C")
        pdf.set_font("Arial", size=11)

        # limit rows so page isn't huge
        data = egram_data[-100:]

        for i, sample in enumerate(data):
            a = float(sample.get("A", 0.0))
            v = float(sample.get("V", 0.0))
            pdf.cell(20, 8, str(i), 1, 0, "C")
            pdf.cell(40, 8, f"{a:.3f}", 1, 0, "C")
            pdf.cell(40, 8, f"{v:.3f}", 1, 1, "C")

    pdf.output(output_filename)
