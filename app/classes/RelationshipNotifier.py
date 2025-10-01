import json
import requests
import uuid


class SoftwareMentionNotification:
    def __init__(self, payload: dict):
        self._payload = payload

    def to_jsonld(self) -> dict:
        return self._payload


class SoftwareMentionNotifier:
    actor_id = "https://datalake.inria.SAMUEL.fr"
    actor_name = "Samuel Scalbert"
    origin_inbox = "https://datalake.inria.fr/inbox"

    # Attribute annotations for static analyzers
    notification: SoftwareMentionNotification
    target_inbox: str

    def __init__(
        self,
        document_id,
        software_name,
        software_repo,
        mention_type,
        mention_context,
        target_id,
        target_inbox,
    ):
        self.target_inbox = target_inbox

        # Generate a random UUID (version 4) and convert to URN
        notification_id = uuid.uuid4().urn

        payload = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://purl.org/coar/notify",
            ],
            "id": notification_id,
            "type": ["Announce", "coar-notify:RelationshipAnnounce"],
            "actor": {
                "id": self.actor_id,
                "type": "Service",
                "name": self.actor_name,
            },
            "origin": {
                "id": self.actor_id,
                "type": "Service",
                "inbox": self.origin_inbox,
            },
            "target": {
                "id": target_id,
                "type": "Service",
                "inbox": target_inbox,
            },
            "object": {
                "id": document_id,
                "ietf:cite-as": None,
                "sorg:citation": {
                    "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
                    "type": "SoftwareSourceCode",
                    "name": software_name,
                    "codeRepository": software_repo,
                    "referencePublication": None,
                },
                "mentionType": mention_type,
                "mentionContext": mention_context,
            }
        }

        self.notification = SoftwareMentionNotification(payload)

    def send(self):
        url = self.target_inbox
        headers = {"Content-Type": "application/ld+json"}
        payload = self.notification.to_jsonld()  # already a dict
        print(type(payload))  # <class 'dict'>
        resp = requests.post(url, headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            print("Status:", resp.status_code)
            raise
        return resp
