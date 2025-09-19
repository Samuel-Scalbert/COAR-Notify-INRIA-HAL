from app.classes.RelationshipNotifier import SoftwareMentionNotifier


if __name__ == "__main__":
    notifier = SoftwareMentionNotifier(
        "https://hal.science/hal-01131395v1",
        "urn:uuid:22222-abcd",
        "Grobid",
        "created",
        "The software is used in the research described by the article.",
        "https://github.com/kermitt2/grobid",
        "https://preprod.archives-ouvertes.fr",
        "https://inbox-preprod.archives-ouvertes.fr"
        # "http://127.0.0.1:5500/inbox"
    )

    # Always output the payload
    print("Payload:")
    print(notifier.notification.to_jsonld())

'''
  "object": {
    "as:object": "https://hal.science/{id_document}",
    "as:relationship": "https://www.w3.org/ns/activitystreams#Application",
    "as:subject": "https://vm_datalake_url/software/{id}",
    "id": "https://vm_datalake_url/software/{id}",
    "type": "Relationship"
'''
