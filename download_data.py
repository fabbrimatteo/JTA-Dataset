
from google_drive_downloader import GoogleDriveDownloader as gdd
import sys
import os

key = input('Please, enter the JTA-Key we have sent you by email: ')
cwd = os.getcwd()

print('The dataset will be download in ', cwd)

gdd.download_file_from_google_drive(file_id=key, dest_path=cwd + '/jta_dataset.zip', unzip=True, showsize=True)

print('Done!')
