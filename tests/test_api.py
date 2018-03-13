import molotov
import time

_BASE_URL = 'https://socorro-webapp.stage.mozaws.net/api/'


@molotov.scenario()
async def test_supersearch_product_results(session):
    qa_id = str(time.time())
    url = _BASE_URL + 'SuperSearch/?product=Firefox&_results_number=11&qa=%s' % qa_id
    async with session.get(url) as resp:
        assert 200 <= resp.status < 400


@molotov.scenario()
async def test_supersearch_histogram(session):
    url = _BASE_URL + 'SuperSearch/?_histogram.date=product&_histogram_interval.date=1h'
    async with session.get(url) as resp:
        assert 200 <= resp.status < 400


@molotov.scenario()
async def test_supersearch_aggregator(session):
    url = _BASE_URL + 'SuperSearch/?_aggs.product=platform'
    async with session.get(url) as resp:
        assert 200 <= resp.status < 400


@molotov.scenario()
async def test_supersearch_platform(session):
    url = _BASE_URL + 'SuperSearch/?_sort=platform&_sort=-build_id'
    async with session.get(url) as resp:
        assert 200 <= resp.status < 400


@molotov.scenario()
async def test_supersearch_cardinality(session):
    url = _BASE_URL + 'SuperSearch/?product=Firefox&_facets=_cardinality.build_id'
    async with session.get(url) as resp:
        assert 200 <= resp.status < 400


@molotov.scenario()
async def test_supersearch_release_channel(session):
    url = _BASE_URL + 'SuperSearch/?release_channel=nightly&_results_offset=0&_results_number=200'
    async with session.get(url) as resp:
        assert 200 <= resp.status < 400


@molotov.scenario()
async def test_supersearch_installations(session):
    url = _BASE_URL + 'SuperSearch/?_aggs.product.version=_cardinality.install_time&product=Firefox'
    async with session.get(url) as resp:
        assert 200 <= resp.status < 400


@molotov.scenario()
async def test_supersearch_regex(session):
    url = _BASE_URL + 'SuperSearch/?_facets=signature&_results_number=0&signature=%40%22OOM%20%7C%20%22.%2A%22%20%7C%20%22.%2A'
    async with session.get(url) as resp:
        assert 200 <= resp.status < 400

