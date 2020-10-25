import zeep

from lxml import etree
from xmljson import badgerfish, XMLData
from urllib.parse import urlparse
from collections import OrderedDict


class UnescapingPlugin(zeep.Plugin):
    def egress(self, envelope, http_headers, operation, binding_options):
        xml_string = etree.tostring(envelope).decode()
        xml_string = xml_string.replace('&amp;', '&')
        new_envelope = etree.fromstring(xml_string)
        return new_envelope, http_headers


class StudentVue:
    """The StudentVue API class"""

    def __init__(self, username: str, password: str,
                 district_domain: str, parent: bool = False,
                 xmljson_serializer: XMLData = badgerfish,
                 zeep_transport: zeep.Transport = None,
                 zeep_settings: zeep.Settings = None,
                 childintid: int = None, debug: bool = False):
        """
        :param username: student's username
        :type username: str
        :param password: student's password
        :type password: str
        :param district_domain: domain that the  school district hosts StudentVue on
        :type district_domain: str
        :param parent: (optional) if set to true uses ParentVue instead of StudentVue
        :type parent: bool
        :param xmljson_serializer: (optional) serializer used to serialize xml to json
        :type xmljson_serializer: xmljson.XMLData
        :param zeep_transport: (optional) custom zeep client transport
        :type zeep_transport: zeep.Transport
        :param zeep_settings: (optional) custom zeep client settings
        :type zeep_settings: zeep.Settings
        :param childintid: (optional) studentvue child id
        :type childintid: int
        :param debug: if set to true, turns on debug logging from zeep
        :type debug: bool
        """
        if debug:
            self._setup_debug()
        else:
            self._suppress_warnings()

        self._username = username
        self._password = password

        if parent and childintid is None:
            self._childintid = 0  # default to child 0
        elif parent and childintid is not None:
            self._childintid = childintid
        self.parent = parent

        parse_result = urlparse(district_domain)
        if parse_result.scheme:
            self.district_domain = parse_result.netloc
        else:
            self.district_domain = parse_result.path
            if self.district_domain[len(self.district_domain) - 1] == '/':
                self.district_domain = self.district_domain[:-1]

        self.xmljson_serializer = xmljson_serializer
        self.client = zeep.Client(
            'https://{0}/Service/PXPCommunication.asmx?WSDL'.format(self.district_domain),
            plugins=[UnescapingPlugin()],
            transport=zeep_transport,
            settings=zeep_settings
        )

    def get_messages(self) -> OrderedDict:
        """
        :return: student's messages
        :rtype: OrderedDict
        """
        return self._xml_json_serialize(self._make_service_request('GetPXPMessages'))

    def get_student_list(self) -> OrderedDict:
        """
        :return: list of students
        :rtype: OrderedDict
        """
        if self.parent:
            return self._xml_json_serialize(self._make_service_request('ChildList'))

    def switch_student(self, childintid=-1):
        if childintid >= 0:
            self._childintid = childintid

    def get_calendar(self) -> OrderedDict:
        """
        :return: student's assignments / events calendar
        :rtype: OrderedDict
        """
        return self._xml_json_serialize(self._make_service_request('StudentCalendar'))

    def get_attendance(self) -> OrderedDict:
        """
        :return: student's attendance
        :rtype: OrderedDict
        """
        return self._xml_json_serialize(self._make_service_request('Attendance'))

    def get_gradebook(self, report_period: int = None) -> OrderedDict:
        """
        :param report_period: (optional) report period to fetch gradebook for
        :type report_period: int
        :return: student's gradebook for the specified report period
        :rtype: OrderedDict
        """
        params = {}

        if report_period is not None:
            params['ReportPeriod'] = report_period

        return self._xml_json_serialize(self._make_service_request('Gradebook', **params))

    def get_class_notes(self) -> OrderedDict:
        """
        :return: student's class notes
        :rtype: OrderedDict
        """
        return self._xml_json_serialize(self._make_service_request('StudentHWNotes'))

    def get_student_info(self) -> OrderedDict:
        """
        :return: student's information
        :rtype: OrderedDict
        """
        return self._xml_json_serialize(self._make_service_request('StudentInfo'))

    def get_schedule(self, term_index: int = None) -> OrderedDict:
        """
        :param term_index: (optional) term index to fetch schedule for
        :type term_index: int
        :return: student's schedule for the specified term
        :rtype: OrderedDict
        """
        params = {}

        if term_index is not None:
            params['TermIndex'] = term_index

        return self._xml_json_serialize(self._make_service_request('StudentClassList', **params))

    def get_school_info(self) -> OrderedDict:
        """
        :return: student's school information
        :rtype: OrderedDict
        """
        return self._xml_json_serialize(self._make_service_request('StudentSchoolInfo'))

    def list_report_cards(self) -> OrderedDict:
        """
        :return: list of student's report cards
        :rtype: OrderedDict
        """
        return self._xml_json_serialize(self._make_service_request('GetReportCardInitialData'))

    def get_report_card(self, document_guid: str) -> OrderedDict:
        """
        :param document_guid: id of the report card to fetch, found using :func:`~studentvue.StudentVue.list_report_cards`
        :type document_guid: str
        :return: content of the specified report card
        :rtype: OrderedDict
        """
        return self._xml_json_serialize(self._make_service_request('GetReportCardDocumentData',
                                                                   DocumentGU=document_guid))

    def list_documents(self) -> OrderedDict:
        """
        :return: list of student's documents
        :rtype: OrderedDict
        """
        return self._xml_json_serialize(self._make_service_request('GetStudentDocumentInitialData'))

    def get_document(self, document_guid: str) -> OrderedDict:
        """
        :param document_guid: id of the document to fetch, found using :func:`~studentvue.StudentVue.list_documents`
        :type document_guid: str
        :return: content of the specified document
        :rtype: OrderedDict
        """
        return self._xml_json_serialize(self._make_service_request('GetContentOfAttachedDoc',
                                                                   DocumentGU=document_guid))

    @staticmethod
    def _suppress_warnings():
        import logging
        logging.getLogger('zeep').setLevel(logging.ERROR)

    @staticmethod
    def _setup_debug():
        import logging.config

        logging.config.dictConfig({
            'version': 1,
            'formatters': {
                'verbose': {
                    'format': '%(name)s: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'zeep.transports': {
                    'level': 'DEBUG',
                    'propagate': True,
                    'handlers': ['console'],
                },
            }
        })

    def _make_service_request(self, method_name, **kwargs) -> str:
        param_str = '&lt;Parms&gt;'
        if method_name != "ChildList":  # may be other methods besides ChildList
            param_str += '&lt;childIntID&gt;'
            param_str += str(self._childintid)
            param_str += '&lt;/childIntID&gt;'
        for key, value in kwargs.items():
            param_str += '&lt;' + key + '&gt;'
            param_str += str(value)
            param_str += '&lt;/' + key + '&gt;'
        param_str += '&lt;/Parms&gt;'

        return self.client.service.ProcessWebServiceRequest(
            userID=self._username,
            password=self._password,
            skipLoginLog=1,
            parent=int(self.parent),
            webServiceHandleName='PXPWebServices',
            methodName=method_name,
            paramStr=param_str
        )

    def _xml_json_serialize(self, xml_string: str) -> OrderedDict:
        return self.xmljson_serializer.data(etree.fromstring(xml_string))
