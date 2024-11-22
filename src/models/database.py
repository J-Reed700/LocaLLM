from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.pydantic import ModelType 
from enum import Enum as PyEnum

Base = declarative_base()

# Association table for many-to-many relationship between Conversation and Category
conversation_categories = Table(
    'conversation_categories',
    Base.metadata,
    Column('conversation_id', Integer, ForeignKey('conversations.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True),
    Index('ix_conversation_categories_conversation_id', 'conversation_id'),
    Index('ix_conversation_categories_category_id', 'category_id')
)

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    conversations = relationship(
        "Conversation",
        secondary=conversation_categories,
        back_populates="categories"
    )
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    model_type = Column(Enum(ModelType), nullable=False)
    model_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    categories = relationship(
        "Category",
        secondary=conversation_categories,
        back_populates="conversations"
    )
    favorites = relationship("FavoriteConversation", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}')>"

class MessageRoleEnum(str, PyEnum):
    USER = "user"
    ASSISTANT = "assistant"

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(Enum(MessageRoleEnum), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generation_info = Column(JSON)  # Renamed from metadata to generation_info
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    favorites = relationship("FavoriteMessage", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role.value}')>"

class FavoriteMessage(Base):
    __tablename__ = "favorite_messages"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), unique=True, nullable=False, index=True)
    bookmarked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    message = relationship("Message", back_populates="favorites")
    
    def __repr__(self):
        return f"<FavoriteMessage(id={self.id}, message_id={self.message_id})>"

class FavoriteConversation(Base):
    __tablename__ = "favorite_conversations"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), unique=True, nullable=False, index=True)
    bookmarked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="favorites")
    
    def __repr__(self):
        return f"<FavoriteConversation(id={self.id}, conversation_id={self.conversation_id})>"
