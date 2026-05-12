"""SQLAlchemy ORM models for Wine-O application."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON, Table
from sqlalchemy.orm import registry, relationship

# Create registry and generate base class (replaces deprecated declarative_base())
registry_obj = registry()
Base = registry_obj.generate_base()

# Association table for Wine and WineCollection (many-to-many)
wine_collection_association = Table(
    "wine_collection_association",
    registry_obj.metadata,
    Column("wine_id", Integer, ForeignKey("wines.id"), primary_key=True),
    Column("collection_id", Integer, ForeignKey("wine_collections.id"), primary_key=True),
)


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    collections = relationship("WineCollection", back_populates="owner", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")


class Wine(Base):
    """Wine catalog model."""

    __tablename__ = "wines"

    id = Column(Integer, primary_key=True, index=True)
    wine_name = Column(String(255), nullable=False, index=True)
    producer = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True, index=True)
    country = Column(String(255), nullable=True)
    vintage = Column(Integer, nullable=True, index=True)
    varietals = Column(JSON, default=list)  # List of grape varieties
    alcohol_content = Column(Float, nullable=True)
    volume_ml = Column(Integer, nullable=True)
    tasting_notes = Column(Text, nullable=True)
    estimated_price = Column(Float, nullable=True)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    collections = relationship(
        "WineCollection",
        secondary=wine_collection_association,
        back_populates="wines"
    )
    analyses = relationship("Analysis", back_populates="wine", cascade="all, delete-orphan")


class WineCollection(Base):
    """User wine collection model."""

    __tablename__ = "wine_collections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    collection_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="collections")
    wines = relationship(
        "Wine",
        secondary=wine_collection_association,
        back_populates="collections"
    )


class OCRSession(Base):
    """OCR processing session model."""

    __tablename__ = "ocr_sessions"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(512), nullable=False)
    raw_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    status = Column(String(50), default="completed")  # queued, processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class Reconstruction(Base):
    """3D reconstruction model."""

    __tablename__ = "reconstructions"

    id = Column(Integer, primary_key=True, index=True)
    reconstruction_id = Column(String(100), unique=True, index=True, nullable=False)
    object_type = Column(String(50), default="wine_bottle")
    mesh_data = Column(JSON, nullable=True)
    texture_url = Column(String(512), nullable=True)
    confidence_score = Column(Float, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    quality_setting = Column(String(50), default="medium")  # low, medium, high
    status = Column(String(50), default="completed")  # queued, processing, completed, failed
    error_message = Column(Text, nullable=True)
    export_format = Column(String(50), default="gltf")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    analyses = relationship("Analysis", back_populates="reconstruction")


class Analysis(Base):
    """Wine analysis result model."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    wine_id = Column(Integer, ForeignKey("wines.id"), nullable=True)
    reconstruction_id = Column(Integer, ForeignKey("reconstructions.id"), nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    identification_confidence = Column(Float, nullable=True)
    reconstruction_confidence = Column(Float, nullable=True)
    overall_quality_score = Column(Float, nullable=True)
    recommendations = Column(JSON, default=list)
    compliance_issues = Column(JSON, default=list)
    estimated_price = Column(Float, nullable=True)
    tasting_profile = Column(JSON, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    status = Column(String(50), default="completed")  # queued, processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="analyses")
    wine = relationship("Wine", back_populates="analyses")
    reconstruction = relationship("Reconstruction", back_populates="analyses")
