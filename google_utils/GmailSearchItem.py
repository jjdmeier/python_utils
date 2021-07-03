
"""
GmailSearchItem: Item class used when searching for a specific email.

    Current search types:
        - string - Matches keyphrase and grabs string from email
        - uuid - Checks that unique identifier in email
        - bool - Matches keyphrase and flips bit based on email

Example usage:
    item = GmailSearchItem(name="Test", type=1, phrase="test=", default="default value", optional=False)
    
    item.get_allowed_types()
    
"""

ALLOWED_TYPES = {
    1: "string",
    2: "uuid",
    3: "bool"
}

class GmailSearchItem:

    """
    GmailSearchItem: constructor - initializes class with pertinent information for searching a message from Gmail

    params:
        name: String - Name of the item
        type: Integer - Types of GmailSearchItems
        phrase: String - Keyphrase to look for in email
        default: Type Matches type parameter - default value returned if phrase not found
        optional: Bool - ensures phrase is in the email if False or the email is ignored

    returns:
    """
    def __init__(self, name, type, phrase, default, optional):

        if optional != True and optional != False:
            raise Exception("Error: parameter 'optional' was not of type bool.")
        if not ALLOWED_TYPES.get(type):
            raise Exception("Error: parameter 'type' was an unkown. Valid Types: {}".format(ALLOWED_TYPES))

        self.name = name
        self.type = ALLOWED_TYPES.get(type)
        self.phrase = phrase
        self.default = default
        self.optional = optional
    
    """
    GmailSearchItem: get_allowed_types - Returns dictionary containing all allowed types

    params:

    returns:
        Dictionary: - contains a mapping of integer with an allowed type
    """
    def get_allowed_types(self):
        return ALLOWED_TYPES