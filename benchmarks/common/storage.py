import threading
import uuid


class RecordStore:
    def __init__(self):
        self.records: dict[str, dict] = {}
        self._lock = threading.RLock()

    def create(self, record_data: dict) -> dict:
        with self._lock:
            record_id = str(uuid.uuid4())
            record = {"id": record_id, **record_data}
            self.records[record_id] = record
            return record

    def get_all(self) -> list[dict]:
        with self._lock:
            return list(self.records.values())

    def get_by_id(self, record_id: str) -> dict | None:
        with self._lock:
            rec = self.records.get(record_id)
            return dict(rec) if rec is not None else None

    def update(self, record_id: str, record_data: dict) -> dict | None:
        with self._lock:
            existing = self.records.get(record_id)
            if not existing:
                return None
            updated = {**existing, **record_data}
            self.records[record_id] = updated
            return updated

    def delete(self, record_id: str) -> bool:
        with self._lock:
            if record_id in self.records:
                del self.records[record_id]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self.records.clear()
