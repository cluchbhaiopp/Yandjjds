import pymongo
from config import DB_URI, DB_NAME

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

user_data = database['users']
admins_collection = database['admins']

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': "",
            'verify_token': "",
            'link': ""
        }
    }

async def present_user(user_id: int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user = new_user(user_id)
    user_data.insert_one({'_id': user_id})
    return

async def db_verify_status(user_id):
    user = user_data.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

async def db_update_verify_status(user_id, verify):
  user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] for doc in user_docs]
    return user_ids

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return

async def add_admin(user_id: int):
    try:
        admins_collection.insert_one({'_id': user_id})
        return True
    except Exception as e:
        print(f"Failed to add admin: {e}")
        return False

# Function to remove aa user from admin
async def remove_admin(user_id: int):
    try:
        admins_collection.delete_one({'_id': user_id})
        return True
    except Exception as e:
        print(f"Failed to remove admin: {e}")
        return False

# Function to check if a user is an admin
async def is_admin(user_id: int):
    return bool(admins_collection.find_one({'_id': user_id}))

async def get_admin_list():
    admin_docs = admins_collection.find()
    admin_ids = [doc['_id'] for doc in admin_docs]
    return admin_ids
