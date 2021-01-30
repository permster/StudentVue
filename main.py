import local_settings
from studentvue import StudentVue
from studentvue import Student

# Connect to StudentVUE/ParentVUE
sv = StudentVue(local_settings.username, local_settings.password, local_settings.domain, parent=True)

# List students
students = sv.get_student_list()['ChildList']['Child']

for stu in students:
    student = Student.Student(studentvue=sv, childintid=stu['@AccessGU'])
    # student.get_missing_assignments(time='7d', notify=True)  # Specific time period
    student.get_missing_assignments(notify=True)

# New student instance (by first name instead of id)
# student = Student.Student(studentvue=sv, firstname="Jonathan")

# Get missing assignments
# missing_all = student.get_missing_assignments()  # All
# missing_by_class = student.get_missing_assignments(classname='Photo I (15400)')  # Specific class
# missing_by_period = student.get_missing_assignments(period=1)  # Specific period
# missing_last_week = student.get_missing_assignments(time='7d', notify=True)  # Specific time period
