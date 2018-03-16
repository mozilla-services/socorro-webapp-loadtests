import collections
import datetime
import os
import random
import time

from aiohttp.client_exceptions import ServerTimeoutError
import isodate
import molotov


# API token to use
API_TOKEN = os.getenv('API_TOKEN', '')

# Host url
HOST_URL = os.getenv('HOST_URL', 'http://localhost:8000').rstrip('/')

# API urls
SUPERSEARCH_API = HOST_URL + '/api/SuperSearch/'
PROCESSED_CRASH_API = HOST_URL + '/api/ProcessedCrash/'

# Maximum number of results per page for SuperSearch API
MAX_PAGE = 1000

# The number of seconds we give a request to complete
TIMEOUT = 10

# Headers to use for requests
HEADERS = {}

# List of crash ids to use--gets populated on startup
CRASH_IDS = []

# Map of request -> response status code--gets populated by track_summary after
# each request has completed
REQ_TO_RESPONSES = {}

START_TIME = 0


def utc_now():
    """Returns datetime in UTC"""
    return datetime.datetime.now(isodate.UTC)


def get_date():
    """Returns now down to the second with a random millisecond as a string

    This can be used for cache-breaking.

    """
    return utc_now().strftime('%Y-%m-%dT%H:%M:%S.') + ('%03dZ' % random.randint(0, 999))


def format_time(secs):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(secs))


@molotov.global_setup()
def setup_tests(args):
    if API_TOKEN:
        print('Using API_TOKEN')
        HEADERS['Auth-Token'] = API_TOKEN
    else:
        print('No API_TOKEN specified.')

    print('Using host %s' % HOST_URL)

    print('Fetching crash ids (this will take a few moments)...')

    def crash_ids_generator(num_results):
        params = {
            '_columns': 'uuid',
            '_results_offset': 0,
            '_results_number': min(MAX_PAGE, num_results),
        }

        crashids_count = 0
        while True:
            resp = molotov.json_request(SUPERSEARCH_API, verb='GET', params=params)
            hits = resp['content']['hits']
            for hit in hits:
                crashids_count += 1
                yield hit['uuid']

                if crashids_count >= num_results:
                    return

            total = resp['content']['total']
            if not hits or crashids_count >= total:
                return

            params['_results_offset'] += MAX_PAGE
            params['_results_number'] = min(
                # MAX_PAGE is the maximum we can request
                MAX_PAGE,

                # The number of results Super Search can return to us that is
                # hasn't returned so far
                total - crashids_count,

                # The number of results we want that we haven't gotten, yet
                num_results - crashids_count
            )

    crash_ids = list(crash_ids_generator(5000))
    print('Loaded %d crash ids...' % len(crash_ids))
    CRASH_IDS.extend(crash_ids)

    global START_TIME
    START_TIME = time.time()
    print('Starting at %s' % format_time(START_TIME))


@molotov.events()
async def track_response(event, **info):
    if event == 'response_received':
        request = info.get('request', None)
        response = info.get('response', None)
        REQ_TO_RESPONSES[request] = response.status


@molotov.global_teardown()
def display_summary():
    end_time = time.time()

    print('')
    print('')
    print('API token: %s' % ('yes' if API_TOKEN else 'no'))
    print('Crash ids: %d' % len(CRASH_IDS))
    print('Host: %s' % HOST_URL)

    counter = collections.Counter(REQ_TO_RESPONSES.values())
    print('Response counts: %s' % counter)

    counter = collections.Counter([
        req.original_url.path
        for req in REQ_TO_RESPONSES.keys()
    ])
    print('API request counts: %s' % counter)

    print('Started at %s' % format_time(START_TIME))
    print('Ending at %s' % format_time(end_time))
    total_seconds = end_time - START_TIME
    print(total_seconds)
    print('Rate: %2.2f req/s' % (len(REQ_TO_RESPONSES) * 1.0 / total_seconds))
    print('')


@molotov.scenario(66)
async def test_supersearch_api(session):
    """Scenario that hits SuperSearch API

    The SuperSearch API is Elasticsearch driven. It has an API rate-limit, so
    we should use an API token and/or spread across multiple nodes. Results are
    cached, so we need a cache-busting value.

    """
    params = {
        'date': '<%s' % get_date()
    }

    try:
        async with session.get(SUPERSEARCH_API, params=params, headers=HEADERS, timeout=TIMEOUT) as resp:
            assert 200 <= resp.status < 500
    except Exception as exc:
        print('\nexc %r %s' % (exc, format_time(time.time())))
        raise


@molotov.scenario(34)
async def test_processed_crash_api(session):
    """Scenario that hits ProcessedCrash API

    The ProcessedCrash API is S3 driven. It has an API rate-limit, so we should
    use an API token and/or spread across multiple nodes. Results are cached,
    so when molotov starts up, we do a SuperSearch to fetch 5000 crash ids that
    we use for this API endpoint.

    Because this is async, the easiest thing to do is pick a random crash id
    from the list every iteration. I think that'll be ok.

    """
    params = {
        'crash_id': random.choice(CRASH_IDS)
    }

    try:
        async with session.get(PROCESSED_CRASH_API, params=params, headers=HEADERS, timeout=TIMEOUT) as resp:
            assert 200 <= resp.status < 500
    except Exception as exc:
        print('\nexc %r %s' % (exc, format_time(time.time())))
        raise
