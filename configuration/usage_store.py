import time
from .database import SessionLocal, CallRecord
from sqlalchemy import func

class UsageStoreManager:
    def record_call(self, provider: str, key_index: int, model_name: str, endpoint: str, 
                    status: str, http_status: int = None, prompt_tokens: int = 0, completion_tokens: int = 0):
        """
        Saves a new API call record (a "receipt") to the PostgreSQL database.
        """
        session = SessionLocal()
        try:
            # Get the current time in milliseconds
            current_time_ms = int(time.time() * 1000)
            
            # Create a new record object
            new_record = CallRecord(
                ts=current_time_ms,
                provider=provider,
                key_index=key_index,
                model_name=model_name,
                endpoint=endpoint,
                status=status,
                http_status=http_status,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Add it to the session and save to the database
            session.add(new_record)
            session.commit()
            
        except Exception as e:
            print(f"Failed to record usage: {e}")
            session.rollback()
        finally:
            # Always close the session when done
            session.close()

    def count_calls_since(self, provider: str, key_index: int, since_ms: int) -> int:
        session = SessionLocal()
        try:
            count = session.query(CallRecord).filter(
                CallRecord.provider == provider,
                CallRecord.key_index == key_index,
                CallRecord.ts >= since_ms
            ).count()
            return count
        except Exception as e:
            print(f"Failed to count calls: {e}")
            return 0
        finally:
            session.close()

    def count_tokens_since(self, provider: str, key_index: int, since_ms: int) -> int:
        session = SessionLocal()
        try:
            result = session.query(
                func.sum(CallRecord.prompt_tokens + CallRecord.completion_tokens)
            ).filter(
                CallRecord.provider == provider,
                CallRecord.key_index == key_index,
                CallRecord.ts >= since_ms
            ).scalar()
            
            if result is None:
                return 0
            else:
                return result
        except Exception as e:
            print(f"Failed to count tokens: {e}")
            return 0
        finally:
            session.close()
