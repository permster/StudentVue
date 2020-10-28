from studentvue import helpers


class Student:

    def __init__(self, studentvue, firstname=None, childintid=None):
        self.permid = self.schoolname = self.image = self.agu = None
        self.studentdict = self.firstname = self.fullname = None
        self.schedule = self.grades = self.assignments = self._sv = None
        self.schooldistrict = None

        if not firstname and not childintid:
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
        return helpers.base64ToFile(self._sv_student['photo']['$'], f'{filename}.png')

    def set_student_schedule(self):
        schedule = self._sv.get_schedule()['StudentClassSchedule']
        courses = []
        for course in schedule['ClassLists']['ClassListing']:
            courses.append([
                course['@Period'],
                course['@CourseTitle'],
                course['@RoomName'],
                course['@Teacher'],
                course['@TeacherEmail']
            ])
        self.schedule = courses

    def set_student_grades(self):
        grades = self._sv.get_gradebook()['Gradebook']['Courses']['Course']
        grades_temp = []
        for grade in grades:
            grades_temp.append([
                grade['@Period'],
                grade['@Title'],
                grade['@Room'],
                grade['@Staff'],
                grade['@StaffEMail'],
                grade['Marks']['Mark']['@CalculatedScoreString'],
                grade['Marks']['Mark']['@CalculatedScoreRaw']
            ])
        self.grades = grades_temp

    def set_student_assignments(self):
        grades = self._sv.get_gradebook()['Gradebook']['Courses']['Course']
        assignments_temp = []
        for grade in grades:
            assignment_temp = []
            for assignment in grade['Marks']['Mark']['Assignments']['Assignment']:
                assignment_temp.append([
                    assignment['@Date'],
                    assignment['@DueDate'],
                    assignment['@Measure'],
                    assignment['@Type'],
                    assignment['@Score'],
                    assignment['@ScoreType'],
                    assignment['@Points'],
                    assignment['@Notes'],
                    assignment['@HasDropBox'],
                    assignment['@DropStartDate'],
                    assignment['@DropEndDate']
                ])
            assignments_temp.append([
                grade['@Period'],
                grade['@Title'],
                assignment_temp
            ])
        self.assignments = assignments_temp

    def get_missing_assignments(self, classname: str = None, period: int = None,
                                time: str = None
                                ):
        missing_assignments = []
        for assignments in self.assignments:
            # classname param found but class name is not a match
            if classname is not None and assignments[1] != classname:
                continue

            # period param found but period is not a match
            if period is not None and assignments[0] != period:
                continue

            missing_assignment = []
            for assignment in assignments[2]:
                if assignment[6].startswith('0.00') or 'missing' in assignment[7].lower():
                    if time:
                        # do time comparison here
                        if helpers.convert_string_to_date(assignment[2]) >= \
                                helpers.now_timedelta_to_date(time):  # need to confirm index of 2 for date
                            missing_assignment.append(assignment)
                    else:
                        missing_assignment.append(assignment)
            missing_assignments.append([
                assignments[0],
                assignments[1],
                missing_assignment
            ])

        return missing_assignments
