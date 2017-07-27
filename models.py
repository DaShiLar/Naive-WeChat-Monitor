from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Time
from database import Base
import time
from flask_login import UserMixin

START = 0
SCANNED = 1
END = 2


def convertTime(timeStamp):
    timeArray = time.localtime(timeStamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime


class User(Base, UserMixin):

    __tablename__ = 'user'

    user_id = Column(String(20), primary_key=True, unique=True)
    password = Column(String(20))
    phone_number = Column(String(20))

    def __init__(self, user_id, password, phone_number):
        self.user_id = user_id
        self.password = password
        self.phone_number = phone_number

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user_id)


class Process(Base):

    __tablename__ = 'process'

    process_id = Column(Integer, primary_key=True)
    user_id = Column(String(20), ForeignKey('user.user_id'))
    status = Column(Integer)
    start_time = Column(Time)
    end_time = Column(Time)

    def __init__(self, process_id, user_id):
        self.process_id = process_id
        self.user_id = user_id
        self.status = START
        self.start_time = convertTime(time.time())
        self.end_time = 0
