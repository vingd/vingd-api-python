from .response import Codes

class GeneralException(Exception):
    """General exception signifies that an Vingd error has been caught, but
    reasons/details were not understood/propagated well enough."""
    def __init__(self, msg, context="Error", code=Codes.CONFLICT):
        self.msg = msg
        self.code = code
        self.context = context
    def __str__(self):
        return "%s: %s" % (self.context, self.msg)

class InvalidData(GeneralException):
    """Verification of user data failed."""
    def __init__(self, msg, context="Invalid data", code=Codes.BAD_REQUEST):
        super(InvalidData, self).__init__(msg, context, code)

class Forbidden(GeneralException):
    """User's request resulted with a forbidden action and was therefore
    cancelled."""
    def __init__(self, msg, context="Forbidden", code=Codes.FORBIDDEN):
        super(Forbidden, self).__init__(msg, context, code)

class NotFound(GeneralException):
    """User's request did not yield any reasonable result."""
    def __init__(self, msg, context="Not found", code=Codes.NOT_FOUND):
        super(NotFound, self).__init__(msg, context, code)

class InternalError(GeneralException):
    """Internal server error: it's our fault. :)"""
    def __init__(self, msg, context="Internal error", code=Codes.INTERNAL_SERVER_ERROR):
        super(InternalError, self).__init__(msg, context, code)
