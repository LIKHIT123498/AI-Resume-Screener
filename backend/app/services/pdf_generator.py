import io
from typing import Dict, Any, Optional
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_candidate_profile_pdf(candidate: Dict[str, Any], job_title: str) -> bytes:
    """
    Generates a candidate evaluation PDF dossier containing scores,
    1-line AI summary, extracted skills, and contact details.
    Used when original uploaded files are not cached or for clean candidate dossiers.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#081b2a")
    accent_green = colors.HexColor("#15803d")
    accent_blue = colors.HexColor("#0284c7")
    slate_dark = colors.HexColor("#1e293b")
    slate_light = colors.HexColor("#64748b")
    bg_light = colors.HexColor("#f8fafc")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=slate_light,
        spaceAfter=12
    )

    candidate_name_style = ParagraphStyle(
        "CandidateName",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=primary_color
    )

    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=slate_dark
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=slate_dark
    )

    summary_box_style = ParagraphStyle(
        "SummaryBoxStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("AI RESUME SCREENER - CANDIDATE EVALUATION", title_style))
    story.append(Paragraph(f"Target Role: <b>{job_title}</b> | Generated on: {datetime.utcnow().strftime('%B %d, %Y')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2ad38a"), spaceAfter=14))

    # 2. Candidate Information & Overall Fit
    name = candidate.get("name") or "Candidate"
    email = candidate.get("email") or "Not specified in resume"
    phone = candidate.get("phone") or "Not specified in resume"
    fit_score = float(candidate.get("overall_fit_score") or 0.0)

    fit_label = "Strong Fit" if fit_score >= 70 else ("Moderate Fit" if fit_score >= 50 else "Low Match")
    fit_color = accent_green if fit_score >= 70 else (colors.HexColor("#a16207") if fit_score >= 50 else colors.HexColor("#b91c1c"))

    info_table_data = [
        [
            Paragraph(f"<b>Candidate:</b> {name}", candidate_name_style),
            Paragraph(f"<font color='{fit_color.hexval()}'><b>Overall Fit: {fit_score:.1f}%</b> ({fit_label})</font>", candidate_name_style)
        ],
        [
            Paragraph(f"<b>Email:</b> {email} &nbsp;|&nbsp; <b>Phone:</b> {phone}", body_style),
            Paragraph("", body_style)
        ]
    ]
    info_table = Table(info_table_data, colWidths=[3.5 * inch, 3.5 * inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # 3. Score Breakdown Cards
    skills_score = float(candidate.get("skills_score") or 0.0)
    seniority_score = float(candidate.get("seniority_score") or 0.0)
    domain_score = float(candidate.get("domain_score") or 0.0)

    scores_data = [
        [
            Paragraph("<b>Skills Match</b>", label_style),
            Paragraph("<b>Seniority Fit</b>", label_style),
            Paragraph("<b>Domain Expertise</b>", label_style)
        ],
        [
            Paragraph(f"<b>{skills_score:.1f}%</b>", title_style),
            Paragraph(f"<b>{seniority_score:.1f}%</b>", title_style),
            Paragraph(f"<b>{domain_score:.1f}%</b>", title_style)
        ]
    ]
    scores_table = Table(scores_data, colWidths=[2.33 * inch, 2.33 * inch, 2.33 * inch])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_light),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(scores_table)
    story.append(Spacer(1, 14))

    # 4. 1-Line AI Executive Summary
    summary = candidate.get("one_line_summary") or "Evaluation completed. Candidate profile matched against job requirements."
    story.append(Paragraph("<b>1-Line AI Executive Summary</b>", label_style))
    story.append(Spacer(1, 4))
    summary_table = Table([[Paragraph(f'"{summary}"', summary_box_style)]], colWidths=[7.0 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#bfdbfe")),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # 5. Extracted Skills
    skills = candidate.get("extracted_skills") or []
    if isinstance(skills, list) and skills:
        skills_str = ", ".join(str(s) for s in skills)
    elif isinstance(skills, str):
        skills_str = skills
    else:
        skills_str = "None explicitly extracted"
    story.append(Paragraph(f"<b>Key Extracted Skills:</b> {skills_str}", body_style))
    story.append(Spacer(1, 8))

    # 6. Stability & Tenure
    company_changes = candidate.get("company_changes", 0)
    avg_duration = float(candidate.get("avg_duration_months") or 0.0)
    tenure_info = f"<b>Career Stability:</b> {company_changes} company change(s) | Average tenure: {avg_duration:.1f} months"
    story.append(Paragraph(tenure_info, body_style))
    story.append(Spacer(1, 8))

    # 7. Red Flags or Notes
    red_flags = candidate.get("red_flags") or []
    if isinstance(red_flags, list) and red_flags:
        rf_text = "; ".join(str(r) for r in red_flags)
        story.append(Paragraph(f"<font color='#b91c1c'><b>Flags / Attention Points:</b> {rf_text}</font>", body_style))
        story.append(Spacer(1, 8))

    # 8. Footer Notice
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
    footer_text = "This candidate profile dossier was generated automatically by the AI Resume Screener evaluation engine."
    story.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=slate_light, alignment=1)))

    doc.build(story)
    return buffer.getvalue()
