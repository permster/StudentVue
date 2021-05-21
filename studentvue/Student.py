from studentvue import helpers
from datetime import datetime


date_format = "%m/%d/%Y"

def assignments_to_dictionary(dic):
    return {'Date': dic['@Date'], 'DueDate': dic['@DueDate'],
            'Measure': dic['@Measure'], 'Type': dic['@Type'],
            'Score': dic['@Score'], 'ScoreType': dic['@ScoreType'],
            'Points': dic['@Points'], 'Notes': dic['@Notes'],
            'HasDropBox': dic['@HasDropBox'],
            'DropStartDate': dic['@DropStartDate'],
            'DropEndDate': dic['@DropEndDate']}


def parse_assignments(grades, term):
    gradebook = grades['Gradebook']['Courses']['Course']
    assignments_temp = []
    for grade in gradebook:
        grade_temp = {'Period': grade['@Period'], 'Classname': grade['@Title'], 'Assignments': []}

        marks = grade['Marks']['Mark']
        if isinstance(marks, dict):
            # Progress report
            if len(marks['Assignments']) > 0:
                assignments = marks['Assignments']['Assignment']
                if isinstance(assignments, dict):  # Workaround for xmltojson conversion issue (single element)
                    grade_temp['Assignments'].append(assignments_to_dictionary(assignments))
                else:
                    for assignment in assignments:
                        grade_temp['Assignments'].append(assignments_to_dictionary(assignment))
        else:
            # Term
            for mark in marks:
                if mark['@MarkName'] == term and len(mark['Assignments']) > 0:
                    assignments = mark['Assignments']['Assignment']
                    if isinstance(assignments, dict):  # Workaround for xmltojson conversion issue (single element)
                        grade_temp['Assignments'].append(assignments_to_dictionary(assignments))
                    else:
                        for assignment in assignments:
                            grade_temp['Assignments'].append(assignments_to_dictionary(assignment))
        assignments_temp.append(grade_temp)
    return assignments_temp


def grades_to_list(grades, term):
    gradebook = grades['Gradebook']['Courses']['Course']
    grades_temp = []
    for grade in gradebook:
        marks = grade['Marks']['Mark']
        if isinstance(marks, dict):
            # Progress report
            grades_temp.append({'Period': grade['@Period'], 'Classname': grade['@Title'],
                                'Grade': marks['@CalculatedScoreString'],
                                'Score': marks['@CalculatedScoreRaw']})
        else:
            # Term
            for mark in marks:
                if mark['@MarkName'] == term:
                    grades_temp.append({'Period': grade['@Period'], 'Classname': grade['@Title'],
                                        'Grade': mark['@CalculatedScoreString'],
                                        'Score': mark['@CalculatedScoreRaw']})
                    break
    return grades_temp


class Student:

    def __init__(self, studentvue, firstname=None, childintid=None, termindex=None, reportperiod=None):
        self.permid = self.schoolname = self.image = self.agu = None
        self.studentdict = self.firstname = self.fullname = None
        self.schedule = self.grades = self.assignments = self._sv = None
        self.schooldistrict = self.assignments_missing = None
        self.gradeterm = self.gradetermname = None
        self.reportingperiodname = None
        self.schoolbegin = self.schoolend = self.isschoolyear = None
        self.gradetermindex = termindex
        self.reportingperiodindex = reportperiod

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

        # Set school year dates
        self.schoolbegin, self.schoolend = self.get_schoolyear()
        if self.schoolbegin <= datetime.today().date() <= self.schoolend:
            self.isschoolyear = True
        else:
            self.isschoolyear = False

        # Set grade term
        self.set_gradeterm(term_index=self.gradetermindex)

        # Set class schedule
        self.set_student_schedule(term_index=self.gradetermindex)

        # Set reporting period
        self.set_reportingperiod(reportperiod_index=self.reportingperiodindex)

        # Set grades/assignments
        self.set_student_grades(reportperiod_index=self.reportingperiodindex)
        self.set_student_assignments(reportperiod_index=self.reportingperiodindex)
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

    def set_gradeterm(self, term_index: int = None):
        schedule = self._sv.get_schedule()['StudentClassSchedule']
        if not term_index:
            term_index = schedule['@TermIndex']
        for term in schedule['TermLists']['TermListing']:
            if term['@TermIndex'] == term_index:
                self.gradetermindex = term['@TermIndex']
                self.gradeterm = term['@TermCode']
                self.gradetermname = term['@TermName']
                return

    def get_schoolyear(self):
        return datetime.strptime(self._sv.get_calendar()['CalendarListing']['@SchoolBegDate'], date_format).date(), \
               datetime.strptime(self._sv.get_calendar()['CalendarListing']['@SchoolEndDate'], date_format).date()

    def set_student_schedule(self, term_index: int = None):
        schedule = self._sv.get_schedule(term_index)['StudentClassSchedule']
        courses = []
        for course in schedule['ClassLists']['ClassListing']:
            course_temp = {'Period': course['@Period'], 'Classname': course['@CourseTitle'],
                           'RoomName': course['@RoomName'], 'Teacher': course['@Teacher'],
                           'TeacherEmail': course['@TeacherEmail']}
            courses.append(course_temp)
        self.schedule = courses

    def set_reportingperiod(self, reportperiod_index: int = None, reportperiod_name: str = None):
        reporting_periods = self._sv.get_gradebook(reportperiod_index)['Gradebook']
        if not reportperiod_name:
            reportperiod_name = reporting_periods['ReportingPeriod']['@GradePeriod']
        for period in reporting_periods['ReportingPeriods']['ReportPeriod']:
            if period['@Index'] == reportperiod_index:
                self.reportingperiodindex = period['@Index']
                self.reportingperiodname = period['@GradePeriod']
                return
            elif period['@GradePeriod'] == reportperiod_name:
                self.reportingperiodindex = period['@Index']
                self.reportingperiodname = period['@GradePeriod']
                return

    def set_student_grades(self, reportperiod_index: int = None, all_periods: bool = False):
        #   If you specify a term report_period (1, 3, 5, 7) then grades can be found here:
        #       grades['Gradebook']['Courses']['Course'][0]['Marks']['Mark'][0]['Assignments']['Assignment']
        #   If you specify a progress report report_period (0, 2, 4, 6) then grades can be found here:
        #       grades['Gradebook']['Courses']['Course'][0]['Marks']['Mark']['Assignments']['Assignment']
        #   If you don't specify a report_period (None) the period is set to the current term:
        #       grades['Gradebook']['Courses']['Course'][0]['Marks']['Mark'][0]['Assignments']['Assignment']
        #   If you specify a report_period of term 4 (7) the period is set to term 4 but it only shows the current
        #   terms grades.  So if it's only term 2 currently it will say term 4 but will show the grades for term 2.
        if all_periods:
            grades = self._sv.get_gradebook(report_period=3)
            term2_grades = grades_to_list(grades, term=self.gradetermname)

            grades = self._sv.get_gradebook(report_period=7)
            term4_grades = grades_to_list(grades, term=self.gradetermname)
            self.grades = term2_grades + term4_grades
        else:
            grades = self._sv.get_gradebook(reportperiod_index)
            self.grades = grades_to_list(grades, term=self.gradetermname)

    def set_student_assignments(self, reportperiod_index: int = None, all_periods: bool = False):
        if all_periods:
            grades = self._sv.get_gradebook(report_period=3)
            self.assignmentterm = grades['Gradebook']['ReportingPeriod']['@GradePeriod']
            term2_grades = parse_assignments(grades, term=self.assignmentterm)

            grades = self._sv.get_gradebook(report_period=7)
            self.assignmentterm = grades['Gradebook']['ReportingPeriod']['@GradePeriod']
            term4_grades = parse_assignments(grades, term=self.assignmentterm)
            self.assignments = term2_grades + term4_grades
        else:
            grades = self._sv.get_gradebook(reportperiod_index)
            self.assignmentterm = grades['Gradebook']['ReportingPeriod']['@GradePeriod']
            self.assignments = parse_assignments(grades, term=self.assignmentterm)

    def set_missing_assignments(self):
        missing_assignments = []
        for course in self.assignments:
            missing_assignment = []
            for assignment in course['Assignments']:
                if assignment['Points'].startswith('0.00') and \
                        not assignment['Points'].endswith('/ 0.0000') and \
                        assignment['Score'] != "Not Graded" and assignment['Score'] != "Not Due":
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
                    assignment_date = helpers.convert_string_to_date(assignment['Date'])
                    date_cutoff = helpers.now_timedelta_to_date(time)
                    if assignment_date >= date_cutoff:
                        missing_assignment.append(assignment)
                        missing_count += 1
                else:
                    missing_assignment.append(assignment)
                    missing_count += 1

            if len(missing_assignment) > 0:
                missing_assignments.append({
                    'Period': course['Period'],
                    'Classname': course['Classname'],
                    'Assignments': missing_assignment
                })

        if notify and len(missing_assignments) > 0:
            body = helpers.convert_assignments_to_html(missing_assignments)
            helpers.send_notifications(f"{self.get_firstname()} has {missing_count}"
                                       f" missing assignment(s)", body, self.agu, self.isschoolyear)
        return missing_assignments
