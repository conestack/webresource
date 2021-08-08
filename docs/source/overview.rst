Overview
========

Declaring resources
-------------------

``webresource`` provides 3 types of resources. ``ScriptResource`` is used for
registering Javascript, ``StyleResource`` for CSS files and ``LinkResource``
can be used for registering all sorts of resource links.

Declare a script:

.. code-block:: python

    import webresource as wr

    my_js = wr.ScriptResource(
        name='my_js',
        directory='./bundle',
        resource='my.js',
        compressed='my.min.js',
        path='js'
    )

``name`` is a unique identifier for the resource. ``directory`` defines the
location in the file system where the resource can be found. ``resource`` is
the default resource file corresponding to this declaration. ``compressed`` is
the minified version of the resource, which gets considered if ``webresource``
is used in production mode. ``path`` defines the path part of the URL at which
this resource is published.

Dependencies between resources are defined by passing ``depends`` argument:

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

If external resources should be declared, pass ``url`` argument. In this case
``path``, ``resource`` and ``compressed`` get ignored:

.. code-block:: python

    external_js = wr.ScriptResource(
        name='external_js',
        url='https://example.org/resource.js'
        ...
    )

This examples uses ``ScriptResource`` but the above described behavior applies
to all provided Resource types.


Resource groups
---------------

Resources can be grouped by adding them to ``ResourceGroup`` objects:

.. code-block:: python

    scripts = wr.ResourceGroup(name='scripts')

Resources can be added to a group at instanciation time if group is known in
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

A group can be used to define the path for all members. The
group path takes precedence over its members paths:

.. code-block:: python

    scripts = wr.ResourceGroup(name='scripts', path='js')


Deliver resources
-----------------

``webresource`` not provides any mechanism to publish the declared resources.
It's up to the user to make the resources in the defined directories available
to the browser at the defined paths.

But it provides a renderer for the resulting resource HTML tags.

First a ``ResourceResolver`` needs to be created knowing about the resources to
deliver. ``members`` can be an instance or list of resources or resource groups

The ``ResourceRenderer`` then is used to create the markup.

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
        'ext_css',
        url='https://ext.org/styles.css'
    )

    script = wr.ScriptResource(
        'script',
        resource='script.js',
        compressed='script.min.js'
    )

    resources = wr.ResourceGroup('resources', path='res')
    resources.add(icon)
    resources.add(css)
    resources.add(ext_css)
    resources.add(script)

    resolver = wr.ResourceResolver(resources)
    renderer = wr.ResourceRenderer(
        resolver,
        base_url='https://example.com'
    )

    rendered = renderer.render()

``rendered`` results in:

.. code-block:: html

    <link href="https://example.com/res/icon.png"
          rel="icon" type="image/png" />
    <link href="https://example.com/res/styles.css" media="all"
          rel="stylesheet" type="text/css" />
    <link href="https://ext.org/styles.css" media="all"
          rel="stylesheet" type="text/css" />
    <script src="https://example.com/res/script.min.js"></script>


Debugging
---------

To prevent ``webresource`` generating links to the compressed versions of
declared resources, ``development`` flag of the config singletion needs to be
set:

.. code-block:: python

    wr.config.development = True
