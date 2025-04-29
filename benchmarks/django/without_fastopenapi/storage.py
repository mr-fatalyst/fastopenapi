import uuid

from .schemas import RecordCreate, RecordResponse, RecordUpdate


class RecordStore:
    def __init__(self):
        self.records: dict[str, dict] = {}

    def create(self, record_data: RecordCreate) -> RecordResponse:
        record_id = str(uuid.uuid4())
        record = {"id": record_id, **record_data.model_dump()}
        self.records[record_id] = record
        return RecordResponse(**record)

    def get_all(self) -> list[RecordResponse]:
        return [RecordResponse(**record) for record in self.records.values()]

    def get_by_id(self, record_id: str) -> RecordResponse | None:
        record = self.records.get(record_id)
        if record:
            return RecordResponse(**record)
        return None

    def update(
        self, record_id: str, record_data: RecordUpdate
    ) -> RecordResponse | None:
        if record_id not in self.records:
            return None

        update_data = record_data.model_dump(exclude_unset=True)
        if not update_data:
            return RecordResponse(**self.records[record_id])

        for key, value in update_data.items():
            if value is not None:
                self.records[record_id][key] = value

        return RecordResponse(**self.records[record_id])

    def delete(self, record_id: str) -> bool:
        if record_id in self.records:
            del self.records[record_id]
            return True
        return False
