

def accept_notification(notification):
    from app.app import db
    hal_id_full = notification['object']['object']['id']
    hal_id = hal_id_full.replace('oai:HAL:', '')
    software_name = notification['object']['object']['sorg:citation']['name']
    print(hal_id,software_name)
    query = f"""
        FOR doc IN documents
        FILTER doc.file_hal_id == "{hal_id}"
        FOR edge_soft IN edge_doc_to_software
            FILTER edge_soft._from == doc._id 
            LET software = DOCUMENT(edge_soft._to)
            FILTER software.software_name.normalizedForm == "{software_name}"
            UPDATE software WITH {{ verification_by_author: True }} IN softwares
        """
    print(query)
    result = db.AQLQuery(query, rawResults=True)

def reject_notification(notification):
    from app.app import db
    hal_id_full = notification['object']['object']['id']
    hal_id = hal_id_full.replace('oai:HAL:', '')
    software_name = notification['object']['object']['sorg:citation']['name']
    print(hal_id, software_name)
    query = f"""
        FOR doc IN documents
        FILTER doc.file_hal_id == "{hal_id}"
        FOR edge_soft IN edge_doc_to_software
            FILTER edge_soft._from == doc._id 
            LET software = DOCUMENT(edge_soft._to)
            FILTER software.software_name.normalizedForm == "{software_name}"
            UPDATE software WITH {{ verification_by_author: False }} IN softwares
        """
    print(query)
    result = db.AQLQuery(query, rawResults=True)