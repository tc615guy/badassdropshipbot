"""
Database models for Badass Dropship Bot
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import settings

Base = declarative_base()


class Product(Base):
    """Product model for discovered items"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # ID from source platform
    source = Column(String, index=True)  # aliexpress, cj, banggood, etc.

    # Basic Info
    title = Column(String)
    original_title = Column(String)
    description = Column(Text)
    original_description = Column(Text)
    category = Column(String, index=True)

    # Pricing
    source_price = Column(Float)
    suggested_price = Column(Float)
    profit_margin = Column(Float)
    shipping_cost = Column(Float)

    # Media
    images = Column(JSON)  # List of image URLs
    video_url = Column(String, nullable=True)

    # Metrics
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    orders = Column(Integer, default=0)

    # SEO
    seo_keywords = Column(JSON)  # {primary, secondary, long_tail}
    slug = Column(String, unique=True)

    # AI Generated Content
    ai_title = Column(String, nullable=True)
    ai_description = Column(Text, nullable=True)
    ai_bullets = Column(JSON, nullable=True)

    # Scores
    trending_score = Column(Float, default=0.0)
    competition_score = Column(Float, default=0.0)
    profit_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)

    # Status
    status = Column(String, default="discovered")  # discovered, generated, published, archived
    is_published = Column(Boolean, default=False)

    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow)
    generated_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    listings = relationship("Listing", back_populates="product")
    analytics = relationship("Analytics", back_populates="product")


class Listing(Base):
    """Published listings on various platforms"""
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))

    platform = Column(String, index=True)  # tiktok, shopify, custom, etc.
    platform_listing_id = Column(String)
    listing_url = Column(String)

    title = Column(String)
    description = Column(Text)
    price = Column(Float)

    status = Column(String, default="active")  # active, paused, deleted

    # Performance
    views = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    orders = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)

    published_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="listings")


class Analytics(Base):
    """Daily analytics for products"""
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    date = Column(DateTime, default=datetime.utcnow, index=True)

    # Metrics
    views = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    orders = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    profit = Column(Float, default=0.0)

    # SEO
    search_ranking = Column(Integer, nullable=True)
    keyword_rankings = Column(JSON, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="analytics")


class Competitor(Base):
    """Competitor tracking"""
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True)
    name = Column(String)
    platform = Column(String)

    # Monitoring
    last_scraped = Column(DateTime, nullable=True)
    product_count = Column(Integer, default=0)
    avg_price = Column(Float, default=0.0)

    # Analysis
    top_products = Column(JSON, nullable=True)
    trending_categories = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database setup
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
