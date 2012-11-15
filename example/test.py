#!/usr/bin/env python

# path hack
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from vingd import Vingd
from datetime import datetime, timedelta

# sandbox backend:
v = Vingd(username="test@knopso.com", password="123", endpoint="https://api.vingd.com/sandbox/broker/v1/", frontend="http://www.sandbox.vingd.com/")

# in production use:
#v = Vingd(username="<vingd-login-username>", password="<vingd-login-password>")

#
# profile/account
#

profile = v.get_user_profile()
print 'I (%s) registered on %s.' % (profile['name'], profile['timestamp_created'])

balance = v.get_user_balance()
print 'My balance is VINGD %.2f.' % (balance/100.0)

#
# voucher rewarding
#

voucher = v.create_voucher(amount=100, expires=datetime.now()+timedelta(days=7))
print "I'm rewarding you with this 1 vingd voucher (%s): %s." % (voucher['raw']['vid_encoded'], voucher['urls']['redirect'])

vouchers = v.get_vouchers()
print "Now I have %d active vouchers." % len(vouchers)

used = v.get_vouchers_history(action='use')
print "Also, %d of my vouchers have been redeemed." % len(used)

expired = v.get_vouchers_history(action='expire')
print "And, %d of my vouchers have expired before anybody used them." % len(expired)

#
# selling
#

oid = v.create_object("My test object", "http://localhost:666/")
print "I've just created an object, just for you. OID is %d." % oid

oid2 = v.update_object(oid, "New object name", "http://localhost:777/")
print "Object updated."

object = v.get_object(oid)
print "Object last modified at %s, new url is %s" % (object['timestamp_created'], object['description']['url'])

objects = v.get_objects()
print 'I have %d active objects.' % len(objects)

order = v.create_order(oid, 200, datetime.now()+timedelta(days=1))
print "I've also created an order (id=%d) for the object (oid=%d): %s" % (order['id'], order['object']['id'], order['urls']['redirect'])

tid = raw_input("After you buy it, enter the Token ID here: ")
purchase = v.purchase_verify(oid, tid)
huid_buyer = purchase['huid']
print "Purchase verified (buyer's HUID = %s)." % huid_buyer

commit = v.purchase_commit(purchase['purchaseid'], purchase['transferid'])
print "Content served, and purchase committed."

#
# direct rewarding
#

reward = v.reward_user(huid_to=huid_buyer, amount=75, description='Testing direct rewarding')
print "User rewarded (transfer id = %s)." % reward['transfer_id']
