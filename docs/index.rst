.. Requests-OIDC documentation master file, created by
   sphinx-quickstart on Tue Jan 10 13:14:17 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Requests-OIDC's documentation!
=========================================

.. sidebar-links::
   :caption: Project Links:
   :github:
   :pypi: requests-oidc

.. include:: ../README.rst
  :start-after: inclusion-marker-do-not-remove

.. automodule:: requests_oidc

Flows
-----

.. autofunction:: make_auth_code_session

.. autofunction:: make_device_code_session

.. autofunction:: make_client_credentials_session

.. autofunction:: make_token_session


Plugins
-------

.. automodule:: requests_oidc.plugins

.. autoclass:: PathPlugin

.. autoclass:: OSCachedPlugin
