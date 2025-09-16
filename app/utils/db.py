import json
import csv
from pyArango.connection import Connection

def check_or_create_collection(db, collection_name, collection_type='Collection'):
    """Return collection if exists, else create it."""
    if db.hasCollection(collection_name):
        return db[collection_name]
    else:
        db.createCollection(collection_type, name=collection_name)
        return db[collection_name]

def load_blacklist(csv_path):
    """Load blacklist terms from CSV (first column)."""
    blacklist = []
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # skip header if exists
        for row in reader:
            if row and row[0]:
                blacklist.append(row[0].strip())
    return set(blacklist)

def remove_duplicates(lst):
    """Remove duplicate JSON objects by hashing."""
    seen = set()
    unique = []
    for item in lst:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique

def insert_json_file(file_json, db, blacklist_csv="./app/static/data/blacklist.csv"):
    """
    Insert a single JSON file (as file object or dict) into ArangoDB,
    but skip if the document already exists.
    """
    documents_collection = check_or_create_collection(db, "documents")
    softwares_collection = check_or_create_collection(db, "softwares")
    doc_soft_edge = check_or_create_collection(db, "edge_doc_to_software", "Edges")
    blacklist = load_blacklist(blacklist_csv)

    # Read JSON if it's a file object
    if hasattr(file_json, "read"):
        data_json = json.load(file_json)
        file_name = getattr(file_json, "filename", "unnamed").replace(".json", "").replace(".software", "")
    else:  # dict directly
        data_json = file_json
        file_name = data_json.get("file_hal_id", "unnamed")

    existing_files = db.AQLQuery(
        "FOR d IN documents FILTER d.file_hal_id == @file_name RETURN d",
        bindVars={"file_name": file_name},
        rawResults=True
    )

    if existing_files:
        print(f"⚠️  File '{file_name}' already exists in DB. Skipping.")
        return False

    # Insert document
    document_document = documents_collection.createDocument({"file_hal_id": file_name})
    document_document.save()

    mentions = remove_duplicates(data_json.get("mentions", []))
    for mention in mentions:
        norm_name = mention["software-name"]["normalizedForm"]
        if norm_name not in blacklist:
            mention["software_name"] = mention.pop("software-name")
            mention["software_type"] = mention.pop("software-type")

            software_document = softwares_collection.createDocument(mention)
            software_document.save()

            # Create edge from document to software
            edge_doc_soft = doc_soft_edge.createEdge()
            edge_doc_soft['_from'] = document_document._id
            edge_doc_soft['_to'] = software_document._id
            edge_doc_soft.save()

    return True

            # Create e

db = None

def init_db(app):
    global db
    conn = Connection(
        arangoURL=f"http://{app.config['ARANGO_HOST']}:{app.config['ARANGO_PORT']}",
        username=app.config["ARANGO_USERNAME"],
        password=app.config["ARANGO_PASSWORD"]
    )

    if not conn.hasDatabase(app.config["ARANGO_DB"]):
        conn.createDatabase(name=app.config["ARANGO_DB"])
    db = conn[app.config["ARANGO_DB"]]
    return db