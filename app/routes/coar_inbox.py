from flask import request, jsonify, render_template
from app.app import app, db
from app.utils.notification_handler import post_notification_to_viz
from app.auth import require_api_key
received_notifications = []

@app.route("/inbox", methods=["POST"])
@require_api_key
def receive_notification():
    """
    COAR Notify inbox.
    Receives a JSON-LD notification and validates it.
    """
    notification = request.get_json(force=True)
    print("Received notification:", notification)  # For debugging

    # Store the notification for display
    received_notifications.append(notification)

    notification_type = getattr(notification, "type", None)
    if notification_type in ("Accept", "Reject"):
        notification_json = notification.to_jsonld()

        hal_id_full = notification_json['object']['object']['id']
        hal_id = hal_id_full.replace('oai:HAL:', '')
        software_name = notification_json['object']['object']['sorg:citation']['name']

        post_notification_to_viz(
            hal_id,
            software_name,
            db,
            accepted=(notification_type == "Accept")
        )

    # Respond with the type and actor info
    return jsonify({
        "status": "ok",
        "type": getattr(notification, "type", None),
        "actor": getattr(notification['actor'], "id", None)
    }), 202

@app.route("/notifications", methods=["GET"])
def show_notifications():
    """
    Display all received notifications on a web page.
    """
    return render_template("notifications.html", notifications=received_notifications)
