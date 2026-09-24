import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

def build_email_html(job_title: str, candidates: List[Dict[str, Any]], notice: Optional[str] = None) -> str:
    """
    Builds a clean, responsive HTML email containing candidate fit scores,
    1-line AI summaries, and optional status notices.
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

    notice_html = ""
    if notice:
        notice_html = f"""
        <div style="background: #fffbeb; border: 1px solid #fde68a; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 13px; color: #92400e;">
            <strong>Notice:</strong> {notice}
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
                {notice_html}
                <p style="margin: 0 0 16px 0; font-size: 14px; color: #475569;">
                    The following <strong>{len(candidates)} resume(s)</strong> have been screened by AI:
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

def _create_smtp_session(host: str, preferred_port: int, timeout: int = 45):
    """
    Establishes an SMTP connection with intelligent fallback between
    SSL (port 465) and STARTTLS (port 587) to prevent timeouts on cloud hosts.
    """
    ports_to_try = [preferred_port]
    if preferred_port == 587 and 465 not in ports_to_try:
        ports_to_try.append(465)
    elif preferred_port == 465 and 587 not in ports_to_try:
        ports_to_try.append(587)
    elif 465 not in ports_to_try:
        ports_to_try.extend([465, 587])

    last_err = None
    for port in ports_to_try:
        try:
            logger.info(f"Attempting SMTP connection to {host}:{port}...")
            if port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=timeout)
                server.ehlo()
                return server
            else:
                server = smtplib.SMTP(host, port, timeout=min(timeout, 12))
                server.ehlo()
                if port in (587, 25):
                    server.starttls()
                    server.ehlo()
                return server
        except Exception as conn_err:
            logger.warning(f"Connection to {host}:{port} failed ({conn_err}). Trying fallback port...")
            last_err = conn_err

    raise ConnectionError(f"Could not connect to SMTP server {host} on any port ({ports_to_try}): {last_err}")

def send_screening_digest_email(
    recipient_email: str,
    job_title: str,
    candidates: List[Dict[str, Any]],
    attachments: Optional[List[Tuple[str, bytes]]] = None
) -> bool:
    """
    Sends an email with candidate fit scores, 1-line AI summaries,
    and attached resume files to the registered user's email.
    Includes a resilient fallback to send without attachments if file sizes
    or slow SMTP network causes an issue.
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

    # If SMTP is not yet configured, log a helpful guide and return cleanly
    if not smtp_user or not smtp_password:
        logger.warning(
            f"SMTP_USER or SMTP_PASSWORD is not configured in environment. "
            f"Skipping email to {recipient_email}. "
            f"To enable email delivery on Render/production, set SMTP_USER and SMTP_PASSWORD in Dashboard -> Environment."
        )
        return False

    attachments = attachments or []
    total_attach_bytes = 0
    MAX_ATTACH_BYTES = 10 * 1024 * 1024  # 10 MB raw limit (safe for Gmail 25MB total mime ceiling)

    attached_files: List[Tuple[str, bytes]] = []
    skipped_count = 0

    for filename, file_bytes in attachments:
        if not file_bytes:
            continue
        if total_attach_bytes + len(file_bytes) > MAX_ATTACH_BYTES:
            skipped_count += 1
            continue
        attached_files.append((filename, file_bytes))
        total_attach_bytes += len(file_bytes)

    notice: Optional[str] = None
    if skipped_count > 0:
        notice = (
            f"{len(attached_files)} of {len(attachments)} resume files attached. "
            f"{skipped_count} attachment(s) were omitted to keep the message within email provider delivery limits. "
            f"All {len(candidates)} candidate summaries and fit scores are included below."
        )
    elif attached_files:
        notice = f"The {len(attached_files)} original resume file(s) are attached to this email."

    # Build primary email message with attachments
    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = recipient_email
    msg["Subject"] = f"[{job_title}] {len(candidates)} Candidate(s) Screened - AI Summary"

    html_content = build_email_html(job_title, candidates, notice=notice)
    msg.attach(MIMEText(html_content, "html"))

    for filename, file_bytes in attached_files:
        try:
            part = MIMEApplication(file_bytes, Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            msg.attach(part)
        except Exception as attach_err:
            logger.error(f"Failed to attach resume {filename}: {attach_err}")

    # Step 1: Attempt sending with attachments (75s timeout)
    try:
        logger.info(
            f"Connecting to SMTP {smtp_host}:{smtp_port} to deliver {len(candidates)} candidates "
            f"({len(attached_files)} attachments, {total_attach_bytes / 1024:.1f} KB) to {recipient_email}..."
        )
        server = _create_smtp_session(smtp_host, smtp_port, timeout=75)
        try:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            logger.info(f"Successfully sent screening digest email for '{job_title}' to {recipient_email}")
            return True
        finally:
            try:
                server.quit()
            except Exception:
                pass

    except Exception as primary_err:
        logger.warning(
            f"Failed to send email with attachments to {recipient_email}: {primary_err}. "
            f"Initiating resilient fallback: delivering HTML summaries without attachments..."
        )

    # Step 2: Resilient Fallback - Send without attachments
    # This guarantees the user ALWAYS gets the candidate evaluations, scores, and 1-line AI summaries!
    try:
        fallback_msg = MIMEMultipart()
        fallback_msg["From"] = f"{from_name} <{smtp_user}>"
        fallback_msg["To"] = recipient_email
        fallback_msg["Subject"] = f"[{job_title}] {len(candidates)} Candidate(s) Screened - AI Summary"

        fallback_notice = (
            "Resume attachments were omitted due to attachment size or mail server delivery constraints. "
            f"All {len(candidates)} candidate evaluations, scores, and 1-line AI summaries are detailed below."
        )
        fallback_html = build_email_html(job_title, candidates, notice=fallback_notice)
        fallback_msg.attach(MIMEText(fallback_html, "html"))

        server = _create_smtp_session(smtp_host, smtp_port, timeout=30)
        try:
            server.login(smtp_user, smtp_password)
            server.send_message(fallback_msg)
            logger.info(f"Successfully delivered fallback digest email (no attachments) to {recipient_email}")
            return True
        finally:
            try:
                server.quit()
            except Exception:
                pass

    except Exception as fallback_err:
        logger.error(f"Fatal: Failed to send fallback digest email to {recipient_email}: {fallback_err}")
        return False
