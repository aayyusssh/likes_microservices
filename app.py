import logging
import os
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)

# Connect to MongoDB
MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))
MONGO_DB = os.environ.get("MONGO_DB", "corider")

client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
db = client[MONGO_DB]

likes_collection = db["likes"]
users_collection = db["users"]
contents_collection = db["contents"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def id_to_string(self):
    self['_id'] = str(self['_id'])
    return self

user_fields = ['name', 'email', 'password']
content_fields = ['user_id',"name","desc"]

class UserResource(Resource):
    def get(self):
       users = list(users_collection.users.find())
       users = [id_to_string(user) for user in users]
       return jsonify(users)

    def post(self):
        _json = request.json
        for field in user_fields:
            if field not in _json:
                return jsonify({'message': f'Missing {field} field'}), 400
        user_id = users_collection.users.insert_one({'name': _json['name'], 'email': _json['email'], 'password': _json['password']}).inserted_id
        new_user = users_collection.users.find_one({'_id': user_id})
        return{"message": "user inserted successfully","new user":id_to_string(new_user)}

class ContentResource(Resource):
    def get(self):
       contents = list(contents_collection.contents.find())
       contents = [id_to_string(content) for content in contents]
       return jsonify(contents)
    def post(self):
        _json = request.json
        for field in content_fields:
            if field not in _json:
                return jsonify({'message': f'Missing {field} field'}), 400
        content_id = contents_collection.contents.insert_one({'user_id': _json['user_id'], 'name': _json['name'], 'desc': _json['desc']}).inserted_id
        new_content = contents_collection.contents.find_one({'_id': content_id})
        return{"message": "new content created successfully","content_info":id_to_string(new_content)}

class LikeResource(Resource):
    def post(self):
        data = request.get_json()
        user_id = data.get("user_id")
        content_id = data.get("content_id")
        
        # Save the like event to MongoDB collection
        likes_collection.insert_one({"user_id": user_id, "content_id": content_id})
        total_likes = likes_collection.count_documents({"content_id": content_id})
    
    # If the total likes reach 100, log the push notification message
        if total_likes == 100:
         push_notification_message = f"[user_id => {user_id}], have received 100 likes for [content_id => {content_id}]"
         logger.info(push_notification_message)
        return {"message": "Like event stored successfully"}

class CheckLikeResource(Resource):
    def get(self):
        user_id = request.args.get("user_id")
        content_id = request.args.get("content_id")
        
        # Check if a like event exists in the MongoDB collection
        like_event = likes_collection.find_one({"user_id": user_id, "content_id": content_id})
        
        return {"liked": bool(like_event)}

class TotalLikesResource(Resource):
    def get(self):
        content_id = request.args.get("content_id")
        
        # Get the total number of likes for the content from MongoDB collection
        total_likes = likes_collection.count_documents({"content_id": content_id})
        
        return {"total_likes": total_likes}

# Add resources to the API
api.add_resource(LikeResource, '/like')
api.add_resource(CheckLikeResource, '/check_like')
api.add_resource(TotalLikesResource, '/total_likes')
api.add_resource(UserResource, '/user')
api.add_resource(ContentResource, '/content')

if __name__ == '__main__':
    app.run(debug=True)
