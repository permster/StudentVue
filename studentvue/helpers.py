import os
import local_settings
from studentvue import notifications, logger
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def send_notifications(title, message, agu, isschoolyear: bool = False):
    if local_settings.email_enabled:
        if local_settings.email_during_schoolyear and not isschoolyear:
            logger.info(u"Email is only enabled during the schoolyear")
            return
        logger.info(u"Sending Email notification")
        email_to = local_settings.email_to
        if local_settings.email_child:
            child_email = getattr(local_settings, f'email_child_to_agu{agu}')
            if len(child_email) > 0:
                email_to += "," + child_email
        email = notifications.Email()
        email.notify(email_to, title, message)
    if local_settings.pushbullet_enabled:
        logger.info(u"Sending PushBullet notification")
        pushbullet = notifications.PUSHBULLET()
        pushbullet.notify(title, message)
    if local_settings.pushover_enabled:
        logger.info(u"Sending Pushover notification")
        prowl = notifications.PUSHOVER()
        prowl.notify(title, message)
    if local_settings.join_enabled:
        logger.info(u"Sending Join notification")
        join = notifications.JOIN()
        join.notify(title, message)


def convert_assignments_to_html(assignments):
    body = ""
    for course in assignments:
        # Start body
        body += f'<p>\n<span style="font-weight:bold;">{course["Classname"]} - {len(course["Assignments"])} missing' \
                f'</span>\n '
        body += '<table>\n<tr>'

        # Add header row to table
        for key in course['Assignments'][0].keys():
            body += f'<th valign="top">{key}</th>\n'

        # End header row
        body += '</tr>\n'

        # Populate table rows
        for assignment in course['Assignments']:
            # Start row
            body += '<tr>\n'

            # Loop through assignments
            for value in assignment.values():
                body += f'<td valign="top">{value}</td>\n'

            # End row
            body += '</tr>\n'

        # End table
        body += '</table>\n</p>'

    html = f"""\
    <html>
        <style>
        table, th, td {{
          border: 1px solid black;
          border-collapse: collapse;
        }}
        </style>
      <body>
        {body}
      </body>
    </html>
    """

    return html


def base64tofile(strbase64, filename):
    import base64
    filedecoded = base64.b64decode(strbase64)

    if not os.path.isabs(filename):
        filename = f'{os.path.dirname(os.path.realpath(__file__))}//{filename}'
    file = open(filename, "wb")
    file.write(filedecoded)
    file.close()

    return os.path.realpath(file.name)


def convert_to_timedelta(time_val):
    """
    Given a *time_val* (string) such as '5d', returns a timedelta object
    representing the given value (e.g. timedelta(days=5)).  Accepts the
    following '<num><char>' formats:

    =========   ======= ===================
    Character   Meaning Example
    =========   ======= ===================
    s           Seconds '60s' -> 60 Second(s)
    m           Minutes '5m'  -> 5 Minute(s)
    h           Hours   '24h' -> 24 Hour(s)
    d           Days    '7d'  -> 7 Day(s)
    w           Weeks   '2w'  -> 2 Week(s)
    M           Months  '2M'  -> 2 Month(s)
    Y           Years   '1y'  -> 1 Year(s)
    =========   ======= ===================
    """

    num = int(time_val[:-1])
    if time_val.endswith('s'):
        return timedelta(seconds=num)
    elif time_val.endswith('m'):
        return timedelta(minutes=num)
    elif time_val.endswith('h'):
        return timedelta(hours=num)
    elif time_val.endswith('d'):
        return timedelta(days=num)
    elif time_val.endswith('w'):
        return timedelta(weeks=num)
    elif time_val.endswith('M'):
        return relativedelta(months=num)
    elif time_val.endswith('y') or time_val.endswith('Y'):
        return relativedelta(years=num)


def now_timedelta_to_date(time_val):
    return (datetime.now() - convert_to_timedelta(time_val)).date()


def is_timedelta_date(time_val):
    suffix_list = ['s', 'm', 'h', 'd', 'w', 'M', 'y', 'Y']
    return time_val.endswith(tuple(suffix_list))


def convert_string_to_date(date):
    return datetime.strptime(date, '%m/%d/%Y').date()


def is_weekday():
    if datetime.today().weekday() < 5:
        return True
    else:
        return False
