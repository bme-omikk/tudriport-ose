import logging
import urllib

logger = logging.getLogger(__name__)

def mtmt2_http_read(url):
    """
    Egy MTMT2 HTTP(S) URL tartalmát olvassa be, és adja vissza utf8 stringként.
    
    Hiba esetén naplózza majd továbbítja az urllib.error.HTTPError hibát, aminek a code attribútuma további infóval szolgál.
    """

    try:
        with urllib.request.urlopen(url) as response:
            result = response.read().decode('utf-8')    
            return result
    except urllib.error.HTTPError as e:
        logger.error('HTTP %s hiba a %s URL letöltése során.'%(e.code, url))
        raise e
    except urllib.error.URLError as e:
        logger.error('URL hiba (%s) a %s URL letöltése során.'%(e.reason, url))
        raise e
