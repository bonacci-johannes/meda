from typing import List, Dict, Optional, Union

import sqlalchemy
from sqlalchemy import Table
from sqlalchemy.orm import Session, Query

from meda.dataclass.dataclass import FeatureDataclass, FeatureDataclassMeta, UniqueCommonFeatureDataclass
from meda.storage.sql.unique import UniqueMixin


class DTOBase(UniqueMixin):
    """
    The autogenerated DTO corresponding to an Assessment or AssessorConfig dataclass.
    See DTORegistry documentation.
    """

    _source_class: FeatureDataclassMeta
    """ The source class connected to this DTO """

    _fields: List[str]
    """The list of names of the base type fields"""

    _optional_dtos: Dict[str, 'DTOBase']
    """The mapping of sub-assessment DTOs in 1-to-0-or-1 relationship"""
    _list_dtos: Dict[str, 'DTOBase']
    """The mapping of sub-assessment DTOs in 1-to-many relationship"""
    _common_unique_dtos: Dict[str, 'DTOBase']
    """The mapping of DTOs with pointing to foreign key constraint in many-to-1 relationship, e.g. config_dto"""

    _required_params: frozenset
    _optional_params: frozenset
    """Parameter set to check consistency of the constructor arguments"""

    _temporary_fields: Dict[str, None]
    """
    A kwarg dict to initialize all temporary fields of the associated dataclass.
    The keys are names of all temporary fields and all values are None.
    """

    @classmethod
    def setup_cls(cls,
                  source_class: FeatureDataclassMeta,
                  fields: List[str],
                  temporary_fields: List[str],
                  optional_dtos: Dict[str, 'DTOBase'],
                  list_dtos: Dict[str, 'DTOBase'],
                  common_unique_dtos: Dict[str, 'DTOBase']):

        cls._source_class = source_class

        cls._fields = fields

        cls._optional_dtos = optional_dtos
        cls._list_dtos = list_dtos
        cls._common_unique_dtos = common_unique_dtos

        cls._required_params = frozenset(
            set.union({f for f in fields},
                      {f"{f}_dto" for f in list_dtos.keys()},
                      {f"{f}_dto" for f in common_unique_dtos.keys()}))
        cls._optional_params = frozenset({f"{f}_dto" for f in optional_dtos.keys()})

        cls._temporary_fields = {f: None for f in temporary_fields}

        return cls

    def __init__(self, **kwargs):
        """
        This __init__ methods is called by internal class_method from_domain.
        This method extracts all parameters from given source_class instance.
        These parameters are then forwarded this __init__ method and a dto instance will be created.
        """

        # check kwargs consistency
        params = set(kwargs.keys())
        if not params.issuperset(self.required_params()):
            raise ValueError(f"Required parameters are missing for construction of the DTO: "
                             f"{self._required_params.difference(params)}")
        if not params.issubset(self.all_params()):
            raise ValueError(f"Too many parameters given for DTO construction: "
                             f"{params.difference(self.all_params())}")

        # Assign fields to their sqlalchemy InstrumentedAttribute.
        # The mapping is defined within the DTOFactory.
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def source_class(cls) -> FeatureDataclassMeta:
        """ The dto source_class """
        return cls._source_class

    @classmethod
    def table(cls) -> Table:
        """
        The sql alchemy table object, mapped to this class using the sqlalchemy mapper.
        This mapper instruments this class and builds up the relation between DTO and table object.

        Note: The class setup and table mapping is done by the DTOFactory class.
        """
        return sqlalchemy.inspection.inspect(cls).local_table

    @classmethod
    def all_params(cls) -> frozenset:
        """Parameter set to check consistency of the constructor arguments"""
        return frozenset.union(cls._required_params, cls._optional_params)

    @classmethod
    def required_params(cls) -> frozenset:
        """Parameter set to check consistency of the constructor arguments"""
        return cls._required_params

    @classmethod
    def optional_params(cls) -> frozenset:
        """Parameter set to check consistency of the constructor arguments"""
        return cls._optional_params

    @classmethod
    def unique_filter(cls, query: Query, domain: Union[UniqueCommonFeatureDataclass, FeatureDataclass]):
        for field in cls._fields:
            query = query.filter(getattr(cls, field) == getattr(domain, field))
        return query

    @classmethod
    def unique_hash(cls, domain):
        def hashify(d):  # This function is need to make dictionaries hashable in the DTO lookup table
            if not isinstance(d, dict):
                return d
            return tuple(sorted(d.items(), key=lambda t: t[0]))

        return tuple(hashify(getattr(domain, ff)) for ff in cls._fields)

    @classmethod
    def from_domain(cls, domain: Union[UniqueCommonFeatureDataclass, FeatureDataclass],
                    session: Optional[Session] = None) -> Optional['DTOBase']:
        if domain is None:
            return None

        # column fields
        kwargs = {f: getattr(domain, f) for f in cls._fields}

        # dto fields
        if session is not None:
            # Optional[Dataclass]: 0/1 -> 1
            for field_name, field_dto in cls._optional_dtos.items():
                kwargs.update(
                    {f"{field_name}_dto": field_dto.from_domain(domain=getattr(domain, field_name), session=session)})

            # FrozenSet[SeriesDataclass]: N -> 1
            for field_name, field_dto in cls._list_dtos.items():
                series_dataclass_set = getattr(domain, field_name)
                kwargs.update({f"{field_name}_dto": [field_dto.from_domain(domain=d_cls, session=session)
                                                     for d_cls in series_dataclass_set]})

            # Optional[CommonUniqueDataclass]: 0/1 -> N
            for field_name, field_dto in cls._common_unique_dtos.items():
                dto = field_dto.as_unique(domain=getattr(domain, field_name), session=session) \
                    if getattr(domain, field_name) is not None else None
                kwargs.update({f"{field_name}_dto": dto})

        # return initialized dto
        return cls(**kwargs)

    def to_domain(self) -> Union[UniqueCommonFeatureDataclass, FeatureDataclass]:
        # column fields
        kwargs = {f: getattr(self, f) for f in self._fields}

        # FrozenSet[SeriesDataclass]: N -> 1
        for f in self._list_dtos.keys():
            kwargs.update({f: frozenset({d.to_domain() for d in getattr(self, f + "_dto") if d is not None})})

        # Optional[CommonUniqueDataclass]: 0/1 -> N
        # Optional[Dataclass]: 0/1 -> 1
        for f in list(self._optional_dtos.keys()) + list(self._common_unique_dtos.keys()):
            kwargs.update({f: getattr(self, f + "_dto").to_domain() if getattr(self, f + "_dto") is not None else None})

        # add none initialized temporary fields
        kwargs.update(self._temporary_fields)

        # return initialized dataclass
        return self._source_class(**kwargs)
