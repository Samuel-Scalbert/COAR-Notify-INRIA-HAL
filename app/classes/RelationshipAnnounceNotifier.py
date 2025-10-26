import requests
import uuid


class RelationshipAnnounceSoftware:
    def __init__(self, payload: dict):
        self._payload = payload

    def to_jsonld(self) -> dict:
        return self._payload


class RelationshipAnnounceNotifier:
    # Attribute annotations for static analyzers
    notification: RelationshipAnnounceSoftware
    target_inbox: str

    def __init__(
        self,
        document_id,
        actor_id,
        actor_name,
        origin_inbox,
        software_name,
        software_repo,
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
            "actor": {
                "id": actor_id,
                "type": "Service",
                "name": actor_name,
            },
            "context": {
                "id": document_id,
                "sorg:name": None,
                "sorg:author": {
                    "@type": "Person",
                    "givenName": None,
                    "email": None,
                },
                "ietf:cite-as": "https://doi.org/XXX/YYY",
                "ietf:item": {
                    "id": document_id,
                    "mediaType": "application/pdf",
                    "type": [
                        "Object",
                        "sorg:ScholarlyArticle",
                    ],
                },
                "type": [
                    "Page",
                    "sorg:AboutPage",
                ],
            },
            "id": notification_id,
            "object": {
                "as:subject": document_id,
                "as:relationship": "https://w3id.org/codemeta/3.0#citation",
                "as:object": software_repo,
                "as:name": software_name,
                "id": uuid.uuid4().urn,
                "type": "Relationship",
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
            "type": [
                "Announce",
                "coar-notify:RelationshipAction",
            ],
        }

        self.notification = RelationshipAnnounceSoftware(payload)

    def send(self):
        url = self.target_inbox
        headers = {"Content-Type": "application/ld+json"}

        # Add Authorization header if token is provided
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        payload = self.notification.to_jsonld()
        resp = requests.post(url, headers=headers, json=payload)
        #print(payload)
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            print("Status:", resp.status_code)
            raise

        return resp
