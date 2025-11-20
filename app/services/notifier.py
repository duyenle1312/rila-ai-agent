from app.config import settings
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


def send_email_notification(blog_title, blog_url):
    """
    Send an email notification using Brevo API when a new blog is uploaded.

    Parameters:
    - blog_title (str): Title of the new blog.
    - blog_url (str): Notion URL link to the blog.
    """

    print("Sending email notification...")

    # Configure API key authorization
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    # Create an instance of the transactional email API
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration))

    # Prepare the email content
    subject = f"New Blog Created!"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 20px auto; padding: 20px;">
        
        <!-- Notification Header -->
        <h2 style="color: #D32F2F; text-align: center;">🎉 New Blog Created!</h2>
        <p style="text-align: center; font-size: 16px; color: #333333;">
            RILA AI Agent has successfully uploaded a new blog for you.
        </p>
        
        <!-- Blog Title -->
        <div style="margin: 20px 0; padding: 15px; background-color: #f8f8f8; border-left: 5px solid #D32F2F;">
            <p style="margin: 0; font-size: 16px; color: #555555;">Blog Title:</p><br/>
            <h4 style="margin: 5px 0 0 0; color: #000000;">{blog_title}</h4>
        </div>
        
        <!-- Blog URL -->
        <p style="font-size: 14px; color: #333333;">
            Please review the blog and click publish on Notion using this URL: <br/> <br/>
            <a href="{blog_url}" style="color: #D32F2F; text-decoration: none;">{blog_url}</a>
        </p>
        
        <!-- Footer -->
        <p style="margin-top: 30px; font-size: 14px; color: #555555;">
            Thanks and have a nice day!<br/><br/>
            Best regards,<br/>
            <strong>Your helpful AI Agent</strong>
        </p>

        <!-- Note about API -->
        <p style="margin-top: 20px; font-size: 12px; color: #999999; text-align: center;">
            This AI agent uses Google Gemini to summarize blog content.
        </p>
        </div>
    </body>
    </html>
    """

    sender = {"name": "RILA AI Agent", "email": settings.BREVO_SENDER_EMAIL}

    recipients = [settings.EMAIL_TO]

    to = [{"email": email} for email in recipients]

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=subject,
        html_content=html_content
    )

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(
            f"Email sent successfully. Message ID: {api_response.message_id}")
        return True
    except ApiException as e:
        print(f"Exception when sending email: {e}")
        return False
