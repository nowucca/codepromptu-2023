import uuid


def make_guid() -> str:
    guid = str(uuid.uuid4()).replace("-", "")
    return guid
