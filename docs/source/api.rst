API
===

Resource
--------

.. autoclass:: webresource::Resource
    :members: __init__, file_name, file_path, resource_url, render


ScriptResource
--------------

.. autoclass:: webresource::ScriptResource
    :show-inheritance:
    :members: __init__, render


LinkResource
------------

.. autoclass:: webresource::LinkResource
    :show-inheritance:
    :members: __init__, render


StyleResource
-------------

.. autoclass:: webresource::StyleResource
    :show-inheritance:
    :members: __init__


ResourceGroup
-------------

.. autoclass:: webresource::ResourceGroup
    :members: __init__, members, add


ResourceResolver
----------------

.. autoclass:: webresource::ResourceResolver
    :members: __init__, resolve


ResourceRenderer
----------------

.. autoclass:: webresource::ResourceRenderer
    :members: __init__, render


Exceptions
----------

.. autoclass:: webresource::ResourceConflictError

.. autoclass:: webresource::ResourceCircularDependencyError

.. autoclass:: webresource::ResourceMissingDependencyError
