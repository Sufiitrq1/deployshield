import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(
    deployment_name: str, 
    namespace: str, 
    image_tag: str, 
    rollout_status: str, 
    smoke_status: str, 
    error_logs: str, 
    output_filename: str = "deployshield_report.pdf"
) -> str:
    """
    Generates a localized, styled PDF incident and remediation report.
    Returns the absolute file path to the generated document.
    """
    # 1. Page setup
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom Palette
    primary_color = colors.HexColor("#A30000") if "fail" in rollout_status.lower() or "fail" in smoke_status.lower() else colors.HexColor("#1E4620")
    text_dark = colors.HexColor("#222222")
    bg_light = colors.HexColor("#F9F9F9")
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=24, leading=28,
        textColor=primary_color, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=colors.HexColor("#555555"), spaceAfter=20
    )
    section_heading = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=14, leading=18,
        textColor=text_dark, spaceBefore=15, spaceAfter=8
    )
    body_style = ParagraphStyle(
        'BodyDark', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=text_dark
    )
    log_style = ParagraphStyle(
        'LogText', parent=styles['Code'],
        fontName='Courier', fontSize=8, leading=11,
        textColor=colors.HexColor("#00FF00")
    )

    # 2. Header Elements
    story.append(Paragraph("DeployShield Automated Incident Report", title_style))
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Generated on: {current_time} | System-Triggered Rollback Trace", subtitle_style))
    story.append(Spacer(1, 10))
    
    # 3. Telemetry Metadata Table
    story.append(Paragraph("Deployment Core Telemetry", section_heading))
    metadata_data = [
        [Paragraph("<b>Target Metric</b>", body_style), Paragraph("<b>Observed Runtime Value</b>", body_style)],
        [Paragraph("Deployment Ident", body_style), Paragraph(deployment_name, body_style)],
        [Paragraph("Target Namespace", body_style), Paragraph(namespace, body_style)],
        [Paragraph("Image Version Tag", body_style), Paragraph(image_tag, body_style)],
        [Paragraph("Rollout Guard Status", body_style), Paragraph(f"<b>{rollout_status}</b>", body_style)],
        [Paragraph("Smoke Verification Status", body_style), Paragraph(f"<b>{smoke_status}</b>", body_style)]
    ]
    
    meta_table = Table(metadata_data, colWidths=[150, 380])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#EAEAEA")),
        ('TEXTCOLOR', (0, 0), (1, 0), text_dark),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # 4. Remediation Actions
    story.append(Paragraph("Automated Remediation Trace", section_heading))
    remediation_text = (
        "<b>Action Taken:</b> Active lifecycle anomalies detected. DeployShield issued an automated "
        "Kubernetes rolling patch sequence, resetting the orchestration state layout to the cluster's "
        "previously valid ReplicaSet configuration."
    )
    story.append(Paragraph(remediation_text, body_style))
    story.append(Spacer(1, 15))
    
    # 5. Diagnostic Log Streams (Code Box)
    story.append(Paragraph("Orchestration Log Stream / Event Buffer Output", section_heading))
    formatted_logs = error_logs.replace("\n", "<br/>").replace(" ", "&nbsp;")
    log_paragraph = Paragraph(formatted_logs, log_style)
    
    log_table = Table([[log_paragraph]], colWidths=[530])
    log_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#1A1A1A")),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('CORNER_RADIUS', (0, 0), (-1, -1), 4),
    ]))
    story.append(log_table)
    
    # Build Document
    doc.build(story)
    return os.path.abspath(output_filename)