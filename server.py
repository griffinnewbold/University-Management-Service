# imports necessary for server.py
import os
import time
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session

# -----Begin Boilerplate Code for DB-----#
tmpl_dir = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'databaseproject'

DATABASE_USERNAME = "gcn2106"
DATABASE_PASSWRD = "3276"
# change to 34.28.53.86 if you used database 2 for part 2
DATABASE_HOST = "34.148.107.47"
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/project1"
person_query = text(
    "INSERT INTO Person (uni, name, email, phone_number, address) VALUES (:a, :b, :c, :d, :e)")

engine = create_engine(DATABASEURI)
with engine.connect() as conn:
    pass


@app.before_request
def before_request():
    try:
        g.conn = engine.connect()
    except BaseException:
        print("uh oh, problem connecting to database")
        import traceback
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    try:
        g.conn.close()
    except Exception as e:
        pass

# -----End Boilerplate Code for DB-----#

# -----Begin Webpage Code for DB-----#
@app.route('/')
@app.route('/homepage')
def index():
    # DEBUG: this is debugging code to see what request looks like
    print(request.args)
    session.pop('textbox', None)
    return render_template("index.html")


@app.route('/student', methods=['POST', 'GET'])
def student():
    try:
        uni = session.pop('textbox', None)
        query = text("SELECT * From Person p FULL JOIN Student s on p.uni = s.uni FULL JOIN takes on p.uni=takes.uni FULL JOIN \"advised by\" a on p.uni = a.uni_s FULL JOIN \"belongs to\" b on p.uni = b.uni Where p.uni = :user_uni")
        query = query.bindparams(user_uni=uni)
        cursor = g.conn.execute(query)
        names = []
        for result in cursor:
            if (result[0] != 'None'):
                names.append(dict(uni=result[0], name=result[1],
                                email=result[2], phone=result[3], addr=result[4],
                                credits_att=result[5], credits_ern=result[6],
                                grad_date=result[7], courses_taken=result[8],
                                advisor=result[14], department=result[15]))
        cursor.close()

        query = text("SELECT * FROM takes Where uni = :uni").bindparams(uni=uni)
        cursor = g.conn.execute(query)
        courses_taking = []
        for res in cursor:
            courses_taking.append((res[0], res[2]))
        cursor.close()
        names[0]['courses_taking'] = courses_taking
        course_sugs = course_suggestion(
            uni,
            courses_taking,
            names[0]['courses_taken'],
            names[0]['department'])
        if (len(course_sugs) > 0):
            names[0]['course_suggestion'] = course_sugs
        else:
            response = []
            response.append("We do not have courses to recommend at this time")
            names[0]['course_suggestion'] = response
        filtered_data = []
        filtered_data.append(names[0])
        names = filtered_data

        context = dict(data=names)
        session['textbox'] = uni
        session['courses_complete'] = names[0]['courses_taken']
        session['courses_taking'] = names[0]['courses_taking']
        session['credits_att'] = names[0]['credits_att']
        session['credits_ern'] = names[0]['credits_ern']
        return render_template("student.html", **context)
    except BaseException as e:
        time.sleep(2)
        return render_template("student.html")


def course_suggestion(uni, courses_taking, courses_taken, dept_id):
    try:
        # checks for courses offered by department and see which ones you
        # have not taken or currently taking and returns them as recommendations
        select_query = text(
            "SELECT * From Department d, \"belongs to\" b Where d.dept_id = :a and b.uni = :b").bindparams(a=dept_id, b=uni)
        cursor = g.conn.execute(select_query)

        course_suggestions_list = []
        dept_offered = []

        for entry in cursor:
            dept_offered = list(entry[2])
        cursor.close()
        for course in dept_offered:
            if (notPresent(course, courses_taken)):
                course_suggestions_list.append(course)

        select_query = text(
            "SELECT * From \"belongs to\" b JOIN Department d on b.dept_id = d.dept_id JOIN Course c on b.course_id = c.course_id WHERE d.dept_id = :a and (b.uni = :b or b.uni = :c)")
        select_query = select_query.bindparams(a=dept_id, b=uni, c='None')
        cursor = g.conn.execute(select_query)
        for entry in cursor:
            if (entry[1] != 'None'):
                if (not notPresent(entry[1], courses_taking)
                        and entry[7] in course_suggestions_list):
                    course_suggestions_list.remove(entry[7])
        cursor.close()
        return course_suggestions_list
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return []


@app.route('/update_student', methods=['POST', 'GET'])
def update_student():
    try:
        exceptionRaised = False
        uni = session.pop('textbox', None)
        courses_complete = session.pop('courses_complete', None)
        courses_taking = session.pop('courses_taking', None)
        credits_att = float(session.pop('credits_att', None))
        credits_ern = float(session.pop('credits_ern', None))

        new_dept = request.form['textbox1']
        course_id = request.form['textbox2']
        willTransfer = request.form['textbox3']
        credits = request.form['textbox4']

        if (new_dept != ''):
            delete_query = text(
                "DELETE FROM \"belongs to\" Where uni = :a").bindparams(a=uni)
            g.conn.execute(delete_query)
            g.conn.commit()
            insert_query = text("INSERT INTO \"belongs to\" (dept_id, course_id, uni) VALUES (:a, :b, :c)").bindparams(
                a=new_dept, b='None', c=uni)
            g.conn.execute(insert_query)
        if (course_id != '' and notPresent(course_id, courses_taking) and notCompleted(course_id, courses_complete)):
            # insert into takes
            insert_query = text("INSERT into takes (course_id, uni, grade) VALUES (:a, :b, :c)").bindparams(
                a=course_id, b=uni, c='')
            g.conn.execute(insert_query)
        elif (course_id != '' and not notPresent(course_id, courses_taking)):
            # delete from takes
            delete_query = text("DELETE FROM takes Where uni = :a and course_id = :b").bindparams(
                a=uni, b=course_id)
            g.conn.execute(delete_query)
        if (credits != '' and isValidNum(credits)):
            credits_att += abs(float(credits))
            credits_ern += abs(float(credits))
            update_query = text("UPDATE Student set credits_attempted = :a Where uni = :b").bindparams(
                a=credits_att, b=uni)
            g.conn.execute(update_query)
            update_query = text("UPDATE Student set credits_earned = :a Where uni = :b").bindparams(
                a=credits_ern, b=uni)
            g.conn.execute(update_query)
        if (willTransfer == 'Yes' or willTransfer == 'yes'):
            # for every (course, grade) pair in takes
            for course in courses_taking:
                # find the title of the course based off course_id
                select_query = text(
                    "SELECT course_title From Course Where course_id = :cid").bindparams(cid=course[0])
                cursor = g.conn.execute(select_query)
                for entry in cursor:
                    # if the title is not present in courses_completed
                    if (notPresent(entry[0],
                                   courses_complete) and course[1] != ''):
                        courses_complete.append([entry[0], course[1]])
                        delete_query = text("DELETE FROM takes Where uni = :a and course_id = :b").bindparams(
                            a=uni, b=course[0])
                        g.conn.execute(delete_query)
                    elif (not notPresent(entry[0], courses_complete)):
                        delete_query = text("DELETE FROM takes Where uni = :a and course_id = :b").bindparams(
                            a=uni, b=course[0])
                        g.conn.execute(delete_query)
                cursor.close()
            update_query = text("UPDATE Student set course_record = :a Where uni = :b").bindparams(
                a=courses_complete, b=uni)
            g.conn.execute(update_query)
        g.conn.commit()
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        exceptionRaised = True
    finally:
        if(exceptionRaised):
            time.sleep(2)
        session['textbox'] = uni
        return redirect('/student')


def notCompleted(val, list_to_search):
    try:
        select_query = text(
                        "SELECT course_title From Course Where course_id = :cid").bindparams(cid=val)
        cursor = g.conn.execute(select_query)
        for entry in cursor:
            for arrPair in list_to_search:
                if(entry[0] in arrPair):
                    cursor.close()
                    return False
        cursor.close()
        return True
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return False

def notPresent(val, list_to_search):
    try:
        for pair in list_to_search:
            if (val == pair[0]):
                return False
        return True
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return False

def isValidNum(c):
    try:
        float(c)
    except ValueError:
        return False
    return True


@app.route('/advisor', methods=['POST', 'GET'])
def advisor():
    try:
        uni = session.pop('textbox', None)
        update_advisees(uni)
        query = text("SELECT * From Person p, Employee e, Advisor a, \"belongs to\" b Where p.uni = :user_uni and e.uni = :user_uni and a.uni = :user_uni and b.uni = :user_uni").bindparams(user_uni=uni)
        cursor = g.conn.execute(query)
        names = []
        for result in cursor:
            if (result[0] != 'None'):
                names.append(
                    dict(
                        uni=result[0],
                        name=result[1],
                        email=result[2],
                        phone=result[3],
                        addr=result[4],
                        years_of_exp=result[5],
                        salary=result[6],
                        alma_mater=result[7],
                        student_advisees=result[9],
                        isAvailable=result[10],
                        time_slots=result[11],
                        dept_code=result[13]))
        cursor.close()
        context = dict(data=names)
        session['textbox'] = uni
        session['dept'] = names[0]['dept_code']
        session['time'] = names[0]['time_slots']
        session['avail'] = names[0]['isAvailable']
        return render_template("advisor.html", **context)
    except BaseException as e:
        time.sleep(2)
        return render_template("advisor.html")


def update_advisees(uni):
    try:
        select_query = text(
            "SELECT student_advisees From Advisor a Where a.uni = :uni").bindparams(uni=uni)
        advised_by_relation = text(
            "SELECT uni_s FROM \"advised by\" Where uni_a = :uni").bindparams(uni=uni)
        cursor = g.conn.execute(select_query)
        uni_list = []
        for entry in cursor:
            uni_list = entry[0]
        cursor.close()
        new_uni_list = []
        cursor = g.conn.execute(advised_by_relation)
        for entry in cursor:
            if (entry[0] not in uni_list):
                new_uni_list.append(entry[0])
        cursor.close()
        for n_uni in new_uni_list:
            uni_list.append(n_uni)

        update_query = text(
            "UPDATE Advisor SET student_advisees = :a WHERE uni = :b").bindparams(a=uni_list, b=uni)
        g.conn.execute(update_query)
        g.conn.commit()
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))


@app.route('/update_advisor', methods=['POST', 'GET'])
def update_advisor():
    try:
        exceptionRaised = False
        uni = session.pop('textbox', None)
        times = session.pop('time', None)
        avail = session.pop('avail', None)
        new_dept = request.form['textbox1']

        time_slot = request.form['textbox2']
        if ('' in times):
            times.remove('')
        if (time_slot in times and len(times) > 1):
            times.remove(time_slot)
        elif (time_slot not in times and time_slot != ''):
            times.append(time_slot)

        switch_avail = request.form['textbox3']
        if (switch_avail == "Yes" or switch_avail == "yes"):
            if (avail == "True"):
                avail = "False"
            else:
                avail = "True"
            update_query = text("UPDATE Advisor SET isavailable = :a, daily_appointments = :b WHERE uni = :c").bindparams(
                    a=avail, b=times, c=uni)
            g.conn.execute(update_query)
            if (new_dept != ''):
                    delete_query = text(
                    "DELETE FROM \"belongs to\" Where uni = :a").bindparams(a=uni)
                    g.conn.execute(delete_query)
                    g.conn.commit()
                    insert_query = text("INSERT INTO \"belongs to\" (dept_id, course_id, uni) VALUES (:a, :b, :c)").bindparams(
                    a=new_dept, b='None', c=uni)
                    g.conn.execute(insert_query)
            g.conn.commit()
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        exceptionRaised = True
    finally:
        if(exceptionRaised):
            time.sleep(2)
        session['textbox'] = uni
        return redirect('/advisor')


@app.route('/instructor', methods=['POST', 'GET'])
def instructor():
    try:
        uni = session.pop('textbox', None)
        query = text("SELECT * From Person p, Employee e, Instructor i, \"belongs to\" b Where p.uni = :user_uni and e.uni = :user_uni and i.uni = :user_uni and b.uni = :user_uni").bindparams(user_uni=uni)
        cursor = g.conn.execute(query)
        names = []
        for result in cursor:
            if (result[0] != 'None'):
                names.append(
                    dict(
                        uni=result[0],
                        name=result[1],
                        email=result[2],
                        phone=result[3],
                        addr=result[4],
                        years_of_exp=result[5],
                        salary=result[6],
                        alma_mater=result[7],
                        courses_taught=result[9],
                        papers_written=result[10],
                        research_exp=result[12],
                        dept_code=result[13],
                        courses_teaching=list()))
        cursor.close()
        query = text(
            "SELECT * From Course c, teaches t WHERE t.course_id = c.course_id and t.uni = :user_uni").bindparams(user_uni=uni)
        cursor = g.conn.execute(query)
        for result in cursor:
            names[0]['courses_teaching'].append(result[1])
        cursor.close()
        context = dict(data=names)

        session['textbox'] = uni
        session['courses_taught'] = names[0]['courses_taught']
        session['courses_teaching'] = names[0]['courses_teaching']
        session['papers'] = names[0]['papers_written']

        return render_template("instructor.html", **context)
    except BaseException as e:
        time.sleep(2)
        return render_template("instructor.html")

@app.route('/submit_grades', methods=['POST', 'GET'])
def submit_grades():
    try:
        uni = session.pop('textbox', None)
        select_query = text(
            "SELECT * From teaches te JOIN takes ta on te.course_id = ta.course_id WHERE te.uni = :a").bindparams(a=uni)
        cursor = g.conn.execute(select_query)
        students = []
        for entry in cursor:
            students.append(
                dict(
                    course_id = entry[0],
                    student_uni = entry[3],
                    current_grade = entry[4]))
        cursor.close()
        context = dict(data=students)
        session['textbox'] = uni
        session['current_enrollment'] = students
        return render_template("instructor_assign_grades.html", **context)
    except BaseException as e:
        return redirect('/')

@app.route('/process_grades', methods=['POST', 'GET'])
def process_grades():
    try:
        course_data = session.pop('current_enrollment', None)
        for key, value in request.form.items():
            try:
                update_query = text(
                    "UPDATE takes SET grade = :a WHERE uni = :b and course_id = :c").bindparams(a=value, b=key, c=course_data[0]['course_id'])
                g.conn.execute(update_query)
                g.conn.commit()
            except BaseException as e:
                print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
                print(str(e))
        return redirect('/submit_grades')
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return redirect('/')


@app.route('/update_instructor', methods=['POST', 'GET'])
def update_instructor():
    try:
        exceptionRaised = False
        uni = session.pop('textbox', None)
        courses_taught = session.pop('courses_taught', None)
        courses_teaching = session.pop('courses_teaching', None)
        papers = session.pop('papers', None)

        new_dept = request.form['textbox1']
        new_course_id = request.form['textbox2']
        willTransfer = request.form['textbox3']
        new_papers = request.form['textbox4']
        if (willTransfer == 'Yes' or willTransfer == 'Yes'):
                for course in courses_teaching:
                        if (course not in courses_taught):
                                courses_taught.append(course)
                update_query = text("UPDATE Instructor SET courses_taught = :a WHERE uni = :c").bindparams(
                a=courses_taught, c=uni)
                delete_query = text(
                "DELETE From teaches WHERE uni = :a").bindparams(a=uni)
                g.conn.execute(update_query)
                g.conn.execute(delete_query)
        if (new_course_id != ''):
                insert_query = text("INSERT into teaches (course_id, uni) VALUES (:a, :b)").bindparams(
                a=new_course_id, b=uni)
                g.conn.execute(insert_query)
        if (new_dept != ''):
                delete_query = text(
                "DELETE FROM \"belongs to\" Where uni = :a").bindparams(a=uni)
                g.conn.execute(delete_query)
                g.conn.commit()
                insert_query = text("INSERT INTO \"belongs to\" (dept_id, course_id, uni) VALUES (:a, :b, :c)").bindparams(
                a=new_dept, b='None', c=uni)
                g.conn.execute(insert_query)
        if (new_papers != ''):
                papers.append(new_papers)
                update_query = text(
                "UPDATE Instructor SET papers_published = :a WHERE uni = :c").bindparams(a=papers, c=uni)
                g.conn.execute(update_query)
        g.conn.commit()
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        exceptionRaised = True
    finally:
        if(exceptionRaised):
            time.sleep(2)
        session['textbox'] = uni
        return redirect('/instructor')

@app.route('/directory', methods=['POST', 'GET'])
def directory():
    try:
        return render_template("directory.html")
    except:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")

@app.route('/course_directory', methods=['POST', 'GET'])
def course_directory():
    try:
        return render_template("course_directory.html")
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")

@app.route('/search_course_db', methods=['POST'])
def search_course_db():
    try:
        search_term = request.form['term']
        search_condition = '%' + search_term + '%'
        query = "SELECT * FROM \"belongs to\" b JOIN Department d on b.dept_id = d.dept_id JOIN Course c on c.course_id = b.course_id, \"located in\" l WHERE l.course_id = " + \
            "c.course_id and (((d.courses_offered::text ILIKE :term_a and c.course_title ILIKE :term_a) or c.course_id = :term_b) or d.dept_id ILIKE :term_a)"
        query = text(query).bindparams(term_a=search_condition, term_b=search_term)
        cursor = g.conn.execute(query)

        if (len(search_term) != 0):
            names = []
            for result in cursor:
                if (result[6] != 'None'):
                    names.append(
                        dict(
                            course_name=result[7],
                            dept_id=result[0],
                            course_code=result[6],
                            time_slot=result[8],
                            building_code=result[11],
                            building_capacity=result[9],
                            dept_name=result[4]))
            cursor.close()
            if (len(names) != 0):
                context = dict(data=names)
                return render_template("course_directory.html", **context)
            result = [
                dict(
                    err_msg="There is no entry in our records relating to your search term, please check your search then try again")]
            context = dict(data=result)
            return render_template("course_directory.html", **context)
        else:
            result = [
                dict(
                    err_msg="There is no entry in our records relating to your search term, please check your search then try again")]
            context = dict(data=result)
            return render_template("course_directory.html", **context)
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")

@app.route('/search_db', methods=['POST'])
def search_db():
    try:
        # gets entry and forms SQL query
        name = request.form['name']
        query = text(
            "SELECT * FROM Person p where p.name ILIKE :search_term or p.uni ILIKE :search_term")
        search_condition = '%' + name + '%'
        query = query.bindparams(search_term=search_condition)

        # executes the query and parses the results
        cursor = g.conn.execute(query)
        names = []
        for result in cursor:
            if (result[0] != 'None'):
                names.append(result)
        cursor.close()

        # updates the page contents then refreshes
        if (len(names) != 0):
            context = dict(data=names)
        else:
            result = [
                "There is no entry in our records relating to your search term, please check your search then try again"]
            context = dict(data=result)
        return render_template("directory.html", **context)
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")

# Example of adding new data to the database
@app.route('/login', methods=['POST'])
def login():
    try:
        # accessing form inputs from user
        name = request.form['name']
        session['textbox'] = name
        params = {}
        params["new_name"] = name
        names = params["new_name"]

        # error checking for empty login field
        if (len(names) == 0):
            return redirect('/')

        # sql query to see if we have a valid user
        select_query = "SELECT uni FROM Person"
        cursor = g.conn.execute(text(select_query))
        res = []
        for result in cursor:
            res.append(result[0])
        cursor.close()

        if (names not in res and names != "admin"):
            context = dict(data="Invalid UNI, Please Try Again!")
            return render_template("index.html", **context)

        if (names == 'admin'):
            return redirect('/admin')
        elif (names[0] == 'a'):
            return redirect('/advisor')
        elif (names[0] == 's'):
            return redirect('/student')
        elif (names[0] == 'i'):
            return redirect('/instructor')
        return redirect('/')
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")

'''
All functionality relating to the Admin
'''
@app.route('/admin', methods=['POST', 'GET'])
def admin():
    try:
        if(session.pop('textbox', None) == "admin"):
            session['textbox'] = "admin"
            return render_template("admin.html")
        context = dict(data="Invalid Credentials, Please Try Again!")
        return render_template("index.html", **context)
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")

@app.route('/admin_enroll', methods=['POST', 'GET'])
def admin_enroll():
    try:
        if(session.pop('textbox', None) != "admin"):
            context = dict(data="Invalid Credentials, Please Try Again!")
            return render_template("index.html", **context)
        session['textbox'] = "admin"
        select_query = "SELECT * FROM Person"
        cursor = g.conn.execute(text(select_query))
        res = []
        for result in cursor:
            if (result[0] != 'None'):
                res.append(
                    dict(
                        uni=result[0],
                        name=result[1],
                        email=result[2],
                        phone=result[3],
                        address=result[4]))
        cursor.close()
        context = dict(data=res)
        return render_template("admin_enroll.html", **context)
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")

@app.route('/admin_catalog', methods=['POST', 'GET'])
def admin_catalog():
    try:
        if(session.pop('textbox', None) != "admin"):
            context = dict(data="Invalid Credentials, Please Try Again!")
            return render_template("index.html", **context)
        session['textbox'] = "admin"
        select_query = "SELECT * FROM Course"
        cursor = g.conn.execute(text(select_query))
        res = []
        for result in cursor:
            if (result[0] != 'None'):
                res.append(
                    dict(
                        course_id=result[0],
                        course_title=result[1],
                        time=result[2],
                        size=result[3]))
        cursor.close()
        context = dict(data=res)
        return render_template("admin_catalog.html", **context)
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")

@app.route('/admin_dept', methods=['POST', 'GET'])
def admin_dept():
    try:
        if(session.pop('textbox', None) != "admin"):
            context = dict(data="Invalid Credentials, Please Try Again!")
            return render_template("index.html", **context)
        session['textbox'] = "admin"
        select_query = text("SELECT * FROM Department")
        cursor = g.conn.execute(select_query)
        res = []
        for result in cursor:
            res.append(
                dict(
                    dept_id=result[0],
                    dept_title=result[1],
                    courses=result[2]))
        cursor.close()
        context = dict(data=res)
        return render_template("admin_dept.html", **context)
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")


@app.route('/admin_construction', methods=['POST', 'GET'])
def admin_construction():
    try:
        if(session.pop('textbox', None) != "admin"):
            context = dict(data="Invalid Credentials, Please Try Again!")
            return render_template("index.html", **context)
        session['textbox'] = "admin"
        select_query = text("SELECT * FROM Building")
        cursor = g.conn.execute(select_query)
        res = []
        for result in cursor:
            res.append(dict(building_id=result[0], addr=result[1], cap=result[2]))
        cursor.close()
        context = dict(data=res)
        return render_template("admin_construction.html", **context)
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")

@app.route('/begin_addition_process', methods=['GET', 'POST'])
def begin_addition_process():
    try:
        if(session.pop('textbox', None) != "admin"):
            context = dict(data="Invalid Credentials, Please Try Again!")
            return render_template("index.html", **context)
        uni = request.form['textbox1']
        name = request.form['textbox2']
        email = request.form['textbox3']
        phone = request.form['textbox4']
        address = request.form['textbox5']
        session['uni'] = uni
        session['name'] = name
        session['email'] = email
        session['phone'] = phone
        session['address'] = address
        session['textbox'] = "admin"

        if (uni[0] == 's'):
            return redirect('/admin_enroll_student')
        elif (uni[0] == 'a'):
            return redirect('/admin_employ_advisor')
        elif (uni[0] == 'i'):
            return redirect('/admin_employ_instructor')
        else:
            return redirect('/admin_enroll')
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")


@app.route('/enroll_student', methods=['GET', 'POST'])
def enroll_student():
    try:
        session['textbox'] = "admin"
        grad_date = request.form['textbox1']
        advisor_uni = request.form['textbox2']
        uni = session.pop('uni', None)
        name = session.pop('name', None)
        email = session.pop('email', None)
        phone = session.pop('phone', None)
        address = session.pop('address', None)
        exceptionRaised = False

        p_query = person_query.bindparams(
            a=uni, b=name, c=email, d=phone, e=address)

        student_query = text(
            "INSERT INTO Student (credits_attempted, credits_earned, expected_grad_year, course_record, uni) VALUES (:a, :b, :c, :d, :e)")
        student_query = student_query.bindparams(
            a=0.0, b=0.0, c=abs(int(grad_date)), d=list(), e=uni)

        assign_advisor = text("INSERT INTO \"advised by\" (uni_s, uni_a) VALUES (:a, :b)").bindparams(
            a=uni, b=advisor_uni)
    
        g.conn.execute(p_query)
        g.conn.execute(student_query)
        g.conn.execute(assign_advisor)
        g.conn.commit()
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        exceptionRaised = True
    finally:
        if(exceptionRaised):
            time.sleep(2)
        return redirect('/admin_enroll')


@app.route('/employ_instructor', methods=['GET', 'POST'])
def employ_instructor():
    try:
        session['textbox'] = "admin"
        uni = session.pop('uni', None)
        name = session.pop('name', None)
        email = session.pop('email', None)
        phone = session.pop('phone', None)
        address = session.pop('address', None)
        exceptionRaised = False

        year_of_exp = request.form['textbox1']
        salary = int(request.form['textbox2'])
        school = request.form['textbox3']
        research_exp = request.form['textbox4']
        dept_id = request.form['textbox5']

        p_query = person_query.bindparams(
            a=uni, b=name, c=email, d=phone, e=address)
        employee_query = text(
            "INSERT INTO Employee (years_of_experience, salary, alma_mater, uni) VALUES (:a, :b, :c, :d)")
        employee_query = employee_query.bindparams(
            a=year_of_exp, b=salary, c=school, d=uni)
        instructor_query = text(
            "INSERT INTO Instructor (courses_taught, papers_published, uni, research_experience) VALUES (:a, :b, :c, :d)")
        instructor_query = instructor_query.bindparams(
            a=list(), b=list(), c=uni, d=research_exp)

        belongs_query = text(
            "INSERT INTO \"belongs to\" (dept_id, course_id, uni) VALUES (:a, :b, :c)")
        belongs_query = belongs_query.bindparams(a=dept_id, b='None', c=uni)
        g.conn.execute(p_query)
        g.conn.execute(employee_query)
        g.conn.execute(instructor_query)
        g.conn.execute(belongs_query)
        g.conn.commit()
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        exceptionRaised = True
    finally:
        if(exceptionRaised):
            time.sleep(2)
        return redirect('/admin_enroll')


@app.route('/employ_advisor', methods=['GET', 'POST'])
def employ_advisor():
    try:
        session['textbox'] = "admin"
        uni = session.pop('uni', None)
        name = session.pop('name', None)
        email = session.pop('email', None)
        phone = session.pop('phone', None)
        address = session.pop('address', None)
        exceptionRaised = False


        year_of_exp = request.form['textbox1']
        salary = int(request.form['textbox2'])
        school = request.form['textbox3']
        time_slot = request.form['textbox4']
        dept_id = request.form['textbox5']

        p_query = person_query.bindparams(
            a=uni, b=name, c=email, d=phone, e=address)
        employee_query = text(
            "INSERT INTO Employee (years_of_experience, salary, alma_mater, uni) VALUES (:a, :b, :c, :d)")
        employee_query = employee_query.bindparams(
            a=year_of_exp, b=salary, c=school, d=uni)
        advisor_query = text(
            "INSERT INTO Advisor (student_advisees, isavailable, daily_appointments, uni) VALUES (:a, :b, :c, :d)")
        advisor_query = advisor_query.bindparams(
            a=list(), b='True', c=[time_slot], d=uni)

        belongs_query = text(
            "INSERT INTO \"belongs to\" (dept_id, course_id, uni) VALUES (:a, :b, :c)")
        belongs_query = belongs_query.bindparams(a=dept_id, b='None', c=uni)
        g.conn.execute(p_query)
        g.conn.execute(employee_query)
        g.conn.execute(advisor_query)
        g.conn.execute(belongs_query)
        g.conn.commit()
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        exceptionRaised = True
    finally:
        if(exceptionRaised):
            time.sleep(2)
        return redirect('/admin_enroll')


@app.route('/admin_enroll_student', methods=['GET', 'POST'])
def admin_enroll_student():
    try:
        if(session.pop('textbox', None) == "admin"):
            session['textbox'] = "admin"
            return render_template('admin_enroll_student.html')
        context = dict(data="Invalid Credentials, Please Try Again!")
        return render_template("index.html", **context)
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")


@app.route('/admin_employ_advisor', methods=['GET', 'POST'])
def admin_employ_advisor():
    try:
        if(session.pop('textbox', None) == "admin"):
            session['textbox'] = "admin"
            return render_template('admin_employ_advisor.html')
        context = dict(data="Invalid Credentials, Please Try Again!")
        return render_template("index.html", **context)
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")


@app.route('/admin_employ_instructor', methods=['GET', 'POST'])
def admin_employ_instructor():
    try:
        if(session.pop('textbox', None) == "admin"):
            session['textbox'] = "admin"
            return render_template('admin_employ_instructor.html')
        context = dict(data="Invalid Credentials, Please Try Again!")
        return render_template("index.html", **context)
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        return render_template("index.html")



@app.route('/add_dept_to_db', methods=['GET', 'POST'])
def add_dept_to_db():
    try:
        session['textbox'] = "admin"
        exceptionRaised = False
        dept_id = request.form['textbox1']
        dept_title = request.form['textbox2']
        insert_query = text(
            "INSERT INTO Department (dept_id, department_title, courses_offered) VALUES (:a, :b, :c)")
        insert_query = insert_query.bindparams(a=dept_id, b=dept_title, c=list())
        g.conn.execute(insert_query)
        g.conn.commit()
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        exceptionRaised = True
    finally:
        if(exceptionRaised):
            time.sleep(2)
        return redirect('/admin_dept')


@app.route('/add_building_to_db', methods=['GET', 'POST'])
def add_building_to_db():
    try:
        session['textbox'] = "admin"
        exceptionRaised = False
        building_id = request.form['textbox1']
        address = request.form['textbox2']
        capacity = int(request.form['textbox3'])
        insert_query = text(
            "INSERT INTO Building (building_id, address, capacity) VALUES (:a, :b, :c)")
        insert_query = insert_query.bindparams(
            a=building_id, b=address, c=capacity)
        g.conn.execute(insert_query)
        g.conn.commit()
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        exceptionRaised = True
    finally:
        if(exceptionRaised):
            time.sleep(2)
        return redirect('/admin_construction')


@app.route('/add_course_to_db', methods=['GET', 'POST'])
def add_course_to_db():
    try:
        session['textbox'] = "admin"
        exceptionRaised = False
        course_id = request.form['textbox1']
        course_title = request.form['textbox2']
        course_capacity = int(request.form['textbox3'])
        course_dept = request.form['textbox4']
        course_time = request.form['textbox5']
        course_building = request.form['textbox6']
        insert_query = "INSERT INTO Course (course_id, course_title, time_slot, course_capacity) VALUES (:a, :b, :c, :d)"
        insert_query = text(insert_query).bindparams(
                a=course_id, b=course_title, c=course_time, d=course_capacity)
        g.conn.execute(insert_query)
        insert_query = text("INSERT INTO \"belongs to\" (dept_id, course_id, uni) VALUES (:a, :b, :c)").bindparams(
                a=course_dept, b=course_id, c='None')
        g.conn.execute(insert_query)
        insert_query = text("INSERT INTO \"located in\" (course_id, building_id) VALUES (:a, :b)").bindparams(
                a=course_id, b=course_building)
        g.conn.execute(insert_query)
        update_query = text("UPDATE Department d SET courses_offered = array_append(courses_offered, :a) WHERE d.dept_id = :b").bindparams(
                a=course_title, b=course_dept)
        g.conn.execute(update_query)
        g.conn.commit()
    except BaseException as e:
        print("Error has occurred, there is a potential error with the SQL query \nHere is more information:\n")
        print(str(e))
        exceptionRaised = True
    finally:
        if(exceptionRaised):
            time.sleep(2)
        return redirect('/admin_catalog')

if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()