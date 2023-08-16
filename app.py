from flask import Flask, render_template, request, jsonify, flash, session, json, redirect, url_for
from cryptography.fernet import Fernet
import joblib
import psycopg2  # For PostgreSQL connectivity
from connect2DB import connectDB
from werkzeug.security import generate_password_hash, check_password_hash

import datetime
from psycopg2.extras import RealDictCursor
# from flask_cors import CORS, cross_origin
from datetime import date, timedelta
# from urllib3 import request
import  socket

app = Flask(__name__)

date_today = date.today()
date_time = datetime.datetime.now()
d = datetime.datetime.strptime('2011-06-09', '%Y-%m-%d')
my_datetime_utc = date_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')

# key = Fernet.generate_key()
# f = Fernet(key)
#
# CORS(app)
app.config['SECRET_KEY'] = 'this is a secret key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

# Database connection setup
base = connectDB()
# base.autocommit = True
cursor = base.cursor()
cur = base.cursor()


# Load the machine learning model using joblib
model = joblib.load('C:/Users/ekodh/OneDrive/Desktop/Heart/modelpickle.pkl')


# Route for updating statistics about reserved and vacant servers
@app.route('/dashboard1', methods=['GET'])
def server_piechart():
    cursor.execute('SELECT * FROM asset WHERE reserved=%s AND status=%s', [True, True])
    reserved_servers = len(cursor.fetchall())
    
    cursor.execute('SELECT * FROM asset WHERE reserved=%s AND status=%s', [False, False])
    vacant_servers = len(cursor.fetchall())
    
    return jsonify({
        "Message": "Updated Statistics",
        "Status": "200 OK",
        "reserved": reserved_servers,
        "vacant": vacant_servers
    })

# Route for updating statistics about clusters
@app.route('/dashboard2', methods=['GET'])
def cluster_piechart():
    cur.execute("""
        SELECT cluster_id,
               COUNT(CASE WHEN reserved='t' THEN 1 ELSE NULL END) AS reserved,
               COUNT(CASE WHEN reserved='f' OR reserved IS NULL THEN 1 ELSE NULL END) AS vacant
        FROM asset
        GROUP BY cluster_id
    """)
    
    cluster_stats = []
    for row in cur.fetchall():
        cluster_stats.append({
            "cluster_id": row[0],
            "reserved": row[1],
            "vacant": row[2]
        })
    
    cluster_stats.append({
        "Message": "Updated Statistics",
        "Status": "200 OK"
    })
    
    return jsonify({"Dashboard": cluster_stats})

# Route for updating statistics about asset locations
@app.route('/dashboard3', methods=['GET'])
def location_piechart():
    cur.execute("""
        SELECT asset_location,
               COUNT(CASE WHEN reserved='True' AND status='True' THEN 1 ELSE NULL END) AS reserved,
               COUNT(CASE WHEN reserved='false' AND status='false' OR reserved IS NULL THEN 1 ELSE NULL END) AS vacant
        FROM asset
        GROUP BY asset_location
    """)
    
    location_stats = []
    for row in cur.fetchall():
        location_stats.append({
            "Location": row[0],
            "Reserved": row[1],
            "Vacant": row[2]
        })
    
    location_stats.append({
        "Message": "Updated Statistics",
        "Status": "200 OK"
    })
    
    return jsonify({"Dashboard": location_stats})



@app.route('/predict.html')
def predict():
    return render_template('predict.html')



@app.route('/predict', methods=['POST'])
def predict_result():
    try:
        conn = connectDB()
        if conn is None:
            return jsonify({'error': 'Database connection error'}), 500
        cursor = conn.cursor()
        _json = request.json  # converting to json

        age = _json['age']
        print(age, "age")
        sex = _json['sex']  # Extract 'sex' field
        print(sex, "sex")
        cp = _json['cp']  # Extract 'cp' field
        print(cp, "cp")
        trtbps = _json['trtbps']  # Extract 'trtbps' field
        print(trtbps, "trtbps")
        chol = _json['chol']  # Extract 'chol' field
        print(chol, "chol")
        fbs = _json['fbs']  # Extract 'fbs' field
        print(fbs, "fbs")
        restecg = _json['restecg']  # Extract 'restecg' field
        print(restecg, "restecg")
        thalachh = _json['thalachh']  # Extract 'thalachh' field
        print(thalachh, "thalachh")
        exng = _json['exng']  # Extract 'exng' field
        print(exng, "exng")
        oldpeak = _json['oldpeak']  # Extract 'oldpeak' field
        print(oldpeak, "oldpeak")
        slp = _json['slp']  # Extract 'slp' field
        print(slp, "slp")
        caa = _json['caa']  # Extract 'caa' field
        print(caa, "caa")
        thall = _json['thall']  # Extract 'thall' field
        print(thall, "thall")
        
        print("Received JSON data:", _json)  # Add this line to print received JSON data for debugging

        # Validate the received values (add more validation as needed)
        if (age is not None and sex is not None and cp is not None and trtbps is not None
                and chol is not None and fbs is not None and restecg is not None and thalachh is not None
                and exng is not None and oldpeak is not None and slp is not None and caa is not None and thall is not None):

        # Prepare the input features for prediction
            input_features = [[sex, exng, caa, cp, fbs, restecg, slp, thall,
                           age, trtbps, chol, thalachh, oldpeak]]


        # Perform prediction using the model
            prediction = model.predict(input_features)[0]
            probability = model.predict_proba(input_features)[0]

        # Format the prediction result
            if prediction == 0:
                prediction_text = 'No chance of heart attack'
            else:
                 prediction_text = 'Yes, chance for heart attack'

        # Return the prediction result and probability as a dictionary
            prediction_result = {'prediction': prediction_text, 'probability': probability.tolist()}

        # Return the prediction result as a JSON response
            return jsonify(prediction_result)
        
        #Check the request type and preferred response format
            if request.method == 'POST' and request.accept_mimetypes.accept_json:
                return jsonify(prediction_result)
            else:
                return render_template('prediction_result.html', prediction_result=prediction_result) 
        else:
            # Handle missing or invalid input fields
            error_response = {'error': 'Missing or invalid input fields'}
            return jsonify(error_response), 400
    
    except psycopg2.Error as e:
        # Handle database-specific exceptions
        print("Database Error:", e)
        conn.rollback()  # Roll back any changes made in the transaction
        error_response = {'error': 'Database error occurred'}
        if request.method == 'POST' and request.accept_mimetypes.accept_json:
            return jsonify(error_response), 500
        else:
            return render_template('error.html', error_message=error_response), 500
    except KeyError as e:
        print("KeyError:", e)
        error_response = {'error': 'Missing or invalid input fields'}
        if request.method == 'POST' and request.accept_mimetypes.accept_json:
            return jsonify(error_response), 400
        else:
            return render_template('error.html', error_message=error_response), 400
    except Exception as e:
        print("Other Error:", e)
        error_response = {'error': 'An unexpected error occurred'}
        if request.method == 'POST' and request.accept_mimetypes.accept_json:
            return jsonify(error_response), 500
        else:
            return render_template('error.html', error_message=error_response), 500
    finally:
        # Close the cursor and connection in the finally block
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    

@app.route('/creater', methods=['POST'])
def create():
    try:
        conn = connectDB()
        if conn is None:
            return jsonify({'error': 'Database connection error'}), 500
        cursor = conn.cursor()  # created a cursor
        # cursor.execute("select User_Id from Users")  # [(1,),(2,)]
        # res1 = cursor.fetchall()
        # Id_alr = len(res1)
        # User_Id = Id_alr + 1

        _json = request.json  # converting to json

        age = _json['age']
        print(age, "age")
        sex = _json['sex']  # Extract 'sex' field
        print(sex, "sex")
        cp = _json['cp']  # Extract 'cp' field
        print(cp, "cp")
        trtbps = _json['trtbps']  # Extract 'trtbps' field
        print(trtbps, "trtbps")
        chol = _json['chol']  # Extract 'chol' field
        print(chol, "chol")
        fbs = _json['fbs']  # Extract 'fbs' field
        print(fbs, "fbs")
        restecg = _json['restecg']  # Extract 'restecg' field
        print(restecg, "restecg")
        thalachh = _json['thalachh']  # Extract 'thalachh' field
        print(thalachh, "thalachh")
        exng = _json['exng']  # Extract 'exng' field
        print(exng, "exng")
        oldpeak = _json['oldpeak']  # Extract 'oldpeak' field
        print(oldpeak, "oldpeak")
        slp = _json['slp']  # Extract 'slp' field
        print(slp, "slp")
        caa = _json['caa']  # Extract 'caa' field
        print(caa, "caa")
        thall = _json['thall']  # Extract 'thall' field
        print(thall, "thall")


        # validate the received values
        if (age and sex and cp and trtbps and chol and fbs and restecg and thalachh
                and exng and oldpeak and slp and caa and thall and request.method == 'POST'):
            sql = "INSERT INTO medical(age, sex, cp, trtbps, chol, fbs, restecg, thalachh, exng, oldpeak, slp, caa, thall)" \
                  " VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"  # Modify the SQL query
            data = (age, sex, cp, trtbps, chol, fbs, restecg, thalachh, exng, oldpeak, slp, caa, thall)  # Pass the new field values

            cursor.execute(sql, data)
            conn.commit()
            resp = jsonify({"Message": " added successfully!", "Status": "200 OK"})
            return resp
        else:
            # Handle missing or invalid input fields
            error_response = {'error': 'Missing or invalid input fields'}
            return jsonify(error_response), 400
        
    except psycopg2.Error as e:
        # Handle database-specific exceptions
        print("Database Error:", e)
        conn.rollback()  # Roll back any changes made in the transaction
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        print("Other Error:", e)
        return jsonify({'error': 'An unexpected error occurred'}), 500
    finally:
        # Close the cursor and connection in the finally block
        if cursor:
            cursor.close()
        if conn:
            conn.close()   


 # Replace 'path_to_model' with the actual path to your model file


@app.route('/Login.html')
def Login():
    return render_template('Login.html')

@app.route('/Login', methods=['POST'])
def login_form():
    user_type = request.form.get('user-type')
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Perform authentication and validation logic here
    # You can check the user type, username, and password against your database
    authentication_successful = False  # Initialize the variable
    
    # Example authentication logic (replace this with your actual logic)
    if user_type == 'user' and username == 'valid_user' and password == 'valid_password':
        authentication_successful = True


    if authentication_successful:
        # Redirect or respond with a success message
        return jsonify({'message': 'Login successful'})
    else:
        # Respond with an error message
        return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/contact.html')
def contact():
    return render_template('contact.html')

# Route to handle contact form submission
@app.route('/contact', methods=['POST'])
def contact_submission():
    try:
        conn = connectDB()
        if conn is None:
            return jsonify({'error': 'Database connection error'}), 500
        cursor = conn.cursor()

        # Extract form data from request
        _json = request.json
        name = _json['name']
        email = _json['email']
        message = _json['message']

        # Insert contact form data into the database
        sql = "INSERT INTO contact_form (name, email, message) VALUES (%s, %s, %s)"
        data = (name, email, message)
        cursor.execute(sql, data)
        conn.commit()

        return jsonify({"Message": "Contact form submitted successfully!", "Status": "200 OK"})
    except psycopg2.Error as e:
        # Handle database-specific exceptions
        print("Database Error:", e)
        conn.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        print("Other Error:", e)
        return jsonify({'error': 'An unexpected error occurred'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/')
def index():
    return render_template('index.html')


# Route to handle signup form submission
@app.route('/index', methods=['POST'])
def signup():
    try:
        conn = connectDB()
        if conn is None:
            return jsonify({'error': 'Database connection error'}), 500
        cursor = conn.cursor()

        # Extract form data from request
        _json = request.json
        username = _json['username']
        password = generate_password_hash(_json['password'])  # Hash the password
        gender = _json['gender']
        email = _json['email']
        phone = _json['phone']

        # Insert user data into the database
        sql = "INSERT INTO users (username, password, gender, email, phone) VALUES (%s, %s, %s, %s, %s)"
        data = (username, password, gender, email, phone)
        cursor.execute(sql, data)
        conn.commit()

        return jsonify({"Message": "User registered successfully!", "Status": "200 OK"})
    except psycopg2.Error as e:
        # Handle database-specific exceptions
        print("Database Error:", e)
        conn.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        print("Other Error:", e)
        return jsonify({'error': 'An unexpected error occurred'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)