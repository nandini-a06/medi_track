from flask import Flask, render_template, request, redirect
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Database Connection
db = pymysql.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    port=3306
)

# Dashboard
@app.route("/")
def dashboard():
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM equipment")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM equipment WHERE status='Active'")
    active = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM equipment WHERE status='Under Maintenance'")
    maintenance = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM equipment WHERE status='Decommissioned'")
    decommissioned = cursor.fetchone()[0]

    cursor.execute("""
        SELECT equipment_name,next_due_date
        FROM equipment e
        JOIN maintenance_log m
        ON e.equipment_id=m.equipment_id
        WHERE next_due_date<CURDATE()
    """)
    overdue = cursor.fetchall()

    return render_template(
        "dashboard.html",
        total=total,
        active=active,
        maintenance=maintenance,
        decommissioned=decommissioned,
        overdue=overdue
    )


# Equipment List
@app.route("/equipment")
def equipment():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM equipment")
    data = cursor.fetchall()
    return render_template("equipment.html", equipment=data)


# Add Equipment
@app.route("/add_equipment", methods=["GET", "POST"])
def add_equipment():

    if request.method == "POST":

        name = request.form["equipment_name"]
        serial = request.form["serial_number"]
        dept = request.form["department"]
        purchase = request.form["purchase_date"]
        status = request.form["status"]

        cursor = db.cursor()

        cursor.execute("""
        INSERT INTO equipment
        (equipment_name,serial_number,department,purchase_date,status)
        VALUES(%s,%s,%s,%s,%s)
        """, (name, serial, dept, purchase, status))

        db.commit()

        return redirect("/equipment")

    return render_template("add_equipment.html")


# Equipment Details
@app.route("/equipment/<int:id>")
def details(id):

    cursor = db.cursor()

    cursor.execute("SELECT * FROM equipment WHERE equipment_id=%s", (id,))
    equipment = cursor.fetchone()

    cursor.execute("""
    SELECT * FROM maintenance_log
    WHERE equipment_id=%s
    """, (id,))
    logs = cursor.fetchall()

    return render_template(
        "equipment_details.html",
        equipment=equipment,
        logs=logs
    )


# Add Maintenance
@app.route("/add_log/<int:id>", methods=["GET", "POST"])
def add_log(id):

    if request.method == "POST":

        date = request.form["maintenance_date"]
        tech = request.form["technician_name"]
        issue = request.form["issue_reported"]
        notes = request.form["resolution_notes"]
        due = request.form["next_due_date"]

        cursor = db.cursor()

        cursor.execute("""
        INSERT INTO maintenance_log
        (equipment_id,maintenance_date,technician_name,
        issue_reported,resolution_notes,next_due_date)
        VALUES(%s,%s,%s,%s,%s,%s)
        """, (id, date, tech, issue, notes, due))

        db.commit()

        return redirect(f"/equipment/{id}")

    return render_template("add_log.html", equipment_id=id)


# Update Status
@app.route("/update_status/<int:id>", methods=["POST"])
def update_status(id):

    status = request.form["status"]

    cursor = db.cursor()

    cursor.execute("""
    UPDATE equipment
    SET status=%s
    WHERE equipment_id=%s
    """, (status, id))

    db.commit()

    return redirect(f"/equipment/{id}")


if __name__ == "__main__":
    app.run(debug=True)