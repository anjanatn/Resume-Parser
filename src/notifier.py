import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import urllib.request

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
HR_EMAIL = os.getenv("HR_EMAIL", "hr@company.com")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

def send_hr_email_alert(candidate, score, target_role="High-Priority Engineering Role"):
    """
    Sends email alert to HR team when a candidate achieves >= 80% suitability match.
    Falls back to console log if SMTP is not configured.
    """
    subject = f"Top Match Alert ({score}%): {candidate.get('name')} for {target_role}"
    
    body = f"""Hello HR Team,

A candidate has scored {score}% suitability for the role '{target_role}':

Candidate: {candidate.get('name')} ({candidate.get('title')})
Experience: {candidate.get('experience_years')} Years
Highest Degree: {candidate.get('highest_degree')}
Top Skills: {', '.join(candidate.get('skills', [])[:6])}
Email: {candidate.get('contact', {}).get('email', 'N/A')}
Phone: {candidate.get('contact', {}).get('phone', 'N/A')}

Summary:
{candidate.get('summary_pitch', '')}

Log in to the Resume Intelligence Platform to schedule an interview or review the full resume.
"""
    
    if SMTP_HOST and SMTP_USER and SMTP_PASS:
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = HR_EMAIL
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            print(f"[NOTIFIER] Sent HR email alert to {HR_EMAIL} for {candidate.get('name')}")
            return True, "Email sent successfully"
        except Exception as e:
            print(f"[NOTIFIER ERROR] Failed to send email via SMTP: {e}")
            return False, str(e)
    else:
        # Simulation mode
        print(f"[SIMULATED HR ALERT] Alert for score {score}% candidate {candidate.get('name')} (Target: {HR_EMAIL})")
        return True, "Alert simulated (Configure SMTP in .env for live sending)"

def dispatch_n8n_event(event_type, payload):
    """
    Send outbound JSON webhook to n8n workflow engine if N8N_WEBHOOK_URL is configured.
    """
    if not N8N_WEBHOOK_URL:
        return False, "N8N_WEBHOOK_URL not configured"
        
    try:
        data = json.dumps({"event": event_type, "data": payload}).encode("utf-8")
        req = urllib.request.Request(
            N8N_WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return True, f"n8n notified (Status {response.status})"
    except Exception as e:
        print(f"[N8N WEBHOOK ERROR] {e}")
        return False, str(e)
