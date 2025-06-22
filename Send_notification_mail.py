import smtplib
from email.message import EmailMessage
from datetime import datetime


SENDER_EMAIL = "qdefender100@gmail.com"
SENDER_PASSWORD = "uygwqktomwztatkf" 

def send_attack_detect_email(email):

 
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Security Alert Notification</title>
        <style>
            /* Inline CSS for email compatibility */
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .email-container {{
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }}
            .header {{
                border-bottom: 1px solid #eaeaea;
                padding-bottom: 20px;
                margin-bottom: 20px;
            }}
            .logo {{
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .alert-banner {{
                background-color: #fff8e6;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .alert-title {{
                color: #d32f2f;
                font-weight: bold;
                font-size: 18px;
                margin-bottom: 15px;
            }}
            .status-item {{
                display: flex;
                margin-bottom: 8px;
            }}
            .status-label {{
                font-weight: bold;
                min-width: 180px;
            }}
            .status-value {{
                color: #2e7d32;
            }}
            .status-value.warning {{
                color: #d32f2f;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eaeaea;
                font-size: 12px;
                color: #777777;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #4285f4;
                color: white !important;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                margin: 15px 0;
            }}
            @media only screen and (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}
                .email-container {{
                    padding: 20px;
                }}
                .status-label {{
                    min-width: 140px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <div class="logo">Unisys Q-Defender System</div>
                <div style="color: #777777;">Security Alert Notification</div>
            </div>
            
            <p>Dear Security Team,</p>
            
            <div class="alert-banner">
                <div class="alert-title">🚨 SECURITY ALERT: Anomaly Detected</div>
                <p>Our system has identified suspicious activity within the Quantum Escape Mechanism secure layer.</p>
            </div>
            
            <p><strong>🕒 Time of Detection:</strong> {timestamp}</p>
            
            <h3 style="margin-top: 25px; margin-bottom: 15px;">Incident Details</h3>
            <ul style="padding-left: 20px; margin-top: 0;">
                <li>An unexpected data pattern was detected by our anomaly detection model</li>
                <li>The breach attempt reached the fourth layer encapsulation</li>
                <li>Escape Protocol has been automatically triggered</li>
                <li>Data fragmentation process completed successfully</li>
            </ul>
            
            <h3 style="margin-top: 25px; margin-bottom: 15px;">System Status</h3>
            <div class="status-item">
                <div class="status-label">Backup Layer:</div>
                <div class="status-value">ACTIVATED </div>
            </div>
            <div class="status-item">
                <div class="status-label">ML Defense Response:</div>
                <div class="status-value">INITIATED </div>
            </div>
            <div class="status-item">
                <div class="status-label">Admin Notification:</div>
                <div class="status-value">DELIVERED </div>
            </div>
            <div class="status-item">
                <div class="status-label">Data Integrity:</div>
                <div class="status-value">SECURE </div>
            </div>
        
            
            <div class="footer">
                <p>This is an automated message. Please do not reply directly to this email.</p>
                <p>© {datetime.now().year} Q-Defender System. All rights reserved.</p>
            </div>
        </div>
        
        <!-- Minimal JavaScript - note most email clients will block this -->
        <script>
            // This would typically be blocked by email clients
            console.log('Security alert notification sent');
        </script>
    </body>
    </html>
    """
    msg = EmailMessage()
    msg.set_content(message_body)
    msg.set_content("This message contains HTML content.", subtype='plain')
    msg.add_alternative(message_body, subtype='html')
    msg['Subject'] = "ALERT: Anomaly Detected in Key wallet"
    msg['From'] = SENDER_EMAIL
    msg['To'] = email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)

        print(f"Message sent successfully!")

    except Exception as e:
        print(f"Failed to send email: {e}")

def send_welcome_email(recipient_email, username):
    login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Q-Defender</title>
        <style>
            /* Inline CSS for email compatibility */
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .email-container {{
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }}
            .header {{
                border-bottom: 1px solid #eaeaea;
                padding-bottom: 20px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .logo {{
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .welcome-banner {{
                background-color: #e8f5e9;
                border-left: 4px solid #4caf50;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .welcome-title {{
                color: #2e7d32;
                font-weight: bold;
                font-size: 18px;
                margin-bottom: 15px;
            }}
            .info-item {{
                display: flex;
                margin-bottom: 8px;
            }}
            .info-label {{
                font-weight: bold;
                min-width: 120px;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #4285f4;
                color: white !important;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                margin: 15px 0;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eaeaea;
                font-size: 12px;
                color: #777777;
                text-align: center;
            }}
            @media only screen and (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}
                .email-container {{
                    padding: 20px;
                }}
                .info-label {{
                    min-width: 100px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <div class="logo">Q-Defender Security Platform</div>
                <div style="color: #777777;">Advanced Threat Protection System</div>
            </div>
            
            <div class="welcome-banner">
                <div class="welcome-title">Welcome to Q-Defender, {username}!</div>
                <p>Thank you for choosing our advanced security solution to protect your digital assets.</p>
            </div>
            
            <p>We're pleased to confirm your successful login to the Q-Defender platform. Below are your login details:</p>
            
            <div class="info-item">
                <div class="info-label">Username:</div>
                <div>{username}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Login Time:</div>
                <div>{login_time} (UTC)</div>
            </div>
            
            
            <h3 style="margin-top: 25px; margin-bottom: 15px;">Getting Started</h3>
            <p>To help you make the most of Q-Defender, we recommend:</p>
            <ol style="padding-left: 20px; margin-top: 0;">
                <li>Reviewing your security settings</li>
                <li>Setting up notification preferences</li>
                <li>Exploring the dashboard features</li>
                <li>Configuring automated threat responses</li>
            </ol>
            
            
            <div class="footer">
                <p>Need help? Contact our <a href="mailto:qdefender100@gmail.com">support team</a> or visit our <a href="https://qdefender.example.com/help">help center</a>.</p>
                <p>© {datetime.now().year} Q-Defender Security Systems. All rights reserved.</p>
                <p style="font-size: 11px; color: #999999;">
                    This email was sent to {recipient_email} as part of your Q-Defender account notifications.
                    <br>If you didn't attempt to login, please secure your account immediately.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    msg = EmailMessage()
    msg.set_content("This message contains HTML content.", subtype='plain')
    msg.add_alternative(message_body, subtype='html')
    msg['Subject'] = f"Welcome to Q-Defender, {username}!"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)

        print(f"Welcome email sent successfully to {recipient_email}!")

    except Exception as e:
        print(f"Failed to send email: {e}")
def send_error_report_email(user_id, error_type, error_details):
 
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 
    system_status = "OPERATIONAL"
    alert_level = "⚠️ WARNING"
    if "critical" in error_type.lower():
        system_status = "DEGRADED"
        alert_level = "🚨 CRITICAL"
    elif "failure" in error_type.lower():
        system_status = "STABLE"
        alert_level = "⚠️ WARNING"

    message_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>System Error Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .email-container {{
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }}
            .header {{
                border-bottom: 1px solid #eaeaea;
                padding-bottom: 20px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
            }}
            .logo {{
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                margin-right: 15px;
            }}
            .alert-level {{
                font-size: 14px;
                padding: 4px 10px;
                border-radius: 4px;
                background-color: #fff8e6;
                color: #d32f2f;
                font-weight: bold;
            }}
            .alert-banner {{
                background-color: #f8f9fa;
                border-left: 4px solid #6c757d;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .error-title {{
                color: #d32f2f;
                font-weight: bold;
                font-size: 18px;
                margin-bottom: 15px;
            }}
            .detail-item {{
                display: flex;
                margin-bottom: 8px;
            }}
            .detail-label {{
                font-weight: bold;
                min-width: 120px;
            }}
            .detail-value {{
                color: #2c3e50;
            }}
            .system-status {{
                display: inline-block;
                padding: 4px 10px;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 5px;
            }}
            .status-normal {{
                background-color: #e8f5e9;
                color: #2e7d32;
            }}
            .status-warning {{
                background-color: #fff8e1;
                color: #ff8f00;
            }}
            .status-critical {{
                background-color: #ffebee;
                color: #d32f2f;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eaeaea;
                font-size: 12px;
                color: #777777;
            }}
            @media only screen and (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}
                .email-container {{
                    padding: 20px;
                }}
                .detail-label {{
                    min-width: 100px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <div class="logo">Q-Defender</div>
                <div class="alert-level">{alert_level}</div>
            </div>
            
            <p>Dear Development Team,</p>
            
            <div class="alert-banner">
                <div class="error-title">SYSTEM ERROR REPORT</div>
                <p>An error has been detected in the Q-Defender security system that requires your attention.</p>
            </div>
            
            <h3 style="margin-top: 25px; margin-bottom: 15px;">Error Details</h3>
            <div class="detail-item">
                <div class="detail-label">Timestamp:</div>
                <div class="detail-value">{timestamp}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">User ID:</div>
                <div class="detail-value">{user_id}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Error Type:</div>
                <div class="detail-value">{error_type}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">System Status:</div>
                <div class="detail-value">
                    <span class="system-status status-{system_status.lower()}">{system_status}</span>
                </div>
            </div>
            
            <h3 style="margin-top: 25px; margin-bottom: 15px;">Error Description</h3>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 4px; font-family: monospace; white-space: pre-wrap;">
                {error_details}
            </div>
            
            <h3 style="margin-top: 25px; margin-bottom: 15px;">Recommended Actions</h3>
            <ul style="padding-left: 20px; margin-top: 0;">
                <li>Review system logs for related events</li>
                <li>Check quantum encryption layer integrity</li>
                <li>Verify backup systems are operational</li>
                <li>Update incident tracking system</li>
            </ul>
            
            <div class="footer">
                <p>This is an automated error report from Q-Defender Monitoring System.</p>
                <p>© {datetime.now().year} Unisys Quantum Security. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    msg = EmailMessage()
    msg.set_content(f"""
    Q-Defender Error Report
    -----------------------
    Timestamp: {timestamp}
    User ID: {user_id}
    Error Type: {error_type}
    System Status: {system_status}
    
    Error Details:
    {error_details}
    
    This is an automated error report from Q-Defender Monitoring System.
    """)
    msg.add_alternative(message_body, subtype='html')
    msg['Subject'] = f"{alert_level} {error_type} - Q-Defender Error Report"
    msg['From'] = SENDER_EMAIL
    msg['To'] = "suriyaprasaadj04@gmail.com"

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"Error report sent successfully to")
    except Exception as e:
        print(f"Failed to send error report email: {e}")