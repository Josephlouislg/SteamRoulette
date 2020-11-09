import re


_pat = re.compile(',\\s*')


def get_remote_address(request):
    address = (
        request.headers.get('X-Real-Ip')
        or request.headers.get('X-Forwarded-For')
        or request.environ.get('REMOTE_ADDR')
    )
    if address and ',' in address:
        address = _pat.split(address)[-1]

    return address or ''
