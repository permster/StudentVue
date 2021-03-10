import local_settings
import json
import smtplib
import email.utils
from studentvue import logger
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote_plus

logger.initLogger()


class PUSHBULLET(object):
    def __init__(self):
        self.apikey = local_settings.pushbullet_apikey
        self.deviceid = local_settings.pushbullet_deviceid

    def notify(self, title, message):
        if not local_settings.pushbullet_enabled:
            return

        url = "https://api.pushbullet.com/v2/pushes"

        data = {'type': "note",
                'title': title,
                'body': message}

        if self.deviceid:
            data['device_iden'] = self.deviceid

        headers = {'Content-type': "application/json",
                   'Authorization': 'Bearer ' +
                                    self.apikey}

        request = Request(url, urlencode(json.dumps(data)).encode('utf-8'), headers)
        response = urlopen(request)

        if response is not None:
            try:
                response = response.json()
            except ValueError:
                logger.error("Response returned invalid JSON data")

        if response:
            logger.info(u"PushBullet notifications sent.")
            return True
        else:
            logger.error(u"PushBullet notification failed.")
            return False


class JOIN(object):
    def __init__(self):

        self.enabled = local_settings.join_enabled
        self.apikey = local_settings.join_apikey
        self.deviceid = local_settings.join_deviceid
        self.url = 'https://joinjoaomgcd.appspot.com/_ah/' \
                   'api/messaging/v1/sendPush?apikey={apikey}' \
                   '&title={title}&text={text}' \
                   '&icon={icon}'

    def notify(self, title, message):
        if not local_settings.join_enabled or \
                not local_settings.join_apikey:
            return

        if not self.deviceid:
            self.deviceid = "group.all"
        devid = [x.strip() for x in self.deviceid.split(',')]
        if len(devid) > 1:
            self.url += '&deviceIds={deviceid}'
        else:
            self.url += '&deviceId={deviceid}'

        response = urlopen(self.url.format(apikey=self.apikey,
                                           title=quote_plus(title),
                                           text=quote_plus(message.encode("utf-8")),
                                           deviceid=self.deviceid))

        if response:
            logger.info(u"Join notifications sent.")
            return True
        else:
            logger.error(u"Join notification failed.")
            return False


class PUSHOVER(object):
    def __init__(self):
        self.enabled = local_settings.pushover_enabled
        self.keys = local_settings.pushover_keys
        self.priority = local_settings.pushover_priority

        if local_settings.pushover_apitoken:
            self.application_token = local_settings.pushover_apitoken

    def notify(self, title, message):
        if not local_settings.pushover_enabled:
            return

        url = "https://api.pushover.net/1/messages.json"

        data = {'token': self.application_token,
                'user': local_settings.pushover_keys,
                'title': title,
                'message': message.encode("utf-8"),
                'priority': local_settings.pushover_priority}

        headers = {'Content-type': "application/x-www-form-urlencoded"}

        request = Request(url, urlencode(data).encode('utf-8'), headers)
        response = urlopen(request)

        if response:
            logger.info(u"Pushover notifications sent.")
            return True
        else:
            logger.error(u"Pushover notification failed.")
            return False


class Email(object):
    def notify(self, to, subject, body):
        """Send out our HTML email"""

        # message = MIMEMultipart('alternative')
        message = MIMEMultipart()
        html_body = MIMEText(body, 'html')
        message['Subject'] = subject
        message['From'] = email.utils.formataddr(
            ('Studentvue', local_settings.email_from))
        message['To'] = to
        message['Date'] = email.utils.formatdate(localtime=True)
        message.preamble = "Preamble"
        message.attach(html_body)

        try:
            if local_settings.email_ssl:
                mailserver = smtplib.SMTP_SSL(
                    local_settings.email_smtp_server,
                    local_settings.email_smtp_port)
            else:
                mailserver = smtplib.SMTP(local_settings.email_smtp_server,
                                          local_settings.email_smtp_port)

            mailserver.ehlo()

            if local_settings.email_tls:
                mailserver.starttls()

            mailserver.ehlo()

            if local_settings.email_smtp_user:
                mailserver.login(local_settings.email_smtp_user,
                                 local_settings.email_smtp_password)

            mailserver.sendmail(local_settings.email_from,
                                to.split(','),
                                message.as_string())

            mailserver.quit()
            return True

        except Exception as e:
            logger.error('Unable to send Email: %s' % e)
            return False
