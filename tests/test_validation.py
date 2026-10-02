import pytest

from scripts.validate_jira_ticket import (
    has_exact_test_label,
    is_empty,
    validate_ticket,
)


def build_issue(
    labels=None,
    due_date=None,
    email="sandeep.kancharla@scoutmotors.com",
):
    """
    Create a reusable Jira issue payload for unit testing.
    """

    return {
        "key": "SYSINT-15133",
        "fields": {
            "summary": "SYSINT - Test Ticket",
            "labels": labels or [],
            "duedate": due_date,
            "assignee": {
                "displayName": "Sandeep Kancharla",
                "emailAddress": email,
            },
        },
    }


@pytest.mark.parametrize(
    "label",
    [
        "Test",
        "test",
        "TEST",
        "TeSt",
        " test ",
    ],
)
def test_exact_test_label_matches_case_insensitively(label):
    """
    Different capitalizations of the exact word Test must match.
    """

    assert has_exact_test_label([label]) is True


@pytest.mark.parametrize(
    "label",
    [
        "Test_Automation",
        "testing",
        "unit-test",
        "test123",
        "pretest",
        "L2_EE_Integration",
        "",
    ],
)
def test_non_exact_test_labels_are_ignored(label):
    """
    Labels containing extra characters must not match Test.
    """

    assert has_exact_test_label([label]) is False


def test_none_labels_are_ignored():
    """
    Jira may return null instead of an empty labels collection.
    """

    assert has_exact_test_label(None) is False


def test_empty_due_date_values():
    """
    None, empty strings, and spaces are empty due-date values.
    """

    assert is_empty(None) is True
    assert is_empty("") is True
    assert is_empty("   ") is True


def test_populated_due_date_value():
    """
    A valid Jira date string is not empty.
    """

    assert is_empty("2026-10-15") is False


def test_exact_test_with_empty_due_date_requires_notification():
    """
    Test plus an empty Due Date must notify and stop CI/CD.
    """

    issue = build_issue(
        labels=["L2_EE_Integration", "Test"],
        due_date=None,
    )

    result = validate_ticket(issue)

    assert result["label_found"] is True
    assert result["due_date_empty"] is True
    assert result["assignee_email_available"] is True
    assert result["notification_required"] is True
    assert result["validation_failed"] is True
    assert result["continue_pipeline"] is False


def test_lowercase_test_with_empty_due_date_requires_notification():
    """
    Lowercase test must behave the same as Test.
    """

    issue = build_issue(
        labels=["test"],
        due_date="",
    )

    result = validate_ticket(issue)

    assert result["label_found"] is True
    assert result["notification_required"] is True
    assert result["validation_failed"] is True
    assert result["continue_pipeline"] is False


def test_exact_test_with_due_date_continues_pipeline():
    """
    Test plus a populated Due Date must pass validation.
    """

    issue = build_issue(
        labels=["Test"],
        due_date="2026-10-15",
    )

    result = validate_ticket(issue)

    assert result["label_found"] is True
    assert result["due_date_empty"] is False
    assert result["notification_required"] is False
    assert result["validation_failed"] is False
    assert result["continue_pipeline"] is True


def test_test_automation_is_ignored():
    """
    Test_Automation is not an exact match and must be ignored.
    """

    issue = build_issue(
        labels=[
            "L2_EE_Integration",
            "Test_Automation",
        ],
        due_date=None,
    )

    result = validate_ticket(issue)

    assert result["label_found"] is False
    assert result["notification_required"] is False
    assert result["validation_failed"] is False
    assert result["continue_pipeline"] is True


def test_testing_label_is_ignored():
    """
    The label testing must not activate the Due Date rule.
    """

    issue = build_issue(
        labels=["testing"],
        due_date=None,
    )

    result = validate_ticket(issue)

    assert result["label_found"] is False
    assert result["notification_required"] is False
    assert result["continue_pipeline"] is True


def test_no_labels_continues_pipeline():
    """
    A ticket without labels is outside the validation rule.
    """

    issue = build_issue(
        labels=[],
        due_date=None,
    )

    result = validate_ticket(issue)

    assert result["label_found"] is False
    assert result["notification_required"] is False
    assert result["validation_failed"] is False
    assert result["continue_pipeline"] is True


def test_missing_assignee_email_fails_without_email_attempt():
    """
    A matching ticket with an empty Due Date must still fail when Jira
    does not expose the assignee's email address.
    """

    issue = build_issue(
        labels=["Test"],
        due_date=None,
        email=None,
    )

    result = validate_ticket(issue)

    assert result["label_found"] is True
    assert result["due_date_empty"] is True
    assert result["assignee_email_available"] is False
    assert result["notification_required"] is False
    assert result["validation_failed"] is True
    assert result["continue_pipeline"] is False


def test_missing_fields_object_is_handled():
    """
    A malformed or minimal issue must not crash validation.
    """

    issue = {
        "key": "SYSINT-15133",
        "fields": None,
    }

    result = validate_ticket(issue)

    assert result["label_found"] is False
    assert result["continue_pipeline"] is True