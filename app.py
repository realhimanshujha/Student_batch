from flask import Flask,render_template,request,redirect,session
import sqlite3
from datetime import datetime

app=Flask(__name__)
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

    conn=db()

    today = datetime.now().strftime("%A")

    data=[]

    for batch in batches:

        pcs=[]

        for pc in range(1,6):

            row=conn.execute("""

            SELECT s.name

            FROM students s

            JOIN schedules sc

            ON s.id=sc.student_id

            WHERE

            s.batch_time=?
            AND s.computer_no=?
            AND sc.day=?

            """,

            (

            batch,
            pc,
            today

            )

            ).fetchone()

            if row:

                pcs.append({

                "pc":pc,

                "name":row["name"],

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

    conn.close()

    return render_template(

    "pcs.html",

    data=data

    )


@app.route("/calendar")

def calendar():

    if "user" not in session:

        return redirect("/login")

    conn=db()

    rows=conn.execute("""

    SELECT

    s.name,
    s.batch_time,
    s.computer_no,
    sc.day

    FROM students s

    JOIN schedules sc

    ON s.id=sc.student_id

    ORDER BY day,batch_time

    """).fetchall()

    conn.close()

    days={

    "Monday":[],

    "Tuesday":[],

    "Wednesday":[],

    "Thursday":[],

    "Friday":[],

    "Saturday":[]

    }

    for r in rows:

        days[
        r["day"]
        ].append(r)

    return render_template(

    "calendar.html",

    days=days

    )



@app.route("/")
def home():

    if "user" not in session:

        return redirect("/login")

    conn=db()

    search=request.args.get(
    "search",
    ""
    )

    students=conn.execute("""

    SELECT

    s.id,
    s.name,
    s.course,
    s.batch_time,
    s.computer_no,

    GROUP_CONCAT(

    CASE sc.day

    WHEN 'Monday' THEN '1-Monday'
    WHEN 'Tuesday' THEN '2-Tuesday'
    WHEN 'Wednesday' THEN '3-Wednesday'
    WHEN 'Thursday' THEN '4-Thursday'
    WHEN 'Friday' THEN '5-Friday'
    WHEN 'Saturday' THEN '6-Saturday'

    END,

    ', '

    ) days

    FROM students s

    LEFT JOIN schedules sc

    ON s.id=sc.student_id

    WHERE

    s.name LIKE ?

    OR

    s.course LIKE ?

    GROUP BY s.id

    """,

    (

    f"%{search}%",

    f"%{search}%"

    )

    ).fetchall()

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

    active_batches=conn.execute("""

    SELECT COUNT(

    DISTINCT batch_time

    )

    FROM students

    """).fetchone()[0]

    conn.close()

    return render_template(

    "index.html",

    students=students,

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

    conn=db()

    if request.method=="POST":

        name=request.form["name"]

        course=request.form["course"]

        batch=request.form["batch"]

        pc=request.form["pc"]

        days=request.form["days"]

        days=days.split(",")

        conn.execute("""

        UPDATE students

        SET

        name=?,
        course=?,
        batch_time=?,
        computer_no=?

        WHERE id=?

        """,

        (

        name,
        course,
        batch,
        pc,
        id

        ))

        conn.execute(

        """

        DELETE FROM schedules

        WHERE student_id=?

        """,

        (id,)

        )

        for d in days:

            conn.execute(

            """

            INSERT INTO schedules(

            student_id,
            day

            )

            VALUES(?,?)

            """,

            (

            id,
            d.strip()

            )

            )

        conn.commit()

        conn.close()

        return redirect("/")



    student=conn.execute("""

    SELECT *

    FROM students

    WHERE id=?

    """,

    (id,)

    ).fetchone()


    rows=conn.execute("""

    SELECT day

    FROM schedules

    WHERE student_id=?

    """,

    (id,)

    ).fetchall()


    current=[]

    for r in rows:

        current.append(

        r["day"]

        )


    conn.close()


    return render_template(

    "edit.html",

    student=student,

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

            cursor=conn.cursor()

            cursor.execute("""

            INSERT INTO students(

                name,
                course,
                batch_time,
                computer_no

                )

                VALUES(?,?,?,?)
            """,

            (

            name,
            course,
            batch,
            pc

            ))

            sid=cursor.lastrowid

            for d in days:

                conn.execute(

                """

                INSERT INTO schedules(

                student_id,
                day

                )

                VALUES(?,?)

                """,

                (sid,d)

                )

            conn.commit()

            conn.close()

            return redirect("/")

        else:

            for batch_time in batches:

                used=set()

                for d in days:

                    rows=conn.execute("""

                    SELECT computer_no

                    FROM students s

                    JOIN schedules sc

                    ON s.id=sc.student_id

                    WHERE

                    batch_time=?
                    AND day=?

                    """,

                    (

                    batch_time,
                    d

                    )).fetchall()

                    for r in rows:

                        used.add(

                        r["computer_no"]

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


@app.route("/delete/<int:id>")

def delete(id):

    if "user" not in session:

        return redirect("/login")

    conn=db()

    conn.execute(

    "DELETE FROM schedules WHERE student_id=?",

    (id,)

    )

    conn.execute(

    "DELETE FROM students WHERE id=?",

    (id,)

    )

    conn.commit()

    conn.close()

    return redirect("/")


if __name__=="__main__":

    app.run(
    host="0.0.0.0",
    port=5000,
    debug=True
    )