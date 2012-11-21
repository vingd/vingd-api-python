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
--------------------

Vingd API enables you to register Vingd objects you're selling, create Vingd
purchase orders, verify and commit Vingd purchases. You can also reward users,
either directly (in backend), or indirectly via Vingd vouchers. For detailed
docs and demos, see `docs.vingd.com`_.


Installation
------------

To install the last stable release of Vingd API: ::

   $ pip install vingd

Or, to install from GitHub source: ::

   $ git clone https://github.com/vingd/vingd-api-python
   $ cd vingd-api-python
   $ make env && source env/bin/activate   (skip if already in virtualenv)
   $ python setup.py install


Example Usage
-------------

.. code-block:: python

   from vingd import Vingd
   
   v = Vingd(username="<vingd-login-username>", password="<vingd-login-password>")
   
   balance = v.get_user_balance()
   print 'My balance is VINGD %.2f.' % (balance/100.0)
   
   vouchers = v.get_vouchers()
   print "I have %d active vouchers." % len(vouchers)

For more examples, see ``example/test.py`` in source.


.. _`Vingd`: http://www.vingd.com/
.. _`docs.vingd.com`: http://docs.vingd.com/