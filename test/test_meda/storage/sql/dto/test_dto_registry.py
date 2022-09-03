import datetime
from typing import Optional, FrozenSet, Any, Mapping

import numpy
from sqlalchemy import Table, BigInteger, Column, Integer, String, MetaData
from meda.dataclass.dataclass import FeatureDataclass, UniqueCommonFeatureDataclass, \
    HeadSeriesFeatureDataclass, ExternMixin
from meda.dataclass.dataclass_factory import FeatureDataclassFactory
from meda.dataclass.defaults import BooleanCases
from meda.dataclass.feature import Feature
from meda.storage.sql.dto.dto_registry import DTORegistry
from test.test_meda.storage.sql.dto import TestDTORegistryMixIn


# todo: improve this test with a better test coverage!!!


class SubConfig(UniqueCommonFeatureDataclass):
    min: float = Feature(comment='1', input_key='')
    max: float = Feature(comment='1', input_key='')


class SubSubConf(SubConfig):
    pass


class SubAssessment1(FeatureDataclass):
    config: SubConfig
    value: float = Feature(comment='1', input_key='')


class SubAssessment2(SubAssessment1):
    pass


class SubAssessment3(SubAssessment1):
    pass


class SubAssessment4(SubAssessment1):
    pass


class SetSubAssessment1(HeadSeriesFeatureDataclass):
    value: float = Feature(input_key=(('abc0', 'dfg0'), ('abc1', 'dfg1'), ('abc2', 'dfg2')))


class SetSubAssessment2(SetSubAssessment1):
    pass


feature_factory = FeatureDataclassFactory(boolean_cases=BooleanCases(true={}, false={}, null={}))
set_sub_assessments_1 = frozenset([feature_factory._generator(feature_dataclass=SetSubAssessment1,
                                                              data_dict={'dfg0': '1', 'dfg1': '2.', 'dfg2': '3.'},
                                                              series_dataclass_key=f'abc{i}') for i in range(3)])


class SuperAssessment(FeatureDataclass):
    some_optional_child: Optional[SubAssessment1]
    some_other_optional_child: Optional[SubAssessment2]
    some_set_of_children: FrozenSet[SetSubAssessment1]


class PicklableConfig(UniqueCommonFeatureDataclass):
    # base types
    double: float = Feature(comment='m^2', input_key='')
    integer: int = Feature(comment='1', input_key='')
    time: datetime.datetime = Feature(input_key='')
    interval: datetime.timedelta = Feature(input_key='')
    string: str = Feature(input_key='')
    blob: bytes = Feature(input_key='')
    flag: bool = Feature(input_key='')
    json: Mapping[str, Any] = Feature()

    temp: Any = Feature(temporary=True)


class PicklableAssessment(FeatureDataclass):
    # config
    config: PicklableConfig

    # base types
    double: float = Feature(comment='m^2', input_key='')
    integer: int = Feature(comment='1', input_key='')
    time: datetime.datetime = Feature(input_key='')
    interval: datetime.timedelta = Feature(input_key='')
    string: str = Feature(input_key='')
    blob: bytes = Feature(input_key='')
    flag: bool = Feature(input_key='')
    json: Mapping[str, Any] = Feature(input_key='')

    # nullable base types
    optional_double: Optional[float] = Feature(comment='m^2', input_key='', null_defaults=frozenset())
    optional_integer: Optional[int] = Feature(comment='1', input_key='', null_defaults=frozenset())
    optional_time: Optional[datetime.datetime] = Feature(input_key='', null_defaults=frozenset())
    optional_interval: Optional[datetime.timedelta] = Feature(input_key='', null_defaults=frozenset())
    optional_string: Optional[str] = Feature(input_key='', null_defaults=frozenset())
    optional_blob: Optional[bytes] = Feature(input_key='', null_defaults=frozenset())
    optional_flag: Optional[bool] = Feature(input_key='', null_defaults=frozenset())

    # subassessments
    multiple: FrozenSet[SetSubAssessment1]
    empty: FrozenSet[SetSubAssessment2]
    single: Optional[SubAssessment3]
    missing: Optional[SubAssessment4]

    # temporary
    temp: Any = Feature(temporary=True)


class TestDTORegistry(TestDTORegistryMixIn):

    def test_schema_support(self):
        class SubAssessment(FeatureDataclass):
            sub_value: float = Feature(comment='m^2', input_key='')

        class Unique(FeatureDataclass, ExternMixin):
            ident: int
            status: str

        class MainAssessment(FeatureDataclass):
            main_value: float = Feature(comment='m^2', input_key='')
            sub_ass: SubAssessment
            uni: Optional[Unique]

        parent_table = Table("parent_test", MetaData(schema="p_schema"),
                             Column("ident", BigInteger().with_variant(Integer, 'sqlite'),
                                    primary_key=True, autoincrement=True),
                             Column("name", String(20), nullable=False))

        self.registry.register(feature_dataclass_cls=MainAssessment,
                               metadata=MetaData(schema="a_schema"),
                               parent_table=(parent_table, True))
        dto_by_class = self.registry[MainAssessment]

        self.assertEqual({'a_schema.main_assessment', 'a_schema.sub_assessment', 'a_schema.unique',
                          'p_schema.parent_test'},
                         self.registry.all_tables.keys())

        d_cls = MainAssessment(main_value=2.4, sub_ass=SubAssessment(sub_value=2.3),
                               uni=Unique(ident=1, status='234'))
        dto = dto_by_class.from_domain(domain=d_cls)

    def test_ignore_temporary(self):
        class GoodAssessment(FeatureDataclass):
            anything: Any = Feature(temporary=True)

        self.registry.register(feature_dataclass_cls=GoodAssessment)

        DTO = self.registry[GoodAssessment]

        session = self.sessionmaker()

        ga = GoodAssessment(anything=None)
        self.assertEqual(ga, DTO.from_domain(domain=ga, session=session).to_domain())

        session.close()

    def test_register_assessment(self):
        class GoodAssessment(FeatureDataclass):
            _table_name: str = 'good_name'
            pass

        self.registry.register(feature_dataclass_cls=GoodAssessment,
                               parent_table=(self.RootDTO.__table__, False))

        self.assertEqual(len(self.registry), 1)
        self.assertIn(GoodAssessment, self.registry)

        self.registry.register(feature_dataclass_cls=GoodAssessment,
                               parent_table=(self.RootDTO.__table__, False))

        self.assertEqual(len(self.registry), 1)

        class OtherConfig(UniqueCommonFeatureDataclass):
            value: float = Feature(comment='K', input_key='')

        class SecondAssessment(FeatureDataclass):
            config: OtherConfig

        self.registry.register(feature_dataclass_cls=SecondAssessment,
                               parent_table=(self.RootDTO.__table__, False))
        self.assertEqual(len(self.registry), 2)
        self.assertIn(SecondAssessment, self.registry)

        self.assertEqual(set(self.registry.all_tables.keys()),
                         {'root', 'good_assessment', 'second_assessment', 'other_config'})

    def test_base_data_types(self):
        types = [int, float, str, bytes, bool, datetime.datetime, datetime.timedelta]
        for i, base_type in enumerate(types):
            registry = DTORegistry()

            class GoodAssessment(FeatureDataclass):
                some_value: base_type = Feature(comment='m', input_key='')
                some_optional_value: Optional[base_type] = Feature(comment='kg', input_key='',
                                                                   null_defaults=frozenset())

            registry.register(feature_dataclass_cls=GoodAssessment,
                              parent_table=(self.RootDTO.__table__, False))

            self.assertIn(GoodAssessment, registry)

    def test_different_dataclasses_same_classname(self):
        # create class and register
        class GoodAssessment(FeatureDataclass):
            some_value: float = Feature(comment='°C', input_key='')

        self.assertTrue(self.registry.register(feature_dataclass_cls=GoodAssessment,
                                               parent_table=(self.RootDTO.__table__, False)))

        # create new identical class and check if the registry state is not changed
        class GoodAssessment(FeatureDataclass):
            some_value: float = Feature(comment='°C', input_key='')

        self.assertFalse(self.registry.register(feature_dataclass_cls=GoodAssessment,
                                                parent_table=(self.RootDTO.__table__, False)))

        # create new identical class but other feature unit and check if registration fails
        class GoodAssessment(FeatureDataclass):
            some_other_value: float = Feature(comment='F', input_key='')

        # try if registering different classes with same classname fails
        with self.assertRaises(AttributeError):
            self.registry.register(feature_dataclass_cls=GoodAssessment,
                                   parent_table=(self.RootDTO.__table__, False))

        # create other class  but with same classname and check if registration fails
        class GoodAssessment(FeatureDataclass):
            some_other_value: float = Feature(comment='°C', input_key='')

        # try if registering different classes with same classname fails
        with self.assertRaises(AttributeError):
            self.registry.register(feature_dataclass_cls=GoodAssessment,
                                   parent_table=(self.RootDTO.__table__, False))

        # create initial class and check if registered
        class GoodAssessment(FeatureDataclass):
            some_value: float = Feature(comment='°C', input_key='')

        self.assertIn(GoodAssessment, self.registry)
        self.assertEqual(len(self.registry), 1)

    def test_recursion(self):
        self.registry.register(feature_dataclass_cls=SuperAssessment,
                               parent_table=(self.RootDTO.__table__, False))
        metadata = self.registry.metadata(SuperAssessment)
        self.assertEqual(len(self.registry), 1)
        print(metadata.tables.keys())
        table_names = {'set_sub_assessment_1_ident', 'set_sub_assessment_1', 'sub_assessment_1', 'sub_assessment_2',
                       'sub_config', 'super_assessment'}
        self.assertEqual(set(metadata.tables.keys()), table_names)
        metadata.create_all(bind=self.engine)

        sc = SubConfig(min=0., max=20.)

        sa = SuperAssessment(some_optional_child=None,
                             some_other_optional_child=SubAssessment2(config=sc, value=numpy.float16(0.4)),
                             some_set_of_children=set_sub_assessments_1)

        DTO = self.registry[SuperAssessment]

        session = self.sessionmaker()

        dto = DTO.from_domain(domain=sa, session=session)
        dto.parent = self.parent_ident  # patch the DTO with the foreign key
        session.add(dto)
        session.commit()

        dto2 = session.query(DTO).first()
        sa2 = dto2.to_domain()
        self.assertEqual(sa, sa2)
        self.assertIsNot(sa, sa2)
        self.assertIs(dto, dto2)

        session.close()

        metadata.drop_all(bind=self.engine)

    def test_get_item(self):
        self.registry.register(feature_dataclass_cls=SuperAssessment)
        self.assertEqual(len(self.registry), 1)

        dto_by_class = self.registry[SuperAssessment]

        self.assertEqual(SuperAssessment, dto_by_class.source_class())

    def test_non_empty_config(self):
        class NonEmptyConfig(UniqueCommonFeatureDataclass):
            threshold: float = Feature(comment='K', input_key='')

        class AssessmentWithConfig(FeatureDataclass):
            config: NonEmptyConfig

        self.registry.register(feature_dataclass_cls=AssessmentWithConfig,
                               parent_table=(self.RootDTO.__table__, False))

        self.assertIn(AssessmentWithConfig, self.registry)
        AssessmentDTO = self.registry[AssessmentWithConfig]
        ConfigDTO = AssessmentDTO._common_unique_dtos['config']
        self.assertIsNotNone(ConfigDTO)

        config = NonEmptyConfig(threshold=1500.)
        config_dto = ConfigDTO.from_domain(domain=config)

        self.assertIsInstance(config_dto, ConfigDTO)
        self.assertEqual(config_dto.threshold, 1500.)
        self.assertEqual(config, config_dto.to_domain())

    def test_toplevel_parent(self):
        class TopAssessment(FeatureDataclass):
            foo: int = Feature(comment='1', input_key='')
            bar: str = Feature(input_key='')

        self.registry.register(feature_dataclass_cls=TopAssessment,
                               parent_table=(self.RootDTO.__table__, False))

        with self.assertRaises(AttributeError):
            other_table = Table("oncle", MetaData(),
                                Column("name", String(20), nullable=False))
            self.registry.register(feature_dataclass_cls=TopAssessment,
                                   parent_table=(other_table, False))

        session = self.sessionmaker()

        self.registry.metadata(TopAssessment).create_all(bind=self.engine, checkfirst=True)
        assessment_dto = self.registry[TopAssessment].from_domain(domain=TopAssessment(foo=1, bar='3'),
                                                                  session=session)
        assessment_dto.parent = self.parent_ident
        session.add(assessment_dto)
        session.commit()
        session.close()

        self.registry.metadata(TopAssessment).drop_all(bind=self.engine)

    def test_storage_engine(self):
        self.registry.register(feature_dataclass_cls=PicklableAssessment,
                               parent_table=(self.RootDTO.__table__, False))

        session = self.sessionmaker()

        AssessmentDTO = self.registry[PicklableAssessment]
        ConfigDTO = AssessmentDTO._common_unique_dtos['config']

        self.registry.metadata(PicklableAssessment).create_all(bind=self.engine, checkfirst=True)

        config = PicklableConfig(
            double=1.,
            string='hello',
            integer=2,
            blob=b"foobar",
            time=datetime.datetime(2020, 2, 20, 20, 20, 0),
            interval=datetime.timedelta(seconds=3.),
            flag=False,
            json={'foo': 'bar'},
            temp=None)

        sc = SubConfig(min=0, max=20)
        sa3 = SubAssessment3(config=sc, value=0.4)
        assessment = PicklableAssessment(
            config=config,
            double=0.5,
            string='hi',
            integer=4,
            blob=b"barfoo",
            time=datetime.datetime(2020, 2, 2, 20, 20, 2),
            interval=datetime.timedelta(seconds=1.),
            flag=True,
            json={'bar': 1, 'foo': 23},
            optional_double=None,
            optional_string=None,
            optional_integer=None,
            optional_blob=None,
            optional_time=None,
            optional_interval=None,
            optional_flag=None,
            multiple=set_sub_assessments_1,
            empty=frozenset(),
            single=sa3,
            missing=None,
            temp=None)

        dto = AssessmentDTO.from_domain(domain=assessment, session=session)
        dto.parent = 1  # the single entry in the 'root' table
        session.add(dto)
        session.commit()

        self.assertEqual(session.query(ConfigDTO).count(), 1)
        self.assertEqual(session.query(AssessmentDTO).count(), 1)

        # test config uniqueness constraint
        assessment1 = PicklableAssessment(
            config=PicklableConfig(
                double=1., string='hello', integer=2, blob=b"foobar", time=datetime.datetime(2020, 2, 20, 20, 20, 0),
                interval=datetime.timedelta(seconds=3.), flag=False, json={'foo': 'bar'},
                temp=None),
            double=0.5,
            string='hi',
            integer=4,
            blob=b"barfoo",
            time=datetime.datetime(2020, 2, 2, 20, 20, 2),
            interval=datetime.timedelta(milliseconds=300.),
            flag=True,
            json={'bar': 1, 'foo': 23},
            optional_double=None,
            optional_string=None,
            optional_integer=None,
            optional_blob=None,
            optional_time=None,
            optional_interval=None,
            optional_flag=None,
            multiple=set_sub_assessments_1,
            empty=frozenset(),
            single=sa3,
            missing=None,
            temp=None)
        dto1 = AssessmentDTO.from_domain(domain=assessment1, session=session)
        dto1.parent = 1  # the single entry in the 'root' table
        session.add(dto1)
        session.commit()

        self.assertIs(dto.config_dto, dto1.config_dto)
        self.assertEqual(session.query(ConfigDTO).count(), 1)
        self.assertEqual(session.query(AssessmentDTO).count(), 2)

        # test retrieving from database
        dto2 = session.query(AssessmentDTO).first()
        assessment2 = dto2.to_domain()
        self.assertEqual(assessment, assessment2)
        self.assertIsNot(assessment, assessment2)

        # test second config
        assessment3 = PicklableAssessment(
            config=PicklableConfig(  # json is different
                double=1., string='hello', integer=2, blob=b"foobar", time=datetime.datetime(2020, 2, 20, 20, 20, 0),
                interval=datetime.timedelta(seconds=2.), flag=True, json={'foo': 'baz'},
                temp=None),
            double=0.5,
            string='hi',
            integer=4,
            blob=b"barfoo",
            time=datetime.datetime(2020, 2, 2, 20, 20, 2),
            interval=datetime.timedelta(seconds=3.),
            flag=False,
            json={'bar': 1, 'foo': 23},
            optional_double=None,
            optional_string=None,
            optional_integer=None,
            optional_blob=None,
            optional_time=None,
            optional_interval=None,
            optional_flag=None,
            multiple=set_sub_assessments_1,
            empty=frozenset(),
            single=sa3,
            missing=None,
            temp=None)
        dto3 = self.registry.from_domain(feature_dataclass=assessment3, session=session)
        dto3.parent = 1  # the single entry in the 'root' table
        session.add(dto3)
        session.commit()

        self.assertEqual(session.query(ConfigDTO).count(), 2)
        self.assertEqual(session.query(AssessmentDTO).count(), 3)

        # test interaction with pickle
        import pickle
        unpickled = pickle.loads(pickle.dumps(assessment))
        self.assertEqual(assessment, unpickled)
        self.assertIsNot(assessment, unpickled)

        dto4 = AssessmentDTO.from_domain(domain=unpickled, session=session)
        dto4.parent = 1  # the single entry in the 'root' table
        session.add(dto4)
        session.commit()

        session.close()

        self.registry.metadata(PicklableAssessment).drop_all(bind=self.engine)
