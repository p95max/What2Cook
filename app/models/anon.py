# app/models/anon.py
import datetime
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db import Base

class AnonUser(Base):
    __tablename__ = "anon_user"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class RecipeAction(Base):
    __tablename__ = "recipe_action"
    id = Column(Integer, primary_key=True, autoincrement=True)
    anon_user_id = Column(UUID(as_uuid=True), ForeignKey("anon_user.id", ondelete="CASCADE"), nullable=False)
    recipe_id = Column(Integer, nullable=False)
    action_type = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (UniqueConstraint("anon_user_id", "recipe_id", "action_type", name="uix_anon_recipe_action"),)
