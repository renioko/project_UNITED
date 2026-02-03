from django.core.mail.backends.base import BaseEmailBackend
from mailjet_rest import Client
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MailjetBackend(BaseEmailBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = Client(
            auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY),
            version='v3.1'
        )
    
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        num_sent = 0
        for message in email_messages:
            try:
                # Przygotuj dane
                data = {
                    'Messages': [
                        {
                            "From": {
                                "Email": settings.DEFAULT_FROM_EMAIL,
                                "Name": "Portal UNITED"
                            },
                            "To": [
                                {"Email": recipient}
                                for recipient in message.to
                            ],
                            "Subject": message.subject,
                            "TextPart": message.body,
                        }
                    ]
                }
                
                # Jeśli email ma HTML (django-allauth zwykle wysyła HTML)
                if hasattr(message, 'alternatives') and message.alternatives:
                    for content, mimetype in message.alternatives:
                        if mimetype == 'text/html':
                            data['Messages'][0]['HTMLPart'] = content
                            break
                
                # Wyślij przez Mailjet API
                result = self.client.send.create(data=data)
                
                if result.status_code == 200:
                    num_sent += 1
                    logger.info(f"✅ Email sent to {message.to}")
                else:
                    logger.error(f"❌ Failed to send email: {result.json()}")
                    
            except Exception as e:
                logger.error(f"❌ Error sending email: {str(e)}")
                if not self.fail_silently:
                    raise
        
        return num_sent