import json
import os
import sys
from pathlib import Path


REQUIRED_LABEL = "Test"


def has_exact_test_label(labels):
    """
    Return True only when one of the Jira labels is exactly 'Test'.
    """

    return any(
        str(label).strip().casefold() == REQUIRED_LABEL.casefold()
        for label in labels or []
    )


def is_empty(value):
    """
    Return True when a value is missing, None, or contains only spaces.
    """

    if value is None:
        return True

    return not bool(str(value).strip())


def validate_ticket(issue):
    """
    Validate the Jira ticket's label, due date, and assignee.
    """

    fields = issue.get("fields") or {}

    labels = fields.get("labels") or []
    due_date = fields.get("duedate")
    assignee = fields.get("assignee") or {}

    issue_key = issue.get("key") or "UNKNOWN"
    summary = fields.get("summary") or "No summary"
    assignee_name = assignee.get("displayName") or "Unassigned"
    assignee_email = assignee.get("emailAddress")

    label_found = has_exact_test_label(labels)
    due_date_empty = is_empty(due_date)
    assignee_email_available = not is_empty(assignee_email)

    validation_failed = label_found and due_date_empty

    notification_required = (
        validation_failed
        and assignee_email_available
    )

    continue_pipeline = not validation_failed

    if not label_found:
        validation_message = (
            "Exact Test label not found. "
            "The Jira due-date validation is not applicable."
        )
    elif not due_date_empty:
        validation_message = (
            "Exact Test label found and Due Date is populated."
        )
    elif not assignee_email_available:
        validation_message = (
            "Exact Test label found and Due Date is empty, "
            "but the assignee email address is unavailable."
        )
    else:
        validation_message = (
            "Exact Test label found and Due Date is empty. "
            "The assignee must be notified."
        )

    return {
        "issue_key": issue_key,
        "summary": summary,
        "labels": labels,
        "label_found": label_found,
        "due_date": due_date,
        "due_date_empty": due_date_empty,
        "assignee_name": assignee_name,
        "assignee_email": assignee_email,
        "assignee_email_available": assignee_email_available,
        "notification_required": notification_required,
        "validation_failed": validation_failed,
        "continue_pipeline": continue_pipeline,
        "validation_message": validation_message,
    }


def format_github_output(value):
    """
    Convert Python values into GitHub Actions output strings.
    """

    if isinstance(value, bool):
        return str(value).lower()

    if value is None:
        return ""

    return str(value)


def write_github_output(name, value):
    """
    Write one output value to the file provided by GitHub Actions.
    """

    github_output = os.getenv("GITHUB_OUTPUT")

    if not github_output:
        return

    formatted_value = format_github_output(value)

    with open(github_output, "a", encoding="utf-8") as output_file:
        output_file.write(f"{name}={formatted_value}\n")


def main():
    """
    Read the Jira webhook payload, validate it, and expose the result
    as GitHub Actions outputs.
    """

    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/validate_jira_ticket.py "
            "jira-payload.json"
        )
        sys.exit(1)

    payload_path = Path(sys.argv[1])

    if not payload_path.exists():
        print(f"Payload file does not exist: {payload_path}")
        sys.exit(1)

    with payload_path.open("r", encoding="utf-8") as payload_file:
        payload = json.load(payload_file)

    issue = payload.get("issue", payload)

    if not isinstance(issue, dict):
        print("The Jira payload does not contain a valid issue object.")
        sys.exit(1)

    result = validate_ticket(issue)

    print("Jira validation result:")
    print(json.dumps(result, indent=2))

    github_output_names = [
        "issue_key",
        "summary",
        "label_found",
        "due_date_empty",
        "assignee_name",
        "assignee_email",
        "assignee_email_available",
        "notification_required",
        "validation_failed",
        "continue_pipeline",
        "validation_message",
    ]

    for output_name in github_output_names:
        write_github_output(
            output_name,
            result.get(output_name),
        )


if __name__ == "__main__":
    main()