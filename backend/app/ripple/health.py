from __future__ import annotations


def health_status(slack_minutes: int | None, amber_minutes: int) -> str:
    if slack_minutes is None or slack_minutes < 0:
        return "red"
    if slack_minutes < amber_minutes:
        return "amber"
    return "green"


def health(slack_minutes: int | None, amber_minutes: int = 1_440) -> str:
    return health_status(slack_minutes, amber_minutes)


def slack_label(slack_minutes: int | None) -> str:
    if slack_minutes is None:
        return "—"
    prefix = "Late " if slack_minutes < 0 else "+"
    absolute = abs(slack_minutes)
    days, remainder = divmod(absolute, 1_440)
    hours, minutes = divmod(remainder, 60)
    pieces: list[str] = []
    if days:
        pieces.append(f"{days} d")
    if hours:
        pieces.append(f"{hours} h")
    if minutes or not pieces:
        pieces.append(f"{minutes} m")
    return prefix + " ".join(pieces)
