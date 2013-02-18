Vingd
=====

`Vingd`_ enables users to pay with money or with time. Money goes directly to
publishers and time is monetized indirectly through interaction with brands,
content creation, loyalty, bringing new users, etc. As a result Vingd
dramatically increases monetization while keeping reach. Vingd's secret sauce
are mathematical models that are adapting to each user in order to extract as
much value as possible from their time.

We use vingds (think of it as "digital currency", points, or credits) to express
the value ("price") of intangible goods (such as TV streams or newspaper
articles), to reward users for their activity (time), or to authorize ("charge")
them access to digital goods.


Vingd API for Python
====================

Vingd API enables you to register Vingd objects you're selling, create Vingd
purchase orders, verify and commit Vingd purchases. You can also reward users,
either directly (in backend), or indirectly via Vingd vouchers. Detailed `docs`_
and `demos`_ are available.


Installation
============

To install the last stable release of Vingd API: ::

   $ pip install vingd

Or, to install from GitHub source: ::

   $ git clone https://github.com/vingd/vingd-api-python
   $ cd vingd-api-python
   $ make env && source env/bin/activate   (skip if already in virtualenv)
   $ python setup.py install


Examples
========

Client initialization and account balance fetching:

.. code-block:: python

    from vingd import Vingd
    
    VINGD_USERNAME = 'test@vingd.com'
    VINGD_PASSWORD = '123'
    
    # Initialize Vingd client.
    v = Vingd(username=VINGD_USERNAME, password=VINGD_PASSWORD,
              endpoint=Vingd.URL_ENDPOINT_SANDBOX, frontend=Vingd.URL_FRONTEND_SANDBOX)
    
    # Fetch user balance.
    balance = v.get_user_balance()

Sell content
------------

Wrap up Vingd order and redirect user to confirm his purchase at Vingd frontend:

.. code-block:: python

    # Selling details.
    OBJECT_NAME = "My test object"
    OBJECT_URL = "http://localhost:666/"
    ORDER_PRICE = 200 # VINGD 2.00
    ORDER_EXPIRES = datetime.now() + timedelta(days=1)
    
    # Register Vingd object (once per selling item).
    oid = v.create_object(OBJECT_NAME, OBJECT_URL)
    
    # Prepare Vingd order.
    order = v.create_order(oid, ORDER_PRICE, ORDER_EXPIRES)
    
    # Order ready, redirect user to confirm his purchase at Vingd frontend.
    redirect_url = order['urls']['redirect']

As user confirms his purchase on Vingd frontend he is redirected back to object URL
expanded with purchase verification parameters.
    
.. code-block:: python

    # User confirmed purchase on Vingd frontend and came back to http://localhost:666/?oid=<oid>&tid=<tid>

    # Verify purchase with received parameters.
    purchase = v.verify_purchase(oid, tid)

    # Purchase successfully verified, serve purchased content to user.
    # ... content serving ...
    
    # Content is successfully served, commit Vingd transaction.
    commit = v.commit_purchase(purchase['purchaseid'], purchase['transferid'])

Reward user
-----------

Reward user with vingd:

.. code-block:: python

    # Vingd hashed user id, as obtained in purchase procedure (previous example).
    REWARD_HUID = purchase['huid']
    REWARD_AMOUNT = 75 # VINGD 0.75
    REWARD_DESCRIPTION = "Testing direct rewarding"
    
    # Reward user.
    reward = v.reward_user(REWARD_HUID, REWARD_AMOUNT, REWARD_DESCRIPTION)
    
For more examples, see `example/test.py`_ in source.


Documentation
=============

Automatically generated documentation for latest stable version is available on:
https://vingd-api-for-python.readthedocs.org/en/latest/.


Copyright and License
=====================

Vingd API is Copyright (c) 2012 Vingd, Inc and licensed under the MIT license.
See the LICENSE file for full details.


.. _`Vingd`: http://www.vingd.com/
.. _`docs`: https://vingd-api-for-python.readthedocs.org/en/latest/
.. _`demos`: http://docs.vingd.com/
.. _`example/test.py`: https://github.com/vingd/vingd-api-python/blob/master/example/test.py