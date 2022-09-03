import dataclasses
from typing import Optional, Union, FrozenSet, Tuple, Any, Callable


class Feature(dataclasses.Field):
    """
    A Feature provides information how two construct a dataclass from an data dictionary
    and how two contruct the sql table.
    To do so this class enriches the default data class field with awareness for:
    __________________________________________________________________________
    :param transformer:
        A Callable function returning a result of field type.
        The function is called by a tuple of input strings which are specified by a tuple of input_keys
    __________________________________________________________________________
    :param input_key:
        The keys for the input from a data dictionary in case the field becomes a sql column,
         or the series identifier if the field type is a SeriesFeatureDataclass.
        - type(input_key) should be a dict for features in SeriesFeatureDataclass (checked by dataclass)
        - input_keys should be of type tuple if transformer is set
            e.g. >>> input_key = ('key_1',) or (('series_id_1','key_1'),)
        - For SeriesFeatureDataclass fields, the input_key is expected to be a tuple of stt (checked by dataclass)
            e.g. >>> input_key = ('series_id_1','series_id_2')

    __________________________________________________________________________
    :param temporary:
        The temporary flag can be used to tag the field as intermediate result that should not be persisted by any
        downstream consumer and instead only serves meta assessors which e.g. could use multiple temporary fields of
        different sub assessors to create a figure or some consolidated feature which is part of the meta assessment.

        Temporary fields are by default never used for the comparison operation. An explicit request for that will
        produce an error.
    __________________________________________________________________________
    :param null_defaults:
        A set of values which will be replaced by none or null
    __________________________________________________________________________
    :param unique_index:
        When all columns with a true flag fullfill an unique constraint which is indexed
    
            To add the :paramref:`_schema.Index.unique` flag to the
            :class:`_schema.Index`, set both the
            :paramref:`_schema.Column.unique` and
            :paramref:`_schema.Column.index` flags to True simultaneously,
            which will have the effect of rendering the "CREATE UNIQUE INDEX"
            DDL instruction instead of "CREATE INDEX".
        
        A more detailed docu at
        >>> import sqlalchemy.Column
    __________________________________________________________________________
    :param comment:
        Optional string that will render an SQL comment on table creation.
        This can be used to provide information about units

    __________________________________________________________________________
    todo: complete docu

    E.g.:
    >>> class SomeTable('FeatureDataclass'):
    >>>     counter: int = Feature(default=0, comment='An event counter')
    >>>     mass: float = Feature(comment='measured in kg')
    >>>     field_with_classes: FrozenSet['SeriesFeatureDataclass'] = Feature(input_key=('series_1_id','series_2_id'))
    >>>     not_to_database = Feature(temporary=True)

    """

    def __init__(self,
                 unique_index: bool = False,
                 comment: str = '',
                 transformer: Optional[Callable[[Any], Any]] = None,
                 is_ident_field: bool = False,
                 is_series_ident_field: bool = False,
                 is_error_field: bool = False,
                 temporary: bool = False,
                 input_key: Optional[
                     Union[str, Tuple[str, ...], Tuple[Tuple[str, Union[str, Tuple[str, ...]]], ...]]] = None,
                 null_defaults: FrozenSet[str] = frozenset(),
                 default=dataclasses.MISSING):
        super().__init__(default=default,
                         default_factory=dataclasses.MISSING,
                         init=True,
                         repr=True,
                         hash=None,
                         compare=not temporary,
                         metadata=None)

        # validate input_key type and structure
        nested_key_type = type(None)
        if input_key is None:
            input_key_type = type(None)
        elif type(input_key) is str:
            input_key_type = str
        elif type(input_key) is tuple:
            if all([type(key) is str for key in input_key]):
                input_key_type = tuple
            elif all([(len(key) == 2) and (type(key[0]) is str) for key in input_key]):
                # the tuple is 'dictionary like' and should be used in a SeriesFeatureDataclass
                input_key_type = dict
                if all([(type(key[1]) is str) for key in input_key]):
                    nested_key_type = str
                elif all([(type(key[1]) is tuple) and all([type(tkey) for tkey in key[1]]) for key in input_key]):
                    nested_key_type = tuple
                else:
                    raise ValueError(f'Error: input_key has unsupported tuple structure: {input_key}')
            else:
                raise ValueError(f'Error: input_key has unsupported tuple structure: {input_key}')
        else:
            raise ValueError(f'Error: input_key is of unsupported type: {type(input_key)}')

        # when transformer is set validate that input_keys are tuples
        if transformer is not None:
            if (input_key_type is tuple) or (nested_key_type is tuple):
                pass
            else:
                raise ValueError(f'Error: transformer is set but input keys are not of tuple type. '
                                 + f'Types are {input_key_type} and {nested_key_type}')

        self.unique_index = unique_index
        self.comment = comment
        self.transformer = transformer
        self.is_ident_field = is_ident_field
        self.is_series_ident_field = is_series_ident_field
        self.is_error_field = is_error_field
        self.temporary = temporary
        self.input_key = input_key
        self.null_defaults = null_defaults

    def __eq__(self, other):
        return self.name == other.name and \
               self.type == other.type and \
               self.unique_index == other.unique_index and \
               self.comment == other.comment and \
               self.transformer == other.transformer and \
               self.is_ident_field == other.is_ident_field and \
               self.is_series_ident_field == other.is_series_ident_field and \
               self.is_error_field == other.is_error_field and \
               self.temporary == other.temporary and \
               self.input_key == other.input_key and \
               self.null_defaults == other.null_defaults and \
               self.default == other.default and \
               self.default_factory == other.default_factory and \
               self.init == other.init and \
               self.repr == other.repr and \
               self.hash == other.hash and \
               self.compare == other.compare and \
               self.metadata == other.metadata

    def __hash__(self):
        return hash((self.name, self.type,
                     self.unique_index, self.comment,
                     self.transformer,
                     self.is_ident_field, self.is_series_ident_field,
                     self.is_error_field,
                     self.temporary, self.input_key,
                     self.null_defaults,
                     self.default, self.default_factory,
                     self.init, self.repr, self.hash, self.compare))

    def __repr__(self):
        return ('Feature('
                f'index={self.unique_index!r},'
                f'comment={self.comment!r},'
                f'transformer={(None if self.transformer is None else self.transformer.__name__)!r},'
                f'is_ident_field={self.is_ident_field!r},'
                f'is_series_ident_field={self.is_series_ident_field!r},'
                f'is_error_field={self.is_error_field!r}',
                f'temporary={self.temporary!r},'
                f'input_key={self.input_key!r},'
                f'null_defaults={self.null_defaults!r},'
                f'default={self.default!r}'
                ')')

    def has_default(self) -> bool:
        return self.default is not dataclasses.MISSING
