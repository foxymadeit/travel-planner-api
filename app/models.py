from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    places = relationship("Place", back_populates="project", cascade="all, delete-orphan", lazy="selectin")


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    artist = Column(String(500), nullable=True)
    thumbnail_url = Column(String(1000), nullable=True)
    notes = Column(Text, nullable=True)
    is_visited = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project", back_populates="places")

    __table_args__ = (
        UniqueConstraint("project_id", "external_id", name="uq_project_external_id"),
    )
