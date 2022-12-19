Overview
========

Declaring resources
-------------------

Webresource provides 3 types of resources. ``ScriptResource`` is used for
registering Javascript, ``StyleResource`` for CSS files and ``LinkResource``
can be used for registering all sorts of resource links.

Declare a script:

.. code-block:: python

    import webresource as wr

    my_js = wr.ScriptResource(
        name='my_js',
        directory='/path/to/scripts',
        resource='my.js',
        compressed='my.min.js',
        path='js'
    )

``name`` is a unique identifier for the resource. ``directory`` defines the
location in the file system where the resource can be found. ``resource`` is
the default resource file corresponding to this declaration. ``compressed`` is
the minified version of the resource, which gets considered if Webresource
is used in production mode. ``path`` defines the path part of the URL at which
this resource is published.

Dependencies between resources are defined by passing ``depends`` argument,
which can be a single dependency or multiple dependencies as tuple or list:

.. code-block:: python

    other_js = wr.ScriptResource(
        name='other_js',
        depends='my_js',
        ...
    )

It's possible to pass a callback funtion as ``include`` argument. It can be
used to calculate whether a resource should be included or not:

.. code-block:: python

    def include_conditional_js():
        # Compute whether to include resource here.
        return True

    conditional_js = wr.ScriptResource(
        name='conditional_js',
        include=include_conditional_js,
        ...
    )

The ``include`` property can also be set as boolean which might be useful for
excluding some already registered resources:

.. code-block:: python

    conditional_js.include = False

Resource URLs can be rendered including a unique key of the resource file.
This is useful in environments with strong caching to make sure changed
resources get reloaded properly. When working with unique resource URLs, the
unique key gets rendered intermediate between path and file name, thus the
integrator needs to implement custom URL rewriting/dispatching/traversal for
correct resource delivery:

.. code-block:: python

    cached_js = wr.ScriptResource(
        name='cached_js',
        unique=True,
        unique_prefix='++webresource++',
        ...
    )

If external resources should be declared, pass ``url`` argument. In this case
``path``, ``resource`` and ``compressed`` get ignored:

.. code-block:: python

    external_js = wr.ScriptResource(
        name='external_js',
        url='https://example.org/resource.js'
        ...
    )

It is possible to render additional attributes on resource tags by passing
additional keyword arguments to the constructor. This can be usefule when
working with web compilers like Diazo.

.. code-block:: python

    custom_attr_js = wr.ScriptResource(
        name='custom_attr_js',
        **{'data-bundle': 'bundle-name'}
    )

This examples uses ``ScriptResource`` but the above described behavior applies
to all provided Resource types.


Resource groups
---------------

Resources can be grouped by adding them to ``ResourceGroup`` objects:

.. code-block:: python

    scripts = wr.ResourceGroup(name='scripts')

Resources can be added to a group at instantiation time if group is known in
advance.

.. code-block:: python

    script = wr.ScriptResource(
        name='script',
        group=scripts
        ...
    )

or an already declared resource can be added to a group:

.. code-block:: python

    scripts.add(script)

Groups can be nested:

.. code-block:: python

    scripts = wr.ResourceGroup(name='scripts')
    base_scripts = wr.ResourceGroup(
        name='base_scripts',
        group=scripts
    )
    addon_scripts = wr.ResourceGroup(
        name='addon_scripts',
        group=scripts
    )

A group can define the default ``path`` for its members. It is taken unless
a contained group member defines a path on its own:

.. code-block:: python

    scripts = wr.ResourceGroup(name='scripts', path='js')

Same applies for the resource ``directory``. If defined on a resource group,
is taken unless a contained member overrides it.

.. code-block:: python

    scripts = wr.ResourceGroup(name='scripts', directory='/path/to/scripts')

To control whether an entire group should be included, define an ``include``
callback funtion or flag.

.. code-block:: python

    def include_group():
        # Compute whether to include resource group here.
        return True

    group = wr.ResourceGroup(
        name='group',
        include=include_group,
        ...
    )


Deliver resources
-----------------

Webresource not provides any mechanism to publish the declared resources.
It's up to the user to make the resources in the defined directories available
to the browser at the defined paths.

But it provides a renderer for the resulting resource HTML tags.

First a ``ResourceResolver`` needs to be created knowing about the resources to
deliver. ``members`` can be an instance or list of resources or resource groups.

The ``ResourceRenderer`` then is used to create the markup.

The ``GracefulResourceRenderer`` creates the markup, but does not fail if one
resource is invalid. It logs an error and places a comment about the failure
instead of a HTML-tag.

A complete example:

.. code-block:: python

    import webresource as wr

    icon = wr.LinkResource(
        name='icon',
        resource='icon.png',
        rel='icon',
        type_='image/png'
    )

    css = wr.StyleResource(name='css', resource='styles.css')

    ext_css = wr.StyleResource(
        name='ext_css',
        url='https://ext.org/styles.css'
    )

    script = wr.ScriptResource(
        name='script',
        resource='script.js',
        compressed='script.min.js'
    )

    resources = wr.ResourceGroup(name='resources', path='res')
    resources.add(icon)
    resources.add(css)
    resources.add(ext_css)
    resources.add(script)

    resolver = wr.ResourceResolver(resources)
    renderer = wr.ResourceRenderer(resolver, base_url='https://tld.org')

    rendered = renderer.render()

``rendered`` results in:

.. code-block:: html

    <link href="https://tld.org/res/icon.png"
          rel="icon" type="image/png" />
    <link href="https://tld.org/res/styles.css" media="all"
          rel="stylesheet" type="text/css" />
    <link href="https://ext.org/styles.css" media="all"
          rel="stylesheet" type="text/css" />
    <script src="https://tld.org/res/script.min.js"></script>


Debugging
---------

To prevent Webresource generating links to the compressed versions of
declared resources, ``development`` flag of the config singleton needs to be
set:

.. code-block:: python

    wr.config.development = True
