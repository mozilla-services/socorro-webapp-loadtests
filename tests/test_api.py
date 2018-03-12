import molotov
import time


@molotov.scenario(weight=100)
async def test_supersearch(session):
    qa_id = str(time.time())
    url = 'https://socorro-webapp.stage.mozaws.net/api/SuperSearch/?product=Firefox&_results_number=11&qa=%s' % qa_id
    #url = 'https://crash-stats.allizom.org/api/SuperSearch/?product=Firefox&_results_number=11&qa=%s' % qa_id
    async with session.get(url) as resp:
        assert 200 <= resp.status < 400



