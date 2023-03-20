
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
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'databaseproject'


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "gcn2106"
DATABASE_PASSWRD = "3276"
DATABASE_HOST = "34.148.107.47" # change to 34.28.53.86 if you used database 2 for part 2
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/project1"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
with engine.connect() as conn:
	create_table_command = """
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	"""
	res = conn.execute(text(create_table_command))
	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	conn.commit()


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


@app.route('/')
@app.route('/homepage')
def index():
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

@app.route('/admin', methods=['POST', 'GET'])
def admin():
	return render_template("admin.html")


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
    return render_template("instructor.html", **context)


@app.route('/directory', methods=['POST', 'GET'])
def directory():
	return render_template("directory.html")

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
	

if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
	    """
	    This function handles command line parameters.
	    Run the server using:

		    python server.py

	    Show the help text using:

		    python server.py --help

	    """
	    HOST, PORT = host, port
	    print("running on %s:%d" % (HOST, PORT))
	    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()

