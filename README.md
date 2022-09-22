# StudentVue API

This repository provides access to the StudentVue/ParentVue portals in Python programs.

This calls on a SOAP API (used by the mobile app) instead of the web api.

See documentation on the underlying SOAP API [here](https://github.com/StudentVue/SOAPI-Docs).

## Initial set up
Clone/download the repository and run `pip install -r requirements.txt`.

## Logging In

```python
from studentvue import StudentVue
sv = StudentVue('username', 'password', 'domain name') 
```

## Documentation

See main.py for additional example usage.  Main.py StudentVue credentials are stored in local_settings.py.  See example file `sample_local_settings.py`.

Rename or copy the `sample_local_settings.py` to `local_settings.py`. Edit the `local_settings.py` file and adjust the values to your needs.

The API data is in XML format, so the data is automatically transformed into json using [xmljson](https://github.com/sanand0/xmljson). You can configure the transformation convention using the `xmljson_serializer` parameter.

### local_settings.py
- **logfile:** Log file path
- **loglevel:** Log level
- **username:** ParentVUE username
- **password:** ParentVUE password
- **domain:** ParentVUE domain name (i.e. synergy.crsk12.org)
- **missing_assignment_cutoff:** Date cutoff for missing assignments
  - "30d" = Show the last 30 days of missing assignments
  - "6M" = Show the last 6 months of missing assignments
  - "09/01/2022" = Don't show missing assignment older than the date specified
- **notify_weekday_only:** Notifications on weekdays only
- **notify_on_holidays:** Notifications on holidays
- **notify_reportperiod_only:** Notifications during a reporting period only
- **notify_schoolyear_only:** Notifications during the school year only
- **pushbullet_enabled:** Pushbullet notifications enabled
- **pushbullet_apikey:** Pushbullet api key
- **pushbullet_deviceid:** Pushbullet device id
- **join_enabled:** Join (joaoapps) notifications enabled
- **join_apikey:** Join (joaoapps) api key
- **join_deviceid:** Join (joaoapps) device id
- **pushover_enabled:** Pushover notifications enabled
- **pushover_keys:** Pushover keys
- **pushover_priority:** Pushover priority
- **pushover_apitoken:** Pushover api token
- **email_enabled:** Email notifications enabled
- **email_from:** Email from address
- **email_to:** Email to addresses (comma separated)
- **email_ssl:** Enable SSL email
- **email_smtp_server:** Email SMTP server address
- **email_smtp_port:** Email SMTP port number
- **email_tls:** Enable TLS email
- **email_smtp_user:** Email SMTP username
- **email_smtp_password:** Email SMTP password
- **email_child:** Whether to also email the child
- **email_child_to_agu0:** Email address of first child
- **email_child_to_agu1:** Email address of second child

See example file `sample_local_settings.py` for reference.

### Notifications
The program supports the following notification services:
- Pushbullet
- Join (joaoapps)
- Pushover
- Email

Each can be configured with relative ease in the `local_settings.py` file.

## Bugs and Contributing

Different school districts may be running incompatible versions of StudentVue. If you find such an instance or to make general improvements, feel free to [raise a new issue](https://github.com/permster/StudentVue/issues/new) and/or [open a pull request](https://github.com/permster/StudentVue/compare).
