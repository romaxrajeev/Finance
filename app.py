from flask import Flask, render_template, redirect, url_for, session, flash
from flask.globals import request
from apiData import *
from oauth2client.client import Error
import pyrebase
import math
import datetime
import time

app = Flask(__name__)
app.secret_key = secretKey

config = {
    "apiKey": apiKey,
    "authDomain": authDomain,
    "databaseURL": dbUrl,
    "projectId": projectID,
    "storageBucket": storage,
    "messagingSenderId": msgSender,
    "appId": appID
}

firebase = pyrebase.initialize_app(config)

db = firebase.database()
auth = firebase.auth()

@app.route('/', methods = ['GET', 'POST'])
def landing():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        idToken = None
        try:
            sign_user = auth.sign_in_with_email_and_password(email,password)
            idToken = sign_user['idToken']
        except:
            print("Error")
            return render_template("index.html",login_error="Your credentials are incorrect. Please try again.")

        key = email.split('.')[0]
        session['user'] = idToken
        session['key'] = key
        if 'user' in session :
            return redirect(url_for('home'))

    return render_template("index.html")

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['uname']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        income = request.form['income']
        key = email.split('.')[0]
        data = {
            "name" : name,
            "email" : email,
            "phone" : phone,
            "income" : income,
            "goals" : None
        }
        try:
            newUser = auth.create_user_with_email_and_password(email,password)
            #Also do sign in
            sign_user = auth.sign_in_with_email_and_password(email,password)
            idToken = sign_user['idToken']
            session['user'] = idToken
            session['key'] = key
            db.child("users").child(key).set(data)
            return redirect(url_for('home'))
        except Error as e:
            print("Could not create account")

    return render_template("signup.html")

@app.route('/forgotpass',methods=['GET','POST'])
def forgotpass():
    if request.method == 'POST':
        email = request.form['email']
        try:
            mail_send = auth.send_password_reset_email(email)
        except:
            print("Unable to send mail.")
    return render_template("forgotpass.html")

@app.route('/home',methods=['GET','POST'])
def home():
    if "user" in session:
        #Get data regarding goals
        goals = db.child("users").child(session["key"]).child("goals").get()       
        userData = dict(db.child("users").child(session["key"]).get().val())
        g = []
        if goals.val():
            for gid,goal in dict(goals.val()).items():
                goal.update({"id":gid})
                g.append(goal)
        if request.method == 'POST':
            expenditure = int(request.form['expenditure'])

            #Calculate if he is forward or backward in goal
            monthlySavings = int(userData["income"]) - expenditure
            expData = {
                "timestamp" : str(datetime.datetime.now()),
                "expenditure" : expenditure,
                "monthlysaving" : monthlySavings 
            }

            #Add expenditure to the database
            db.child("users").child(session['key']).child("expenditure").push(expData)

            #All savings to be divided for each goal
            for goal in g:
                if goal["percentage"] < 100:
                    updateGoal = {}
                    
                    #If monthly savings is more than expected amount, then deduct the expected amount
                    if monthlySavings >= goal["expectedamount"]:
                        savedtillnow = goal["savedtillnow"] + goal["expectedamount"]
                        monthlySavings -= goal["expectedamount"]
                    
                    #If Monthly savings is less than current expected amount, then add entire amount as saved till now for current goal
                    else:
                        savedtillnow = goal["savedtillnow"] + monthlySavings
                        monthlySavings = 0
                    
                    expectedsavingtillnow = goal["expectedsavetillnow"] + goal["expectedamount"]
                    if savedtillnow >= expectedsavingtillnow:
                        status = "success"
                    else:
                        status = "danger"
                    percent = math.ceil(savedtillnow / goal["amount"] * 100)
                    updateGoal.update({"savedtillnow" : savedtillnow,
                    "expectedsavetillnow" : expectedsavingtillnow,
                    "percentage" : percent, "status" : status})

                    #Update in database
                    db.child("users").child(session["key"]).child("goals").child(goal["id"]).update(updateGoal)

            #If any monthly saving is left, then add it to last goal
            if monthlySavings > 0:
                lastGoal = g[-1]
                last = dict(db.child("users").child(session["key"]).child("goals").child(lastGoal["id"]).get().val())
                savedtillnow = last["savedtillnow"] + monthlySavings
                if savedtillnow >= last["expectedsavetillnow"]:
                    status = "success"
                else:
                    status = "danger"
                percent = math.ceil(savedtillnow / last["amount"] * 100)
                updateGoal = {
                    "savedtillnow" : savedtillnow,
                    "percentage" : percent,
                    "status" : status
                }                
                db.child("users").child(session["key"]).child("goals").child(lastGoal["id"]).update(updateGoal)
                time.sleep(4.0)
                return redirect(url_for('home'))
        return render_template('home.html',goals=g)
    return redirect(url_for('landing'))

@app.route('/logout')
def logout():
    session.pop("user",None)
    return redirect(url_for('landing'))

@app.route('/addgoal/<goaltype>', methods=['GET','POST'])
def addGoal(goaltype):
    expectedAmount = 0.0
    if request.method == 'POST':
        goalname = request.form['goalname']
        amount = int(request.form['amount'])
        months = int(request.form['months'])
        expectedAmount = round((amount / months),2)
        key = session['key']
        goalData = {
            "type" : goaltype,
            "name" : goalname,
            "amount" : amount,
            "months" : months,
            "expectedamount" : expectedAmount,
            "savedtillnow": 0,
            "expectedsavetillnow": 0,
            "percentage": 0,
            "status" : "success"
        }
        #Set the goal in firebase
        db.child("users").child(key).child("goals").push(goalData)
        db.child("users").child(key).child("")
        flash(str(expectedAmount))
        time.sleep(3.0)
        return redirect(url_for("home"))
    return render_template("add_new_goal.html",expectedAmount=expectedAmount,goaltype=goaltype)

@app.route('/showgoal/<goalid>')
def showgoal(goalid):
    #fetch from db
    goal_info = dict(db.child("users").child(session["key"]).child("goals").child(goalid).get().val())
    print(goal_info)
    return render_template("show_goal.html",goal = goal_info, goaltype = goal_info["type"])

if __name__ == '__main__':
    app.run()
