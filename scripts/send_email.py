import os
import sys

import requests


def get_required_environment_variable(name):
    """
    Read a required environment variable.

    Raise an error when the value is missing or empty.
    """

    value = os.getenv(name)

    if value is None or not value.strip():
        raise ValueError(
            f"Required environment variable is missing: {name}"
        )

    return value.strip()


def get_access_token(tenant_id, client_id, client_secret):
    """
    Request an application access token from Microsoft Entra ID.
    """

    token_url = (
        "https://login.microsoftonline.com/"
        f"{tenant_id}/oauth2/v2.0/token"
    )

    response = requests.post(
        token_url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=30,
    )

    response.raise_for_status()

    token_response = response.json()
    access_token = token_response.get("access_token")

    if not access_token:
        raise ValueError(
            "Microsoft Entra ID did not return an access token."
        )

    return access_token


def send_email(
    access_token,
    sender_email,
    recipient_email,
    assignee_name,
    issue_key,
    issue_summary,
    jira_base_url,
):
    """
    Send the missing Due Date notification to the Jira assignee.
    """

    issue_url = (
        f"{jira_base_url.rstrip('/')}/browse/{issue_key}"
    )

    request_url = (
        "https://graph.microsoft.com/v1.0/"
        f"users/{sender_email}/sendMail"
    )

    subject = (
        f"Action required: Due Date missing for {issue_key}"
    )

    body = f"""
Hello {assignee_name},

The Jira ticket assigned to you has the exact label "Test", but its Due Date field is empty.

Ticket: {issue_key}
Summary: {issue_summary}
Ticket link: {issue_url}

Please add a Due Date to the Jira ticket before continuing the CI/CD process.

This is an automated notification from the Jira validation pipeline.
""".strip()

    email_payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body,
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": recipient_email,
                    }
                }
            ],
        },
        "saveToSentItems": True,
    }

    response = requests.post(
        request_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=email_payload,
        timeout=30,
    )

    response.raise_for_status()


def main():
    """
    Load configuration, obtain an access token, and send the email.
    """

    tenant_id = get_required_environment_variable(
        "AZURE_TENANT_ID"
    )
    client_id = get_required_environment_variable(
        "AZURE_CLIENT_ID"
    )
    client_secret = get_required_environment_variable(
        "AZURE_CLIENT_SECRET"
    )
    sender_email = get_required_environment_variable(
        "SENDER_EMAIL"
    )
    jira_base_url = get_required_environment_variable(
        "JIRA_BASE_URL"
    )

    recipient_email = get_required_environment_variable(
        "ASSIGNEE_EMAIL"
    )
    assignee_name = get_required_environment_variable(
        "ASSIGNEE_NAME"
    )
    issue_key = get_required_environment_variable(
        "ISSUE_KEY"
    )
    issue_summary = get_required_environment_variable(
        "ISSUE_SUMMARY"
    )

    access_token = get_access_token(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )

    send_email(
        access_token=access_token,
        sender_email=sender_email,
        recipient_email=recipient_email,
        assignee_name=assignee_name,
        issue_key=issue_key,
        issue_summary=issue_summary,
        jira_base_url=jira_base_url,
    )

    print(
        f"Due Date notification sent to {recipient_email} "
        f"for Jira ticket {issue_key}."
    )


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as error:
        print(f"Email API request failed: {error}")
        sys.exit(1)
    except ValueError as error:
        print(f"Email configuration error: {error}")
        sys.exit(1)
    except Exception as error:
        print(f"Unexpected email notification error: {error}")
        sys.exit(1)