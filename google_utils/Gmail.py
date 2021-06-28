import os
import sys
import time
import base64
import httplib2
from email import message
from mimetypes import MimeTypes
from posixpath import expanduser
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets

"""
Gmail: Class for interacting with a gmail account programmatically 

Example usage:

    gmail = Gmail()
    
    message = gmail.create_message(to="email@gmail.com", subject="Automated subject", message_text="Automated message body")
    gmail.send_message(message=message)
    
    gmail.pull_and_set_message_ids(max_results=1)
    print(gmail.message_ids)
    
    gmail.pull_and_set_message_contents_from_message_ids()
    print(gmail.message_contents)

    example_items_to_match = [
        {"name": "uuid", "type": "uuid", "phrase": "0123456789", "optional": False},
        {"name": "test", "type": "bool", "phrase": "test=true", "default": False, "optional": True},
        {"name": "test2", "type": "string", "phrase": "test2=", "default": "default_test2", "optional": True},
    ]    
    gmail.poll_email_and_get_response_from_user(items_to_match=example_items_to_match, retry_count=5, seconds_between_retries=10)

"""

"""
TODO: constructor - Do not auth in the constructor. Not generic enough. 
Make the program that is using it set the application name and secrets 
file path and call auth explicitly.
TODO: items_to_match - create a class for this object so that all possible
types are obvious to a user.
"""

class Gmail:

    """
    Gmail(): constructor

    returns:
        Gmail class object

    params:
        scopes: String - google developer scope. Example: 'https://mail.google.com/'
        client_secret_file_path: String - path to google creds json from google developer account
        application_name: String - google developer application name

    """
    def __init__(
        self,
        scopes = 'https://mail.google.com/',
        client_secret_file_path = './client_secrets.json',
        application_name = '',
    ):
        self.scopes = scopes
        self.client_secret_file_path = client_secret_file_path
        self.application_name = application_name
        self.message_ids = []
        self.message_contents = []

        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)

    """
    Gmail(): get_credentials - checks if credentials already exist, if not save them to credential

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
                                    'gmail-python-quickstart.json')
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.client_secret_file_path, self.scopes)
            flow.user_agent = self.application_name
            credentials = tools.run_flow(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    """
    Gmail(): create_message - Create a message for an email.

    params:
        to: String - Email address of the receiver.
        subject: String - The subject of the email message.
        message_text: String - The text of the email message.

    returns:
        Dictionary (object): - email safe message string stored in item "raw"
    """
    def create_message(self, to, subject, message_text):
        message = MIMEText(message_text)
        message['To'] = to
        message['Subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_string().encode("utf-8"))
        return {
            'raw': raw_message.decode("utf-8")
        }

    """
    Gmail(): create_message_with_attachment - Create a message for an email.

    params:
        sender: String - Email address of the sender.
        to: String - Email address of the receiver.
        subject: String - The subject of the email message.
        message_text: String - The text of the email message.
        file: String - The path to the file to be attached.

    returns:
        An object containing a base64url encoded email object.
    """
    def create_message_with_attachment(to, subject, message_text, file):

        message = MIMEMultipart()
        message['To'] = to
        message['Subject'] = subject

        msg = MIMEText(message_text)
        message.attach(msg)

        mime_types = MimeTypes()
        content_type, encoding = mime_types.guess_type(file)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(file, 'rb')
            msg = MIMEText(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(file, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(file, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(file, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(file)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

        return {'raw': base64.urlsafe_b64encode(message.as_string())}

    
    """
    Gmail(): send_message - Send an email message.

    params:
        message: Message object - Message to be sent.

    returns:
        Dictionary (object): Sent message object
    """
    def send_message(self, message):
        try:
            message = (self.service.users().messages().send(userId='me', body=message)
               .execute())
            print("Sent message id: {}".format(message.get('id')))
            return message
        except Exception as e: 
            raise Exception("Error: issue occured while sending message: {}".format(e))

    
    """
    Gmail(): pull_and_set_message_ids - loop through max_results number of message ids and set class variable message_ids eqaul to the ids

    params:
        max_results: Integer - number of (most recent) emails to pull and set ids for

    returns:
    """
    def pull_and_set_message_ids(self, max_results=5):
        self.message_ids = []
        result = self.service.users().messages().list(userId='me', maxResults=max_results).execute()
        messages = result.get('messages')
        for message in messages:
            if message.get("id"):
                self.message_ids.append(message.get("id"))

    
    """
    Gmail(): pull_and_set_message_contents_from_message_ids - loop through class variable message_ids and set class variable relevant message_contents

    params:
        inbox: String - Ensure message came from a specifc inbox
        users: List - Ensure message came from a specific email address

    returns:
    """
    def pull_and_set_message_contents_from_message_ids(self, inbox="INBOX", users=[]):
        self.message_contents = []

        for message_id in self.message_ids:
            self.message_contents.append(self.get_message_content(message_id=message_id, inbox=inbox, users=users))


    """
    Gmail(): save_attachment_from_message_id - pull relevant message using its id and download attachment to specified path

    params:
        message_id: String - message id provided by Google API
        path_for_attachment: String - path to where the file will be saved. Defaults to current directory.

    returns:
    """
    def save_attachment_from_message_id(self, message_id, path_for_attachment="."):
        message = {}
        try:
            message = self.service.users().messages().get(userId='me', id=message_id).execute()
        except Exception as e: 
            raise Exception("Error: unable to get messageId through google API call: {}".format(e))
        
        message_parts = message.get("payload").get("parts")
        if message_parts:
            for part in message_parts:
                if part.get('filename'):
                    if 'data' in part.get('body'):
                        data = part.get('body').get('data')
                    else:
                        att_id = part.get('body').get('attachmentId')
                        try:
                            att = self.service.users().messages().attachments().get(userId='me', messageId=message_id, id=att_id).execute()
                        except Exception as e: 
                            raise Exception("Error: unable to get attachmentId from messageId through google API call: {}".format(e))
                        data = att.get('data')
                    
                    if data:
                        file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                        path = path_for_attachment+"/"+part['filename']

                        with open(path, 'wb') as f:
                            f.write(file_data)
                    else:
                        raise Exception("Error: data not found for attachment in message that contains filename")


    """
    Gmail(): get_message_content - returns custom object with pertinent content from a google response to a get

    params:
        message_id: String - message id provided by Google API
        inbox: String - Ensure message came from a specifc inbox
        users: List - Ensure message came from a specific email address

    returns:
        Dictionary (object): Custom object with pertinent content from a google response. 
    """
    def get_message_content(self, message_id, inbox="INBOX", users=[]):
        response = {}
        try:
            response = self.service.users().messages().get(userId='me', id=message_id).execute()
        except Exception as e: 
            raise Exception("Error: unable to get messageId through google API call: {}".format(e))
        
        msg = dict()
        if response and response.get("labelIds") and inbox in response.get("labelIds"): 
            payload = response.get("payload")           
            headers = payload.get("headers")
            msg["Message-ID"] = message_id
            
            for header in headers:
                if header.get("name") == "Subject":
                    msg["Subject"] = header.get("value", "Subject has no value").replace('“','"').replace('”','"').replace("\r\n"," ")
                if header.get("name") == "From":
                    if len(users) > 0 and not any(user in header.get("value") for user in users):
                        return dict()
                    msg["From"] = header.get("value", "From has no value")
                if header.get("name") == "To":
                    msg["To"] = header.get("value", "To has no value")

            if payload.get("body").get("data"):
                base64_encoded_data = payload.get("body").get("data")
                msg["Body"] = base64.b64decode(base64_encoded_data.encode("utf8")).decode("utf8").replace('“','"').replace('”','"').replace("\r\n"," ")
            elif payload.get("parts"):
                for part in payload.get("parts"):
                    if part.get("mimeType") == "multipart/alternative":
                        if part.get("parts"):
                            for inner_part in part.get("parts"):
                                if inner_part.get("mimeType") == "text/plain":
                                    base64_encoded_data = inner_part.get("body").get("data")
                                    if base64_encoded_data:
                                        msg["Body"] = base64.b64decode(base64_encoded_data.encode("utf8")).decode("utf8").replace('“','"').replace('”','"').replace("\r\n"," ")
                    elif part.get("mimeType") == "text/plain":
                        base64_encoded_data = part.get("body").get("data")
                        if base64_encoded_data:
                            msg["Body"] = base64.b64decode(base64_encoded_data.encode("utf8")).decode("utf8").replace('“','"').replace('”','"').replace("\r\n"," ")
            else:
                raise Exception("Error: Not able to parse email: {}".format(response))

        return msg


    """
    Gmail(): is_correct_email - checks to see if email header/body contains all non-optional phrases

    params:
        message_text: String - email header and body text
        items_to_match: List - list of item keywords to search for in an email

    returns:
        Dictionary (object): Custom object with pertinent content from a google response. 
    """
    def is_correct_email(self, message_text, items_to_match):
        for item in items_to_match:
            if not item.get("optional") and item.get("phrase") not in message_text:
                return False
        return True

    """
    Gmail(): get_response_string - grabs string from email text based on keyword phrase

    params:
        message_text: String - email header and body text
        item: Dictionary - contains keyword to match with user email

    returns:
        String: string that is related to the keyword phrase or default if string not found in mail
    """
    def get_response_string(self, message_text, item):
        response_string = ""
        string_start = message_text.find(item.get("phrase"))
        while string_start < len(message_text):
            if message_text[string_start] == '"':
                string_start += 1
                while string_start < len(message_text) and message_text[string_start] != '"':
                    response_string += message_text[string_start]
                    string_start += 1
                break
            string_start += 1
        
        return response_string if response_string != "" else item.get("default")


    """
    Gmail(): get_response_for_item_from_message - builds and returns response for a given message

    params:
        message_text: String - email header and body text
        item: Dictionary - contains keywords to match with user email

    returns:
        response is varied based on item type. Could return string or bool. Defaults if value cannot be pulled from message
    """
    def get_response_for_item_from_message(self, message_text, item):
        response = item.get("default")
        item_type = item.get("type")

        if item_type == "string":
            if item.get("phrase") in message_text:
                response = self.get_response_string(message_text=message_text, item=item)
        elif item_type == "bool":
            response = True if item.get("phrase") in message_text else False
        elif item_type == "uuid":
            response = item.get("phrase")
        elif not item_type:
            raise Exception("Error: no type provided for item to find in email. Item is: {}".format(item))
        else:
            raise Exception("Error: Unknown type provided for item to find in email. Item is: {}".format(item))
        return response

    """
    Gmail(): get_response_from_user_email - builds and returns object for a given email

    params:
        items_to_match: List - list of item keywords to search for in an email

    returns:
        List: list of objects containing pertinent response data for items passed in
    """
    def get_response_from_user_email(self, items_to_match=[]):
        user_response = []
        for message_content in self.message_contents:
            combined_message_text = "{message_subject} {message_body}".format(message_subject=message_content.get("Subject"), message_body=message_content.get("Body"))
            if self.is_correct_email(message_text=combined_message_text, items_to_match=items_to_match):
                for item in items_to_match:
                    user_response.append({
                        "name": item.get("name"),
                        "type": item.get("type"),
                        "from": message_content.get("From"),
                        "message_id": message_content.get("Message-ID"),
                        "response": self.get_response_for_item_from_message(message_text=combined_message_text, item=item),
                    })
        return user_response

    """
    Gmail(): poll_email_and_get_response_from_user - polls email inbox and returns object for a given email

    params:
        items_to_match: List - list of item keywords to search for in an email
        inbox: String - Ensure message came from a specifc inbox
        users: List - Ensure message came from a specific email address
        retry_count: Integer - number of times to retry search for email
        seconds_between_retries: Integer - number of seconds to wait before retry

    returns:
        List: list of objects containing pertinent response data for items passed in
    """
    def poll_email_and_get_response_from_user(self, items_to_match, inbox="INBOX", users=[], retry_count=20, seconds_between_retries=10, max_results=1):
        
        tries = 0
        user_response = None
        while not user_response and tries < retry_count:
            
            print("Polling email. Try #: ", str(tries+1))
            self.pull_and_set_message_ids(max_results=max_results)
            self.pull_and_set_message_contents_from_message_ids(inbox=inbox, users=users)
            user_response = self.get_response_from_user_email(items_to_match=items_to_match)
            if user_response:
                break
            time.sleep(seconds_between_retries)
            tries += 1
        
        return user_response