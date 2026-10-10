from app.ripple.health import health_status, slack_label


def test_health_thresholds_are_inclusive_at_zero_and_amber_limit() -> None:
    assert health_status(None, 1_440) == "red"
    assert health_status(-1, 1_440) == "red"
    assert health_status(0, 1_440) == "amber"
    assert health_status(1_439, 1_440) == "amber"
    assert health_status(1_440, 1_440) == "green"


def test_slack_label_uses_days_hours_and_late_prefix() -> None:
    assert slack_label(1_620) == "+1 d 3 h"
    assert slack_label(-360) == "Late 6 h"
    assert slack_label(None) == "—"
