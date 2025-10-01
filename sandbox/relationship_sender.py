from app.classes.RelationshipNotifier import SoftwareMentionNotifier


if __name__ == "__main__":
    notifier = SoftwareMentionNotifier(
        "https://hal.science/hal-01131395v1",
        "SOFTware-Viz",
        None,
        "created",
        "I like SOFTware-Viz",
        "https://inria.hal.science",
        "https://inbox-preprod.archives-ouvertes.fr/",
        # "http://127.0.0.1:5500/inbox"
    )

    # Always output the payload
    print("Payload:")
    print(notifier.notification.to_jsonld())

    # Try sending; don't crash if inbox is not available
    resp = notifier.send()
    if resp is not None:
        print(f"Sent. HTTP {resp.status_code}")
