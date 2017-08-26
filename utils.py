import os
import json

def getFriendList(user_id):
    contactListFileName = os.path.join(os.getcwd(),'static','user',user_id,'ContactList.json')
    if not os.path.exists(contactListFileName):
        return False

    with open(os.path.join(os.getcwd(),'static','user',user_id,'ContactList.json')) as fp:
        contactList = json.loads(fp.read())

    ret = []

    for contact in contactList:
        if contact["RemarkName"] != '':
            ret.append({"RemarkName":contact['RemarkName'],"NickName": contact['NickName']})

    return ret

def create_filter(remove_list):
    def filter_func(x):
        return not (x['NickName'] in remove_list)

    return filter_func


def removeSelectPeople(user_id, remove_list):
    with open(os.path.join(os.getcwd(),'static','user',user_id,'ContactList.json')) as fp:
        contactList = json.loads(fp.read())
        new_contactList = list(filter(create_filter(remove_list), contactList))

    with open(os.path.join(os.getcwd(), 'static', 'user', user_id, 'ContactList.json'), 'w') as fp:
        fp.write(json.dumps(new_contactList))



if __name__ == '__main__':
    print(getFriendList('jdluo'))
