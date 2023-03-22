
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'databaseproject'

DATABASE_USERNAME = "gcn2106"
DATABASE_PASSWRD = "3276"
DATABASE_HOST = "34.148.107.47" # change to 34.28.53.86 if you used database 2 for part 2
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/project1"

engine = create_engine(DATABASEURI)
with engine.connect() as conn:
	pass


@app.before_request
def before_request():
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	try:
		g.conn.close()
	except Exception as e:
		pass



@app.route('/')
@app.route('/homepage')
def index():

	# DEBUG: this is debugging code to see what request looks like
	print(request.args)
	session.pop('textbox', None)
	return render_template("index.html")

@app.route('/student', methods=['POST', 'GET'])
def student():
	uni = session.pop('textbox', None)
	query = text("SELECT * From Person p JOIN Student s on p.uni = s.uni JOIN takes on p.uni=takes.uni JOIN \"advised by\" a on p.uni = a.uni_s JOIN \"belongs to\" b on p.uni = b.uni Where p.uni = :user_uni")
	query = query.bindparams(user_uni=uni)
	cursor = g.conn.execute(query)
	names = []
	for result in cursor:
		if(result[0] != 'None'):
			names.append(dict(uni=result[0], name = result[1], 
		     email=result[2], phone=result[3], addr=result[4],
			 credits_att=result[5], credits_ern=result[6], 
			 grad_date = result[7], courses_taken=result[8],
			 advisor=result[14], department = result[15]))
	
	cursor.close()
	context = dict(data = names)
	session['textbox'] = uni
	return render_template("student.html", **context)

@app.route('/advisor', methods=['POST', 'GET'])
def advisor():
	uni = session.pop('textbox', None)
	query = text("SELECT * From Person p, Employee e, Advisor a, \"belongs to\" b Where p.uni = :user_uni and e.uni = :user_uni and a.uni = :user_uni and b.uni = :user_uni").bindparams(user_uni=uni)
	cursor = g.conn.execute(query)
	names = []
	for result in cursor:
		if(result[0] != 'None'):
			names.append(dict(uni=result[0], name = result[1], email = result[2],
		     phone=result[3], addr=result[4], years_of_exp=result[5],
			 salary=result[6], alma_mater=result[7], student_advisees=result[9],
			 isAvailable = result[10], time_slots = result[11], dept_code = result[13]))
	cursor.close()
	context = dict(data = names)
	session['textbox'] = uni
	return render_template("advisor.html", **context)


@app.route('/instructor', methods=['POST', 'GET'])
def instructor():
	uni = session.pop('textbox', None)
	query = text("SELECT * From Person p, Employee e, Instructor i, \"belongs to\" b Where p.uni = :user_uni and e.uni = :user_uni and i.uni = :user_uni and b.uni = :user_uni").bindparams(user_uni=uni)
	cursor = g.conn.execute(query)
	names = []
	for result in cursor:
		if(result[0] != 'None'):
			names.append(dict(uni=result[0], name = result[1], email = result[2],
		     phone=result[3], addr=result[4], years_of_exp=result[5],
			 salary=result[6], alma_mater=result[7], courses_taught=result[9],
			 papers_written = result[10], research_exp = result[12], dept_code = result[13]))
	cursor.close()
	context = dict(data = names)
	session['textbox'] = uni
	return render_template("instructor.html", **context)

@app.route('/directory', methods=['POST', 'GET'])
def directory():
	return render_template("directory.html")


@app.route('/course_directory', methods=['POST', 'GET'])
def course_directory():
	return render_template("course_directory.html")

@app.route('/search_course_db', methods=['POST'])
def search_course_db():
	search_term = request.form['term']
	search_condition= '%'+search_term+'%'
	query = "SELECT * FROM \"belongs to\" b JOIN Department d on b.dept_id = d.dept_id JOIN Course c on c.course_id = b.course_id, \"located in\" l WHERE l.course_id = " + \
	"c.course_id and (((d.courses_offered::text ILIKE :term_a and c.course_title ILIKE :term_a) or c.course_id = :term_b) or d.dept_id ILIKE :term_a)"
	query = text(query).bindparams(term_a=search_condition,term_b=search_term)
	cursor = g.conn.execute(query)

	if(len(search_term) != 0):
		names = []
		for result in cursor:
			if(result[6] != 'None'):
				names.append(dict(course_name = result[7], dept_id = result[0], course_code = result[6], time_slot=result[8], building_code=result[11], 
				building_capacity=result[9], dept_name = result[4]))
		cursor.close()
		if(len(names) != 0):
			context = dict(data = names)
			return render_template("course_directory.html", **context)
		result = [dict(err_msg = "There is no entry in our records relating to your search term, please check your search then try again")]
		context = dict(data = result)
		return render_template("course_directory.html", **context)
	else:
		result = [dict(err_msg = "There is no entry in our records relating to your search term, please check your search then try again")]
		context = dict(data = result)
		return render_template("course_directory.html", **context)

@app.route('/search_db', methods=['POST'])
def search_db():
	#gets entry and forms SQL query
	name = request.form['name']
	query = text("SELECT * FROM Person p where p.name ILIKE :search_term or p.uni ILIKE :search_term")
	search_condition= '%'+name+'%'
	query = query.bindparams(search_term=search_condition)

	#executes the query and parses the results
	cursor = g.conn.execute(query)
	names = []
	for result in cursor:
		if(result[0] != 'None'):
			names.append(result)
	cursor.close()

	#updates the page contents then refreshes
	if(len(names) != 0):
		context = dict(data = names)
	else:
		result = ["There is no entry in our records relating to your search term, please check your search then try again"]
		context = dict(data = result)
	return render_template("directory.html", **context)


# Example of adding new data to the database
@app.route('/login', methods=['POST'])
def login():
	# accessing form inputs from user
	name = request.form['name']
	session['textbox'] = name
	params = {}
	params["new_name"] = name
	names = params["new_name"]

	#error checking for empty login field
	if(len(names) == 0):
		return redirect('/')
	
	#sql query to see if we have a valid user
	select_query = "SELECT uni FROM Person"
	cursor = g.conn.execute(text(select_query))
	res = []
	for result in cursor:
		res.append(result[0])
	cursor.close()

	if(names not in res and names != "admin"):
		context = dict(data = "Invalid UNI, Please Try Again!")
		return render_template("index.html", **context)
	
	if(names == 'admin'):
		return redirect('/admin')
	elif(names[0] == 'a'):
		return redirect('/advisor')
	elif(names[0] == 's'):
		return redirect('/student')
	elif(names[0] == 'i'):
		return redirect('/instructor')
	return redirect('/')

'''
All functionality relating to the Admin
'''
@app.route('/admin', methods=['POST', 'GET'])
def admin():
	return render_template("admin.html")

@app.route('/admin_enroll', methods=['POST', 'GET'])
def admin_enroll():
	select_query = "SELECT * FROM Person"
	cursor = g.conn.execute(text(select_query))
	res = []
	for result in cursor:
		if(result[0] != 'None'):
			res.append(dict(uni=result[0], name=result[1], email=result[2], phone = result[3], address = result[4]))
	cursor.close()
	context = dict(data = res)
	return render_template("admin_enroll.html", **context)

@app.route('/admin_catalog', methods=['POST', 'GET'])
def admin_catalog():
	select_query = "SELECT * FROM Course"
	cursor = g.conn.execute(text(select_query))
	res = []
	for result in cursor:
		if(result[0] != 'None'):
			res.append(dict(course_id = result[0], course_title = result[1], time = result[2], size = result[3]))
	cursor.close()
	context = dict(data = res)
	return render_template("admin_catalog.html", **context)

@app.route('/admin_dept', methods=['POST', 'GET'])
def admin_dept():
	select_query = text("SELECT * FROM Department")
	cursor = g.conn.execute(select_query)
	res = []
	for result in cursor:
		res.append(dict(dept_id=result[0], dept_title = result[1], courses=result[2]))
	cursor.close()
	context = dict(data = res)
	return render_template("admin_dept.html", **context)

@app.route('/admin_construction', methods=['POST', 'GET'])
def admin_construction():
	select_query = text("SELECT * FROM Building")
	cursor = g.conn.execute(select_query)
	res = []
	for result in cursor:
		res.append(dict(building_id=result[0], addr = result[1], cap=result[2]))
	cursor.close()
	context = dict(data = res)
	return render_template("admin_construction.html", **context)

@app.route('/begin_addition_process', methods=['GET', 'POST'])
def begin_addition_process():
	uni = request.form['textbox1'] 
	name = request.form['textbox2'] 
	email = request.form['textbox3']
	phone = request.form['textbox4']
	address = request.form['textbox5']
	insert_query = text("INSERT INTO Person (uni, name, email, phone_number, address) VALUEs (:a, :b, :c, :d, :e)")
	insert_query = insert_query.bindparams(a=uni, b=name, c=email, d=phone, e=address)
	if(uni[0] == 's'):
		return redirect('/admin_enroll_student')
	elif(uni[0] == 'a'):
		return redirect('/admin_employ_advisor')
	elif(uni[0] == 'i'):
		return redirect('/admin_enroll_instructor')
	else:
		return redirect('/admin_enroll')

@app.route('/admin_enroll_student', methods=['GET','POST'])
def admin_enroll_student():
	return render_template('admin_enroll_student.html')

@app.route('/admin_employ_advisor', methods=['GET','POST'])
def admin_employ_advisor():
	return render_template('admin_employ_advisor.html')

@app.route('/admin_employ_instructor', methods=['GET','POST'])
def admin_employ_instructor():
	return render_template('admin_employ_instructor.html')





@app.route('/add_dept_to_db', methods=['GET', 'POST'])
def add_dept_to_db():
	dept_id = request.form['textbox1']
	dept_title = request.form['textbox2']
	insert_query = text("INSERT INTO Department (dept_id, department_title, courses_offered) VALUES (:a, :b, :c)")
	insert_query = insert_query.bindparams(a=dept_id,b=dept_title,c=list())
	g.conn.execute(insert_query)
	g.conn.commit()
	return redirect('/admin_dept')

@app.route('/add_building_to_db', methods=['GET', 'POST'])
def add_building_to_db():
	building_id = request.form['textbox1']
	address = request.form['textbox2']
	capacity = int(request.form['textbox3'])
	insert_query = text("INSERT INTO Building (building_id, address, capacity) VALUES (:a, :b, :c)")
	insert_query = insert_query.bindparams(a=building_id,b=address,c=capacity)
	g.conn.execute(insert_query)
	g.conn.commit()
	return redirect('/admin_construction')

@app.route('/add_course_to_db', methods=['GET', 'POST'])
def add_course_to_db():
	course_id = request.form['textbox1'] 
	course_title = request.form['textbox2'] 
	course_capacity = int(request.form['textbox3'])
	course_dept = request.form['textbox4']
	course_time = request.form['textbox5']
	course_building = request.form['textbox6']
	insert_query = "INSERT INTO Course (course_id, course_title, time_slot, course_capacity) VALUES (:a, :b, :c, :d)"
	insert_query = text(insert_query).bindparams(a = course_id, b = course_title, c=course_time, d = course_capacity)
	g.conn.execute(insert_query)
	g.conn.commit()
	insert_query = text("INSERT INTO \"belongs to\" (dept_id, course_id, uni) VALUES (:a, :b, :c)").bindparams(a = course_dept, b =course_id, c = 'None')
	g.conn.execute(insert_query)
	g.conn.commit()
	insert_query = text("INSERT INTO \"located in\" (course_id, building_id) VALUES (:a, :b)").bindparams(a = course_id, b = course_building)
	g.conn.execute(insert_query)
	g.conn.commit()
	update_query = text("UPDATE Department d SET courses_offered = array_append(courses_offered, :a) WHERE d.dept_id = :b").bindparams(a=course_title,b=course_dept)
	g.conn.execute(update_query)
	g.conn.commit()
	return redirect('/admin_catalog')

def delete_course():
	delete_query = text("DELETE FROM \"located in\" Where course_id = \'2402\'")
	g.conn.execute(delete_query)
	g.conn.commit()
	delete_query = text("DELETE FROM \"belongs to\" Where course_id = \'2402\'")
	g.conn.execute(delete_query)
	g.conn.commit()
	delete_query = text("DELETE FROM Course Where course_id = \'2402\'")
	g.conn.execute(delete_query)
	g.conn.commit()



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

