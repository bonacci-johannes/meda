from dataclasses import dataclass
from unittest import TestCase

from sqlalchemy import create_engine, BIGINT, Column, JSON, ARRAY, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class TestDTORegistry(TestCase):

    def setUp(self):
        # Set up a fresh empty in memory sqlite for every test.
        # In principle, this can be replaced by any other database connector string, which is available at runtime.
        # self.engine = create_engine('sqlite:////tmp/sqlite-test.sqlite', echo=True)
        self.engine = create_engine('sqlite:///:memory:', echo=True)
        self.session = sessionmaker(bind=self.engine)()

    def test_mapping_type(self):
        """It should be possible to store a dictionary in a single sqlite column by converting it to a json string."""
        Base = declarative_base()

        class DTO(Base):
            __tablename__ = "dto"
            ident = Column(BIGINT, primary_key=True)
            value = Column(JSON)
            # maps to primitives of maps of primitives must be convertible via json.dumps/loads

        dto = DTO(ident=1, value={"foo": "bar"})
        Base.metadata.create_all(bind=self.engine, checkfirst=True)
        self.session.add(dto)
        self.session.commit()

    def test_unique_mapping_type(self):
        """The json column should have a unique constraint"""
        Base = declarative_base()

        class DTO(Base):
            __tablename__ = "dto_unique"
            ident = Column(BIGINT, primary_key=True)
            value = Column(JSON, unique=True)
            # maps to primitives of maps of primitives must be convertible via json.dumps/loads

        dto = DTO(ident=1, value={"foo": "bar"})
        Base.metadata.create_all(bind=self.engine, checkfirst=True)
        self.session.add(dto)
        self.session.commit()

    def test_array_type(self):
        """The json column should have a unique constraint"""
        Base = declarative_base()

        class DTO(Base):
            __tablename__ = "dto_array"
            ident = Column(BIGINT, primary_key=True)
            values = Column(ARRAY(item_type=int).with_variant(JSON, 'sqlite'))

        dto = DTO(ident=3, values=(1, 2, 3))
        Base.metadata.create_all(bind=self.engine, checkfirst=True)
        self.session.add(dto)
        self.session.commit()

    def test_attribute_access(self):
        """This is an experiment about how sqlalchemy reads and writes attributes to a class."""
        Base = declarative_base()

        class DTO(Base):
            __tablename__ = "dto_array"
            ident = Column(BIGINT, primary_key=True)
            value = Column(types.VARCHAR)

            def __init__(self, value):
                self.value = value
                self.ident = 1
                print("constructor end")

            def __getattr__(self, item):
                print("getattr", item)
                return super().__getattr__(item)

            def __setattr__(self, key, value):
                print("setattr", key, value)
                return super().__setattr__(key, value)

        dto = DTO(value="hello")
        print(dto.ident, dto.value)
        Base.metadata.create_all(bind=self.engine, checkfirst=True)
        self.session.add(dto)
        self.session.commit()
        dto = self.session.query(DTO).all()[0]
        print(dto.ident, dto.value)
