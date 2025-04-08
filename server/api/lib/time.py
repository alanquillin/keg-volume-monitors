import datetime


def parse_iso8601_utc(in_str):

    """Parse an isoformat()'d str assuming UTC if no tzinfo is provided."""

    timestamp = datetime.datetime.fromisoformat(in_str)

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)

    return timestamp


def utcnow_aware():

    """Return an aware datetime in UTC."""

    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

def utcfromtimestamp_aware(timestamp):

    return datetime.fromtimestamp(timestamp, datetime.timezone.utc)
