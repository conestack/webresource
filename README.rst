webresource
===========

Register, compile and deliver web resources for your application.


Features
--------

- Register web resources via python.

- Manage dependencies between resources.

- Grouping of resources.

- Provide a develoment and a production mode, delivering resources uncompressed
  for debugging or compressed.


Overview
---------

.. code-block:: python

    from webresource import resource_group
    from webresource import js_resource
    from webresource import css_resource

    base_js = resource_group(name='base_js', merge=False)

    jquery = js_resource(
        name='jquery',
        directory='my.pkg:static',
        path='static',
        resource='jquery.js',
        compressed='jquery.min.js',
        group=base_js
    )
    bootstrap_js = js_resource(
        name='bootstrap',
        basepath='static',
        resource='bootstrap.js',
        compressed='bootstrap.min.js',
        group=base_js
    )
    app_js = js_resource(
        name='app',
        basepath='static',
        resource='app.js',
        depends='jquery',
        group='base_js
    )

Two types of resources are available. Javascript resources and CSS resources.
They get registered via ``js_resource`` repective ``css_resource``:

.. code-block:: python

    from webresource import css_resource
    from webresource import js_resource


Declare dependencies
~~~~~~~~~~~~~~~~~~~~

Resources have unique identifiers which are used for dependency graph building
and must be unique inside the related registry (CSS/JS):

.. code-block:: python

    js_resource(
        uid='my_app',
        source='app.js',
    )
    js_resource(
        uid='my_addon',
        depends='my_app',
        source='addon.js',
    )
    css_resource(
        uid='my_app',
        source='app.css',
    )

Resources may depend on multiple other resources:

.. code-block:: python

    js_resource(
        uid='other_js',
        depends=['my_app', 'my_addon'],
        source='addon.js',
    )

Just in case you want do do something with it, ``js_resource`` and
``css_resource`` return the already created registered resource instance:

.. code-block:: python

    res = js_resource(
        uid='myjs',
        source='my.js',
    )

It's not necessarily needed to explicitely define all single resource
dependencies if some JS side mechanisam like ``require.js`` is used for solving
dependencies. In such a case, you just need to make sure require.js gets
delivered before the actual other resources, thus depending the subsequent
resources to ``require.js`` only:

.. code-block:: python

    js_resource(
        uid='requirejs',
        source='require.js'
    )
    js_resource(
        uid='app',
        depends='requirejs',
        source='app.js'
    )
    js_resource(
        uid='addon',
        depends='requirejs',
        source='addon.js'
    )


Resource groups
~~~~~~~~~~~~~~~

An additional concept in this package is the use of resource groups. It's used
to group several resources by some semantic meaning.

A usecase for resource groups is to declare dependencies in addons, which
should not be delivered in some circumstances:

.. code-block:: python

    from webresource import ResourceGroup

    deps = ResourceGroup(uid='deps')
    js_resource(
        uid='jquery',
        source='jquery.js'
        group='deps'
    )
    js_resource(
        uid='jqueryui',
        depends='jquery',
        source='jqueryui.js'
        group='deps'
    )
    js_resource(
        uid='app',
        depends='jqueryui'
        source='app.js'
    )

    # in a dev environ we are fine to deliver dependencies defined in deps
    # group but in an app integration these resources might have already been
    # delivered from somewhere else
    deps.skip = True

Another usecase is to provide different flavors of the same resources, like
different integration stylesheets into different frameworks:

.. code-block:: python

    plone_css = ResourceGroup(uid='plone_css', skip=True)
    css_resource(
        uid='appcss',
        source='app_plone.css',
        group='plone_css'
    )

    bootstrap_css = ResourceGroup(uid='bootstrap_css', skip=True)
    css_resource(
        uid='appcss',
        source='app_bootstrap.css',
        group='bootstrap_css'
    )

    # now enable the one or the other resource group depending on the framework
    # we're running in
    bootstrap_css.skip = False
