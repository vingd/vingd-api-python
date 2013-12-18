import re
from hashlib import sha1
from datetime import datetime, timedelta, tzinfo
from itertools import count

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
    return sha1(msg.encode('utf-8')).hexdigest() if msg else None


class tzutc(tzinfo):
    '''UTC time zone info.'''
    
    def utcoffset(self, dt):
        return timedelta(0)
    
    def dst(self, dt):
        return timedelta(0)
    
    def tzname(self, dt):
        return "UTC"


def localnow():
    """Local time without time zone (local time @ local time zone)."""
    return datetime.now()

def utcnow():
    """Current UTC/GMT time without time zone (local time @ UTC)."""
    return datetime.utcnow()

def now():
    """Current UTC/GMT time with time zone."""
    return datetime.now(tzutc())


def parse_duration(string):
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
        
        rel = parse_duration('P1m')     # +1 month
        rel = parse_duration('P 1y 1m T 2m 1s')
        rel = parse_duration('P12w')    # +12 weeks
        rel = parse_duration('P 0001-02-03 T 03:02:01')
        rel = parse_duration('P00010203T030201')
        
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


class ConversionError(TypeError):
    """Raised by `safeformat` when argument can't be cast to the type proscribed
    with `format_string`."""


def safeformat(format_string, *args):
    """String formatter with type validation. Python `format`-alike.
    
    Examples::
        
        - implicit indexing:
        
            safeformat("Decimal {:int}, hexadecimal {1:hex}", 2, "abc")
            --> "Decimal 2, hexadecimal abc"
    
        - reusable arguments:
        
            safeformat("{:hex}. item: {0:str}", 13)
            --> "13. item: 13"
        
        - safe paths:
        
            safeformat("objects/{:int}/tokens/{:hex}", 123, "ab2e36d953e7b634")
            --> "objects/123/tokens/ab2e36d953e7b634"
    
    Format pattern is `{[index]:type}`, where `index` is optional argument
    index, and `type` is one of the predefined typenames (currently: `int`,
    `hex`, `str`, `ident`).
    """
    
    def hex(x):
        """Allow hexadecimal digits."""
        if re.match('^[a-fA-F\d]*$', str(x)):
            return str(x)
        raise ValueError("Non-hex digits in hex number.")
    
    def identifier(x):
        """Allow letters, digits, underscore and minus/dash."""
        if re.match('^[-\w]*$', str(x)):
            return str(x)
        raise ValueError("Non-identifier characters in string.")
    
    converters = {
        'int': int,
        'hex': hex,
        'str': str,
        'ident': identifier
    }
    
    argidx = count(0)
    
    def replace(match):
        idx, typ = match.group('idx', 'typ')
        
        if idx is None:
            idx = next(argidx)
        else:
            try:
                idx = int(idx)
            except:
                raise ConversionError("Non-integer index: '%s'." % idx)
        
        try:
            arg = args[idx]
        except:
            raise ConversionError("Index out of bounds: %d." % idx)
        
        try:
            conv = converters[typ]
        except:
            raise ConversionError("Invalid converter/type: '%s'." % typ)
        
        try:
            val = conv(arg)
        except:
            raise ConversionError("Argument '%s' not of type '%s'." % (arg, typ))
        
        return str(val)
    
    return re.sub("{(?:(?P<idx>\d+))?:(?P<typ>\w+)}", replace, format_string)
