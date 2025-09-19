import json

import requests


class SoftwareMentionNotification:
    def __init__(self, payload: dict):
        self._payload = payload

    def to_jsonld(self) -> dict:
        return self._payload


class SoftwareMentionNotifier:
    actor_id = "https://datalake.inria.fr"
    actor_name = "Datalake Inria"
    origin_inbox = "https://datalake.inria.fr/inbox"

    # Attribute annotations for static analyzers
    notification: SoftwareMentionNotification
    target_inbox: str
    def __init__(
            self,
            document_id,
            software_id,
            mention_name,
            mention_type,
            mention_context,
            mention_url,
            target_id,
            target_inbox
    ):
        self.target_inbox = target_inbox

        notification_id = f"{self.actor_id}/notifications/{document_id}-{software_id}"

        payload = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/notify#"
            ],
            "id": notification_id,
            "type": ["Announce", "coar-notify:ReviewAction"],
            "actor": {
                "id": self.actor_id,
                "type": "Service",
                "name": self.actor_name
            },
            "origin": {
                "id": self.actor_id,
                "type": "Service",
                "inbox": self.origin_inbox
            },
            "target": {
                "id": target_id,
                "type": "Service",
                "inbox": target_inbox
            },
            "object": {
                "mentionType": mention_type,
                "mentionContext": mention_context,
                "cite_as": document_id,
                "sorg:citation":
                    {
                        "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
                        "type": "SoftwareSourceCode",
                        "name": mention_name,
                        "codeRepository": mention_url
                        # "referencePublication":
                    },
            },
            "context": {
                "id": document_id
            }
        }

        self.notification = SoftwareMentionNotification(payload)

    def send(self, validate=True):
        headers = {"Content-Type": "application/ld+json"}
        data = json.dumps(self.notification.to_jsonld())
        resp = requests.post(self.target_inbox, data=data, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp
