"""Base CRUD operations for database models."""

import json
import logging
from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)

from apis.redis_interfacce import RedisInterface
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseCRUD(ABC, Generic[T]):
    """Base class for CRUD operations."""

    def __init__(self, model: Type[T], redis_interface: RedisInterface):
        self.model = model
        self.redis_interface = redis_interface

    def get_cache_key(self, obj_id: str) -> str:
        """Get the cache key for an object."""
        return f"{self.model.__name__}: {obj_id}"

    @abstractmethod
    def to_dict(self, obj: T) -> Dict[str, Any]:
        """Convert the model object to a dictionary."""

    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> T:
        """Create a model object from a dictionary."""

    def create(self, db: Session, obj_in: Dict[str, Any]) -> T:
        """Create a new object in the database."""
        logger.debug("Creating new %s object", self.model.__name__)
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
        except IntegrityError:
            db.rollback()
            raise ValueError("Object with these details already exists")

        obj_dict = self.to_dict(db_obj)
        cache_key = self.get_cache_key(db_obj.id)
        self.redis_interface.set(cache_key, json.dumps(obj_dict), ex=3600)
        logger.debug("Cache set complete")

        return db_obj

    def get(self, db: Session, obj_id: str) -> Optional[T]:
        """Get an object from the database by ID."""
        logger.debug("Getting  object %s with id: %s", self.model.__name__, id)
        cache_key = self.get_cache_key(obj_id)
        cached_obj = self.redis_interface.get(cache_key)
        if cached_obj:
            logger.debug("Cache hit for key: %s", cache_key)
            try:
                obj_dict = json.loads(cached_obj)
                return self.from_dict(obj_dict)
            except json.JSONDecodeError:
                logger.warning("Failed to decode cached object for key: %s", cache_key)

        logger.debug("Cache miss for key: %s", cache_key)
        db_obj = db.query(self.model).filter(self.model.id == obj_id).first()
        if db_obj:
            obj_dict = self.to_dict(db_obj)
            self.redis_interface.set(cache_key, json.dumps(obj_dict), ex=3600)  # Cache for 1 hour
            logger.debug("Object cached with key: %s", cache_key)
        return db_obj

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[T]:
        """Get multiple objects from the database."""
        logger.debug("Getting multiple %s objects. Skip: %s Limit: %s", self.model.__name__, skip, limit)
        return db.query(self.model).offset(skip).limit(limit).all()

    def update(self, db: Session, *, db_obj: T, obj_in: Dict[str, Any]) -> T:
        """Update an object in the database."""
        logger.debug("Updating %s object with id: %s", self.model.__name__, db_obj.id)
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        cache_key = self.get_cache_key(db_obj.id)
        obj_dict = self.to_dict(db_obj)
        self.redis_interface.set(cache_key, json.dumps(obj_dict), ex=3600)  # Update cache
        logger.debug("Updated object cached with key: %s", cache_key)
        return db_obj

    def delete(self, db: Session, *, obj_id: str) -> T:
        """Delete an object from the database."""
        logger.debug("Deleting %s object with id: %s", self.model.__name__, obj_id)
        obj = db.get(self.model, obj_id)
        if obj is None:
            raise ValueError(f"Object with id {obj_id} not found")
        db.delete(obj)
        db.commit()
        cache_key = self.get_cache_key(obj_id)
        self.redis_interface.delete(cache_key)  # Remove from cache
        logger.debug("Deleted object from cache with key: %s", cache_key)
        return obj
