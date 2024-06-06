import unittest

from sqlalchemy import create_engine, event, Table, BigInteger, Column, Integer, String, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from adpkd.observation.enums.defaults import boolean_cases
from meda.storage.sql.dto.dto_registry import DTORegistry
from meda.dataclass.dataclass_factory import FeatureDataclassFactory


class TestDTORegistryMixIn(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """
        See https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#foreign-key-support
        Without this statement the FK-test in test_feature_dtos will fail.
        So this seems to affect the so far used sqlite dbs.
        """

        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if "sqlite3" in str(dbapi_connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.close()

    def setUp(self):
        # initialize feature dataclass factory
        self.feature_dataclass_factory = FeatureDataclassFactory(boolean_cases=boolean_cases)

        # Set up a fresh empty in memory sqlite for every test.
        # In principle, this can be replaced by any other database connector string, which is available at runtime.
        self.engine = create_engine('sqlite+pysqlite:///:memory:', echo=True)

        # Unfortunately, SQLite does not support schemas. Therefore, we need a branching here.
        self.schema = None if self.engine.name == 'sqlite' else 'public'

        self.metadata = MetaData(schema=self.schema)
        self.registry = DTORegistry()
        self.sessionmaker = sessionmaker(bind=self.engine)

        # setup parent_table for tests
        self.Base = declarative_base()

        class RootDTO(self.Base):
            __tablename__: str = 'root'
            __table__: Table
            __table_args__ = {'schema': self.schema}
            ident = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True, autoincrement=True)
            name = Column(String(20), nullable=False)

        self.RootDTO = RootDTO
        self.Base.metadata.create_all(bind=self.engine, checkfirst=True)

        root_dto = self.RootDTO(name='my root object')
        session = self.sessionmaker()
        session.add(root_dto)
        session.commit()
        self.parent_ident = root_dto.ident
        session.close()

    def tearDown(self) -> None:
        self.Base.metadata.drop_all(bind=self.engine)
