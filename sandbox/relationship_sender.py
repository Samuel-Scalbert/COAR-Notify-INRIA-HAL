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

    # Try sending; don't crash if inbox is not available
    resp = notifier.send(validate=False)
    if resp is not None:
        print(f"Sent. HTTP {resp.status_code}")
