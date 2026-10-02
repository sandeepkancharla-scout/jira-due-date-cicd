from api.app import app


def test_health_endpoint():

    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200


def test_webhook_missing_body():

    client = app.test_client()

    response = client.post(
        "/webhook/jira",
        content_type="application/json"
    )

    assert response.status_code == 400