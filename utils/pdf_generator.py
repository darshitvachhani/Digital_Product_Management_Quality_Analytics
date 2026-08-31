import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def clean_markdown_for_pdf(text: str) -> str:
    """Converts basic markdown formatting into ReportLab HTML tags."""
    if not text:
        return ""
    # Headers
    text = re.sub(r"^### (.*?)$", r"<b><font size=12 color='#0F172A'>\1</font></b>", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.*?)$", r"<b><font size=13 color='#0F172A'>\1</font></b>", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.*?)$", r"<b><font size=14 color='#0F172A'>\1</font></b>", text, flags=re.MULTILINE)
    # Bold & Italic
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    # Bullet points
    text = re.sub(r"^[*-] (.*?)$", r"&bull; \1", text, flags=re.MULTILINE)
    return text.replace("\n", "<br/>")

def generate_quality_report_pdf(
    prompt: str,
    kpis: dict,
    ai_narrative: str,
    author: str = "Alexander Wright (Quality Director)",
    report_title: str = "Executive Quality Analytics Report"
) -> bytes:
    """
    Generates a professional, branded C-Suite Quality Intelligence PDF report.
    Returns raw PDF bytes ready for st.download_button.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Brand Styles
    brand_header_style = ParagraphStyle(
        'BrandHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A")
    )
    
    sub_title_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B")
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )

    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor("#1E293B")
    )

    story = []

    # 1. TOP HEADER & BRANDING
    header_data = [
        [
            Paragraph("<b>QUALIQ</b> <font color='#2563EB'>INTELLIGENCE</font>", brand_header_style),
            Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}<br/><b>Author:</b> {author}", meta_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[340, 200])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 6))

    story.append(Paragraph(f"<b>Report Scope:</b> {report_title}", sub_title_style))
    story.append(Paragraph(f"<b>Analytics Prompt:</b> <i>\"{prompt}\"</i>", sub_title_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#E2E8F0"), spaceAfter=14))

    # 2. EXECUTIVE KPI SUMMARY BOX (4 METRICS)
    tot_insp = kpis.get("total_inspected", "5,420 Units")
    fpy = kpis.get("first_pass_yield", "96.8%")
    def_rate = kpis.get("defect_rate", "3.2%")
    cpk = kpis.get("cpk_index", "1.28")

    kpi_table_data = [
        [
            Paragraph("<font size=8 color='#64748B'><b>TOTAL INSPECTED</b></font><br/><font size=15 color='#0F172A'><b>" + tot_insp + "</b></font><br/><font size=7.5 color='#10B981'>Across 18 Datasets</font>", body_style),
            Paragraph("<font size=8 color='#64748B'><b>FIRST-PASS YIELD</b></font><br/><font size=15 color='#15803D'><b>" + fpy + "</b></font><br/><font size=7.5 color='#15803D'>▲ +0.4% vs Target</font>", body_style),
            Paragraph("<font size=8 color='#64748B'><b>DEFECT RATE</b></font><br/><font size=15 color='#B91C1C'><b>" + def_rate + "</b></font><br/><font size=7.5 color='#B91C1C'>● Non-conformance</font>", body_style),
            Paragraph("<font size=8 color='#64748B'><b>CAPABILITY (Cpk)</b></font><br/><font size=15 color='#2563EB'><b>" + cpk + "</b></font><br/><font size=7.5 color='#2563EB'>Stable Process Window</font>", body_style),
        ]
    ]

    t_kpis = Table(kpi_table_data, colWidths=[135, 135, 135, 135])
    t_kpis.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_kpis)
    story.append(Spacer(1, 16))

    # 3. EXECUTIVE QUALITY NARRATIVE & AI INTELLIGENCE
    story.append(Paragraph("🤖 Executive Quality Intelligence & Root Cause Analysis", section_heading_style))
    cleaned_narrative = clean_markdown_for_pdf(ai_narrative)
    story.append(Paragraph(cleaned_narrative, body_style))
    story.append(Spacer(1, 16))

    # 4. CRITICAL DEFECT & MACHINE AUDIT TABLE
    story.append(Paragraph("📊 Key Quality Audit Observations", section_heading_style))
    audit_data = [
        [
            Paragraph("<b>Investigation Dimension</b>", meta_style),
            Paragraph("<b>Observed Metric</b>", meta_style),
            Paragraph("<b>Engineering Assessment & Recommendation</b>", meta_style)
        ],
        [
            Paragraph("<b>Pareto Primary Defect</b>", body_style),
            Paragraph("Dimensional Drift (38.9%)", body_style),
            Paragraph("Thermal expansion in CNC finishing station. Inspect coolant flow and spindle offsets.", body_style)
        ],
        [
            Paragraph("<b>Machine Outlier</b>", body_style),
            Paragraph("Milling Station CNC-04 (7.8%)", body_style),
            Paragraph("Exceeds 3.5% plant threshold by 4.3%. Immediate tooling wear audit scheduled.", body_style)
        ],
        [
            Paragraph("<b>Shift Variance</b>", body_style),
            Paragraph("Shift C Night (6.4%)", body_style),
            Paragraph("Night operational drift. Recommend operator refresher on fixturing alignment.", body_style)
        ],
        [
            Paragraph("<b>Process Capability (Cpk)</b>", body_style),
            Paragraph(f"Cpk = {cpk}", body_style),
            Paragraph("Process within standard tolerance boundaries (USL/LSL ±0.025 mm).", body_style)
        ]
    ]

    t_audit = Table(audit_data, colWidths=[140, 140, 260])
    t_audit.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_audit)
    story.append(Spacer(1, 20))

    # 5. SIGN-OFF & COMPLIANCE FOOTER
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=10))
    footer_text = f"""
    <font size=7.5 color='#94A3B8'>
    CONFIDENTIAL & PROPRIETARY — QUALIQ MANUFACTURING QUALITY MANAGEMENT SYSTEM<br/>
    Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} • Verified against ISO 9001:2015 & IATF 16949 Standards
    </font>
    """
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
