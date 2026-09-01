"""Request fingerprint utilities for uniquely identifying requests."""
import hashlib

from scrapy.utils.python import to_bytes
from w3lib.url import canonicalize_url


def get_request_fingerprint(request):
    """
    SHA1 of method + canonical URL.

    Used to uniquely identify requests and to look up parent_url when
    request.meta is lost after replace() or middleware.
    """
    fp = hashlib.sha1()
    fp.update(to_bytes(request.method))
    fp.update(to_bytes(canonicalize_url(request.url)))
    return fp.hexdigest()
