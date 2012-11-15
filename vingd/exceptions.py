from .response import Codes

# general exception signifies that an vingd error has been caught, but
# reasons/details were not understood/propagated well enough
class GeneralException(Exception):
    def __init__(self, msg, context="Error", code=Codes.CONFLICT):
        self.msg = msg
        self.code = code
        self.context = context
    def __str__(self):
        return "%s: %s" % (self.context, self.msg)

# verification of user data failed
class InvalidData(GeneralException):
    def __init__(self, msg, context="Invalid data", code=Codes.BAD_REQUEST):
        super(InvalidData, self).__init__(msg, context, code)

# user's request resulted in an forbidden action and was therefore cancelled
class Forbidden(GeneralException):
    def __init__(self, msg, context="Forbidden", code=Codes.FORBIDDEN):
        super(Forbidden, self).__init__(msg, context, code)

# user's request did not yield any reasonable results
class NotFound(GeneralException):
    def __init__(self, msg, context="Not found", code=Codes.NOT_FOUND):
        super(NotFound, self).__init__(msg, context, code)

# internal server error: it's our fault :)
class InternalError(GeneralException):
    def __init__(self, msg, context="Internal error", code=Codes.INTERNAL_SERVER_ERROR):
        super(InternalError, self).__init__(msg, context, code)
