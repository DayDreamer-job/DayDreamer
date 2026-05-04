# Install: pip install google-auth-oauthlib google-api-python-client

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/indexing"]

# This opens a browser window to login with YOUR Google account
flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret_524036274691-r5vpgiimg609gvfi7urfgk7nc2e0b42t.apps.googleusercontent.com.json",  # download this from Cloud Console (explained below)
    SCOPES
)
credentials = flow.run_local_server(port=0)
service = build("indexing", "v3", credentials=credentials)

result = service.urlNotifications().publish(body={
    "url": "https://jobs.newsmatrix.in",
    "type": "URL_UPDATED"
}).execute()

print("✅ Success:", result)