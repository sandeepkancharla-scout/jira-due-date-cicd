import os

import requests
from flask import Flask, jsonify, request

from scripts.validate_jira_ticket import validate_issue

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy"
        }
    ), 200


def trigger_github_workflow(result):
    """
    Trigger GitHub Actions using repository_dispatch.
    """

    github_owner = os.environ.get("GH_OWNER")
    github_repository = os.environ.get("GH_REPOSITORY")
    github_pat = os.environ.get("GH_PAT")

    if not github_owner:
        raise ValueError("GH_OWNER is not configured")

    if not github_repository:
        raise ValueError("GH_REPOSITORY is not configured")

    if not github_pat:
        raise ValueError("GH_PAT is not configured")

    url = (
        f"https://api.github.com/repos/"
        f"{github_owner}/"
        f"{github_repository}/dispatches"
    )

    payload = {
        "event_type": "jira_validation",
        "client_payload": result
    }

    response = requests.post(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_pat}"
        },
        json=payload,
        timeout=30
    )

    response.raise_for_status()


@app.route("/webhook/jira", methods=["POST"])
def jira_webhook():

    payload = request.get_json(silent=True)

    if payload is None:
        return jsonify(
            {
                "status": "ERROR",
                "message": "Invalid JSON payload"
            }
        ), 400

    try:

        result = validate_issue(payload)

        trigger_github_workflow(result)

        return jsonify(
            {
                "status": "SUCCESS",
                "github_dispatch": True,
                "validation": result
            }
        ), 200

    except ValueError as error:

        return jsonify(
            {
                "status": "ERROR",
                "message": str(error)
            }
        ), 500

    except requests.RequestException as error:

        return jsonify(
            {
                "status": "ERROR",
                "message": "GitHub dispatch failed",
                "details": str(error)
            }
        ), 500

    except Exception as error:

        return jsonify(
            {
                "status": "ERROR",
                "message": str(error)
            }
        ), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )