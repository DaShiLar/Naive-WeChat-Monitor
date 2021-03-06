from database import db_session
from models import User, Process, START, SCANNED, END, convertTime
import time
import os
from sqlalchemy import or_

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
    results = query.filter(Process.user_id==user_id).all()
    ##找出属于这个用户的所有进程，然后一个一个判断是否进程存在，存在就杀掉,不存在抛出异常继续

    for result in results:
        try:
            result.status = END
            result.end_time = convertTime(time.time())
            print("process_id to be killed is {0}".format(result.process_id))
            checkProcess = os.kill(result.process_id, 0)
        except OSError:
            continue
        else:
            os.kill(result.process_id, 9)

    db_session.commit()


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
    result = query.filter(Process.user_id == user_id).filter(or_(Process.status == START,  Process.status == SCANNED)).first()

    if result is None:
        return True
    else:
        print ("user_id={0}".format(user_id))
        print(result)
        return False

