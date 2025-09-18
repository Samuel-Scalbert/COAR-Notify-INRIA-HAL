from coarnotify.client import COARNotifyClient
from coarnotify.core.activitystreams2 import ActivityStreamsTypes
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
        actor.type = ActivityStreamsTypes.ORGANIZATION
        self.announcement.actor = actor

        # Object (Relationship)
        obj = NotifyObject()
        obj.id = software_id
        obj.type =  ActivityStreamsTypes.RELATIONSHIP
        obj.subject =  article_id
        obj.object = software_id
        obj.relationship = relationship_uri
        self.announcement.obj = obj

        # Context (Relationship)
        cont = NotifyObject()
        cont.id = "https://doi.org/10.1101/2022.10.06.511170"
        self.announcement.context = cont

        # Origin
        origin = NotifyService()
        origin.id = origin_service_id
        origin.inbox = origin_inbox
        origin.type = ActivityStreamsTypes.SERVICE
        self.announcement.origin = origin

        # Target
        target = NotifyService()
        target.id = target_service_id
        target.inbox = target_inbox
        target.type = ActivityStreamsTypes.SERVICE
        self.announcement.target = target

        # Client
        self.client = COARNotifyClient()
        self.target_inbox = target_inbox

    def send(self, validate=True):
        """Send the notification via COARNotifyClient"""
        print(f"➡️ Sending notification to {self.target_inbox}")
        return self.client.send(self.announcement, self.target_inbox, validate=validate)
