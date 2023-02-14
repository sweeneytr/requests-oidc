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


Authorization Code Flow
+++++++++++++++++++++++

.. autofunction:: requests_oidc.make_oidc_session


.. autofunction:: requests_oidc.make_path_session


.. autofunction:: requests_oidc.make_os_cached_session

Client Credentials Flow
+++++++++++++++++++++++

.. autofunction:: requests_oidc.make_client_credentials_session