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
        token=None,
    ):
        self.target_inbox = target_inbox
        self.token = token

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

        # Add Authorization header if token is provided
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        payload = self.notification.to_jsonld()

        # Add debugging information
        # print(f"Sending notification to: {url}")
        # print(f"Headers: {headers}")
        # print(f"Payload: {payload}")

        # Add timeout to prevent hanging
        resp = None
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"Response status: {resp.status_code}")
            print(f"Response body: {resp.text}")
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            print(f"Timeout while sending notification to {url}")
            raise
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error while sending to {url}: {e}")
            raise
        except requests.HTTPError:
            print(f"HTTP error: {resp.status_code} - {resp.text}")
            raise

        return resp
