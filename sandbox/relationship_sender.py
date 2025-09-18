from app.classes.RelationshipNotifier import SoftwareInArticleNotifier


import json
if __name__ == "__main__":
    notifier = SoftwareInArticleNotifier(
        actor_id="https://sofair.org/",
        actor_name="SoFAIR project",
        software_id="urn:uuid:22222-abcd",
        article_id="https://www.science.org/doi/10.1126/scitranslmed.adn2401",
        relationship_uri="http://purl.org/vocab/frbr/core#adaption",
        origin_service_id="https://sofair.org/relationships",
        origin_inbox="https://sofair.org/inbox/",
        target_service_id="https://archive.softwareheritage.org",
        target_inbox="http://127.0.0.1:5500/inbox"
    )

    # Send the notification
    notifier.send()