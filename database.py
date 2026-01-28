from pymongo import MongoClient

# Establish the connection with MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['timetable_db_ai']
teachers_col = db['teachers']

def save_teacher_to_mongo(data):
    """Upserts the JSON data extracted by AI into MongoDB."""
    teachers_col.update_one(
        {"name": data["name"]},
        {"$set": data},
        upsert=True
    )