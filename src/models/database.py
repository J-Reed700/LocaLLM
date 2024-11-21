from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.pydantic import ModelType 
from websrc.models.pydantic import TextModelName, ImageModelName

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    api_key = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    model_configs = relationship("UserModelConfig", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200))
    model_type = Column(Enum(ModelType))
    model_name = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    generation_info = Column(JSON)  # Renamed from metadata to generation_info
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class UserModelConfig(Base):
    __tablename__ = "user_model_configs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_type = Column(Enum(ModelType))
    model_name = Column(String(50))
    parameters = Column(JSON)  # Store model-specific parameters
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="model_configs")
