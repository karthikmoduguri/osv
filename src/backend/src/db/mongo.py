from pymongo import MongoClient

MONGO_URI = "mongodb+srv://karthikmoduguri:karthik123@cluster0.ujuj4.mongodb.net"

client = MongoClient(MONGO_URI)

db = client["osv_db"]
users = db["users"]
