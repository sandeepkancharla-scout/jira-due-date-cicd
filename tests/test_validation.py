from scripts.validate_jira_ticket import has_exact_test_label
from scripts.validate_jira_ticket import validate_issue


def test_test_label():
    assert has_exact_test_label(["Test"]) is True


def test_test_label_case_insensitive():
    assert has_exact_test_label(["TEST"]) is True


def test_continuing_test_is_false():
    assert has_exact_test_label(
        ["continuing test"]
    ) is False


def test_test_automation_is_false():
    assert has_exact_test_label(
        ["Test_Automation"]
    ) is False


def test_due_date_present():
    payload = {
        "issue": {
            "fields": {
                "labels": ["Test"],
                "duedate": "2026-10-10"
            }
        }
    }

    result = validate_issue(payload)

    assert result["status"] == "PASS"


def test_due_date_missing():
    payload = {
        "issue": {
            "fields": {
                "labels": ["Test"],
                "duedate": None
            }
        }
    }

    result = validate_issue(payload)

    assert result["status"] == "FAIL"