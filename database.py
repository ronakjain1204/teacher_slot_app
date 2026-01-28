from pymongo import MongoClient

# Use the connection string from your image
# Note: I've included the password from your screenshot, but keep this private!
uri = "mongodb+srv://ronakjain1204_db_user:qpBddb6xT4FxPCkh@cluster0.x7vhzra.mongodb.net/?appName=Cluster0"

client = MongoClient(uri)
db = client['timetable_db_ai']
teachers_col = db['teachers']

def save_teacher_to_mongo(data):
    """Upserts the JSON data extracted by AI into MongoDB."""
    teachers_col.update_one(
        {"name": data["name"]},
        {"$set": data},
        upsert=True
    )