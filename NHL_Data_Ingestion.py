# Import required packages
import pandas as pd
import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# Prepare auth json for google connection
cred_json = os.environ['SERVICE_ACCOUNT_CREDENTIALS_JSON']
s_char = cred_json.index('~~~')
e_char = cred_json.index('%%%')
service_account_cred = eval(cred_json[s_char+3:e_char])

# Connect to the google service account
scope = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_info(
                              info=service_account_cred, 
                              scopes=scope)
ggl_drive = build('drive', 'v3', credentials=credentials)

# Setup Connection
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(service=service, options=options)
# Access Website
driver.get('https://www.pro-football-reference.com/teams/pit/2024.htm')
# Beautiful Soup
page_source = driver.page_source
soup = BeautifulSoup(page_source)
# Player Stats Table
player_stats = pd.read_html(str(soup.find_all('table',{'id':'rushing_and_receiving'})[0]))[0]
player_stats.columns = [x[1] for x in player_stats.columns]

# Write File
t_csv_stream = io.StringIO()
player_stats.to_csv(t_csv_stream, sep=";")

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': '2024 Steelers - 10.30.csv',
                'parents':['1GTyaZ1tRX1Wrh9LpHGRNoGJo6MWLEqsQ']}
media = MediaIoBaseUpload(t_csv_stream,
                        mimetype='text/csv')
file = ggl_drive.files().create(body=file_metadata, media_body=media,
                              fields=returned_fields).execute()
