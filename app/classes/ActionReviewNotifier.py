import requests
import uuid


class ActionReviewSoftware:
    def __init__(self, payload: dict):
        self._payload = payload

    def to_jsonld(self) -> dict:
        return self._payload


class ActionReviewNotifier:

    # Attribute annotations for static analyzers
    notification: ActionReviewSoftware
    target_inbox: str

    def __init__(
        self,
        document_id,
        actor_id,
        actor_name,
        origin_inbox,
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
                "https://purl.org/coar/notify"
            ],
            "id": notification_id,
            "type": ['Offer', 'coar-notify:ReviewAction'],
            "actor": {
                "id": actor_id,
                "type": "Service",
                "name": actor_name,
            },
            "origin": {
                "id": actor_id,
                "type": "Service",
                "inbox": origin_inbox,
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

        self.notification = ActionReviewSoftware(payload)

    def send(self):
        url = self.target_inbox
        headers = {"Content-Type": "application/ld+json"}
        payload = self.notification.to_jsonld()  # already a dict
        resp = requests.post(url, headers=headers, json=payload)
        #print(payload)
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            print("Status:", resp.status_code)
            raise
        return resp
