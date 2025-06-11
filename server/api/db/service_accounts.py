# pylint: disable=wrong-import-position
_TABLE_NAME = "service_accounts"
_PKEY = "id"

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import Column, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.schema import Index

from lib.logging import getLogger
from db import Base, DictifiableMixin, QueryMethodsMixin

LOG = getLogger(__name__)

class ServiceAccount(Base, DictifiableMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=True)
    api_key = Column(String, nullable=True)


    __table_args__ = (
        Index("ix_service_accounts_name", name, unique=True), 
        Index("ix_service_accounts_api_key", api_key, unique=True),
    )

    @classmethod
    def get_by_api_key(cls, session, api_key, **kwargs):
        res = cls.query(session, api_key=api_key, **kwargs)
        if not res:
            return None

        return res[0]