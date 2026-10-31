from datetime import datetime, timezone
from sqlalchemy import TypeDecorator, DateTime

class UTCDateTime(TypeDecorator):
    """
    Platform-independent UTC DateTime type.
    Ensures datetime values are always stored in UTC and returned with timezone.utc.
    Generates TIMESTAMP WITH TIME ZONE on PostgreSQL.
    """
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not isinstance(value, datetime):
                raise TypeError("Expected datetime object")
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
        return value
