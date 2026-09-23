import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

def build_email_html(job_title: str, candidates: List[Dict[str, Any]]) -> str:
    """
    Builds a clean, responsive HTML email containing candidate fit scores
    and 1-line AI summaries.
    """
    candidate_rows = ""
    for candidate in candidates:
        name = candidate.get("name") or "Candidate"
        fit_score = candidate.get("overall_fit_score", 0.0)
        summary = candidate.get("one_line_summary") or "No summary generated."
        
        # Color coding for fit score
        if fit_score >= 70:
            badge_bg = "#dcfce7"
            badge_color = "#15803d"
            badge_border = "#86efac"
        elif fit_score >= 50:
            badge_bg = "#fef9c3"
            badge_color = "#a16207"
            badge_border = "#fde047"
        else:
            badge_bg = "#fee2e2"
            badge_color = "#b91c1c"
            badge_border = "#fca5a5"

        candidate_rows += f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 16px; color: #0f172a; font-weight: 700;">{name}</h3>
                <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; font-size: 13px; font-weight: 700; padding: 3px 10px; border-radius: 9999px;">
                    {fit_score:.1f}% Fit
                </span>
            </div>
            <div style="background: #f8fafc; border-left: 3px solid #0284c7; padding: 10px 12px; border-radius: 4px; margin-top: 8px;">
                <span style="font-size: 11px; font-weight: 700; color: #0284c7; text-transform: uppercase; letter-spacing: 0.5px;">1-Line AI Summary</span>
                <p style="margin: 4px 0 0 0; color: #334155; font-size: 14px; line-height: 1.5;">
                    {summary}
                </p>
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; color: #334155;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #cbd5e1; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <!-- Header -->
            <div style="background: #081b2a; padding: 24px; text-align: left; border-bottom: 3px solid #2ad38a;">
                <div style="font-size: 12px; color: #7ef0be; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;">AI Resume Screener</div>
                <h1 style="margin: 6px 0 0 0; color: #ffffff; font-size: 20px; font-weight: 800;">New Resumes Screened</h1>
                <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">Role: <strong style="color: #f8fafc;">{job_title}</strong></p>
            </div>

            <!-- Body -->
            <div style="padding: 24px; background: #f8fafc;">
                <p style="margin: 0 0 16px 0; font-size: 14px; color: #475569;">
                    The following <strong>{len(candidates)} resume(s)</strong> have been screened by AI. The original resume files are attached to this email.
                </p>
                {candidate_rows}
            </div>

            <!-- Footer -->
            <div style="padding: 16px 24px; background: #edf2f7; text-align: center; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b;">
                Generated automatically by <strong>AI Resume Screener</strong>.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_screening_digest_email(
    recipient_email: str,
    job_title: str,
    candidates: List[Dict[str, Any]],
    attachments: List[Tuple[str, bytes]]
) -> bool:
    """
    Sends an email with candidate fit scores, 1-line AI summaries,
    and attached resume files to the registered user's email.
    """
    if not recipient_email or not candidates:
        logger.info("No recipient email or candidates provided for email digest.")
        return False

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port_raw = os.getenv("SMTP_PORT", "587")
    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        smtp_port = 587

    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_name = os.getenv("SMTP_FROM_NAME", "AI Resume Screener")

    # If SMTP is not yet configured, log a helpful guide and return cleanly without crashing
    if not smtp_user or not smtp_password:
        logger.warning(
            f"SMTP_USER or SMTP_PASSWORD is not configured in .env. "
            f"Skipping email to {recipient_email}. "
            f"To enable email delivery, set SMTP_USER and SMTP_PASSWORD in your backend .env file."
        )
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = f"{from_name} <{smtp_user}>"
        msg["To"] = recipient_email
        msg["Subject"] = f"[{job_title}] {len(candidates)} New Candidate(s) Screened - AI Summary"

        # Attach HTML body
        html_content = build_email_html(job_title, candidates)
        msg.attach(MIMEText(html_content, "html"))

        # Attach resumes
        for filename, file_bytes in attachments:
            if not file_bytes:
                continue
            try:
                part = MIMEApplication(file_bytes, Name=filename)
                part["Content-Disposition"] = f'attachment; filename="{filename}"'
                msg.attach(part)
            except Exception as attach_err:
                logger.error(f"Failed to attach resume {filename}: {attach_err}")

        # Send via SMTP
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.ehlo()
            if smtp_port in (587, 25):
                server.starttls()
                server.ehlo()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Successfully sent screening digest email for '{job_title}' to {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send screening digest email to {recipient_email}: {e}")
        return False
