from dataclasses import dataclass
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix=False,
    settings_files=["settings.toml", ".secrets.toml"],
    environments=True,
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.


@dataclass
class CalendarConfig:
    url: str
    username: str
    password: str


def init_calendar_config() -> CalendarConfig:
    if not (
        settings.calendar_url
        and settings.calendar_username
        and settings.calendar_password
    ):
        raise ValueError(
            "config missing calendar_url, calendar_username or calendar_password"
        )

    return CalendarConfig(
        url=str(settings.calendar_url),
        username=str(settings.calendar_username),
        password=str(settings.calendar_password),
    )


try:
    calendar_config = init_calendar_config()
except ValueError as ve:
    print("Cannot initialise configuration")
    print(ve)
