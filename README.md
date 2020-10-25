# StudentVue API

This repository provides access to the StudentVue/ParentVue portals in Python programs.

This call on a SOAP API (used in app) instead of the web api.

See documentation on the underlying SOAP API [here](https://github.com/StudentVue/SOAPI-Docs).

## Initial set up
Clone/download the repository and run `pip install -r requirements.txt`.

## Logging In

```python
from studentvue import StudentVue
sv = StudentVue('username', 'password', 'domain name') 
```

## Documentation

See main.py for additional example usage.

The API data is in XML format, so the data is automatically transformed into json using [xmljson](https://github.com/sanand0/xmljson). You can configure the transformation convention using the `xmljson_serializer` parameter.

## Bugs and Contributing

Different districts may be running incompatible versions of StudentVue. If you find such an instance or to make general improvements, feel free to [raise a new issue](https://github.com/kajchang/StudentVue/issues/new) and/or [open a pull request](https://github.com/kajchang/StudentVue/compare).
