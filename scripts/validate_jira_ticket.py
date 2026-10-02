def has_exact_test_label(labels):
    """
    Match only the exact label Test.
    """

    if not labels:
        return False

    for label in labels:
        if str(label).strip().lower() == "test":
            return True

    return False


def validate_issue(payload):
    issue = payload.get("issue", {})
    fields = issue.get("fields", {})

    labels = fields.get("labels", [])
    due_date = fields.get("duedate")

    if not has_exact_test_label(labels):
        return {
            "status": "PASS",
            "message": "Test label not found"
        }

    if due_date:
        return {
            "status": "PASS",
            "message": "Due date exists"
        }

    return {
        "status": "FAIL",
        "message": "Test label exists but due date is empty",
        "email_required": True
    }