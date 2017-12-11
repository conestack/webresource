===========
webresource
===========

Register, compile and deliver web resources for your application.


Features
========

- Register web resources via python.

- Manage dependencies between resources via unique identifiers.

- Grouping of resources to be able to selectively skip delivering of some
  resources.

- Compile resources in-place or to bundles.

- Provide delegating compilation to external tools, e.g. webpack.

- Provide a develoment mode for debugging, delivering resources uncompiled and
  unbundled.

- Provide hooking resources from the outside, thus supporting any kind of addon
  mechanism.


Register resources
==================

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


Declare targets
~~~~~~~~~~~~~~~

Resources may be merged into bundles. This happens by declaring targets.
For building a bundle, the entry resource needs to get a file name as target,
while resources which should end up in the same file must declare the entry
resource uid as target:

.. code-block:: python

    js_resource(
        uid='app',
        source='app.js',
        target='bundle.js'
    )
    js_resource(
        uid='addon',
        depends='app',
        source='addon.js',
        target='uid:app'
    )

Please not that dependencies and targets are orthogonal concepts. Dependencies
only describe which resources a specific other resource depends on (aka the
delivery order) while target defines the location the resource lives (aka the
target bundle). Of course it's possible to define conflicts this way when
registering resources, but the compiler will tell you if you try something
nasty.


Use a compiler
~~~~~~~~~~~~~~

Targets are also needed if a single resource not ends up in a bundle but is
compiled in some way, like a less compiler for CSS or javascript minification:

.. code-block:: python

    js_resource(
        uid='app',
        source='app.js',
        target='app.min.js',
        compiler='slimit'
    )
    css_resource(
        uid='app',
        source='app.less',
        target='app.css',
        compiler='lesscpy'
    )

Of course also compiled resources might end up in a bundle:

.. code-block:: python

    js_resource(
        uid='app',
        source='app.js',
        target='bundle.js',
        compiler='slimit'
    )
    js_resource(
        uid='addon',
        source='addon.js',
        target='uid:app',
        compiler='slimit'
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


Compile resources
-----------------

XXX


Deliver resources
-----------------

XXX
