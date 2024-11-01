#################
## START INTRO ##
#################

# Import required packages
import pandas as pd
import os
import io
import time
import re
import pickle
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# Define Important Variables
szns = range(2010,2023)

###############
## END INTRO ##
###############

# -- GOOGLE CONNECTION -- #
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

# -- SELENIUM CONNECTION -- #
# Setup Connection
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(service=service, options=options)

# -- SELENIUM ACTION -- #
# Initialize 
all_players = {}
id_df = pd.DataFrame()

# Access Website
url = 'https://moneypuck.com/stats.htm'
driver.get(url)
time.sleep(3)

## Loop through Years
for yr in szns:
    stryr = str(yr)  
    # Change Year
    driver.find_element(By.XPATH,'//select[@id="season_type"]').click()
    time.sleep(0.2)
    driver.find_element(By.XPATH,'//option[@value="'+stryr+'"]').click()
    time.sleep(4)

    ## Static Website Pull
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')

    ## Pull Table
    # Initiate blank vectors
    names = []
    pids = []
    positions = []
    teams = []

    # Loop through rows
    for x in soup.find_all('table')[8].find('tbody').find_all('tr',{'role':'row'}):
        # Pull out info
        name = x.find('a').text
        player_id = re.search("p=(.*)", x.find('a')['href']).group(1)
        position = x.find_all('td')[3].text
        team = re.search("logos/(.*)\.png", x.find_all('td')[1].find('img')['src']).group(1) 

        # Append to lists
        names.append(name)
        pids.append(player_id)
        positions.append(position)
        teams.append(team)

    # Merge into DF
    all_players[stryr] = pd.DataFrame({'Player':names,
                               'ID':pids,
                               'Position':positions,
                               'Team':teams})
    # Fix column type
    all_players[stryr]['ID'] = pd.to_numeric(all_players[stryr]['ID'])

    time.sleep(5)

# Expand Dictionary to DataFrame
for x in all_players.keys():
    id_df = pd.concat([id_df,all_players[x]],ignore_index=True)
id_df = id_df.drop_duplicates('ID').copy()
id_df = id_df[['Player','ID','Position']].copy()

# -- Upload to Google Drive -- #
# Write Pickle File #
id_df.to_pickle('nhl_id_df.pkl')

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': 'nhl_id_df.pkl',
                'parents':['1URkiueYI82LUyz8NG7NALvFyVSRhar5T']}
media = MediaFileUpload('nhl_id_df.pkl',
                        mimetype='application/octet-stream')
file = ggl_drive.files().create(body=file_metadata, media_body=media,
                              fields=returned_fields).execute()

# -- Download Pickle File -- #
# Read Pickle File
raw_result = service.files().get_media(fileId='1dAZTdqM1HWT8Ix5f4Ks6T0mqDUyEe-ex').execute()
new_id_df = pd.read_pickle(io.BytesIO(raw_result))

## Prove it has been read
print('This should say Antti Miettinen:',new_id_df.loc[2,'Player'])
