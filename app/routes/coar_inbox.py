from flask import request, jsonify, render_template

from app.app import app
from app.utils.notification_handler import accept_notification, reject_notification

received_notifications = []

@app.route("/inbox", methods=["POST"])
def receive_notification():
    """
    COAR Notify inbox.
    Receives a JSON-LD notification and validates it.
    """
    notification = request.get_json(force=True)
    print("Received notification:", notification)  # For debugging

    # Store the notification for display
    received_notifications.append(notification)

    if getattr(notification, "type", None)=="Accept":
        accept_notification(notification.to_jsonld())
    if getattr(notification, "type", None)=="Reject":
        reject_notification(notification.to_jsonld())

    # Respond with the type and actor info
    return jsonify({
        "status": "ok",
        "type": getattr(notification, "type", None),
        "actor": getattr(notification['actor'], "id", None)
    }), 202

@app.route("/inbox", methods=["GET"])
def inbox_description():
    """
    COAR Notify inbox description.
    Returns information about how to send notifications to this inbox.
    """
    return jsonify({
        "title": "COAR Notify Inbox",
        "description": "This inbox receives COAR-compliant notifications for software mention verification",
        "version": "1.0",
        "endpoints": {
            "POST": {
                "url": "/inbox",
                "method": "POST",
                "content_type": "application/json",
                "description": "Send a COAR notification to verify or reject software mentions"
            },
            "GET": {
                "url": "/inbox",
                "method": "GET",
                "description": "Get this API documentation"
            }
        },
        "supported_notification_types": [
            {
                "type": "Accept",
                "description": "Accepts a software mention as verified by the author",
                "purpose": "Marks software as verified in the database"
            },
            {
                "type": "Reject",
                "description": "Rejects a software mention",
                "purpose": "Marks software as not verified by the author"
            }
        ],
        "request_format": {
            "content_type": "application/ld+json",
            "required_fields": [
                "type",
                "actor",
                "object"
            ],
            "example_accept": {
                "type": "Accept",
                "actor": {
                    "type": "Person",
                    "id": "https://orcid.org/0000-0000-0000-0000"
                },
                "object": {
                    "type": "Offer",
                    "id": "urn:uuid:12345678-1234-1234-1234-123456789012",
                    "object": {
                        "type": "Document",
                        "id": "oai:HAL:hal-01478788",
                        "sorg:citation": {
                            "name": "SoftwareName",
                            "type": "Software"
                        }
                    }
                }
            },
            "example_reject": {
                "type": "Reject",
                "actor": {
                    "type": "Person",
                    "id": "https://orcid.org/0000-0000-0000-0000"
                },
                "object": {
                    "type": "Offer",
                    "id": "urn:uuid:12345678-1234-1234-1234-123456789012",
                    "object": {
                        "type": "Document",
                        "id": "oai:HAL:hal-01478788",
                        "sorg:citation": {
                            "name": "SoftwareName",
                            "type": "Software"
                        }
                    }
                }
            }
        },
        "usage_examples": {
            "curl_accept": "curl -X POST http://localhost:5000/inbox \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\n    \"type\": \"Accept\",\n    \"actor\": {\n      \"type\": \"Person\",\n      \"id\": \"https://orcid.org/0000-0000-0000-0000\"\n    },\n    \"object\": {\n      \"type\": \"Offer\",\n      \"id\": \"urn:uuid:12345678-1234-1234-1234-123456789012\",\n      \"object\": {\n        \"type\": \"Document\",\n        \"id\": \"oai:HAL:hal-01478788\",\n        \"sorg:citation\": {\n          \"name\": \"SoftwareName\",\n          \"type\": \"Software\"\n        }\n      }\n    }\n  }'",
            "curl_reject": "curl -X POST http://localhost:5000/inbox \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\n    \"type\": \"Reject\",\n    \"actor\": {\n      \"type\": \"Person\",\n      \"id\": \"https://orcid.org/0000-0000-0000-0000\"\n    },\n    \"object\": {\n      \"type\": \"Offer\",\n      \"id\": \"urn:uuid:12345678-1234-1234-1234-123456789012\",\n      \"object\": {\n        \"type\": \"Document\",\n        \"id\": \"oai:HAL:hal-01478788\",\n        \"sorg:citation\": {\n          \"name\": \"SoftwareName\",\n          \"type\": \"Software\"\n        }\n      }\n    }\n  }'",
            "python": "import requests\nimport json\n\n# Send Accept notification\naccept_payload = {\n    \"type\": \"Accept\",\n    \"actor\": {\n        \"type\": \"Person\",\n        \"id\": \"https://orcid.org/0000-0000-0000-0000\"\n    },\n    \"object\": {\n        \"type\": \"Offer\",\n        \"id\": \"urn:uuid:12345678-1234-1234-1234-123456789012\",\n        \"object\": {\n            \"type\": \"Document\",\n            \"id\": \"oai:HAL:hal-01478788\",\n            \"sorg:citation\": {\n                \"name\": \"SoftwareName\",\n                \"type\": \"Software\"\n            }\n        }\n    }\n}\n\nresponse = requests.post(\n    \"http://localhost:5000/inbox\",\n    headers={\"Content-Type\": \"application/json\"},\n    json=accept_payload\n)\n\nprint(f\"Status: {response.status_code}\")\nprint(f\"Response: {response.json()}\")"
        },
        "responses": {
            "202": {
                "description": "Notification accepted and processed",
                "example": {
                    "status": "ok",
                    "type": "Accept",
                    "actor": "https://orcid.org/0000-0000-0000-0000"
                }
            },
            "400": {
                "description": "Invalid notification format",
                "example": {
                    "error": "Invalid notification format"
                }
            }
        },
        "view_notifications": {
            "url": "/notifications",
            "method": "GET",
            "description": "View all received notifications in a web interface"
        }
    })


@app.route("/notifications", methods=["GET"])
def show_notifications():
    """
    Display all received notifications on a web page.
    """
    return render_template("notifications.html", notifications=received_notifications)
