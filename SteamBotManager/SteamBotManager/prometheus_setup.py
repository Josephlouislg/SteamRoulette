from prometheus_client import Histogram

RESPONSE_TIME = Histogram("response_time", "time spent in requests", ['view'])
