from studentvue import helpers, logger
from datetime import datetime


def assignments_to_dictionary(dic):
    return {'Date': dic['@Date'], 'DueDate': dic['@DueDate'],
            'Measure': dic['@Measure'], 'Type': dic['@Type'],
            'Score': dic['@Score'], 'ScoreType': dic['@ScoreType'],
            'Points': dic['@Points'], 'Notes': dic['@Notes'],
            'HasDropBox': dic['@HasDropBox'],
            'DropStartDate': dic['@DropStartDate'],
            'DropEndDate': dic['@DropEndDate']}


def get_assignment_marks(grade, term):
    grade_temp = None
    if isinstance(grade, dict):
        if len(grade['Marks']) == 0:
            # No grades for course
            return

        grade_temp = {'Period': grade['@Period'], 'Classname': grade['@Title'], 'Assignments': []}
        marks = grade['Marks']['Mark']
    else:
        # Unexpected format
        return

    # marks = grade['Marks']['Mark']
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

    return grade_temp


def parse_assignments(grades, term):
    gradebook = grades['Gradebook']['Courses']['Course']
    assignments_temp = []

    if isinstance(gradebook, dict):
        grade_temp = get_assignment_marks(gradebook, term)
        if grade_temp:
            assignments_temp.append(grade_temp)
    else:
        for grade in gradebook:
            grade_temp = get_assignment_marks(grade, term)
            if grade_temp:
                assignments_temp.append(grade_temp)

    return assignments_temp


def grades_to_list(grades, term):
    gradebook = grades['Gradebook']['Courses']['Course']
    grades_temp = []
    for grade in gradebook:
        if isinstance(grade, dict):
            if len(grade['Marks']) == 0:
                # No grades for course
                continue

            marks = grade['Marks']['Mark']
            period = grade['@Period']
            classname = grade['@Title']
        else:
            if len(gradebook['Marks']) == 0:
                # No grades for course
                continue

            marks = gradebook['Marks']['Mark']
            period = gradebook['@Period']
            classname = gradebook['@Title']

        # marks = grade['Marks']['Mark']
        if isinstance(marks, dict):
            # Progress report
            grades_temp.append({'Period': period, 'Classname': classname,
                                'Grade': marks['@CalculatedScoreString'],
                                'Score': marks['@CalculatedScoreRaw']})
        else:
            # Term
            for mark in marks:
                if mark['@MarkName'] == term:
                    grades_temp.append({'Period': period, 'Classname': classname,
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
        self.gradeterm = self.gradetermname = self.gradetermstart = self.gradetermend = None
        self.reportingperiodname = self.assignmentterm = self.isreportingperiod = None
        self.reportingperiodstart = self.reportingperiodend = None
        self.schoolbegin = self.schoolend = self.isschoolyear = self.isschoolholiday = None
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

        # Set school year dates and holidays
        self.schoolbegin, self.schoolend = self.get_schoolyear()
        if self.schoolbegin <= datetime.today().date() <= self.schoolend:
            self.isschoolyear = True
        else:
            self.isschoolyear = False
        self.set_school_holiday()

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
                self.gradetermstart = helpers.convert_string_to_date(term['@BeginDate'])
                self.gradetermend = helpers.convert_string_to_date(term['@EndDate'])
                return

    def get_schoolyear(self):
        return helpers.convert_string_to_date(self._sv.get_calendar()['CalendarListing']['@SchoolBegDate']), \
            helpers.convert_string_to_date(self._sv.get_calendar()['CalendarListing']['@SchoolEndDate'])

    def set_school_holiday(self):
        events = self._sv.get_calendar()['CalendarListing']['EventLists']['EventList']
        if isinstance(events, list):
            for event in events:
                if event['@Date'] == datetime.today().strftime("%m/%d/%Y") and event['@DayType'] == 'Holiday':
                    self.isschoolholiday = True
        else:
            if events['@Date'] == datetime.today().strftime("%m/%d/%Y") and events['@DayType'] == 'Holiday':
                self.isschoolholiday = True

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
        period_index = None
        reporting_periods = self._sv.get_gradebook(reportperiod_index)['Gradebook']
        period = reporting_periods['ReportingPeriod']
        period_name = period['@GradePeriod']
        for period_temp in reporting_periods['ReportingPeriods']['ReportPeriod']:
            if period_temp['@GradePeriod'] == period_name:
                period_index = period_temp['@Index']
                break
        period_startdate = helpers.convert_string_to_date(period['@StartDate'])
        period_enddate = helpers.convert_string_to_date(period['@EndDate'])

        if reportperiod_index is not None or reportperiod_name is not None:
            for period in reporting_periods['ReportingPeriods']['ReportPeriod']:
                period_index = period['@Index']
                period_name = period['@GradePeriod']
                period_startdate = helpers.convert_string_to_date(period['@StartDate'])
                period_enddate = helpers.convert_string_to_date(period['@EndDate'])

                # Try to match period index first otherwise match period name
                if period['@Index'] == reportperiod_index:
                    break
                elif period['@GradePeriod'] == reportperiod_name:
                    break

        # Set reporting period properties
        self.reportingperiodindex = period_index
        self.reportingperiodname = period_name
        self.reportingperiodstart = period_startdate
        self.reportingperiodend = period_enddate

        # Set property to true if in a reporting period
        if period_startdate <= datetime.today().date() <= period_enddate:
            self.isreportingperiod = True
        else:
            self.isreportingperiod = False

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
                                date_cutoff: str = None, gradeterm_filter: bool = False,
                                date_cutoff_by_class: dict = None, reportperiod_filter: bool = False,
                                notify: bool = False, notify_weekdays: bool = False,
                                notify_holidays: bool = False, notify_reportperiod: bool = False):
        missing_assignments = []
        missing_count = 0
        logger.info(f'Getting missing assignments for {self.get_firstname()}')

        for course in self.assignments_missing:
            # classname param found but class name is not a match
            if classname is not None and course['Classname'] != classname:
                continue

            # period param found but period is not a match
            if period is not None and course['Period'] != period:
                continue

            # filter out assignments
            missing_assignment = []
            for assignment in course['Assignments']:
                assignment_date = helpers.convert_string_to_date(assignment['Date'])

                if date_cutoff:
                    # do date comparison here
                    if helpers.is_timedelta_date(date_cutoff):
                        date_compare = helpers.now_timedelta_to_date(date_cutoff)
                    else:
                        date_compare = helpers.convert_string_to_date(date_cutoff)
                    if assignment_date < date_compare:
                        # date cutoff not met
                        continue

                if date_cutoff_by_class:
                    class_date_cutoff = [value for key, value in date_cutoff_by_class.items()
                                         if course['Classname'] in key]

                    # do date comparison for each class in the dictionary
                    if len(class_date_cutoff) > 0:
                        # do date comparison here
                        if helpers.is_timedelta_date(class_date_cutoff[0]):
                            date_compare = helpers.now_timedelta_to_date(class_date_cutoff[0])
                        else:
                            date_compare = helpers.convert_string_to_date(class_date_cutoff[0])

                        if assignment_date < date_compare:
                            # date cutoff not met
                            continue

                if gradeterm_filter:
                    if self.gradetermstart <= assignment_date <= self.gradetermend:
                        pass
                    else:
                        continue

                if reportperiod_filter:
                    if self.reportingperiodstart <= assignment_date <= self.reportingperiodend:
                        pass
                    else:
                        continue

                missing_assignment.append(assignment)
                missing_count += 1

            if len(missing_assignment) > 0:
                missing_assignments.append({
                    'Period': course['Period'],
                    'Classname': course['Classname'],
                    'Assignments': missing_assignment
                })

        title = f'{self.get_firstname()} has {missing_count} missing assignment(s)'
        logger.info(title)
        if len(missing_assignments) > 0:
            logger.info(missing_assignments)

        # Only notify on weekdays
        if notify_weekdays and not helpers.is_weekday():
            logger.debug('Notifications are restricted to weekdays only')
            notify = False

        # Only notify on non-holidays
        if not notify_holidays and self.isschoolholiday:
            logger.debug('Notifications are restricted on holidays')
            notify = False

        # Only notify during reporting period
        if notify_reportperiod and not self.isreportingperiod:
            logger.debug('Notifications are restricted to during the reporting period only')
            notify = False

        if notify:
            body = helpers.convert_assignments_to_html(missing_assignments)
            helpers.send_notifications(title, body, self.agu, self.isschoolyear)

        return missing_assignments
