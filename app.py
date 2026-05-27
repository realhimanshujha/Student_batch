from flask import Flask,render_template,request,redirect,session
import sqlite3
from datetime import datetime
import requests

app=Flask(__name__)
SHEET_API="https://script.google.com/macros/s/AKfycbz-L2LCsEuqzUCvZ5mFMbArj6luGKHGpZs3XXHDCkHPEvU-hOzqToiPoHSDPUcjb1BkGg/exec"
app.secret_key="vistaeducare123"

def db():

    conn=sqlite3.connect("students.db")
    conn.row_factory=sqlite3.Row
    return conn


def setup():

    conn=db()

    conn.execute("""

        CREATE TABLE IF NOT EXISTS students(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        course TEXT,

        batch_time TEXT,

        computer_no INTEGER

        )

    """)

    conn.execute("""

    CREATE TABLE IF NOT EXISTS schedules(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_id INTEGER,

    day TEXT

    )

    """)

    conn.commit()

    conn.close()


setup()


batches=[

"8:00-9:30",
"9:30-11:00",
"11:00-12:30",
"12:30-2:00",
"2:00-3:30",
"3:30-5:00",
"5:00-6:30"

]


USERNAME="admin"

PASSWORD="vista123"

@app.route(
"/login",
methods=["GET","POST"]
)

def login():

    error=""

    if request.method=="POST":

        username=request.form["username"]

        password=request.form["password"]

        if(

        username==USERNAME

        and

        password==PASSWORD

        ):

            session["user"]=username

            return redirect("/")

        else:

            error="Wrong Username or Password"

    return render_template(

    "login.html",

    error=error

    )


@app.route("/logout")

def logout():

    session.clear()

    return redirect("/login")


@app.route("/pcs")

def pcs():

    if "user" not in session:

        return redirect("/login")

    students=requests.get(

    SHEET_API

    ).json()

    today=datetime.now().strftime("%A")

    data=[]

    for batch in batches:

        pcs=[]

        for pc in range(1,6):

            found=None

            for s in students:

                days=[

                d.strip()

                for d in

                s["Days"].split(",")

                ]

                if(

                s["Batch"]==batch

                and

                int(s["PC"])==pc

                and

                today in days

                ):

                    found=s

                    break

            if found:

                pcs.append({

                "pc":pc,

                "name":

                found["Name"],

                "free":False

                })

            else:

                pcs.append({

                "pc":pc,

                "free":True

                })

        data.append({

        "batch":batch,

        "pcs":pcs

        })

    return render_template(

    "pcs.html",

    data=data

    )

@app.route("/calendar")

def calendar():

    if "user" not in session:

        return redirect("/login")

    students=requests.get(

    SHEET_API

    ).json()

    batch_order={

    "8:00-9:30":1,

    "9:30-11:00":2,

    "11:00-12:30":3,

    "12:30-2:00":4,

    "2:00-3:30":5,

    "3:30-5:00":6,

    "5:00-6:30":7

    }

    students=sorted(

    students,

    key=lambda s:(

    batch_order.get(

    s["Batch"],

    999

    ),

    int(

    s["PC"]

    )

    )

    )

    days={

    "Monday":[],

    "Tuesday":[],

    "Wednesday":[],

    "Thursday":[],

    "Friday":[],

    "Saturday":[]

    }

    for s in students:

        student_days=[

        x.strip()

        for x in

        s["Days"].split(",")

        ]

        for d in student_days:

            if d in days:

                days[d].append({

                "name":

                s["Name"],

                "batch_time":

                s["Batch"],

                "computer_no":

                s["PC"]

                })

    today= datetime.now().strftime(

    "%A"

    )

    return render_template(

    "calendar.html",

    days=days,

    current_day=today

    )



@app.route("/",methods=["GET","POST"])

def home():

    if "user" not in session:

        return redirect("/login")

    if request.method=="POST":

        search=request.form.get(
        "search",
        ""
        )

    else:

        search=""

    students= requests.get(

    SHEET_API

    ).json()

    for s in students:

        s["id"]=students.index(s)+1

        s["batch_time"]=s["Batch"]

        s["computer_no"]=s["PC"]

        s["course"]=s["Course"]

        s["name"]=s["Name"]

        s["days"]=s["Days"]

    batch_order={

    "8:00-9:30":1,
    "9:30-11:00":2,
    "11:00-12:30":3,
    "12:30-2:00":4,
    "2:00-3:30":5,
    "3:30-5:00":6,
    "5:00-6:30":7

    }

    students=sorted(

    students,

    key=lambda x:

    batch_order.get(

    x["batch_time"],

    999

    )

    )

    if search:

        students=[

        s for s in students

        if

        search.lower() in s["name"].lower()

        or

        search.lower() in s["course"].lower()

        ]

    total_students=len(students)

    mwf_capacity=35
    tts_capacity=35

    mwf_used=0
    tts_used=0

    day_order = {

    "Monday":1,
    "Tuesday":2,
    "Wednesday":3,
    "Thursday":4,
    "Friday":5,
    "Saturday":6

    }

    students_fixed=[]

    for s in students:

        row=dict(s)

        if row["days"]:

            items=[]

            for x in row["days"].split(","):

                day=x.strip()

                if "-" in day:

                    day=day.split("-")[1]

                items.append(day)

            items.sort(

            key=lambda x:

            day_order[x]

            )

            row["days"]=", ".join(items)

        students_fixed.append(row)

    students=students_fixed

    for s in students:

        days=s["days"]

        if days:

            if (

            "Monday" in days

            or

            "Wednesday" in days

            or

            "Friday" in days

            ):

                mwf_used += 1

            if (

            "Tuesday" in days

            or

            "Thursday" in days

            or

            "Saturday" in days

            ):

                tts_used += 1


    mwf_left = mwf_capacity - mwf_used

    tts_left = tts_capacity - tts_used

    total_left = mwf_left + tts_left

    active_batches=len(

    set(

    s["batch_time"]

    for s in students

    )

    )

    return render_template(

    "index.html",

    students=students,

    search=search,

    total_students=total_students,

    active_batches=active_batches,

    mwf_left=mwf_left,

    tts_left=tts_left,

    total_left=total_left

    )

@app.route(
"/edit/<int:id>",
methods=["GET","POST"]
)

def edit(id):

    if "user" not in session:

        return redirect("/login")

    students = requests.get(

    SHEET_API

    ).json()

    student = students[id-1]

    current = student["Days"].split(",")

    old_batch=student["Batch"]

    old_pc=student["PC"]

    if request.method=="POST":

        old_course=student["Course"]
        old_batch=student["Batch"]
        old_pc=student["PC"]
        old_days=student["Days"]

        name=request.form["name"]
        course=request.form["course"]
        batch=request.form["batch"]
        pc=request.form["pc"]
        days=request.form["days"]

        session["popup"]={

        "name":name,

        "old_course":old_course,
        "new_course":course,

        "old_batch":old_batch,
        "new_batch":batch,

        "old_pc":old_pc,
        "new_pc":pc,

        "old_days":old_days,
        "new_days":days

        }

        requests.post(

        SHEET_API,

        json={

        "action":"update",

        "row":

        student["row"],

        "name":

        name,

        "course":

        course,

        "batch":

        batch,

        "pc":

        pc,

        "days":

        days

        }

        )

        session["popup"]={

        "name":name,

        "old_batch":old_batch,
        "new_batch":batch,

        "old_pc":old_pc,
        "new_pc":pc,

        "old_days":old_days,
        "new_days":days

        }

        return redirect("/")

    return render_template(

    "edit.html",

    student={

    "name":

    student["Name"],

    "course":

    student["Course"],

    "batch_time":

    student["Batch"],

    "computer_no":

    student["PC"]

    },

    current=current,

    batches=batches

    )

@app.route("/add",methods=["GET","POST"])

def add():

    if "user" not in session:

        return redirect("/login")

    conn=db()

    available=[]

    if request.method=="POST":

        name=request.form["name"].strip()

        course=request.form["course"].strip()

        days=request.form.get("days","")

        if not name or not course or not days:

            conn.close()

            return render_template(

            "add_student.html",

            available=[]

            )

        days=days.split(",")

        batch=request.form.get("batch")

        pc=request.form.get("pc")

        if batch and pc:

            requests.post(

            SHEET_API,

            json={

            "name":name,

            "course":course,

            "batch":batch,

            "pc":pc,

            "days":",".join(days)

            }

            )

            conn.close()

            return """

            <html>

            <head>

            <style>

            body{

            margin:0;

            background:

            rgba(0,0,0,.65);

            display:flex;

            justify-content:center;

            align-items:center;

            height:100vh;

            font-family:Arial;

            overflow:hidden;

            backdrop-filter:

            blur(8px);

            }

            .popup{

            background:

            linear-gradient(

            135deg,

            #111a4b,

            #171752

            );

            padding:40px;

            border-radius:25px;

            text-align:center;

            width:340px;

            box-shadow:

            0 0 40px

            #7c3aed;

            animation:

            popup .3s ease;

            color:white;

            }

            h1{

            margin:0;

            font-size:34px;

            }

            p{

            font-size:20px;

            margin:

            18px 0;

            color:#d5d8ff;

            }

            .btns{

            display:flex;

            gap:15px;

            justify-content:center;

            margin-top:25px;

            }

            button{

            border:none;

            padding:

            15px 28px;

            font-size:18px;

            font-weight:bold;

            border-radius:14px;

            cursor:pointer;

            transition:.3s;

            }

            .add{

            background:

            linear-gradient(

            90deg,

            #7c3aed,

            #3b82f6

            );

            color:white;

            box-shadow:

            0 0 18px

            #7c3aed;

            }

            .home{

            background:

            #4a4a4a;

            color:white;

            }

            button:hover{

            transform:

            scale(1.08);

            }

            @keyframes popup{

            from{

            opacity:0;

            transform:

            scale(.7);

            }

            to{

            opacity:1;

            transform:

            scale(1);

            }

            }

            </style>

            </head>

            <body>

            <div class='popup'>

            <h1>

            ✅ Added

            </h1>

            <p>

            Student added successfully

            </p>

            <p>

            Add another student?

            </p>

            <div class='btns'>

            <button

            class='home'

            onclick=

            "location.href='/'"

            >

            Dashboard

            </button>

            <button

            class='add'

            onclick=

            "location.href='/add'"

            >

            Add More

            </button>

            </div>

            </div>

            </body>

            </html>

            """

            

        else:

            students = requests.get(

            SHEET_API

            ).json()

            for batch_time in batches:

                used=set()

                for student in students:

                    student_days = student["Days"].split(",")

                    if student["Batch"] == batch_time:

                        for d in days:

                            if d.strip() in student_days:

                                used.add(

                                    int(student["PC"])

                                )

                free=[]

                for pc in range(1,6):

                    if pc not in used:

                        free.append(pc)

                if free:

                    available.append({

                    "batch":batch_time,

                    "pcs":free

                    })

    conn.close()

    return render_template(

    "add_student.html",

    available=available

    )


@app.route(
"/delete/<int:id>"
)

def delete(id):

    if "user" not in session:

        return redirect(
        "/login"
        )

    students=requests.get(
    SHEET_API
    ).json()

    row=students[
    id-1
    ]["row"]

    requests.get(

    SHEET_API+

    "?action=delete&row="+

    str(row)

    )

    return redirect(
    "/"
    )

import os

if __name__=="__main__":

    app.run(

    host="0.0.0.0",

    port=int(

    os.environ.get(

    "PORT",

    5000

    )

    ),

    debug=False

    )