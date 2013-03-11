import hashlib
import datetime

try:
    from urllib.parse import quote
except ImportError:
    # python2 sucks at unicoding
    from urllib import quote as ascii_quote
    def quote(url, safe='/=:%{}'):
        try:
            return ascii_quote(url.encode('utf-8'), safe).encode('ascii')
        except Exception as e:
            raise Exception("Malformed URL: '" + url + "'")


def hash(msg):
    return hashlib.sha1(msg.encode('utf-8')).hexdigest() if msg else None


class tzutc(datetime.tzinfo):
    '''UTC time zone info.'''
    
    def utcoffset(self, dt):
        return datetime.timedelta(0)
    
    def dst(self, dt):
        return datetime.timedelta(0)
    
    def tzname(self, dt):
        return "UTC"


def parseDuration(string):
    '''
    Parses duration/period stamp expressed in a subset of ISO8601 duration
    specification formats and returns a dictionary of time components (as
    integers). Accepted formats are:
    
     * ``PnYnMnDTnHnMnS``
     
       Note: n is positive integer! Floats are NOT supported. Any component (nX)
       is optional, but if any time component is specified, ``T`` spearator is
       mandatory. Also, ``P`` is always mandatory.
       
     * ``PnW``
     
       Note: n is positive integer representing number of weeks.
       
     * ``P<date>T<time>``
     
       Note: This format is basically standard ISO8601 timestamp format, without
       the time zone and with ``P`` prepended. We support both basic and
       extended format, which translates into following two subformats:
       
        - ``PYYYYMMDDThhmmss`` for basic, and
        - ``PYYYY-MM-DDThh:mm:ss`` for extended format.
       
       Note that all subfields are mandatory. 
    
    Note: whitespaces are ignored.
    
    Examples::
    
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        rel = parseDuration('P1m')     # +1 month
        rel = parseDuration('P 1y 1m T 2m 1s')
        rel = parseDuration('P12w')    # +12 weeks
        rel = parseDuration('P 0001-02-03 T 03:02:01')
        rel = parseDuration('P00010203T030201')
        
        future = datetime.now() + relativedelta(**rel)
    
    Returns: dictionary with (some of the) fields: ``years``, ``months``,
    ``weeks``, ``days``, ``hours``, ``minutes`` or ``seconds``. If nothing is
    matched, an empty dict is returned.
    '''

    string = string.replace(' ', '').upper()
    
    # try `PnYnMnDTnHnMnS` form
    match = re.match(
        "^P(?:(?:(?P<years>\d+)Y)?(?:(?P<months>\d+)M)?(?:(?P<days>\d+)D)?)?" \
        "(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$",
        string
    )
    if match:
        d = match.groupdict(0)
        return dict(zip(d.keys(), map(int, d.values())))
    
    # try `PnW` form
    match = re.match(
        "^P(?P<weeks>\d+)W$",
        string
    )
    if match:
        d = match.groupdict(0)
        return dict(zip(d.keys(), map(int, d.values())))
    
    # try `P<date>T<time>` form, subforms `PYYYYMMDDThhmmss` and `PYYYY-MM-DDThh:mm:ss`
    match = re.match(
        "^P(?P<years>\d{4})(-)?(?P<months>\d{2})(?(2)-)(?P<days>\d{2})T(?P<hours>\d{2})(?(2):)(?P<minutes>\d{2})(?(2):)(?P<seconds>\d{2})$",
        string
    )
    if match:
        d = match.groupdict(0)
        return dict(zip(d.keys(), map(int, d.values())))
    
    return {}
