import typing
import uuid

import docent.core


class DatabaseClient:
    """A simple, example database client."""

    DATA = {}

    @classmethod
    def delete_one(cls, _id: str) -> dict:
        """Delete an existing record from database."""

        if _id in cls.DATA and (record := cls.DATA.pop(_id)):
            docent.core.log.info(
                {
                    'client': 'database',
                    'operation': 'delete',
                    'record': record,
                    }
                )

    @classmethod
    def find_many(cls, query: dict[str, typing.Any]) -> dict:
        """Get records from database that match the query."""

        return [
            record
            for record
            in cls.DATA.values()
            if all(record[k] == v for k, v in query.items())
            ]

    @classmethod
    def find_one(cls, _id: str) -> dict:
        """Get one record from database by primary key."""

        return cls.DATA.get(_id)

    @classmethod
    def insert_one(cls, record: dict) -> dict:
        """Generate unique id, assign to record, and add to database."""

        record['_id'] = (_id := uuid.uuid1().hex)
        docent.core.log.info(
            {
                'client': 'database',
                'operation': 'write',
                'record': record,
                }
            )
        cls.DATA[_id] = record
        return record

    @classmethod
    def update_one(cls, record: dict) -> dict:
        """Update existing record in database."""

        docent.core.log.info(
            {
                'client': 'database',
                'operation': 'update',
                'record': record,
                }
            )
        cls.DATA[record['_id']] = record
        return record
