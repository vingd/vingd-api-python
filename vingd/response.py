try:
    import httplib
except:
    import http.client as httplib


class Codes:
    """
    Standard HTTP response codes used inside Vingd ecosystem.
    """
    # success
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    PARTIAL_CONTENT = 206
    # error
    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    BAD_REQUEST = 400
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    GONE = 410
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501

CodeValues = [v for k, v in Codes.__dict__.items() if k[0] != '_']
CodeNames = httplib.responses


class Data:
    """
    Holds any successful (2xx) response data.
    """
    def __init__(self, data, code, summary=[]):
        """
        :param data:
            MUST be a JSON-formattable structure (i.e. it MUST NOT be a single
            string or a number, but rather a list or a dictionary).
        :param code:
            MUST be from Codes, i.e. CodeValues. It represents HTTP response
            code used while talking back to client.
        :param summary:
            Can me anything as long it is also JSON-formattable, since it is
            used merly for describing 'data' in application logs. It is not
            being transfered over network.
        """
        self.data = data
        self.code = code
        self.summary = summary


class SimpleData(Data):
    """
    Holds the response data of a single fetch query, or any other query with a
    simple response that does not incorporate the errors list.
    """
    def __init__(self, data, count=0):
        Data.__init__(self,
            data=data,
            summary={'count': count, 'errors': 0},
            code=Codes.OK
        )


class ComplexData(Data):
    """
    Holds the response data of a BATCH query.
    
    Batch query acts on several objects, users, etc. The result is packed in a
    customized dictionary structure which is usually comprised of a results list
    and an errors list.

    Returned HTTP code depends on a total items vs. errors count ratio.
    """
    def __init__(self, data, count=(0,0)):
        total, errors = count
        Data.__init__(self,
            data=data,
            summary={'count': total, 'errors': errors},
            code=(Codes.PARTIAL_CONTENT if errors else Codes.CREATED)
        )
