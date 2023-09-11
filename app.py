from flask_jwt_extended import create_access_token, JWTManager
from flask import Flask, jsonify, request,Response
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import CORS
from bson import ObjectId
import bcrypt
import os
import io

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'eZ-works'
app.config['JWT_SECRET_KEY'] = 'eZ-works'
jwt = JWTManager(app)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

mongo_uri = os.environ.get('API_URL')

client = MongoClient(mongo_uri)
db = client['database']
opt_usercollections = db['opt_users']
pdf_fileCollections = db["pdf_fileCollections"]
UPLOAD_FOLDER = 'uploadedFiles'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from pathlib import Path

def allowed_file(filename):
    return '.' in filename and filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS



# route for register a OPT user

@app.route('/register', methods=['POST'])
def add_user():
    newdata = request.get_json()

    password = newdata['password']
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=5))
    newdata['password'] = hashed_password.decode('utf-8')

    document = newdata

    result = opt_usercollections.insert_one(document)

    return jsonify({'id': str(result.inserted_id)})


# route for login a user

@app.route('/login', methods=['POST'])
def login():
    newdata = request.get_json()
    username = newdata['email']
    password = newdata['password']

    user = opt_usercollections.find_one({'email': username})

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        access_token = create_access_token(identity=str(user['_id']))
        return jsonify({'access_token': access_token})

    return jsonify({'message': 'Password and username are invalid'}), 401




# route for file upload

@app.route('/addfile', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file found'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'file is not selected'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Save file to our database
        with open(file_path, 'rb') as pdf_file:
            pdf_data = pdf_file.read()
            pdf_fileCollections.insert_one({'filename': filename, 'pdf_data': pdf_data})

        return jsonify({'message': 'Data added successfully'})

    return jsonify({'error': 'File type is invalid'})



# route for download a file

@app.route('/download/<id>', methods=['GET'])
def download_file(id):
    try:
        document = pdf_fileCollections.find_one({'_id': ObjectId(id)})

        if document:
            pdf_data = document["pdf_data"]
            filename = document["filename"]
            response = Response(io.BytesIO(pdf_data))
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            return 'File not found', 404

    except Exception as e:
        print(str(e))
        return 'Internal Server Error', 500
    


# route for download all the files

@app.route('/getall', methods=['GET'])
def get_all():
   
    pdf_data = list(pdf_fileCollections.find())

    all_files = []
    for elements in pdf_data:
        all_files.append({
            'id': str(elements['_id']),
            'filename': elements['filename'],
        })

    return jsonify(all_files)



if __name__ == '__main__':
    app.run()


# ************************************************* Completed  *************************************************************