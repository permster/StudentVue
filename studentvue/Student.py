from studentvue import helpers


class Student:

    def __init__(self, studentvue, firstname=None, childintid=None):
        self.permid = self.schoolname = self.image = self.agu = None
        self.studentdict = self.firstname = self.fullname = None
        self.schedule = self.grades = self.assignments = self._sv = None
        self.schooldistrict = self.assignments_missing = None

        if firstname is None and childintid is None:
            raise ValueError("No firstname or childintid parameter was specified.")

        # StudentVue instance
        self._sv = studentvue

        # Get StudentVue student
        if firstname:
            self._sv_student = self.get_student_by_firstname(firstname)
        else:
            self._sv_student = self.get_student_by_id(childintid)

        self.permid = self.get_permid()
        self.agu = self.get_agu()
        self.firstname = self.get_firstname()
        self.fullname = self.get_fullname()
        self.image = self.get_student_image(self.firstname)
        self.schoolname = self.get_schoolname()
        self.schooldistrict = self.get_schooldistrict()

        # Set child id for later calls to StudentVue
        self._sv.switch_student(self.agu)

        # Set class schedule
        self.set_student_schedule()

        # Set grades/assignments
        self.set_student_grades()
        self.set_student_assignments()
        self.set_missing_assignments()

    def get_student_by_firstname(self, firstname):
        studentlist = self._sv.get_student_list()['ChildList']['Child']
        for student in studentlist:
            for key, value in student.items():
                if key == '@ChildFirstName' and value == firstname:
                    return student

    def get_student_by_id(self, childid):
        studentlist = self._sv.get_student_list()['ChildList']['Child']
        for student in studentlist:
            for key, value in student.items():
                if key == '@AccessGU' and value == childid:
                    return student

    def get_schooldistrict(self):
        return self._sv.get_student_list()['ChildList']['@DistrictName']

    def get_permid(self):
        return self._sv_student['@ChildPermID']

    def get_agu(self):
        return self._sv_student['@AccessGU']

    def get_firstname(self):
        return self._sv_student['@ChildFirstName']

    def get_fullname(self):
        return self._sv_student['ChildName']['$']

    def get_schoolname(self):
        return self._sv_student['OrganizationName']['$']

    def get_student_image(self, filename):
        return helpers.base64tofile(self._sv_student['photo']['$'], f'{filename}.png')

    def set_student_schedule(self):
        schedule = self._sv.get_schedule()['StudentClassSchedule']
        courses = []
        for course in schedule['ClassLists']['ClassListing']:
            course_temp = {'Period': course['@Period'], 'Classname': course['@CourseTitle'],
                           'RoomName': course['@RoomName'], 'Teacher': course['@Teacher'],
                           'TeacherEmail': course['@TeacherEmail']}
            courses.append(course_temp)
        self.schedule = courses

    def set_student_grades(self):
        grades = self._sv.get_gradebook()['Gradebook']['Courses']['Course']
        grades_temp = []
        for grade in grades:
            grade_temp = {'Period': grade['@Period'], 'Classname': grade['@Title'],
                          'Grade': grade['Marks']['Mark'][0]['@CalculatedScoreString'],
                          'Score': grade['Marks']['Mark'][0]['@CalculatedScoreRaw']}
            grades_temp.append(grade_temp)
        self.grades = grades_temp

    def set_student_assignments(self):
        grades = self._sv.get_gradebook()['Gradebook']['Courses']['Course']
        assignments_temp = []
        for grade in grades:
            grade_temp = {'Period': grade['@Period'], 'Classname': grade['@Title'],
                          'Assignments': []}

            for assignment in grade['Marks']['Mark'][0]['Assignments']['Assignment']:
                assignment_temp = {'Date': assignment['@Date'], 'DueDate': assignment['@DueDate'],
                                   'Measure': assignment['@Measure'], 'Type': assignment['@Type'],
                                   'Score': assignment['@Score'], 'ScoreType': assignment['@ScoreType'],
                                   'Points': assignment['@Points'], 'Notes': assignment['@Notes'],
                                   'HasDropBox': assignment['@HasDropBox'],
                                   'DropStartDate': assignment['@DropStartDate'],
                                   'DropEndDate': assignment['@DropEndDate']}

                grade_temp['Assignments'].append(assignment_temp)
            assignments_temp.append(grade_temp)
        self.assignments = assignments_temp

    def set_missing_assignments(self):
        missing_assignments = []
        for course in self.assignments:
            missing_assignment = []
            for assignment in course['Assignments']:
                if assignment['Points'].startswith('0.00') and \
                        not assignment['Points'].endswith('/ 0.0000') and \
                        assignment['Score'] != "Not Graded":
                    missing_assignment.append(assignment)

            if len(missing_assignment) > 0:
                missing_assignments.append({
                    'Period': course['Period'],
                    'Classname': course['Classname'],
                    'Assignments': missing_assignment
                })

        self.assignments_missing = missing_assignments

    def get_missing_assignments(self, classname: str = None, period: int = None,
                                time: str = None, notify: bool = False):
        missing_assignments = []
        missing_count = 0
        for course in self.assignments_missing:
            # classname param found but class name is not a match
            if classname is not None and course['Classname'] != classname:
                continue

            # period param found but period is not a match
            if period is not None and course['Period'] != period:
                continue

            missing_assignment = []
            for assignment in course['Assignments']:
                if time:
                    # do time comparison here
                    if helpers.convert_string_to_date(assignment['Date']) >= \
                            helpers.now_timedelta_to_date(time):
                        missing_assignment.append(assignment)
                        missing_count += 1
                else:
                    missing_assignment.append(assignment)

            if len(missing_assignment) > 0:
                missing_assignments.append({
                    'Period': course['Period'],
                    'Classname': course['Classname'],
                    'Assignments': missing_assignment
                })

        if notify and len(missing_assignments) > 0:
            body = helpers.convert_assignments_to_html(missing_assignments)
            helpers.send_notifications(f"{self.get_firstname()} has {missing_count}"
                                       f" missing assignment(s)", body)
        return missing_assignments
