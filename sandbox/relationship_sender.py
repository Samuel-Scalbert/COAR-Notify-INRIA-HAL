from app.classes.RelationshipNotifier import SoftwareInArticleNotifier


import json
if __name__ == "__main__":
    notifier = SoftwareInArticleNotifier(
        actor_id="https://ror.org/02kvxyf05",
        actor_name="Inria",
        context_id="https://hal.science/hal-01131395v1",
        software_id="urn:uuid:22222-abcd",
        article_id="https://www.science.org/doi/10.1126/scitranslmed.adn2401",
        relationship_uri="http://purl.org/vocab/frbr/core#adaption",
        origin_service_id="https://ror.org/02kvxyf05",
        origin_inbox="http://127.0.0.1:5500/inbox",
        target_service_id="https://archive.softwareheritage.org",
        target_inbox="http://127.0.0.1:5500/inbox"
    )

    # Send the notification
    print(notifier.announcement.obj.to_jsonld())
    notifier.send()

'''
  "object": {
    "as:object": "https://hal.science/{id_document}",
    "as:relationship": "https://www.w3.org/ns/activitystreams#Application",
    "as:subject": "https://vm_datalake_url/software/{id}",
    "id": "https://vm_datalake_url/software/{id}",
    "type": "Relationship"
'''
