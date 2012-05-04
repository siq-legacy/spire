from threading import Lock

from scheme import Boolean, Text
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm.session import sessionmaker

from spire.assembly import Configuration, Dependency
from spire.local import ContextLocals
from spire.unit import Unit

__all__ = ('Schema', 'SchemaDependency', 'SchemaInterface')

SessionLocals = ContextLocals.create_prefixed_proxy('schema.session')

class Schema(object):
    guard = Lock()
    schemas = {}

    def __init__(self, name):
        self.metadata = MetaData()
        self.name = name

    def construct_test_interface(self, url='sqlite://', **params):
        interface = SchemaInterface(self, url, **params)
        interface.create_tables()
        return interface

    @classmethod
    def register(cls, name):
        cls.guard.acquire()
        try:
            if name not in cls.schemas:
                cls.schemas[name] = cls(name)
                SessionLocals.declare(name)
            return cls.schemas[name]
        finally:
            cls.guard.release()
    
class SchemaInterface(Unit):
    configuration = Configuration({
        'echo': Boolean(default=False),
        'schema': Text(nonempty=True),
        'url': Text(nonempty=True),
    })

    def __init__(self, schema, url, echo=False):
        if isinstance(schema, basestring):
            schema = Schema.schemas[schema]

        self.engine = create_engine(url, echo=echo)
        self.schema = schema
        self.session_maker = sessionmaker(bind=self.engine)

    @property
    def session(self):
        return self.get_session()

    def get_session(self, independent=False):
        if independent:
            return self.session_maker()

        session = SessionLocals.get(self.schema.name)
        if session:
            return session

        session = self.session_maker()
        return SessionLocals.push(self.schema.name, session)

    def create_tables(self):
        self.schema.metadata.create_all(self.engine)
        return self

    def drop_tables(self):
        self.schema.metadata.drop_all(self.engine)
        return self

class SchemaDependency(Dependency):
    def __init__(self, schema, **params):
        self.schema = schema
        super(SchemaDependency, self).__init__(SchemaInterface, 'schema:%s' % schema, **params)

    def contribute(self):
        return {'schema': self.schema}
