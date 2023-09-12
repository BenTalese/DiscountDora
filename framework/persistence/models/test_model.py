import uuid

from persistence.infrastructure.persistence_context import db
from sqlalchemy_utils import UUIDType


class TestModel(db.Model):
    __tablename__ = 'Test'

    id = db.Column(
        UUIDType(binary=False, native=False),
        primary_key=True,
        default=uuid.uuid4,
        unique=True) #TODO: Is unique necessary?

    name = db.Column(
        db.String(255))
