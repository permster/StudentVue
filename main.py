import local_settings
from studentvue import StudentVue
from studentvue import Student


# Connect to StudentVUE/ParentVUE
sv = StudentVue(local_settings.username, local_settings.password, local_settings.domain, parent=True)

# New student instance (by first name)
student = Student.Student(studentvue=sv, firstname="Jonathan")

# Set class schedule on student instance
student.set_student_schedule()

# Set grades/assignments on student instance
student.set_student_grades()
student.set_student_assignments()

# Get missing assignments
missing_all = student.get_missing_assignments()  # All
missing_by_class = student.get_missing_assignments(classname='Photo I (15400)')  # Specific class
missing_by_period = student.get_missing_assignments(period=1)  # Specific period
