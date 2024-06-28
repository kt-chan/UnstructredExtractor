# # set this to ip to MongoDB atlas firewall rules, https://cloud.mongodb.com/v2/667549db2c13183084c47650#/security/network/accessList
# !curl ifconfig.me
# print()
# !python -m pip install "pymongo[srv]"

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from google.colab import userdata


user = userdata.get('mongodb_username')  ## replace with mongodb atlas username
password = userdata.get('mongodb_password')## replace with mongodb atlas password
uri = "mongodb+srv://"+user+":"+password+"@ktchan-mongo-atlast.mvx53s5.mongodb.net/?retryWrites=true&w=majority&appName=ktchan-mongo-atlast"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)