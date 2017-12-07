webresource
===========

Describe resources which should be delivered TTW.

Declare resources:

.. code-block:: python

    from webresource import css_resource
    from webresource import js_resource

    # javascripts

    # declare JS resource without dependencies
    js_resource(
        uid='jquery',
        source='assets/jquery.js',
        target='assets/jquery.min.js'
        compiler='minify'
    )

    # declare JS resource depending on another resource
    js_resource(
        uid='addon',
        depends='jquery',
        source='assets/addon.js',
        target='assets/addon.min.js'
        compiler='minify'
    )

    # declare JS resource depending on another resource ending up in the
    # dependency target file
    js_resource(
        uid='other',
        depends='addon',
        source='assets/other.js',
        compiler='minify'
    )

    # of course, a target might be specified, which ends up in a separate file
    # still considering the dependency tree
    js_resource(
        uid='nomerge',
        depends='addon',
        source='assets/nomerge.js',
        target='assets/nomerge.min.js'
        compiler='minify'
    )

    # stylesheets

    # declare CSS resource without dependency.
    # source and target are the same file.
    css_resource(
        uid='base',
        source='assets/base.css'
    )

    # declare CSS resource depending on another resource
    # source is a less file, can not be delivered without a compile step
    # generating the target CSS
    css_resource(
        uid='addon',
        depends='base',
        source='assets/addon.less',
        target='assets/addon.css'
        compiler='less'
    )

Define development and live mode:

.. code-block:: python

    from webresource import MODE_DEVELOPMENT
    from webresource import MODE_LIVE
    import webresource

    webresource.mode = MODE_DEVELOPMENT

Deliver resources:

.. code-block:: python

    from webresource import css
    from webresource import html

    js_markup = js.markup(debug=True)
    css_markup = css.markup(debug=True)

Dump definitons as JSON:

.. code-block:: python

    js_dump = js.dump(dialect=None)
    css_dump = css.dump()
