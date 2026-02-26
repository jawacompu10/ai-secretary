from caldav import DAVClient, Calendar


class CalDavBase:
    """Base class providing shared CalDAV infrastructure for all service implementations."""

    def __init__(self, url: str, username: str, password: str):
        """Initialize the CalDAV base with connection details.

        Args:
            url (str): CalDAV server URL
            username (str): Username for authentication
            password (str): Password for authentication
        """
        try:
            self.client = DAVClient(url=url, username=username, password=password)
            self.principal = self.client.principal()
            self._calendars = None
        except Exception as e:
            raise ConnectionError(f"Failed to connect to CalDAV server: {e}")

    @property
    def calendars(self) -> list[Calendar]:
        """Get all calendars, cached after first access."""
        if self._calendars is None:
            try:
                self._calendars = self.principal.calendars()
            except Exception as e:
                raise RuntimeError(f"Failed to fetch calendars: {e}")
        return self._calendars

    def invalidate_calendar_cache(self) -> None:
        """Invalidate the cached calendars list."""
        self._calendars = None
