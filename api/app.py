from flask import Flask
from flask import jsonify
from flask import request

from scripts.validate_jira_ticket import validate_issue

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy"
        }
    )


@app.route("/webhook/jira", methods=["POST"])
def jira_webhook():

    payload = request.get_json()

    if payload is None:
        return jsonify(
            {
                "status": "ERROR",
                "message": "Invalid JSON payload"
            }
        ), 400

    result = validate_issue(payload)

    return jsonify(result), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
