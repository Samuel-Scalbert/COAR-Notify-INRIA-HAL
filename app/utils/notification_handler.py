
def accept_notification(notification):
    from app.app import app, db
    from pyArango.connection import Connection

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
                UPDATE software WITH {{ verification_by_author: true }} IN software
    """

    result = db.AQLQuery(query, rawResults=True)

    try:
        host = app.config['ARANGO_HOST']
        port = app.config['ARANGO_PORT']
        username = app.config['ARANGO_USERNAME']
        password = app.config['ARANGO_PASSWORD']

        conn = Connection(
            arangoURL=f"http://{host}:{port}",
            username=username,
            password=password
        )

        Viz_db = conn["SOF-viz-COAR"]
        result = Viz_db.AQLQuery(query, rawResults=True)
    except Exception as error:
        print(error)


def reject_notification(notification):
    from app.app import app, db
    from pyArango.connection import Connection
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
            UPDATE software WITH {{ verification_by_author: False }} IN software
        """
    result = db.AQLQuery(query, rawResults=True)

    try:
        host = app.config['ARANGO_HOST']
        port = app.config['ARANGO_PORT']
        username = app.config['ARANGO_USERNAME']
        password = app.config['ARANGO_PASSWORD']

        conn = Connection(
            arangoURL=f"http://{host}:{port}",
            username=username,
            password=password
        )

        Viz_db = conn["SOF-viz-COAR"]
        result = Viz_db.AQLQuery(query, rawResults=True)
    except Exception as error:
        print(error)
