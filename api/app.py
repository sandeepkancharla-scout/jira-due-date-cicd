from flask import Flask
from flask import jsonify
from flask import request

from scripts.validate_jira_ticket import validate_issue

app = Flask(__name__)


@app.route("/health")
def health():
    return {
        "status": "healthy"
    }


@app.route("/webhook/jira", methods=["POST"])
def jira_webhook():
    payload = request.get_json()

    if not payload:
        return jsonify(
            {
                "error": "Invalid payload"
            }
        ), 400

    result = validate_issue(payload)

    return jsonify(result), 200


if __name__ == "__main__":
    app.run(debug=True)