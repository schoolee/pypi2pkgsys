# usage page of pypi-logstats.py

# Usage of pypi-logstats.py #

Command line:
```
# pypi-logstats.py LOG_PATH ...
```
Read in the provided log file, and show how many packages are passed, and
how many packages are failed.

Multiple log file can be provided. Root privilege is required because it want
to access the log lock.