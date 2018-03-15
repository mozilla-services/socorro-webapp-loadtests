import collections
import datetime
import os
import random
import time

import isodate
import molotov


HOST_URL = os.getenv('HOST_URL', 'http://localhost:8000').rstrip('/')


def utc_now():
    """Returns datetime in UTC"""
    return datetime.datetime.now(isodate.UTC)


def get_date():
    """Returns now down to the second with a random millisecond as a string

    This can be used for cache-breaking.

    """
    return utc_now().strftime('%Y-%m-%dT%H:%M:%S.') + ('%03dZ' % random.randint(0, 999))


REQ_TO_RESPONSES = {}


@molotov.events()
async def track_response(event, **info):
    if event == 'response_received':
        request = info.get('request', None)
        response = info.get('response', None)
        REQ_TO_RESPONSES[request] = response.status


@molotov.global_teardown()
def display_response_summary():
    counter = collections.Counter(REQ_TO_RESPONSES.values())
    print('\nResponse counts: %s' % counter)


@molotov.scenario()
async def test_supersearch_product_results(session):
    resource = '/SuperSearch/?product=Firefox&_results_number=10&date=<%s' % get_date()
    async with session.get(HOST_URL + resource) as resp:
        assert 200 <= resp.status < 400


# @molotov.scenario()
# async def test_supersearch_histogram(session):
#     url = HOST_URL + 'SuperSearch/?_histogram.date=product&_histogram_interval.date=1h'
#     async with session.get(url) as resp:
#         assert 200 <= resp.status < 400


# @molotov.scenario()
# async def test_supersearch_aggregator(session):
#     url = HOST_URL + 'SuperSearch/?_aggs.product=platform'
#     async with session.get(url) as resp:
#         assert 200 <= resp.status < 400


# @molotov.scenario()
# async def test_supersearch_platform(session):
#     url = HOST_URL + 'SuperSearch/?_sort=platform&_sort=-build_id'
#     async with session.get(url) as resp:
#         assert 200 <= resp.status < 400


# @molotov.scenario()
# async def test_supersearch_cardinality(session):
#     url = HOST_URL + 'SuperSearch/?product=Firefox&_facets=_cardinality.build_id'
#     async with session.get(url) as resp:
#         assert 200 <= resp.status < 400


# @molotov.scenario()
# async def test_supersearch_release_channel(session):
#     url = HOST_URL + 'SuperSearch/?release_channel=nightly&_results_offset=0&_results_number=200'
#     async with session.get(url) as resp:
#         assert 200 <= resp.status < 400


# @molotov.scenario()
# async def test_supersearch_installations(session):
#     url = HOST_URL + 'SuperSearch/?_aggs.product.version=_cardinality.install_time&product=Firefox'
#     async with session.get(url) as resp:
#         assert 200 <= resp.status < 400


# @molotov.scenario()
# async def test_supersearch_regex(session):
#     url = HOST_URL + 'SuperSearch/?_facets=signature&_results_number=0&signature=%40%22OOM%20%7C%20%22.%2A%22%20%7C%20%22.%2A'
#     async with session.get(url) as resp:
#         assert 200 <= resp.status < 400
