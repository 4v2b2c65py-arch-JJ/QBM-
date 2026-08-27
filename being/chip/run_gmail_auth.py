import sys
sys.path.insert(0, '.')
from gmail_oauth import GmailOAuthEngine

engine = GmailOAuthEngine()
print('Opening browser for Google login...')
if engine.authenticate():
    print(f'SUCCESS: Logged in as {engine.user_email}')
    result = engine.send_email(
        to=engine.user_email,
        subject='ManaCiel - Gmail Active',
        body_text='Gmail OAuth is working!'
    )
    print(f'Test email: {"sent" if result.success else "failed"}')
else:
    print('FAILED: Authentication did not complete')
