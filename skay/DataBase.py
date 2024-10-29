import os
from skay.Models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DataBase:

    def __init__(self):
        self.db = None

    def set_db(self, name='db'):
        basedir = os.path.abspath(os.path.dirname(__file__))

        db_sqlite = 'sqlite:///' + os.path.join(basedir, f'../{name}.sqlite')
        engine = create_engine(db_sqlite, echo=False)

        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()
        return self.db
