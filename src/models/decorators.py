from functools import wraps

def validate_db_model(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        from .dto import ConversationDTO, MessageDTO
        from .database import MessageRoleEnum
        
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
        return func(self, *args, **kwargs)
    return wrapper 