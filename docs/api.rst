.. _api:


Vingd API
=========

.. toctree::
   :maxdepth: 2


Overview of key functions
-------------------------

.. module:: vingd.Vingd
   :noindex:

Account related functions
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   get_user_profile
   get_user_balance

Vingd authorization ("selling access")
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   create_object
   create_order
   verify_purchase
   commit_purchase

Vingd rewarding
~~~~~~~~~~~~~~~

.. autosummary::
   create_voucher
   revoke_vouchers
   reward_user
   

Interface
---------

.. module:: vingd

.. autoclass:: Vingd
   :members:


Exceptions
----------

.. module:: vingd.exceptions

.. autoexception:: GeneralException
.. autoexception:: InvalidData
.. autoexception:: Forbidden
.. autoexception:: NotFound
.. autoexception:: InternalError
