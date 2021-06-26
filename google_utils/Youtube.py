import sys
import io
import http.client
import httplib2
import time
import random
import os
from mimetypes import MimeTypes
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError, flow_from_clientsecrets

try:
	from googleapiclient.errors import HttpError
	from apiclient import discovery
	import oauth2client
	from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
	from oauth2client import client
	from oauth2client import tools
except ImportError:
    print('goole-api-python-client is not installed. Try:')
    print('sudo pip install --upgrade google-api-python-client')
    sys.exit(1)

MAX_RETRIES = 10
httplib2.RETRIES = 1

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
VALID_PRIVACY_STATUSES = ["public", "private", "unlisted"]
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
  http.client.IncompleteRead, http.client.ImproperConnectionState,
  http.client.CannotSendRequest, http.client.CannotSendHeader,
  http.client.ResponseNotReady, http.client.BadStatusLine)



"""
GoogleDrive: Class for interacting with a google drive account programmatically 

Example usage:

    youtube = Youtube()
    youtube.initialize_upload(
        options = dict(
            file = "./test.mp4",
            keywords = "test, test1, test2",
            title = "video test",
            description = "this is from an api",
            categoryId = 1,
            privacyStatus = VALID_PRIVACY_STATUSES[1]
        )
    )
"""

"""
TODO: constructor - Do not auth in the constructor. Not generic enough. 
Make the program that is using it set the application name and secrets 
file path and call auth explicitly.
"""


class Youtube:

    """
    Youtube(): constructor

    returns:
        Youtube class object

    params:
        scopes: String - google developer scope. Example: "https://www.googleapis.com/auth/youtube"
        client_secret_file_path: String - path to google creds json from google developer account
        application_name: String - google developer application name

    """
    def __init__(
        self,
        scopes = "https://www.googleapis.com/auth/youtube",
        client_secret_file_path = './client_secrets.json',
        application_name = '',
    ):
        self.scopes = scopes
        self.client_secret_file_path = client_secret_file_path
        self.application_name = application_name

        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('youtube', 'v3', http=http)


    """
    Youtube(): get_credentials - checks if credentials already exist, if not save them to credential

    params:

    returns:
        credentials for oauth2client
    """
    def get_credentials(self):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                    'youtube-python-quickstart.json')
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.client_secret_file_path, self.scopes)
            flow.user_agent = self.application_name
            credentials = tools.run_flow(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    """
    Youtube(): resumable_upload - uploads provided file in a resumable approach

    params:
        insert_request: Object - created by insert Youtube API call

    returns:
        String: video id from succesful video upload
    """
    def resumable_upload(self, insert_request):
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                print ("Uploading file...")
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print ("Video id '%s' was successfully uploaded." % response['id'])
                        return response['id']
                    else:
                        exit("The upload failed with an unexpected response: %s" % response)
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
                else:
                    raise
            except RETRIABLE_EXCEPTIONS as e:
                error = "A retriable error occurred: %s" % e

            if error is not None:
                print (error)
                retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print ("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)

    """
    Youtube(): initialize_upload - gathers and sets all information needed for file upload

    params:
        options: Object - contains pertinent items for video upoload.
            example: 
                options = dict(
                    file = "./test.mp4",
                    keywords = "test, test1, test2",
                    title = "video test",
                    description = "this is from an api",
                    categoryId = 1,
                    privacyStatus = VALID_PRIVACY_STATUSES[1]
                )

    returns:
        String: video id from succesful video upload
    """
    def initialize_upload(self, options):
        keywords = options.get("keywords", "")
        if keywords:
            tags = keywords.split(",")
        body = dict(
            snippet = dict(
                title = options.get("title", ""),
                description = options.get("description", ""),
                tags = tags,
                categoryId = options.get("categoryId", "")
            ),
            status = dict(
                privacyStatus = options.get("privacyStatus", VALID_PRIVACY_STATUSES[2]) # default to unlisted if not provided
            )
        )
        insert_request = self.service.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(options.get("file"), chunksize=-1, resumable=True)
        ) 
        return self.resumable_upload(insert_request)