from typing import Optional, Dict, Union, Tuple

from sqlalchemy import Table, MetaData
from sqlalchemy.orm import Session

from meda.dataclass.dataclass import FeatureDataclass, UniqueCommonFeatureDataclass, FeatureDataclassMeta
from meda.storage.sql.dto.dto_base import DTOBase
from meda.storage.sql.dto.dto_factory import DTOFactory


class DTORegistry:
    """
    This class is a registry class, that provides access to a highly normalized database store based
    on SQLAlchemy DTO classes autogenerated from Assessment and corresponding AssessorConfig dataclasses.

    The DTOs are generated via recursion on the dataclass fields. There are two different types standing pairwise in a
    1-to-many relationship:

    The AssessmentDTO:
        This DTO gives access to the feature_dataclass result tree, generated by the assessors. If they are not root
        elements in the feature_dataclass data tree, they define a parent field as a foreign key on the superordinate
        feature_dataclass table. If the assessor uses any configurable parameters, they also define a foreign key
        pointing to a configuration table accessible via the ConfigDTO.

        The following columns always exist:
            ident bigserial primary key
            created_at datetime on update now() on insert now()
            config bigint
                -- foreign key references table_config(ident)     in case there is configuration
                -- default 0                                      in case there is no configuration
            parent bigint foreign key references(parent_table.ident)
                                                                  in case this is not a toplevel feature_dataclass

    The ConfigDTO:
        This DTO gives access to the configuration used for a given feature_dataclass.
        The configuration table may not have nullable columns and has a unique constraint on the full rows.
        This allows to group by feature_dataclass configuration in a fast and consistent way.
        The naming convention between the data table and the configuration table is, that the config table
        suffixes the data table name with a "_config".

        The following columns always exist:
            ident bigserial primary key
            created_at datetime on update now() on insert now()
            unique constraint on all remaining plain data columns
    """

    def __init__(self):
        self._by_feature_dataclass_class: Dict[FeatureDataclassMeta, DTOBase] = dict()
        """
        This is a registry for a reduced view of the toplevel DTOs to which the parent foreign keys of the registered
        feature_dataclass DTOs point. They are organized by the toplevel parent name. All of them are required to have a
        (big) integer column 'ident' used as the foreign key target.
        """

        self._metadatas: Dict[FeatureDataclassMeta, MetaData] = dict()
        """
        This is a registry for the SQLAlchemy metadata objects that will be used for all created ORM mappings
        between the registered feature_dataclass and configuration classes. This allows to e.g. use a separate schema
        for all the classes by providing a metadata=MetaData(schema="foo") argument.
        """

        self._parent_tables: Dict[FeatureDataclassMeta, Table] = dict()
        """
        This is a registry for all optional parent tables to which feature_dataclasses might have foreign key relations.
        When an feature_dataclass_class is registered together with a parent table, the top level feature_dataclass
        table will have a foreign_key relation to the parent table.
        """

        self._parent_uniqueness: Dict[FeatureDataclassMeta, bool] = dict()
        """
        This is a registry for the uniqueness of all optional parent tables to which feature_dataclasses might have 
        foreign key relations.
        When an feature_dataclass_class is registered together with a parent table, the top level feature_dataclass
        table will have a foreign_key relation to the parent table.
        """

    def __len__(self):
        return len(self._by_feature_dataclass_class)

    def __getitem__(self, item: FeatureDataclassMeta) -> DTOBase:
        if isinstance(item, FeatureDataclassMeta):
            return self._by_feature_dataclass_class[item]
        raise KeyError(f"Invalid key: {item}")

    def __contains__(self, item):
        if isinstance(item, FeatureDataclassMeta):
            return item in self._by_feature_dataclass_class
        raise KeyError(f"Invalid key: {item}")

    def metadata(self, feature_dataclass: FeatureDataclassMeta) -> MetaData:
        return self._metadatas[feature_dataclass]

    def parent_table(self, feature_dataclass: FeatureDataclassMeta) -> Table:
        return self._parent_tables[feature_dataclass]

    @property
    def metadatas(self) -> Dict[FeatureDataclassMeta, MetaData]:
        return self._metadatas

    @property
    def parent_tables(self) -> Dict[FeatureDataclassMeta, Table]:
        return self._parent_tables

    @property
    def all_tables(self) -> Dict[str, Table]:
        """ This property returns a dictionary with all registered tables """
        return {**{table.fullname: table
                   for metadata in self._metadatas.values()
                   for table in metadata.tables.values()},
                **{parent_table[0].fullname: parent_table[0]
                   for parent_table in self._parent_tables.values()}}

    def from_domain(self, session: Session,
                    feature_dataclass: Union[FeatureDataclass, UniqueCommonFeatureDataclass],
                    name: Optional[str] = None):
        if name is not None:
            return self._by_table_name[name].from_domain(domain=feature_dataclass, session=session)
        return self._by_feature_dataclass_class[type(feature_dataclass)].from_domain(domain=feature_dataclass,
                                                                                     session=session)

    def register(self,
                 feature_dataclass_cls: FeatureDataclassMeta,
                 metadata: Optional[MetaData] = None,
                 parent_table: Optional[Tuple[Table, bool]] = None) -> bool:

        """
        This method accepts a subclass of Assessment, constructs the DTO and registers it.
        :param feature_dataclass_cls: The feature_dataclass class to register.
        :param metadata: An optional SQLAlchemy MetaData object which specifies the schema.
        :param parent_table: An optional (parent_table,bool) to which a foreign key relation will be introduced.
                             The bool specifying if the foreign key to the parent table is unique
        :return: True if the feature_dataclass class is newly registered, False otherwise.
        """

        """Add an feature_dataclass class to the registry and reference to the parent table with name parent_name."""
        # todo: create a separate meta object for each schema, caution parent table might be from other schema
        # todo: introduce an already registered checker

        metadata = metadata if metadata is not None else MetaData()
        table_name = DTOFactory.get_table_name(feature_dataclass_cls)

        if feature_dataclass_cls not in self._by_feature_dataclass_class:
            if table_name in self.all_tables.keys():
                raise AttributeError(
                    f"The name of the feature_dataclass matches the name of some other feature_dataclass\n"
                    + f"conflict table_name: {table_name}")
            self._metadatas[feature_dataclass_cls] = metadata
            if parent_table is not None:
                self._parent_tables[feature_dataclass_cls] = parent_table
            dto = DTOFactory.generate_feature_dataclass_dto_class(metadata=self._metadatas[feature_dataclass_cls],
                                                                  feature_dataclass_cls=feature_dataclass_cls,
                                                                  parent_table=parent_table)
            self._by_feature_dataclass_class[feature_dataclass_cls] = dto
            return True
        elif parent_table is not None and parent_table != self._parent_tables[feature_dataclass_cls]:
            raise AttributeError(f"The feature_dataclass class {feature_dataclass_cls} is already registered.\n"
                                 + f"But the parent_table changed!\n"
                                 + f"Was: {self._parent_tables[feature_dataclass_cls]}\n"
                                 + f"Now: {parent_table} or parent changed")
        else:
            return False
