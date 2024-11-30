from datetime import datetime, date, time
from typing import Any, Type, Union
from uuid import UUID
import json
from src.models.database import SettingValueType

class SettingValueHandler:
    @staticmethod
    def validate_and_convert(value: Any, value_type: SettingValueType) -> Any:
        handlers = {
            SettingValueType.STRING: SettingValueHandler._handle_string,
            SettingValueType.INTEGER: SettingValueHandler._handle_integer,
            SettingValueType.FLOAT: SettingValueHandler._handle_float,
            SettingValueType.BOOLEAN: SettingValueHandler._handle_boolean,
            SettingValueType.JSON: SettingValueHandler._handle_json,
            SettingValueType.ARRAY: SettingValueHandler._handle_array,
            SettingValueType.DATETIME: SettingValueHandler._handle_datetime,
            SettingValueType.DATE: SettingValueHandler._handle_date,
            SettingValueType.TIME: SettingValueHandler._handle_time,
            SettingValueType.URL: SettingValueHandler._handle_url,
            SettingValueType.UUID: SettingValueHandler._handle_uuid,
            SettingValueType.ENUM: SettingValueHandler._handle_enum
        }
        
        handler = handlers.get(value_type)
        if not handler:
            raise ValueError(f"Unsupported setting value type: {value_type}")
            
        return handler(value)

    @staticmethod
    def _handle_string(value: Any) -> str:
        return str(value)

    @staticmethod
    def _handle_integer(value: Any) -> int:
        return int(value)

    @staticmethod
    def _handle_float(value: Any) -> float:
        return float(value)

    @staticmethod
    def _handle_boolean(value: Any) -> bool:
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    @staticmethod
    def _handle_json(value: Any) -> dict:
        if isinstance(value, str):
            return json.loads(value)
        if isinstance(value, (dict, list)):
            return value
        raise ValueError("Invalid JSON value")

    @staticmethod
    def _handle_array(value: Any) -> list:
        if isinstance(value, str):
            return json.loads(value)
        if isinstance(value, list):
            return value
        raise ValueError("Invalid array value")

    @staticmethod
    def _handle_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)

    @staticmethod
    def _handle_date(value: Any) -> date:
        if isinstance(value, date):
            return value
        return date.fromisoformat(value)

    @staticmethod
    def _handle_time(value: Any) -> time:
        if isinstance(value, time):
            return value
        return time.fromisoformat(value)

    @staticmethod
    def _handle_url(value: Any) -> str:
        from urllib.parse import urlparse
        url = str(value)
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL")
        return url

    @staticmethod
    def _handle_uuid(value: Any) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @staticmethod
    def _handle_enum(value: Any) -> str:
        return str(value) 