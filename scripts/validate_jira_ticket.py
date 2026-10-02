def has_exact_test_label(labels):

    if not labels:
        return False

    return any(
        str(label).strip().lower() == "test"
        for label in labels
    )


def validate_issue(payload):

    issue = payload.get("issue", {})
    fields = issue.get("fields", {})

    issue_key = issue.get("key", "UNKNOWN")

    labels = fields.get("labels", [])
    due_date = fields.get("duedate")

    changelog = payload.get("changelog", {})

    status_changed_to_developing = False

    for item in changelog.get("items", []):

        field = item.get("field")
        to_string = item.get("toString")

        VALID_STATUSES = [
"in progress",
"developing"
]
        if (
            field == "status"
            and str(to_string).lower() in VALID_STATUSES
        ):
            status_changed_to_developing = True
            break

    if not status_changed_to_developing:

        return {
            "status": "SKIP",
            "issue_key": issue_key,
            "message": "Status not changed to In Progress"
        }

    if not has_exact_test_label(labels):

        return {
            "status": "PASS",
            "issue_key": issue_key,
            "message": "Test label not found"
        }

    if due_date:

        return {
            "status": "PASS",
            "issue_key": issue_key,
            "message": "Due date exists"
        }

    return {
        "status": "FAIL",
        "issue_key": issue_key,
        "message": "Test label exists and due date is empty",
        "email_required": True
    }