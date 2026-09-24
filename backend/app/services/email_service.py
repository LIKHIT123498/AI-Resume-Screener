import os
import smtplib
import logging
import base64
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

def build_email_html(
    job_title: str,
    candidates: List[Dict[str, Any]],
    notice: Optional[str] = None,
    has_attachments: bool = True
) -> str:
    """
    Builds a clean, responsive HTML email containing candidate fit scores,
    1-line AI summaries, and indicating attached resume files (PDF/DOC).
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

        status_badge = (
            '<span style="font-size: 11px; color: #166534; font-weight: 600;">📎 Resume file attached</span>'
            if has_attachments else
            '<span style="font-size: 11px; color: #64748b; font-weight: 500;">AI Profile Evaluated</span>'
        )

        candidate_rows += f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">📄</span>
                    <div>
                        <h3 style="margin: 0; font-size: 15px; color: #0f172a; font-weight: 700;">{name}</h3>
                        {status_badge}
                    </div>
                </div>
                <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; font-size: 12px; font-weight: 700; padding: 4px 11px; border-radius: 9999px;">
                    {fit_score:.1f}% Fit
                </span>
            </div>
            <div style="background: #f8fafc; border-left: 3px solid #0284c7; padding: 9px 12px; border-radius: 4px; margin-top: 6px;">
                <span style="font-size: 10px; font-weight: 700; color: #0284c7; text-transform: uppercase; letter-spacing: 0.5px;">1-Line AI Summary</span>
                <p style="margin: 3px 0 0 0; color: #334155; font-size: 13px; line-height: 1.45;">
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

    intro_text = (
        f"The original resume files (PDF/DOC) for <strong>{len(candidates)} candidate(s)</strong> are attached to this email along with their 1-line AI evaluation summaries and fit scores:"
        if has_attachments else
        f"Candidate screening summaries and fit scores for <strong>{len(candidates)} candidate(s)</strong> are listed below:"
    )

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
                <h1 style="margin: 6px 0 0 0; color: #ffffff; font-size: 20px; font-weight: 800;">Candidate Screening Digest</h1>
                <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">Role: <strong style="color: #f8fafc;">{job_title}</strong></p>
            </div>

            <!-- Body -->
            <div style="padding: 24px; background: #f8fafc;">
                {notice_html}
                <p style="margin: 0 0 16px 0; font-size: 14px; color: #475569;">
                    {intro_text}
                </p>
                {candidate_rows}
            </div>

            <!-- Footer -->
            <div style="padding: 16px 24px; background: #edf2f7; text-align: center; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b;">
                Delivered automatically by <strong>AI Resume Screener</strong>.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def _send_via_resend(
    api_key: str,
    recipient_email: str,
    job_title: str,
    candidates: List[Dict[str, Any]],
    attachments: Optional[List[Tuple[str, bytes]]] = None
) -> bool:
    """
    Sends email via the Resend HTTP API (Port 443).
    Bypasses outbound SMTP port blocks on Render, AWS, and other cloud providers.
    Attaches the candidate resume files (PDF/DOC/DOCX) and includes 1-line AI summaries.
    """
    attachments = attachments or []
    from_sender = os.getenv("RESEND_FROM_EMAIL", "AI Resume Screener <onboarding@resend.dev>")
    
    total_attach_bytes = 0
    MAX_ATTACH_BYTES = 18 * 1024 * 1024  # 18 MB raw limit (stays under 25MB after base64 encoding)
    attached_files = []
    skipped_count = 0

    for fname, fbytes in attachments:
        if not fbytes:
            continue
        if total_attach_bytes + len(fbytes) > MAX_ATTACH_BYTES:
            skipped_count += 1
            continue
        attached_files.append((fname, fbytes))
        total_attach_bytes += len(fbytes)

    notice: Optional[str] = None
    if skipped_count > 0:
        notice = (
            f"📎 <strong>{len(attached_files)} of {len(attachments)} resume files attached.</strong> "
            f"({skipped_count} attachment(s) were omitted to stay within email delivery limits). "
            f"All {len(candidates)} candidates and 1-line summaries are listed below."
        )
    elif attached_files:
        notice = f"📎 <strong>All {len(attached_files)} candidate resume file(s) are attached to this email.</strong>"

    has_attachments = bool(attached_files)
    html_content = build_email_html(job_title, candidates, notice=notice, has_attachments=has_attachments)

    target_recipient = os.getenv("RESEND_RECIPIENT_OVERRIDE") or recipient_email

    subject_suffix = "Resumes & AI Summaries Attached" if has_attachments else "Candidate Screening Digest"
    payload = {
        "from": from_sender,
        "to": [target_recipient],
        "subject": f"[{job_title}] {len(candidates)} Candidate(s) Screened - {subject_suffix}",
        "html": html_content,
    }

    if attached_files:
        payload["attachments"] = [
            {
                "filename": fname,
                "content": base64.b64encode(fbytes).decode("utf-8")
            }
            for fname, fbytes in attached_files
        ]

    try:
        logger.info(f"Sending email via Resend HTTP API (Port 443) to {target_recipient} ({len(attached_files)} attachments)...")
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=35
        )
        if resp.status_code in (200, 201):
            logger.info(f"Successfully delivered screening digest email via Resend to {target_recipient} with {len(attached_files)} attachments")
            return True

        logger.warning(f"Resend API error {resp.status_code}: {resp.text}")

        # Case A: Resend Free Tier sandbox limitation
        # "You can only send testing emails to your own email address (owner@gmail.com)..."
        if resp.status_code == 403 and "only send testing emails to your own email address" in resp.text:
            import re
            match = re.search(r'\(([^)]+@[^)]+)\)', resp.text)
            sandbox_owner = match.group(1) if match else None
            if sandbox_owner and sandbox_owner.lower() != target_recipient.lower():
                logger.warning(
                    f"Resend sandbox limitation: cannot deliver to {target_recipient}. "
                    f"Automatically redirecting to Resend account owner: {sandbox_owner}..."
                )
                sandbox_notice = (
                    f"Delivered to your Resend account email ({sandbox_owner}) because "
                    f"onboarding@resend.dev is in test sandbox mode. "
                    f"(Intended recipient was: {target_recipient}). "
                    f"To deliver directly to {target_recipient}, sign up for Resend using {target_recipient} "
                    f"or verify your custom domain."
                )
                combined_notice = f"{sandbox_notice}<br/><br/>{notice}" if notice else sandbox_notice
                payload["to"] = [sandbox_owner]
                payload["html"] = build_email_html(job_title, candidates, notice=combined_notice, has_attachments=has_attachments)
                redirect_resp = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=35
                )
                if redirect_resp.status_code in (200, 201):
                    logger.info(f"Successfully redirected email to Resend account owner {sandbox_owner} with {len(attached_files)} attachments")
                    return True
                else:
                    logger.warning(f"Redirect attempt error: {redirect_resp.status_code}: {redirect_resp.text}")

        # Case B: If rejected due to payload size, retry without attachments
        if payload.get("attachments"):
            logger.info("Retrying Resend send without attachments...")
            payload.pop("attachments")
            payload["html"] = build_email_html(
                job_title,
                candidates,
                notice="Resume attachments exceeded maximum email size limits and were omitted. Candidate summaries are shown below.",
                has_attachments=False
            )
            retry_resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=25
            )
            if retry_resp.status_code in (200, 201):
                logger.info(f"Successfully delivered fallback digest email via Resend to {payload['to']}")
                return True
        return False
    except Exception as e:
        logger.error(f"Resend HTTP request exception: {e}")
        return False

def _create_smtp_session(host: str, preferred_port: int, timeout: int = 25):
    """
    Establishes an SMTP connection with intelligent fallback between
    SSL (port 465) and STARTTLS (port 587).
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
                server = smtplib.SMTP(host, port, timeout=min(timeout, 10))
                server.ehlo()
                if port in (587, 25):
                    server.starttls()
                    server.ehlo()
                return server
        except Exception as conn_err:
            logger.warning(f"Connection to {host}:{port} failed ({conn_err}). Trying fallback port...")
            last_err = conn_err

    raise ConnectionError(f"Could not connect to SMTP server {host} on any port ({ports_to_try}): {last_err}")

def _send_via_smtp(
    recipient_email: str,
    job_title: str,
    candidates: List[Dict[str, Any]],
    attachments: Optional[List[Tuple[str, bytes]]] = None
) -> bool:
    """
    Sends email via traditional SMTP.
    Used for local development or cloud environments where SMTP egress is permitted.
    Attaches the original candidate resume files (PDF/DOC/DOCX) and includes 1-line AI summaries.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port_raw = os.getenv("SMTP_PORT", "587")
    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        smtp_port = 587

    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_name = os.getenv("SMTP_FROM_NAME", "AI Resume Screener")

    if not smtp_user or not smtp_password:
        logger.warning(
            f"Neither RESEND_API_KEY nor SMTP credentials (SMTP_USER/SMTP_PASSWORD) are configured. "
            f"Skipping email delivery to {recipient_email}."
        )
        return False

    attachments = attachments or []
    total_attach_bytes = 0
    MAX_ATTACH_BYTES = 18 * 1024 * 1024  # 18 MB raw limit

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

    has_attachments = bool(attached_files)
    notice: Optional[str] = None
    if skipped_count > 0:
        notice = (
            f"📎 <strong>{len(attached_files)} of {len(attachments)} resume files attached.</strong> "
            f"({skipped_count} attachment(s) were omitted to keep the message within email provider delivery limits). "
            f"All {len(candidates)} candidates and 1-line summaries are listed below."
        )
    elif attached_files:
        notice = f"📎 <strong>All {len(attached_files)} resume file(s) are attached to this email.</strong>"

    subject_suffix = "Resumes & AI Summaries Attached" if has_attachments else "Candidate Screening Digest"
    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = recipient_email
    msg["Subject"] = f"[{job_title}] {len(candidates)} Candidate(s) Screened - {subject_suffix}"

    html_content = build_email_html(job_title, candidates, notice=notice, has_attachments=has_attachments)
    msg.attach(MIMEText(html_content, "html"))

    for filename, file_bytes in attached_files:
        try:
            part = MIMEApplication(file_bytes, Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            msg.attach(part)
        except Exception as attach_err:
            logger.error(f"Failed to attach resume {filename}: {attach_err}")

    # Primary attempt: send with attachments
    try:
        logger.info(f"Connecting to SMTP {smtp_host}:{smtp_port} to deliver to {recipient_email}...")
        server = _create_smtp_session(smtp_host, smtp_port, timeout=30)
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
            f"Failed to send email with attachments via SMTP ({primary_err}). "
            f"Attempting fallback send without attachments..."
        )

    # Fallback: send clean HTML digest without attachments
    try:
        fallback_msg = MIMEMultipart()
        fallback_msg["From"] = f"{from_name} <{smtp_user}>"
        fallback_msg["To"] = recipient_email
        fallback_msg["Subject"] = f"[{job_title}] {len(candidates)} Candidate(s) Screened - Resumes & AI Summaries Attached"

        fallback_notice = (
            "Resume attachments were omitted due to mail delivery constraints. "
            f"All {len(candidates)} candidate evaluations, scores, and 1-line AI summaries are detailed below."
        )
        fallback_html = build_email_html(job_title, candidates, notice=fallback_notice)
        fallback_msg.attach(MIMEText(fallback_html, "html"))

        server = _create_smtp_session(smtp_host, smtp_port, timeout=20)
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

def send_screening_digest_email(
    recipient_email: str,
    job_title: str,
    candidates: List[Dict[str, Any]],
    attachments: Optional[List[Tuple[str, bytes]]] = None
) -> bool:
    """
    Unified email dispatcher:
    1. If RESEND_API_KEY is configured: Uses Resend HTTP API (Port 443),
       which works reliably on Render Free Tier where outbound SMTP ports are blocked.
    2. Otherwise: Uses SMTP (ports 587/465), suitable for localhost or non-blocked hosts.
    Includes both the 1-line AI summaries and attached resume files.
    """
    if not recipient_email or not candidates:
        logger.info("No recipient email or candidates provided for email digest.")
        return False

    resend_api_key = os.getenv("RESEND_API_KEY")
    if resend_api_key:
        return _send_via_resend(
            api_key=resend_api_key,
            recipient_email=recipient_email,
            job_title=job_title,
            candidates=candidates,
            attachments=attachments
        )

    return _send_via_smtp(
        recipient_email=recipient_email,
        job_title=job_title,
        candidates=candidates,
        attachments=attachments
    )
