from prometheus_client import Counter, Histogram

app_exceptions = Counter(
    'app_exceptions', "Amount of app exceptions"
)

page_generation_time = Histogram(
    'page_generation_time', "Time to generate flask response",
)
