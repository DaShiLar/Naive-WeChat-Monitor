from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DB_CONNECT_STRING = 'mysql+pymysql://root:She68105028@localhost:3306/test'
engine = create_engine(DB_CONNECT_STRING, echo=False)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.qeury = db_session.query_property()

def init_db():

    import models
    Base.metadata.create_all(bind=engine)
