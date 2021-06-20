import sys
import io
import httplib2
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

"""
GoogleDrive: Class for interacting with a google drive account programmatically 

Example usage:

google_drive = GoogleDrive()

google_drive.upload("./example.mp4")
file_ids = google_drive.get_file_ids(example.mp4")
for file_id in file_ids:
    google_drive.share(file_id, "email@gmail.com")

print(google_drive.drive_files)
google_drive.pull_and_set_drive_files()
print(google_drive.drive_files)

google_drive.create_folder("Test folder")
file_id = google_driver.get_file_ids("Test folder")
print(google_drive.drive_files)
google_drive.delete(file_id)
print(google_drive.drive_files)
"""

class GoogleDrive:

    """
    GoogleDrive(): constructor

    returns:
        GoogleDrive class object

    params:
        scopes: String - google developer scope. Example: 'https://www.googleapis.com/auth/drive'
        client_secret_file_path: String - path to google creds json from google developer account
        application_name: String - google developer application name
        drive_files: List - used by multiple functions in the class to have a local list of google drive files

    """
    def __init__(
        self,
        scopes = 'https://www.googleapis.com/auth/drive',
        client_secret_file_path = './client_secrets.json',
        application_name = '',
        drive_files = []
    ):
        self.scopes = scopes
        self.client_secret_file_path = client_secret_file_path
        self.application_name = application_name
        self.drive_files = drive_files

        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('drive', 'v3', http=http)

    """
    GoogleDrive(): get_credentials - checks if credentials already exist, if not save them to credential

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
                                    'drive-python-quickstart.json')
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.client_secret_file_path, self.scopes)
            flow.user_agent = self.application_name
            credentials = tools.run_flow(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    """
    GoogleDrive(): upload - uploads a file to google drive

    params:
        file_path: String - full file path to the file that will be uploaded
        folder_id: String - Google Drive ID for the folder that you want to upload the file. Defaults to None
    
    returns:
        file id: String - the id of the uploaded file from Google Drive
    """
    def upload(self, file_path, folder_id=None):
        mime = MimeTypes()
        file_metadata = { 'name': os.path.basename(file_path) }

        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(
            file_path,
            mimetype=mime.guess_type(os.path.basename(file_path))[0],
            resumable=True
        )
        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
        except HttpError:
            print('File could not be uploaded to google drive. Could be corrupted.')
            pass
        print(file.get('id'))
        return file.get('id')

        
    """
    GoogleDrive(): pull_and_set_drive_files - grabs files from authed google drive account and saves them on a class variable: drive_files

    params:
    
    returns:

    """
    def pull_and_set_drive_files(self):
        results = self.service.files().list(fields="nextPageToken, files(id, name, mimeType)").execute()
        self.drive_files = results.get('files', [])


    """
    GoogleDrive(): get_file_ids - grabs and returns the id(s) for a specific file_name from authed google drive account

    params:
        file_name: String - name of the file on Google Drive
    
    returns:
        List: - with file id(s) because there can be multiple instances of a file with the same name
    """
    def get_file_ids(self, file_name):
        self.pull_and_set_drive_files()
        file_ids = []
        for item in self.drive_files:
                if file_name == item['name']:
                    file_ids.append(item['id'])
        return file_ids


    """
    GoogleDrive(): delete - remove file with specific id from Google Drive

    params:
        file_id: String - ID of the file that will be deleted from Google Drive
    
    returns:
    """
    def delete(self, file_id):
        self.service.files().delete(fileId=file_id).execute()
        self.pull_and_set_drive_files() # update list after deletion

    
    """
    GoogleDrive(): get_folder_contents_by_id - return all fild id(s) from a given folder

    params:
        folder_id: String - folder id in google drive that will be checked for its contents
    
    returns:
        List: - returns a list of the file id(s) in a given folder
    """
    def get_folder_contents_by_id(self, folder_id):
        folder_contents = []
        page_token = None
        while True:
            try:
                param = {}
                if page_token:
                    param['pageToken'] = page_token
                children = self.service.children().list(
                    folderId=folder_id, **param).execute()

                for child in children.get('items', []):
                    folder_contents.append(child['id'])
                page_token = children.get('nextPageToken')
                if not page_token:
                    break
            except:
                print ('An error occurred')
                break
        return folder_contents
    

    """
    GoogleDrive(): download - downloads a file to the current or specified directory

    params:
        file_id: String - ID of the file that will be downloaded from Google Drive
        path: String - path to directory where the download will go
    
    returns:

    """
    def download(self, file_id, path = os.getcwd()):
        request = self.service.files().get_media(fileId=file_id)
        name = self.service.files().get(fileId=file_id).execute()['name']
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(int(status.progress() * 100))
        f = open(path + '/' + name, 'wb')
        f.write(fh.getvalue())
        f.close()


    """
    GoogleDrive(): create_folder - creates either a single folder or replicates entire local folder structure in Google Drive

    params:
        folder: String - name of the folder that will be created
        recursive: Bool - will walk down the path starting at the root and upload the contents.
    
    returns:
        String: - Id of the folder that is now created in Google Drive
    """
    def create_folder(self, folder, recursive=False):
        if recursive:
            print('recursive ON')
            ids = {}
            for root, sub, files in os.walk(folder):
                par = os.path.dirname(root)

                file_metadata = {
                    'name': os.path.basename(root),
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if par in ids.keys():
                    file_metadata['parents'] = [ids[par]]
                file = self.service.files().create(body=file_metadata, fields='id').execute()
                id = file.get('id')
                ids[root] = id
                for f in files:
                    self.upload(root + '/' + f, id)
        else:
            print('recursive OFF')
            file_metadata = {
                    'name': os.path.basename(folder),
                    'mimeType': 'application/vnd.google-apps.folder'
                }
            file = self.service.files().create(body=file_metadata,
                                            fields='id').execute()
            print(file.get('id'))
            return(file.get('id'))


    """
    GoogleDrive(): share - shares a file or folder with a specified email

    params:
        file_id: String - ID of the file that will be shared from Google Drive
        email: String - email address that file will be shared with
    
    returns:

    """
    def share(self, file_id, email):
        def callback(request_id, response, exception):
            if exception:
                # Handle error
                print(exception)
            else:
                print("Got response: " + str(response.get('id')) + ". For request: " + str(request_id))

        batch = self.service.new_batch_http_request(callback=callback)
        user_permission = {
            'type': 'user',
            'role': 'reader',
            'emailAddress': email
        }
        batch.add(self.service.permissions().create(
            fileId=file_id,
            body=user_permission,
            fields='id',
        ))
        batch.execute()