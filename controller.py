from database import db_session
from models import User, Process, START, SCANNED, END, convertTime
import time

def verify_password(user_id, password):
    query = db_session.query(User)
    result = query.filter(User.user_id == user_id).filter(User.password == password).first()

    if result:
        return result
    else:
        return None


def verify_register(user):
    query = db_session.query(User)
    result = query.filter(User.user_id == user.user_id).first()
    print('result {0}'.format(result))
    if result != None:
        return False
    else:
        return True


def getInstanceOfUser(user_id):
    query = db_session.query(User)
    result = query.get(user_id)
    return result


def add_user(user):
    db_session.add(user)
    db_session.commit()

##Process
def addNewProcess(user_id, process_id):
    process = Process(process_id, user_id)
    db_session.add(process)
    db_session.commit()


def scanProcess(process_id):
    query = db_session.query(Process)
    print('process_id {0} need to be scanned'.format(process_id))
    result = query.filter(Process.process_id==process_id).first()
    print('scanProcess {0}'.format(result) )

    result.status = SCANNED
    db_session.commit()


def endProcess(user_id):
    query = db_session.query(Process)
    result = query.filter(Process.user_id==user_id).filter(Process.status!=END).first()
    result.status = END
    result.end_time = convertTime(time.time())
    db_session.commit()


def changeStatusOfProcess(user_id, status):
    query = db_session.query(Process)
    result = query.get(user_id)
    result.status = status
    db_session.commit()


def getProcessId(user_id):
    query = db_session.query(Process)
    result = query.filter(Process.user_id == user_id).filter(Process.status == SCANNED).first()
    return result.process_id


def checkWhetherScanned(user_id):
    query =db_session.query(Process)
    result = query.filter(Process.user_id == user_id).filter(Process.status == SCANNED).first()

    print(result)

    if result != None:
        return True
    else:
        return False


def startNewProcessPermission(user_id):
    query = db_session.query(Process)
    result = query.filter(Process.user_id == user_id).filter(Process.status==START or Process.status==SCANNED).first()

    if result is None:
        return True
    else:
        return False

