from coarnotify.client import COARNotifyClient
from coarnotify.patterns import AnnounceRelationship
from coarnotify.core.notify import NotifyActor, NotifyObject, NotifyService, NotifyProperties

class SoftwareInArticleNotifier:
    def __init__(
        self,
        actor_id: str,               # URI of the actor announcing the relation
        actor_name: str,             # Human-readable name of the actor
        software_id: str,            # URI of the software found
        article_id: str,             # URI of the article
        relationship_uri: str,       # e.g., "http://purl.org/vocab/frbr/core#supplement"
        origin_service_id: str,      # URI of the origin service
        origin_inbox: str,           # Inbox URL of the origin service
        target_service_id: str,      # URI of the target service
        target_inbox: str,           # Inbox URL of the target service
        context_id: str,             # URI of the article page
        context_cite_as: str,        # DOI of the article
        context_item_id: str,        # URL of the software file
        context_item_media_type: str,# Media type of the software
        context_item_type: list      # Type of the item (e.g., ["Object", "Software"])
    ):
        # Create COAR Notify pattern
        self.announcement = AnnounceRelationship()

        # Actor
        self.actor = NotifyActor()
        self.actor.id = actor_id
        self.actor.name = actor_name
        self.actor.set_property("type", "Organization")

        # Relationship object
        self.obj = NotifyObject()
        self.obj.set_property("type", "Relationship")
        self.obj.set_property("id", software_id)
        self.obj.set_property("as:subject", article_id)
        self.obj.set_property("as:object", context_id)
        self.obj.set_property("as:relationship", relationship_uri)

        # Origin service
        self.origin = NotifyService()
        self.origin.id = origin_service_id
        self.origin.inbox = origin_inbox
        self.origin.set_property("type", "Service")

        # Target service
        self.target = NotifyService()
        self.target.id = target_service_id
        self.target.inbox = target_inbox
        self.target.set_property("type", "Service")

        # Context (article page)
        context_obj = NotifyObject()
        context_obj.set_property("id", context_id)
        context_obj.set_property(NotifyProperties.CITE_AS, context_cite_as)
        item_obj = NotifyObject()
        item_obj.set_property("id", context_item_id)
        item_obj.set_property("mediaType", context_item_media_type)
        item_obj.set_property("type", context_item_type)
        context_obj.set_property("ietf:item", item_obj.to_jsonld())
        context_obj.set_property("type", ["Page", "sorg:AboutPage"])
        self.context = context_obj

        # Assemble notification
        self.announcement.actor = self.actor
        self.announcement.set_property("object", self.obj.to_jsonld())
        self.announcement.origin = self.origin
        self.announcement.target = self.target
        self.announcement.set_property("context", self.context.to_jsonld())
        self.announcement.set_property("@context", ["https://www.w3.org/ns/activitystreams", "https://coar-notify.net"])
        self.announcement.set_property("type", ["Announce", "coar-notify:RelationshipAction"])

        # Client
        self.client = COARNotifyClient()

    def send(self):
        inbox = self.target.inbox
        print(f"➡️ Sending notification to {inbox}")
        response = self.client.send(self.announcement, inbox)
        print("✅ Response status:", response)
        return response