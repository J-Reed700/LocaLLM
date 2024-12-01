from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum, Table, Index, JSON, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.models.pydantic import ModelType 
from enum import Enum as PyEnum
from sqlalchemy import UniqueConstraint

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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
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
    system_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    generation_info = Column(JSON)  # Renamed from metadata to generation_info
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    favorites = relationship("FavoriteMessage", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role.value}')>"

class FavoriteMessage(Base):
    __tablename__ = "favorite_messages"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), unique=True, nullable=False, index=True)
    bookmarked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    message = relationship("Message", back_populates="favorites")
    
    def __repr__(self):
        return f"<FavoriteMessage(id={self.id}, message_id={self.message_id})>"

class FavoriteConversation(Base):
    __tablename__ = "favorite_conversations"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), unique=True, nullable=False, index=True)
    bookmarked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="favorites")
    
    def __repr__(self):
        return f"<FavoriteConversation(id={self.id}, conversation_id={self.conversation_id})>"

class SettingScope(PyEnum):
    GLOBAL = "global"
    CHAT = "chat" 
    API = "api"

class SettingValueType(str, PyEnum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY = "array"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    URL = "url"
    UUID = "uuid"
    ENUM = "enum"
    OBJECT = "object"

class SettingKey(str, PyEnum):
    # Chat settings
    MODEL_NAME = "model_name"
    MAX_LENGTH = "max_length"
    TEMPERATURE = "temperature"
    TOP_P = "top_p"
    TOP_K = "top_k"
    REPETITION_PENALTY = "repetition_penalty"
    
    # API settings
    API_KEY = "api_key"
    RATE_LIMIT = "rate_limit"
    SYSTEM_PROMPT = "system_prompt"


class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True)
    scope = Column(Enum(SettingScope), nullable=False)
    scope_id = Column(Integer, nullable=True)  # For user/model/conversation specific settings
    key = Column(Enum(SettingKey), nullable=False)
    value_type = Column(Enum(SettingValueType), nullable=False, default=SettingValueType.STRING)
    value = Column(Text, nullable=False)  # Stores all values as strings, JSON encoded when needed
    description = Column(String, nullable=True)  # Description of what this setting does
    additional_metadata = Column(JSON, nullable=True)  # Additional metadata like validation rules, UI hints etc
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
        
    __table_args__ = (
        UniqueConstraint('scope', 'scope_id', 'key', name='unique_setting_constraint'),
    )

class ModelInfo(Base):
    __tablename__ = "model_info"
    
    id = Column(Integer, primary_key=True)
    model_id = Column(String, unique=True, nullable=False)  # HuggingFace model ID
    name = Column(String, nullable=False)
    type = Column(Enum(ModelType), nullable=False)
    description = Column(Text, nullable=True)
    
    # Model stats
    downloads = Column(Integer, nullable=True)
    likes = Column(Integer, nullable=True)
    tags = Column(JSON, nullable=True)  # Store as JSON array
    
    # Local information
    is_local = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    local_path = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)  # in bytes
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Additional metadata
    model_info_metadata = Column(JSON, nullable=True)  # For storing additional HF model info
    
    def __repr__(self):
        return f"<ModelInfo(id={self.id}, name='{self.name}', type='{self.type}')>"
 
