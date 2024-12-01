from functools import wraps

def validate_db_model(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        from .dto import ConversationDTO, MessageDTO, SettingDTO, ModelInfoDTO
        from .database import MessageRoleEnum, SettingScope, SettingValueType
        
        if isinstance(self, ConversationDTO):
            if not self.title.strip():
                raise ValueError("Cannot create Conversation with empty title")
            if not self.model_type:
                raise ValueError("Cannot create Conversation without model_type")
            if not self.model_name:
                raise ValueError("Cannot create Conversation without model_name")
        elif isinstance(self, MessageDTO):
            if not self.conversation_id:
                raise ValueError("Cannot create Message without conversation_id")
            if not self.role in (MessageRoleEnum.USER.value, MessageRoleEnum.ASSISTANT.value):
                raise ValueError("Message role must be either 'user' or 'assistant'")
            if not self.content.strip():
                raise ValueError("Cannot create Message with empty content")
        elif isinstance(self, SettingDTO):
            if not self.key.strip():
                raise ValueError("Cannot create Setting with empty key")
            if not self.value_type:
                raise ValueError("Cannot create Setting without value_type")
            if not self.scope:
                raise ValueError("Cannot create Setting without scope")
        elif isinstance(self, ModelInfoDTO):
            if not self.model_id.strip():
                raise ValueError("Cannot create ModelInfo without model_id")   
            if not self.name.strip():
                raise ValueError("Cannot create ModelInfo without name")
            if not self.type:
                raise ValueError("Cannot create ModelInfo without type")
        return func(self, *args, **kwargs)
    return wrapper 