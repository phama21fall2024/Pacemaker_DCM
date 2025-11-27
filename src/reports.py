from fpdf import FPDF
from datetime import datetime

def generate_report(device_model: str,
                    device_serial: str,
                    application_model: str,
                    application_version: str,
                    dcm_serial: str,
                    report_name: str,
                    labels: list[str],
                    parameters: list[float],
                    output_filename: str = "report.pdf"):

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "McMaster University", ln=True, align="C")

    pdf.set_font("Arial", size=12)
    pdf.ln(5)

    # Date & Time
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(0, 8, f"Report Generated: {timestamp}", ln=True)

    # Device information
    pdf.cell(0, 8, f"Device Model: {device_model}", ln=True)
    pdf.cell(0, 8, f"Device Serial Number: {device_serial}", ln=True)
    pdf.cell(0, 8, f"DCM Serial Number: {dcm_serial}", ln=True)
    pdf.cell(0, 8, f"Application Model: {application_model}", ln=True)
    pdf.cell(0, 8, f"Application Version: {application_version}", ln=True)
    pdf.cell(0, 8, f"Report Name: {report_name}", ln=True)

    pdf.ln(10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Report Parameters", ln=True)
    pdf.set_font("Arial", size=12)

    for label, value in zip(labels, parameters):
        pdf.cell(0, 8, f"{label}: {value}", ln=True)

    # Save PDF
    pdf.output(output_filename)


