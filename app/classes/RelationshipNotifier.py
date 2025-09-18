from coarnotify.client import COARNotifyClient
from coarnotify.patterns import AnnounceRelationship
from coarnotify.core.notify import NotifyActor, NotifyObject, NotifyService
import json

class SoftwareInArticleNotifier:
    def __init__(self, actor_id, actor_name, software_id, article_id,
                 relationship_uri, origin_service_id, origin_inbox,
                 target_service_id, target_inbox):

        # Create announcement
        self.announcement = AnnounceRelationship()

        # Actor
        actor = NotifyActor()
        actor.id = actor_id
        actor.name = actor_name
        actor.set_property("type", ActivityStreamsTypes.ORGANIZATION)
        self.announcement.set_property("actor", actor)

        # Object (Relationship)
        obj = NotifyObject()
        obj.id = software_id
        obj.set_property("type", "Relationship")
        obj.set_property("as:subject", article_id)
        obj.set_property("as:object", software_id)
        obj.set_property("as:relationship", relationship_uri)
        self.announcement.set_property("object", obj)

        # Context (Relationship)
        cont = NotifyObject()
        cont.id = "https://doi.org/10.1101/2022.10.06.511170"
        self.announcement.set_property("context", cont)

        # Origin
        origin = NotifyService()
        origin.id = origin_service_id
        origin.inbox = origin_inbox
        origin.set_property("type", "Service")
        self.announcement.set_property("origin", origin)

        # Target
        target = NotifyService()
        target.id = target_service_id
        target.inbox = target_inbox
        target.set_property("type", "Service")
        self.announcement.set_property("target", target)

        # Client
        self.client = COARNotifyClient()
        self.target_inbox = target_inbox

    def send(self, validate=True):
        """Send the notification via COARNotifyClient"""
        print(f"➡️ Sending notification to {self.target_inbox}")
        return self.client.send(self.announcement, self.target_inbox, validate=validate)
