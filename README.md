COMS W4111 - Introduction to Databases Semester Project
Team Members: Griffin Newbold (gcn2106) and Amanda Jenkins (alj2155)
Application Tested on the Following: Edge, Chrome, and FireFox.

Introduction
------------
This README is to go along with the Project Part 3 Submission on Gradescope. The README is divided into two parts, the first part is the part that is required for grading and is listed on the proj1-3.html file on CourseWorks. The second part will be a generic readme, describing how to interact with the Web Interface and stuff of that nature. 

Part 1
------
Web Interface Description in Connection to Part 1:

Recall the description from the first part of the project: 
“For part 3 of the project, we are choosing to implement a web front end. The purpose of this would be like a modified and more user-friendly version of Columbia’s SSOL, where students will be able to see courses they are currently enrolled in along with course grades for past courses, instructors will also be able to login to see the courses they are currently instructing and all other information of that nature. The system will be designed to differentiate between instructors and students by the identification strings that we assign in our database model with the strings having predesignated encodings to allow for such functionality. Students will be able to search through courses in order to see what is available to enroll in. Also, with student user IDs known, we could implement a search bar that will allow students to find trade-specific courses through a “suggestion” algorithm. Also, advisors will also be able to use this web application to see what students they currently have assigned to them. You can think of this web application as a modified version of SSOL, it will look cleaner (hopefully) but overall be more geared toward a technical/vocational college with the necessary educational components. “
From this description, we do allow students to see what courses they are currently taking, and course information from completed courses, and instructors can see what courses they are teaching. The system does differentiate between students, instructors and advisors using the encodings for their unis, s denotes student, i denotes instructor and a denotes advisor. The term “admin” is reserved for the admin of the system. We also implemented a basic suggestion algorithm which recommends courses from the student’s department that they are currently not taking or have taken in the past. Advisors are also able to see the unis of students they are currently advising.

Two most interesting Web Pages and their connections to the DB:
Definitely the two most interesting pages on the server are the student.html and the admin_enroll.html pages. 

For student, it is the most expansive in terms of items to select from the database as we have to select from the Person, Student, advised by, takes, and belongs to tables. It also has the potential to perform the most complex updates and inserts of the whole operation, all of which attempt to happen essentially simultaneously. Some values will be updated, others will be deleted, and more will be inserted etc. 

For admin_enroll (I am including its essential subsidiary pages, admin_enroll_student, admin_employ_advisor, admin_employ_instructor) it was complex as it had to insert into the most places and the decisions necessary in order to differentiate the kind of person the admin is adding and then redirect to the proper page to continue.

Part 2
------
This describes the actions able to be performed on each page, and what kind of input is expected whenever prompted:

index.html
----------
Actions:
Login:
You can enter either a valid uni, or “admin”, student unis begin with s, instructors i, and advisors a. Any incorrect attempt will result in redirecting to the same page with a proper message telling you it has received an invalid entry
Go to Directory: Click the blue hyperlink to go to this page

directory.html
--------------
Actions:
Go to Homepage: Click the blue hyperlink to go to this page
Search the Person Table: Empty searches result in the whole table being displayed, exact matches return exact matches and partial matches return any partial match

student.html
------------
Actions:
Go to Homepage: Click the proper hyperlink to log out
Go to Course Directory: Click the proper hyperlink to view the directory of courses 
Update Information: There are 4 text boxes properly labeled here is the kind of information each expects
Change Dept, if you intend to switch departments, you will need to enter the proper 4 character department code so COMS, APMA, EVEN etc. 
Add/Drop Course: To add or drop a course enter its course_id which is a 4 digit number, like 1004 or 3261, if you enter a number into the box that is listed under “taking” it will be dropped 
Transfer Course: Needs the word Yes or No if left blank defaults to No. Deletes all proper entries in taking and moves to courses completed, a proper entry is defined as one that has a grade assigned to it. 
How Many Credits Being Transferred?: expects a number, if a negative number is entered it will be treated as a positive. 
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user. 

course_directory.html
---------------------
Actions:
Go to Homepage: Click the proper hyperlink to log out 
Return to Dashboard: Click the proper hyperlink to return to the dashboard of the student you were just viewing.
Search, empty string returns no entries, searching a department returns all courses in the department for course ids exact matches are expected, for titles the match can be both partial and exact.

instructor.html
---------------
Actions:
Go to Homepage: Click the proper hyperlink to log out
Submit Grades: Brings you to a page to enter grades for students in your courses. 
Update Information: There are 4 text boxes properly labeled here is the kind of information each expects
Change Dept, if you intend to switch departments, you will need to enter the proper 4 character department code so COMS, APMA, EVEN etc. 
Teach a Course: To teach a course enter its course_id which is a 4 digit number, like 1004 or 3261, once you begin teaching a course you cannot remove it unless through the transfer courses
Transfer Course: Needs the word Yes or No if left blank defaults to No. Deletes all entries in teaching and moves to courses taught, duplicates will not be allowed in courses taught 
New Paper Written: Adds the entry to papers written, if blank, no paper is added.
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user.

submit_grades.html
------------------
Actions:
Return to Dashboard: Click the proper hyperlink to return to the dashboard of the instructor you were just viewing.
Allows instructors to enter and submit grades for students in the courses the instructors teach, if multiple instructors teach the same course, they will both be able to alter grades of any student. Students will receive a grade after instructors click submit, the student will be removed from the roster only after they transferred the course. Until then instructors have the ability to change grades of students. 
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user.

advisor.html
------------
Actions:
Go to homepage: Logs out and returns to homepage
Update Information:
Change Dept, if you intend to switch departments, you will need to enter the proper 4 character department code so COMS, APMA, EVEN etc.  
Add/Remove Time Slots: Expects entries of the form (x)x:xx-(x)x:xx so examples would be 11:40-12:55 or 1:10-1:25 if you enter a timeslot you already have it will be removed
Switch Availability: Expects “Yes” or “No” default if left blank is “No” if you switch availability and then switch back, your original time slots remain in tacts.
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user.

admin.html
----------
Actions:
View/Enroll/Employ People: Takes admin to page to view all information about people and then has the ability to add more people
View/Add to Course Catalog: Takes admin to page to view all information about courses and then has the ability to add more courses
View/Add Available Departments: Takes admin to page to view all information about departments and then has the ability to add more departments
View/Add Buildings: Takes admin to page to view all information about buildings and then has the ability to add more buildings








admin_enroll.html
-----------------
Actions:
 Log Out: Logs out and returns to homepage
 Return to Dashboard: Returns to admin.html
 Add a Person!
uni: a string beginning with s,i,or a 
name: a string representing a name  
email: in the form uni@columbia.edu (nothing prevents other entries though since email is really display only) 
Phone number: String in the form XXX-XXX-XXXX 
Campus Address: A String for the Address
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user.

admin_enroll_student
--------------------
Actions:
Log Out: Logs out and returns to homepage
Return to Dashboard: Returns to admin.html
Add a Student
Expected Graduation year: integer representing year, if a negative is entered the positive is added  
Uni for Advisor: uni for advisor, database constraint check should handle issues with advisor uni
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user.

admin_employ_instructor
-----------------------
Actions:
Log Out: Logs out and returns to homepage
Return to Dashboard: Returns to admin.html
Add an Instructor 
Years of experience: numeric string 	
Salary: numeric string
Alma Mater: String representing college
Research Experience: String representing research
Department Code: 4 letter String ideally in all capitals eg COMS 
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user.




admin_employ_advisor
--------------------
Actions:
Log Out: Logs out and returns to homepage
Return to Dashboard: Returns to admin.html
Add an Instructor 
Years of experience: numeric string 	
Salary: numeric string
Alma Mater: String representing college
Time Slot for Appointments: A single time slot entry in the form (x)x:xx-(x)x:xx
Department Code: 4 letter String ideally in all capitals eg COMS  
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user.








admin_construction.html
-----------------------
Actions:
 Log Out: Logs out and returns to homepage
 Return to Dashboard: Returns to admin.html
 Add Building:
Building ID: a 3 character String usually in all capitals 
Address: A String containing an address 
Capacity: A String representation of a number
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user.



admin_dept.html
---------------
Actions:
 Log Out: Logs out and returns to homepage
 Return to Dashboard: Returns to admin.html
 Add Department:
Department Code: 4 letter String ideally in all capitals eg COMS 
Department Title: A String representing the full name of the department
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user.

admin_catalog.html
------------------
Actions:
Log Out: Logs out and returns to homepage
Return to Dashboard: Returns to admin.html 
Add a Course 
Course ID: a 4 digit number 
Course Title: A String for the Title of the Course 	
Course Capacity: A numeric value 
Course Department ID: 4 character String eg COMS 
Time Slot: String in the form (x)x:xx-(x)x:xx
Building Code: A 3 character String connecting to a Building eg LER or MUD
All of this potential updating is surrounded by a try except block, if an error occurs, there will be a 2 second delay prior to the page updating and an error message is displayed to the terminal but not to the user.


Random gibberish in directory
Can’t add time to Advisor
