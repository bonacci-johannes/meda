import datetime
from typing import Any, Type, Tuple, Optional, List, Dict, Mapping, Set

from meda.utils.helper import camel_to_snake
from sqlalchemy import Column, Table, BigInteger, MetaData, ForeignKey, UniqueConstraint
from sqlalchemy import Date, DateTime, Integer, LargeBinary, String, Float, Boolean, Interval
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.sqltypes import JSON
from sqlalchemy.orm import relationship, mapper

from meda.dataclass.feature import Feature
from meda.dataclass.dataclass import FeatureDataclassMeta, UniqueCommonFeatureDataclass, \
    is_unique_common_feature_dataclass, HeadSeriesFeatureDataclass, is_feature_dataclass, NestSeriesFeatureDataclass, \
    is_nest_series_feature_dataclass, is_series_dataclass
from meda.dataclass.reflection import is_optional, get_nested_type, get_nested_optionals, get_type
from meda.storage.sql.dto.dto_base import DTOBase


class DTOFactory:
    """
    The DTOFactory recursively produces all DTO classes for given Observation class.

    A single DTO class is based on the DTOBase.

    To setup a DTO class one has to perform three steps:
        1.: Create a fresh empty subclass of DTO-base.
        2.: Setup all static DTO class variables using a the DTOBase.setup_cls() method.
        3.: Map the sqlalchemy table to the DTO class using the sqlalchemy mapper function
    Attention: Step 1 is crucial because Step 2 and 3 modifies the class and introduces a "class-state"
    """

    _parent_table = None
    _dto_producer_cache = dict()

    base_types = {
        float: Float,
        int: Integer,
        str: String,
        bytes: LargeBinary,
        bool: Boolean,
        datetime.date: Date,
        datetime.datetime: DateTime,
        datetime.timedelta: Interval,
        Mapping[str, Any]: JSONB().with_variant(JSON, "sqlite")
    }
    """Mapping of python plain data types to SQLAlchemy column data types"""

    @staticmethod
    def _unique_common_table_foreign_key_column(field: Feature, unique_common_dto_cls: DTOBase) -> Column:
        """ The data table foreign key column pointing to a unique constraint table holding common values """
        return Column(field.name, BigInteger().with_variant(Integer, 'sqlite'),
                      ForeignKey(column=unique_common_dto_cls.table().columns['ident']),
                      nullable=is_optional(field.type))

    @classmethod
    def _build_base_type_column(cls, field: Feature) -> Column:
        """ Helper function creating sqlalchemy table column for fields"""
        nullable = is_optional(field.type)
        data_type = cls.base_types[get_nested_type(field.type) if nullable else field.type]
        column_options = {'nullable': nullable,
                          'index': field.unique_index,
                          'unique': field.unique_index,
                          'comment': field.comment}

        # Note setting the column field.name requires the instrumented class to have an attribute with name==field.name.
        return Column(field.name, data_type, **column_options)

    @staticmethod
    def get_table_name(feature_dataclass: FeatureDataclassMeta) -> str:
        """ Transform camel to snake case 'FooBar1' -> 'foo_bar_1' """
        return camel_to_snake(feature_dataclass.__name__)

    @classmethod
    def generate_feature_dataclass_dto_class(cls,
                                             feature_dataclass_cls: FeatureDataclassMeta,
                                             metadata: MetaData,
                                             parent_table: Optional[Tuple[Table, bool]]) -> Type[DTOBase]:
        """
        This function recursively generates the dto_class for given assessment class.
        """
        try:
            cls._parent_table = parent_table
            cls._dto_producer_cache = dict()
            """ The cache for the recursive dto_producer """
            res: List[Type[DTOBase]] = list(cls._recursive_dto_class_generator(
                metadata=metadata,
                source_class=feature_dataclass_cls,
                parent_table=None if parent_table is None else parent_table[0]))
        finally:
            # clear the cache
            cls._parent_table = None
            cls._dto_producer_cache = dict()
        return res[-1]

    @classmethod
    def _recursive_dto_class_generator(
            cls, metadata: MetaData,
            source_class: FeatureDataclassMeta,
            parent_table: Optional[Table],
    ) -> Tuple[Type[DTOBase], Optional[Type]]:
        """
        Recursive generation of source_class related dto's.
        This function requires a cache and should only be called by cls.produce_assessment_dto_classes
        """
        table_name = cls.get_table_name(source_class)

        # Construct the database table+
        if table_name in cls._dto_producer_cache.keys():
            yield cls._dto_producer_cache[table_name]
        else:
            # Dictionaries for related dto_classes
            # todo: rename *_dto fields more intuitive
            unique_dtos: Dict[str, DTOBase] = {}
            optional_dtos: Dict[str, DTOBase] = {}
            set_dtos: Dict[str, DTOBase] = {}
            foreign_key_columns: Dict[str, Column] = {}

            # Extract all class related fields
            res = cls._extract_fields_and_build_columns(source_class)
            generic_columns, columns, base_fields, temporary_fields, dto_field_dict = res

            # Generate a foreign key column to given parent table
            if parent_table is not None:
                if (cls._parent_table is not None) and (parent_table == cls._parent_table[0]):
                    unique = cls._parent_table[1]
                else:
                    unique = not issubclass(source_class, (UniqueCommonFeatureDataclass,
                                                           HeadSeriesFeatureDataclass,
                                                           NestSeriesFeatureDataclass))
                foreign_key_columns["parent"] = (Column("parent", BigInteger().with_variant(Integer, 'sqlite'),
                                                        ForeignKey(column=parent_table.columns['ident'],
                                                                   onupdate="cascade",
                                                                   ondelete="cascade"),
                                                        unique=unique,
                                                        nullable=False))

            # If applicable:
            #   - Generate the the unique-constraint-dataclass dto class and load from recursive cache
            #   - Generate a foreign key column to the related common unique table
            for field in dto_field_dict['UniqueCommon']:
                sub_feature_dataclass_cls = get_nested_optionals(field.type)
                yield from cls._recursive_dto_class_generator(metadata=metadata,
                                                              source_class=sub_feature_dataclass_cls,
                                                              parent_table=None)
                unique_dtos[field.name] = cls._dto_producer_cache[cls.get_table_name(sub_feature_dataclass_cls)]
                foreign_key_columns[field.name] = cls._unique_common_table_foreign_key_column(
                    field=field, unique_common_dto_cls=unique_dtos[field.name])

            # Determine unique constraint
            unique_constraint = UniqueConstraint(*columns) \
                if issubclass(source_class, UniqueCommonFeatureDataclass) else None

            # create sql alchemy table object
            database_table = Table(table_name, metadata,
                                   *generic_columns,
                                   *columns,
                                   *foreign_key_columns.values(),
                                   unique_constraint,
                                   extend_existing=True)

            # Generate all related dtos and load from recursive cache
            # todo: simplify all for loops below to one general and fix annotations
            for field in dto_field_dict['FeatureDataclass']:
                sub_feature_dataclass_cls = get_nested_optionals(field.type)
                yield from cls._recursive_dto_class_generator(metadata=metadata,
                                                              source_class=sub_feature_dataclass_cls,
                                                              parent_table=database_table)
                optional_dtos[field.name] = cls._dto_producer_cache[cls.get_table_name(sub_feature_dataclass_cls)]
            for field in dto_field_dict['HeadSeries']:
                sub_feature_dataclass_cls = get_type(field.type)
                yield from cls._recursive_dto_class_generator(metadata=metadata,
                                                              source_class=sub_feature_dataclass_cls,
                                                              parent_table=database_table)
                set_dtos[field.name] = cls._dto_producer_cache[cls.get_table_name(sub_feature_dataclass_cls)]
            for field in dto_field_dict['NestSeries']:
                sub_feature_dataclass_cls = get_type(field.type)
                yield from cls._recursive_dto_class_generator(metadata=metadata,
                                                              source_class=sub_feature_dataclass_cls,
                                                              parent_table=database_table)
                optional_dtos[field.name] = cls._dto_producer_cache[cls.get_table_name(sub_feature_dataclass_cls)]

            # Create a fresh DTOBase class
            class DTO(DTOBase):
                pass

            # Setup the DTOBase to be a dto for given source_class
            DTO.setup_cls(source_class=source_class,
                          fields=base_fields,
                          temporary_fields=temporary_fields,
                          optional_dtos=optional_dtos,
                          list_dtos=set_dtos,
                          common_unique_dtos=unique_dtos)

            # Instrument the DTO class using the sqlalchemy mapper
            # Docu can be found at: https://docs.sqlalchemy.org/en/13/orm/mapping_api.html
            #
            # Define the relation ship where to find related dto objects within the dto instance
            # The properties dict is organized as:
            #   - key:      Field name within dto instance
            #   - value:    Relationship to linked dto
            properties = {}
            for field_name, dto in optional_dtos.items():
                properties[f"{field_name}_dto"] = relationship(dto, uselist=False, lazy="select")
            for field_name, dto in set_dtos.items():
                properties[f"{field_name}_dto"] = relationship(dto, uselist=True, lazy="select")
            for field_name, dto in unique_dtos.items():
                properties[f"{field_name}_dto"] = relationship(dto, uselist=False, lazy="select",
                                                               foreign_keys=foreign_key_columns[field_name])
            mapper(DTO, database_table, properties=properties)

            # Add generated DTO class to cache and yield
            cls._dto_producer_cache.update({table_name: DTO})
            yield DTO

    @classmethod
    def _extract_fields_and_build_columns(cls, source_cls: FeatureDataclassMeta):
        """
        This functions classifies and validates all features for given source_cls.
        To avoid redundant classification/validation table columns are created where applicable.
        """

        generic_columns: List[Column] = []
        columns: List[Column] = []
        base_fields: List[str] = []
        temporary_fields: List[str] = []
        dto_field_dict: Dict[FeatureDataclassMeta: Set[Feature]] = {'FeatureDataclass': set(),
                                                                    'UniqueCommon': set(),
                                                                    'HeadSeries': set(),
                                                                    'NestSeries': set()}

        generic_columns.append(
            Column(
                "ident",
                BigInteger().with_variant(Integer, "sqlite"),
                primary_key=True,
                autoincrement=not ('ident' in set([field.name for field in source_cls.features]))
            )
        )

        for field in source_cls.features:
            # todo: check if we should handle series unique dataclasses separately
            if field.name == 'ident':
                base_fields.append(field.name)
            elif field.temporary:
                temporary_fields.append(field.name)
            elif get_nested_optionals(field.type) in cls.base_types.keys():
                columns.append(cls._build_base_type_column(field=field))
                base_fields.append(field.name)
            elif is_unique_common_feature_dataclass(field.type):
                dto_field_dict['UniqueCommon'].add(field)
            elif is_feature_dataclass(field.type):
                dto_field_dict['FeatureDataclass'].add(field)
            elif is_series_dataclass(field.type) and not is_series_dataclass(source_cls):
                dto_field_dict['HeadSeries'].add(field)
            elif is_nest_series_feature_dataclass(field.type):
                dto_field_dict['NestSeries'].add(field)
            else:
                raise TypeError(f"The storage engine detected an unsupported type in the assessment class: {field}")

        return generic_columns, columns, base_fields, temporary_fields, dto_field_dict
