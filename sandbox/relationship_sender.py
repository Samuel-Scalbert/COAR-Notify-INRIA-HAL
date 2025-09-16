from app.classes.RelationshipNotifier import SoftwareInArticleNotifier

if __name__ == "__main__":
    notifier = SoftwareInArticleNotifier(
        actor_id="https://research-organisation.org",
        actor_name="Research Organisation",
        software_id="urn:uuid:74FFB356-0632-44D9-B176-888DA85758DC",
        article_id="https://research-organisation.org/repository/item/201203/421/",
        relationship_uri="http://purl.org/vocab/frbr/core#supplement",
        origin_service_id="https://research-organisation.org/repository",
        origin_inbox="https://research-organisation.org/inbox/",
        target_service_id="https://another-research-organisation.org/repository",
        target_inbox="http://127.0.0.1:5500/inbox",
        context_id="https://another-research-organisation.org/repository/datasets/item/201203421/",
        context_cite_as="https://doi.org/10.5555/999555666",
        context_item_id="https://another-research-organisation.org/repository/datasets/item/201203421/data_archive.zip",
        context_item_media_type="application/zip",
        context_item_type=["Object", "sorg:Software"]
    )

    notifier.send()
