from coarnotify.client import COARNotifyClient
from coarnotify.core.activitystreams2 import ActivityStreamsTypes
from coarnotify.patterns import AnnounceReview
from coarnotify.core.notify import NotifyActor, NotifyObject, NotifyService
import json

class SoftwareInArticleNotifier:
    def __init__(self, actor_id, actor_name, context_id,software_id, article_id,
                 relationship_uri, origin_service_id, origin_inbox,
                 target_service_id, target_inbox):

        # Create announcement
        self.announcement = AnnounceReview()

        # Actor
        actor = NotifyActor()
        actor.id = actor_id
        actor.name = actor_name
        actor.type = ActivityStreamsTypes.SERVICE
        self.announcement.actor = actor

        # Context (Relationship)
        cont = NotifyObject()
        cont.id = context_id
        self.announcement.context = cont

        # Object
        obj = NotifyObject()
        obj.cite_as =  "https://doi.org/10.5063/schema/codemeta-2.0"
        obj.id = "oai:HAL:hal-03685380v1"
        # citation sub-object
        citation = {
            "type": "SoftwareSourceCode",
            "name": "PyPDEVS",
            "codeRepository": "https://github.com/capocchi/PythonPDEVS",
            "referencePublication": None
        }
        # assign with prefix in the key
        obj.set_property("sorg:citation", citation)
        self.announcement.actor = actor
        print(obj.to_jsonld())

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
