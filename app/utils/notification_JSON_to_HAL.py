from app.classes.ActionReviewNotifier import ActionReviewNotifier

def notification_JSON_to_HAL(file):
    from app.app import db
    file = file.filename
    filename = file.replace('.software.json','')
    query = f"""
              FOR doc IN documents
                  FILTER doc.file_hal_id == "{filename}"
                  FOR edge IN edge_doc_to_software
                    FILTER edge._from == doc._id
                    LET mention = DOCUMENT(edge._to)
                    COLLECT softwareName = mention.software_name.normalizedForm INTO mentionsGroup
                    // Compute the max score per attribute across all mentions
                    LET maxScores = {{
                      used: MAX(mentionsGroup[*].mention.documentContextAttributes.used.score),
                      created: MAX(mentionsGroup[*].mention.documentContextAttributes.created.score),
                      shared: MAX(mentionsGroup[*].mention.documentContextAttributes.shared.score)
                    }}
                    // Find the attribute with the overall max score
                    LET maxAttribute = FIRST(
                      FOR attr IN ATTRIBUTES(maxScores)
                        FILTER maxScores[attr] == MAX(VALUES(maxScores))
                        RETURN attr
                    )
                    RETURN {{
                      softwareName: softwareName,
                      maxDocumentAttribute: maxAttribute,
                      contexts: mentionsGroup[*].mention.context
                    }}

                                    """
    notification_list = db.AQLQuery(query, rawResults=True)
    for notification in notification_list:
        notifier = ActionReviewNotifier(
            filename,
            notification['softwareName'],
            None,
            notification['maxDocumentAttribute'],
            notification['contexts'],
            "https://inria.hal.science",
        "https://inbox-preprod.archives-ouvertes.fr/",
            # "http://127.0.0.1:5500/",
            # "http://127.0.0.1:5500/inbox"
        )

        # Always output the payload

        # Try sending; don't crash if inbox is not available
        resp = notifier.send()