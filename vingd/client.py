"""
:newfield access: Access
:newfield resource: Resource path
"""

try:
    import simplejson as json
except ImportError:
    import json

try:
    import httplib
except ImportError:
    import http.client as httplib

import base64
from urlparse import urljoin, urlparse
from datetime import datetime, timedelta

from .exceptions import Forbidden, GeneralException, InternalError, InvalidData, NotFound
from .response import Codes
from .util import quote, hash, tzutc


class Vingd:
    # production urls
    URL_ENDPOINT = "https://api.vingd.com/broker/v1"
    URL_FRONTEND = "https://www.vingd.com"
    # sandbox urls
    URL_ENDPOINT_SANDBOX = "https://api.vingd.com/sandbox/broker/v1"
    URL_FRONTEND_SANDBOX = "https://www.sandbox.vingd.com"
    
    EXP_ORDER = {'minutes': 15}
    EXP_VOUCHER = {'days': 7}
    
    api_key = None
    api_secret = None
    api_endpoint = URL_ENDPOINT
    usr_frontend = URL_FRONTEND
    
    def __init__(self, key=None, secret=None, endpoint=None, frontend=None,
                 username=None, password=None):
        # `key`, `secret` are forward compatible arguments (we'll switch to oauth soon)
        self.api_key = key or username
        self.api_secret = secret or hash(password)
        if not self.api_key or not self.api_secret:
            raise Exception("API key/username and/or API secret/password undefined.")
        if endpoint: self.api_endpoint = endpoint
        if frontend: self.usr_frontend = frontend
    
    def request(self, verb, subpath, data=''):
        """
        Generic Vingd-backend authenticated request (currently HTTP Basic Auth
        over HTTPS, but OAuth1 in the future).
        
        :returns: Data ``dict``, or raises exception.
        """
        if not self.api_key or not self.api_secret:
            raise Exception("Vingd authentication credentials undefined.")
        
        endpoint = urlparse(self.api_endpoint)
        if endpoint.scheme != 'https':
            raise Exception("Invalid Vingd endpoint URL (non-https).")
        
        host = endpoint.netloc.split(':')[0]
        port = 443
        path = urljoin(endpoint.path+'/', subpath)
        
        headers = {'Authorization': 'Basic ' + base64.b64encode("%s:%s" % (self.api_key, self.api_secret)) }
        try:
            conn = httplib.HTTPSConnection(host, port)
            conn.request(verb.upper(), quote(path), data, headers)
            r = conn.getresponse()
            content = r.read().decode('ascii')
            code = r.status
            conn.close()
        except httplib.HTTPException as e:
            raise InternalError('HTTP request failed! (Network error? Installation error?)')
        
        try:
            content = json.loads(content)
        except:
            raise GeneralException(content, 'Non-JSON server response', code)
        
        if 200 <= code <= 299:
            try:
                return content['data']
            except:
                raise InvalidData('Invalid server DATA response format!')
        
        try:
            message = content['message']
            context = content['context']
        except:
            raise InvalidData('Invalid server ERROR response format!')
        
        if code == Codes.BAD_REQUEST:
            raise InvalidData(message, context)
        elif code == Codes.FORBIDDEN:
            raise Forbidden(message, context)
        elif code == Codes.NOT_FOUND:
            raise NotFound(message, context)
        elif code == Codes.INTERNAL_SERVER_ERROR:
            raise InternalError(message, context)
        elif code == Codes.CONFLICT:
            raise GeneralException(message, context)
        
        raise GeneralException(message, context, code)
    
    @staticmethod
    def _extract_id_from_batch_response(r, name='id'):
        """ Unholy, forward-compatible, mess for extraction of id/oid from a
        soon-to-be (deprecated) batch response. """
        names = name + 's'
        if names in r:
            # soon-to-be deprecated batch reponse
            if 'errors' in r and r['errors']:
                raise GeneralException(r['errors'][0]['desc'])
            id = r[names][0]
        else:
            # new-style simplified api response
            id = r[name]
        return int(id)
    
    def create_object(self, name, url):
        """
        CREATES a single object in Vingd Object registry.
        
        :type name: ``string``
        :param name:
            Object's name.
        :type url: ``string``
        :param url:
            Callback URL (object's resource location - on your server).
        
        :rtype: `bigint`
        :returns: Object ID for the newly created object.
        :raises GeneralException:s
        
        :resource: ``registry/objects/``
        :access: authorized users
        """
        r = self.request('post', 'registry/objects/', json.dumps({
            'description': {
                'name': name,
                'url': url
            }
        }))
        return self._extract_id_from_batch_response(r, 'oid')
    
    def verify_purchase(self, oid, tid):
        """
        VERIFIES token ``tid`` and returns token data associated with ``tid``
        and bound to object ``oid``. At the same time decrements entitlement
        validity counter for ``oid`` and ``uid`` bound to this token.
        
        :type oid: ``bigint``
        :param oid:
            Object ID.
        :type tid: ``alphanumeric(40)``
        :param tid:
            Token ID.
        
        :rtype: ``dict``
        :returns:
            A single token data dictionary::
            
                token = {
                    "object": <object_name>,
                    "huid": <hashed_user_id_bound_to_seller> / None,
                    "context": <order_context> / None,
                    ...
                }
            
            where:
            
                * ``object`` is object's name, as stored in object's
                  ``description['name']`` Registry entry, at the time of token
                  creation/purchase (i.e. if object changes its name in the
                  meantime, ``object`` field will hold the old/obsolete name).
                * ``huid`` is Hashed User ID - The unique ID for a user, bound
                  to the object owner/seller. Each user/buyer of the ``oid``
                  gets an arbitrary (random) identification alphanumeric handle
                  associated with her, such that ``huid`` is unique in the set
                  of all buyers (users) of all of the seller's objects. In other
                  words, each seller can treat a retrieved ``huid`` as unique in
                  his little microcosm of all of his users. On the other hand,
                  that same ``huid`` has absolutely no meaning to anyone else --
                  and user's privacy is guaranteed. Also, note that the value of
                  ``huid`` **will be** ``null`` iff buyer chose anonymous
                  purchase.
                * ``context`` is an arbitrary purchase context defined when
                  creating order.
        
        :raises GeneralException:
        :raises Forbidden:
            User no longer entitled to ``oid`` (count-wise).
        
        :see: `commit_purchase`.
        :resource: ``objects/<oid>/tokens/<tid>``
        :access: authenticated user MUST be the object's owner
        """
        return self.request('get', 'objects/%d/tokens/%s' % (oid, tid))
    
    def commit_purchase(self, purchaseid, transferid):
        """
        DECLARES a purchase defined with ``purchaseid`` (bound to vingd transfer
        referenced by ``transferid``) as finished, with user being granted the
        access to the service or goods.
        
        If seller fails to commit the purchase, the user (buyer) shall be
        refunded full amount paid (reserved).
        
        :type purchaseid: ``bigint``
        :param purchaseid:
            Purchase ID, as returned in purchase description, upon
            token/purchase verification.
        :type transferid: ``bigint``
        :param transferid:
            Transfer ID, as returned in purchase description, upon
            token/purchase verification.
        
        :rtype: ``dict``
        :returns:
            ``{'ok': <boolean>}``.
        :raises InvalidData: invalid format of input parameters
        :raises NotFound: non-existing order/purchase/transfer
        :raises GeneralException: depends on details of error
        :raises InternalError: Vingd internal error (network, server, app)
        
        :see: `verify_purchase`.
        :resource: ``purchases/<purchaseid>``
        :access: authorized users (ACL flag: ``type.business``)
        """
        return self.request(
            'put',
            'purchases/%d' % int(purchaseid),
            json.dumps({'transferid': transferid})
        )
    
    def create_order(self, oid, price, context=None, expires=None):
        """
        CREATES a single order for object ``oid``, with price set to ``price``
        and validity until ``expires``.
        
        :type oid: ``bigint``
        :param oid:
            Object ID.
        :type price: ``bigint``
        :param price:
            Vingd amount (in cents) the user/buyer shall be charged upon
            successful purchase.
        :type context: ``string``
        :param context:
            Purchase (order-related) context. Retrieved upon purchase
            verification.
        :type expires: ``datetime``/``dict``
        :param expires:
            Order expiry timestamp, absolute (``datetime``) or relative
            (``dict``). Valid keys for relative expiry timestamp dictionary are
            same as keyword arguments for `datetime.timedelta` (``days``,
            ``seconds``, ``minutes``, ``hours``, ``weeks``). Default:
            `Vingd.EXP_ORDER`.
        
        :rtype: ``dict``
        :returns:
            Order dictionary::
            
                order = {
                    'id': <order_id>,
                    'expires': <order_expiry>,
                    'context': <purchase_context>,
                    'object': {
                        'id': <oid>,
                        'price': <amount_in_cents>
                    },
                    'urls': {
                        'redirect': <url_for_failsafe_redirect_purchase_mode>,
                        'popup': <url_for_popup_purchase_mode>
                    }
                }
        
        :raises GeneralException:
        :resource: ``objects/<oid>/orders/``
        :access: authorized users
        """
        if expires is None:
            expires = self.EXP_ORDER
        if isinstance(expires, dict):
            expires = datetime.now(tzutc())+timedelta(**expires)
        orders = self.request('post', 'objects/%d/orders/' % int(oid), json.dumps({
            'price': price,
            'order_expires': expires.isoformat(),
            'context': context
        }))
        orderid = self._extract_id_from_batch_response(orders)
        return {
            'id': orderid,
            'expires': expires.isoformat(),
            'context': context,
            'object': {
                'id': oid,
                'price': price
            },
            'urls': {
                'redirect': urljoin(self.usr_frontend, '/orders/%d/add/' % orderid),
                'popup': urljoin(self.usr_frontend, '/popup/orders/%d/add/' % orderid)
            }
        }
    
    def get_orders(self, oid=None, include_expired=False, orderid=None):
        """
        FETCHES filtered orders. All arguments are optional.
        
        :type oid: ``bigint``
        :param oid:
            Object ID.
        :type include_expired: ``boolean``
        :param include_expired:
            Fetch also expired orders.
        :type orderid: ``bigint``
        :param orderid:
            Order ID. If specified, exactly one order shall be returned, or
            `NotFound` exception raised. Otherwise, a LIST of orders is
            returned.
        
        :rtype: ``list``/``dict``
        :returns: (A list of) order(s) description dictionary(ies).
        :raises GeneralException:
        
        :resource: ``[objects/<oid>/]orders/[<all>/]<orderid>``
        :access: authorized users (authenticated user MUST be the object/order
            owner)
        """
        return self.request(
            'get',
            '%sorders/%s%s' % (
                ('objects/%d/' % oid) if oid else "",
                "all/" if include_expired else "",
                orderid if orderid else ""
            )
        )
    
    def get_order(self, orderid):
        """
        FETCHES a single order defined with ``orderid``, or fails if order is
        non-existing (with `NotFound`).
        
        :type orderid: ``bigint``
        :param orderid:
            Order ID
        
        :rtype: ``dict``
        :returns:
            The order description dictionary.
        :raises GeneralException:
        
        :see: `get_orders` ``(orderid=...)``
        :resource: ``orders/<orderid>``
        :access: authorized users (authenticated user MUST be the object/order
            owner)
        """
        return self.get_orders(orderid=orderid)
    
    def update_object(self, oid, name, url):
        """
        UPDATES a single object in Vingd Object registry.
        
        :type oid: ``bigint``
        :param oid:
            Object ID of the object being updated.
        :type name: ``string``
        :param name:
            New object's name.
        :type url: ``string``
        :param url:
            New callback URL (object's resource location).
        
        :rtype: `bigint`
        :returns: Object ID of the updated object.
        :raises GeneralException:
        
        :resource: ``registry/objects/<oid>/``
        :access: authorized user MUST be the object owner
        """
        r = self.request(
            'put', 'registry/objects/%d/' % oid,
            json.dumps({
                'description': {
                    'name': name,
                    'url': url
                }
            })
        )
        return self._extract_id_from_batch_response(r, 'oid')
    
    def get_objects(self, oid=None,
                    since=None, until=None, last=None, first=None):
        """
        FETCHES a filtered collection of objects created by the authenticated
        user.
        
        :type oid: ``bigint``
        :param oid:
            Object ID
        :type since: ``string``
        :param since:
            Object has to be newer than this timestamp (in ISO 8601 basic
            format).
        :type until: ``string``
        :param until:
            Object has to be older than this timestamp (in ISO 8601 basic
            format).
        :type last: ``bigint``
        :param last:
            The number of newest objects (that satisfy all other criteria) to
            return.
        :type first: ``bigint``
        :param first:
            The number of oldest objects (that satisfy all other criteria) to
            return.
        
        :rtype: ``list``/``dict``
        :returns:
            A list of object description dictionaries. If ``oid`` is specified,
            a single dictionary is returned instead of a list.
        :raises GeneralException:
        
        :resource:
            ``registry/objects[/<oid>]``
            ``[/since=<since>][/until=<until>][/last=<last>][/first=<first>]``
        :access: authorized users (only objects owned by the authenticated user
            are returned)
        """
        resource = 'registry/objects'
        if oid: resource += '/%d' % int(oid)
        if since: resource += '/since=%s' % since
        if until: resource += '/until=%s' % until
        if first: resource += '/first=%d' % int(first)
        if last: resource += '/last=%d' % int(last)
        return self.request('get', resource)
    
    def get_object(self, oid):
        """
        FETCHES a single object, referenced by its ``oid``.
        
        :type oid: ``bigint``
        :param oid:
            Object ID
        
        :rtype: ``dict``
        :returns:
            The object description dictionary.
        :raises GeneralException:
        
        :note:
            `get_objects` can be used instead, but then specifying any other
            (conflicting) constraint (except ``oid``) yields a non-existing
            resource exception (`NotFound`).
        
        :resource: ``registry/objects/<oid>``
        :access: authorized users (only objects owned by the authenticated user
            are returned)
        """
        return self.request('get', 'registry/objects/%d' % oid)
    
    def get_user_profile(self):
        """
        FETCHES profile dictionary of the authenticated user.
        
        :rtype: ``dict``
        :returns:
            A single user description dictionary.
        :raises GeneralException:
        :resource: ``/id/users/<uid>``
        
        :access: authorized users; only authenticated user's metadata can be
            fetched (UID is automatically set to the authenticated user's UID)
        """
        return self.request('get', 'id/users')
    
    def get_account_balance(self):
        """
        FETCHES the account balance for the authenticated user.
        
        :rtype: ``bigint``
        :returns: ``<amount_in_cents>``
        :raises GeneralException:
        :resource: ``fort/accounts/``
        
        :access: authorized users; authenticated user's account data will be
            fetched
        """
        return int(self.request('get', 'fort/accounts')['balance'])
    
    def authorized_get_account_balance(self, huid):
        """
        FETCHES the account balance for the user defined with `huid`.
        
        :rtype: ``bigint``
        :returns: ``<amount_in_cents>``
        :raises GeneralException:
        :resource: ``fort/accounts/<huid>``
        
        :access: authorized users; delegate permission required for the
            requester to read user's balance: ``get.account.balance``
        """
        return int(self.request('get', 'fort/accounts/%s' % huid)['balance'])
    
    def authorized_purchase_object(self, oid, price, huid):
        """Does delegated (pre-authorized) purchase of `oid` in the name of
        `huid`, at price `price` (vingd transferred from `huid` to consumer's
        acc).
        
        :raises GeneralException:
        :resource: ``objects/<oid>/purchases``
        
        :access: authorized users with ACL flag ``purchase.object.authorize`` +
            delegate permission required for the requester to charge the
            user: ``purchase.object``
        """
        return self.request('post', 'objects/%d/purchases' % oid, json.dumps({
            'price': price,
            'huid': huid,
            'autocommit': True
        }))
    
    def authorized_create_user(self, identities, primary, permissions=None):
        """Creates Vingd user (profile & account), links it with the provided
        identities (to be verified later), and sets the delegate-user
        permissions (creator being the delegate). Returns Vingd user's `huid`
        (hashed user id).
        
        Example::
        
            vingd.authorized_create_user(
                identities={"facebook": "12312312", "mail": "user@example.com"},
                primary="facebook",
                delegate_permissions=["get.account.balance", "purchase.object"]
            )
        
        :rtype: ``string``
        :returns: ``<huid>``
        :raises GeneralException:
        :resource: ``id/objects/<oid>/purchases``
        
        :access: authorized users with ACL flag ``user.create``
        """
        return self.request('post', 'id/users/', json.dumps({
            'identities': identities,
            'primary_identity': primary,
            'delegate_permissions': permissions
        }))
    
    def reward_user(self, huid_to, amount, description=None):
        """
        PERFORMS a single reward. User defined with `huid_to` is rewarded with
        `amount` cents, transfered from the account of the authenticated user.
        
        :type huid_to: ``alphanumeric(40)``
        :param huid_to:
            Hashed User ID, bound to account of the authenticated user (doing
            the request).
        :type amount: ``integer``
        :param amount:
            Amount in cents.
        :type description: ``string``
        :param description:
            Transaction description (optional).
        
        :rtype: ``dict``
        :returns: ``{'transfer_id': <transfer_id>}``
            Fort Transfer ID packed inside a dict.
        :raises Forbidden: consumer has to have ``transfer.outbound`` ACL flag
            set.
        :raises GeneralException: :raises NotFound:
        
        :resource: ``rewards/``
        :access: authorized users (ACL flag: ``transfer.outbound``)
        """
        return self.request('post', 'rewards', json.dumps({
            'huid_to': huid_to,
            'amount': amount,
            'description': description
        }))
    
    def create_voucher(self, amount, expires=None, message='', gid=None):
        """
        CREATES a new preallocated voucher with ``amount`` vingd cents reserved
        until ``expires``.
        
        :type amount: ``bigint``
        :param amount:
            Voucher amount in vingd cents.
        :type expires: ``datetime``/``dict``
        :param expires:
            Voucher expiry timestamp, absolute (``datetime``) or relative
            (``dict``). Valid keys for relative expiry timestamp dictionary are
            same as keyword arguments for `datetime.timedelta` (``days``,
            ``seconds``, ``minutes``, ``hours``, ``weeks``). Default:
            `Vingd.EXP_VOUCHER`.
        :type message: ``string``
        :param message:
            Short message displayed to user when she redeems the voucher on
            Vingd frontend.
        :type gid: ``alphanum(32)``
        :param gid:
            Voucher group id. An user can redeem only one voucher per group.
        
        :rtype: ``dict``
        :returns:
            Created voucher description::
                
                voucher = {
                    'vid': <voucher_integer_id>,
                    'vid_encoded': <voucher_string_id>,
                    'amount_allocated': <int_cents | None if not allocated>,
                    'amount_vouched': <int_cents>,
                    'id_fort_transfer': <id_of_allocating_transfer |
                                         None if not allocated>,
                    'fee': <int_cents>,
                    'uid_from': <source_account_uid>,
                    'uid_proxy': <broker_id>,
                    'uid_to': <destination_account_id | None if not given>,
                    'gid': <voucher_group_id | None if undefined>,
                    'ts_valid_until': <iso8601_timestamp_absolute>,
                    'description': <string | None>,
                    'message': <string | None>
                }
            
            combined with voucher redeem urls on Vingd frontend.
        
        :raises GeneralException:
        
        :resource: ``vouchers/``
        :access: authorized users (ACL flag: ``voucher.add``)
        """
        if expires is None:
            expires = self.EXP_VOUCHER
        if isinstance(expires, dict):
            expires = datetime.now(tzutc())+timedelta(**expires)
        voucher = self.request('post', 'vouchers/', json.dumps({
            'amount': amount,
            'until': expires.isoformat(),
            'message': message,
            'gid': gid
        }))
        return {
            'raw': voucher,
            'urls': {
                'redirect': urljoin(self.usr_frontend, '/vouchers/%s' % voucher['vid_encoded']),
                'popup': urljoin(self.usr_frontend, '/popup/vouchers/%s' % voucher['vid_encoded'])
            }
        }
    
    def get_vouchers(self, vid_encoded=None,
                     uid_from=None, uid_to=None, gid=None,
                     valid_after=None, valid_before=None,
                     last=None, first=None):
        """
        FETCHES a filtered list of vouchers.
        
        :type vid_encoded: ``alphanumeric(64)``
        :param vid_encoded:
            Voucher ID, as a string with CRC.
        :type uid_from: ``bigint``
        :param uid_from:
            Filter by source account UID.
        :type uid_to: ``bigint``
        :param uid_to:
            Filter by destination account UID.
        :type gid: ``alphanumeric(32)``
        :param gid:
            Filter by voucher Group ID. GID is localized to `uid_from`.
        :type valid_after: ``string``
        :param valid_after:
            Voucher has to be valid after this timestamp (in ISO 8601 basic
            format).
        :type valid_before: ``string``
        :param valid_before:
            Voucher was valid until this timestamp (in ISO 8601 basic format).
        :type last: ``bigint``
        :param last:
            The number of newest vouchers (that satisfy all other criteria) to
            return.
        :type first: ``bigint``
        :param first:
            The number of oldest vouchers (that satisfy all other criteria) to
            return.
        
        :note:
            If `first` or `last` are used, the vouchers list is sorted by time
            created, otherwise it is sorted alphabetically by `vid_encoded`.
        
        :rtype: ``list``/``dict``
        :returns:
            A list of voucher description dictionaries. If `vid_encoded` is
            specified, a single dictionary is returned instead of a list.
        :raises GeneralException:
        
        :resource:
            ``vouchers[/<vid_encoded>][/from=<uid_from>][/to=<uid_to>]``
            ``[/valid_after=<valid_after>][/valid_before=<valid_before>]``
            ``[/last=<last>][/first=<first>]``
        :access: authorized users (ACL flag: ``voucher.get``)
        """
        resource = 'vouchers'
        if vid_encoded: resource += '/%s' % vid_encoded
        if uid_from: resource += '/from=%d' % int(uid_from)
        if uid_to: resource += '/to=%d' % int(uid_to)
        if gid: resource += '/gid=%s' % gid
        if valid_after: resource += '/valid_after=%s' % valid_after
        if valid_before: resource += '/valid_before=%s' % valid_before
        if first: resource += '/first=%d' % int(first)
        if last: resource += '/last=%d' % int(last)
        return self.request('get', resource)
    
    def get_vouchers_history(self, vid_encoded=None, vid=None, action=None,
                             uid_from=None, uid_to=None, gid=None,
                             valid_after=None, valid_before=None,
                             create_after=None, create_before=None,
                             last=None, first=None):
        """
        FETCHES a filtered list of vouchers log entries.
        
        :type vid_encoded: ``alphanumeric(64)``
        :param vid_encoded:
            Voucher ID, as a string with CRC.
        :type vid: ``bigint``
        :param vid:
            Voucher ID.
        :type action: ``string`` (add | use | revoke | expire)
        :param action:
            Filter only these actions on vouchers.
        :type uid_from: ``bigint``
        :param uid_from:
            Filter by source account UID.
        :type uid_to: ``bigint``
        :param uid_to:
            Filter by destination account UID.
        :type gid: ``alphanumeric(32)``
        :param gid:
            Filter by voucher Group ID. GID is localized to `uid_from`.
        :type valid_after: ``string``
        :param valid_after:
            Voucher has to be valid after this timestamp (in ISO 8601 basic
            format).
        :type valid_before: ``string``
        :param valid_before:
            Voucher was valid until this timestamp (in ISO 8601 basic format).
        :type create_after: ``string``
        :param create_after:
            Voucher has to be created after this timestamp (in ISO 8601 basic
            format).
        :type create_before: ``string``
        :param create_before:
            Voucher was created until this timestamp (in ISO 8601 basic format).
        :type last: ``bigint``
        :param last:
            The number of newest voucher entries (that satisfy all other
            criteria) to return.
        :type first: ``bigint``
        :param first:
            The number of oldest voucher entries (that satisfy all other
            criteria) to return.
        
        :note:
            If `first` or `last` are used, the vouchers list is sorted by time
            created, otherwise it is sorted alphabetically by `id`.
        
        :rtype: ``list``/``dict``
        :returns:
            A list of voucher log description dictionaries.
        :raises GeneralException:
        
        :resource:
            ``vouchers/history[/<vid_encoded>][/from=<uid_from>][/to=<uid_to>]``
            ``[/vid=<vid>][/action=<action>][/last=<last>][/first=<first>]``
            ``[/valid_after=<valid_after>][/valid_before=<valid_before>]``
            ``[/create_after=<create_after>][/create_before=<create_before>]``
            ``[/gid=<group_id>]``
        :access: authorized users (ACL flag: ``voucher.history``)
        """
        resource = 'vouchers/history'
        if vid_encoded: resource += '/%s' % vid_encoded
        if vid: resource += '/vid=%d' % long(vid)
        if action: resource += '/action=%s' % action
        if uid_from: resource += '/from=%d' % int(uid_from)
        if uid_to: resource += '/to=%d' % int(uid_to)
        if gid: resource += '/gid=%s' % gid
        if valid_after: resource += '/valid_after=%s' % valid_after
        if valid_before: resource += '/valid_before=%s' % valid_before
        if create_after: resource += '/create_after=%s' % create_after
        if create_before: resource += '/create_before=%s' % create_before
        if first: resource += '/first=%d' % int(first)
        if last: resource += '/last=%d' % int(last)
        return self.request('get', resource)
    
    def revoke_vouchers(self, vid_encoded=None,
                        uid_from=None, uid_to=None, gid=None,
                        valid_after=None, valid_before=None,
                        last=None, first=None):
        """
        REVOKES/INVALIDATES a filtered list of vouchers.
        
        :type vid_encoded: ``alphanumeric(64)``
        :param vid_encoded:
            Voucher ID, as a string with CRC.
        :type uid_from: ``bigint``
        :param uid_from:
            Filter by source account UID.
        :type uid_to: ``bigint``
        :param uid_to:
            Filter by destination account UID.
        :type gid: ``alphanumeric(32)``
        :param gid:
            Filter by voucher Group ID. GID is localized to `uid_from`.
        :type valid_after: ``string``
        :param valid_after:
            Voucher has to be valid after this timestamp (in ISO 8601 basic
            format).
        :type valid_before: ``string``
        :param valid_before:
            Voucher was valid until this timestamp (in ISO 8601 basic format).
        :type last: ``bigint``
        :param last:
            The number of newest vouchers (that satisfy all other criteria) to
            return.
        :type first: ``bigint``
        :param first:
            The number of oldest vouchers (that satisfy all other criteria) to
            return.
        
        :note:
            As with `get_vouchers`, filters are restrictive, narrowing down the
            set of vouchers, which initially includes complete voucher
            collection. That means, in turn, that a naive empty-handed
            `revoke_vouchers()` call shall revoke **all** un-used vouchers (both
            valid and expired)!
        
        :rtype: ``dict``
        :returns:
            A dictionary of successfully revoked vouchers, i.e. a map
            ``vid_encoded``: ``refund_transfer_id`` for all successfully revoked
            vouchers.
        :raises GeneralException:
        
        :resource:
            ``vouchers[/<vid_encoded>][/from=<uid_from>][/to=<uid_to>]``
            ``[/valid_after=<valid_after>][/valid_before=<valid_before>]``
            ``[/last=<last>][/first=<first>]``
        :access: authorized users (ACL flag: ``voucher.revoke``)
        """
        resource = 'vouchers'
        if vid_encoded: resource += '/%s' % vid_encoded
        if uid_from: resource += '/from=%d' % int(uid_from)
        if uid_to: resource += '/to=%d' % int(uid_to)
        if gid: resource += '/gid=%s' % gid
        if valid_after: resource += '/valid_after=%s' % valid_after
        if valid_before: resource += '/valid_before=%s' % valid_before
        if first: resource += '/first=%d' % int(first)
        if last: resource += '/last=%d' % int(last)
        return self.request('delete', resource, json.dumps({'revoke': True}))
