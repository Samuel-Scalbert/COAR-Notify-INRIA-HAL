import requests

def post_notification_to_viz(hal_id: str, software_name: str, db, accepted: bool = True):
    """
    Send a notification to coar-viz (accepted or rejected) and update local DB.
    """
    # Update DB
    query = """
    FOR doc IN documents
      FILTER doc.file_hal_id == @hal_id
      FOR edge_soft IN edge_doc_to_software
        FILTER edge_soft._from == doc._id
        LET software = DOCUMENT(edge_soft._to)
        FILTER software.software_name.normalizedForm == @software_name
        UPDATE software WITH { verification_by_author: @verification } IN software
    """
    bind_vars = {
        "hal_id": hal_id,
        "software_name": software_name,
        "verification": accepted
    }
    result = db.AQLQuery(query, bindVars=bind_vars, rawResults=True)

    # POST notification
    endpoint = "accepted_notification" if accepted else "rejected_notification"
    url = f"http://coar-viz:8080/api/{endpoint}/{hal_id}/{software_name}"

    try:
        response = requests.post(url, timeout=5)
        response.raise_for_status()
        print(f"✅ Successfully sent {endpoint} notification to {url}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send notification: {e}")
        return None
