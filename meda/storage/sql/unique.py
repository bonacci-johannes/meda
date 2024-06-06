class UniqueMixin(object):
    """
    Mixing allowing to get or create instances of DTOs which have unique constraints.
    See https://github.com/sqlalchemy/sqlalchemy/wiki/UniqueObject for explanation.
    """

    @classmethod
    def unique_hash(cls, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def from_domain(cls, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        cache = getattr(session, '_unique_cache', None)
        if cache is None:
            session._unique_cache = cache = {}

        key = (cls, cls.unique_hash(*arg, **kw))
        if key in cache:
            return cache[key]
        else:
            with session.no_autoflush:
                q = session.query(cls)
                q = cls.unique_filter(q, *arg, **kw)
                obj = q.first()
                if not obj:
                    obj = cls.from_domain(*arg, **kw)
                    session.add(obj)
            cache[key] = obj
            return obj
