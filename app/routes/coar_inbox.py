import json

from flask import request, jsonify, render_template
from app.app import app
from coarnotify.factory import COARNotifyFactory
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

@app.route("/notifications", methods=["GET"])
def show_notifications():
    """
    Display all received notifications on a web page.
    """
    return render_template("notifications.html", notifications=received_notifications)
