# from tkinter import W
from sqlalchemy import DateTime, Column, String, Integer, Boolean, Table, ForeignKey, create_engine, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
import settings


postgresql_url = f'postgresql://{settings.POSTGRESQL_USER}:{settings.POSTGRESQL_PASSWORD}@{settings.POSTGRESQL_HOST}:{settings.POSTGRESQL_PORT}/{settings.POSTGRESQL_DB}'
engine = create_engine(postgresql_url)
_SessionFactory = sessionmaker(bind=engine)

Base = declarative_base()


def get_or_create(session, model, **kwargs):
    '''Get or create new object'''
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def session_factory():
    '''Generate the session factory'''
    Base.metadata.create_all(engine)
    return _SessionFactory()


association_table = Table(
    'user_repo_association', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('repo_id', Integer, ForeignKey('repo.id')),
    PrimaryKeyConstraint('user_id', 'repo_id')
)


class User(Base):
    '''The user object'''
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    teleg_user_id = Column(Integer)
    repos = relationship("Repo", secondary=association_table, backref="users")


class Repo(Base):
    '''The repo object'''
    __tablename__ = 'repo'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    stars_init = Column(Boolean, default=False)
    last_updated_time = Column(DateTime, nullable=True)
    #users = relationship("User", secondary=association_table)
    #likes = relationship("Like", back_populates="repo")


# class Like(Base):
#     '''Like info'''

#     __tablename__ = 'like'

#     id = Column(Integer, primary_key=True)
#     user = Column(String)
#     datetime = Column(DateTime)
#     repo_id = Column(Integer, ForeignKey('repo.id'))
#     repo = relationship("Repo", back_populates="likes")

if __name__ == '__main___':
    if not database_exists(engine.url):
        create_database(engine.url)
        print(database_exists(engine.url))
