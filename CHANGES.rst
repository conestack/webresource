Changelog
=========

1.0b8 (unreleased)
------------------

- No changes yet.


1.0b7 (2021-08-16)
------------------

- Add auto integrity hash calculation on ``ScriptResource``.

- Add ``hash_`` and ``hash_algorithm`` keyword arguments to ``Resource``,
  ``ScriptResource``, ``LinkResource`` and ``FileResource``.

- Add ``Resource.file_hash`` property.

- Add ``Resource.file_data`` property.


1.0b6 (2021-08-10)
------------------

- Raise explicit ``ResourceError`` instead of generic ``ValueError``.


1.0b5 (2021-08-09)
------------------

- Make ``Resource.directory`` a R/W property.


1.0b4 (2021-08-08)
------------------

- Change ``path`` cascading behavior. Path set on ``ResourceGroup`` always takes
  precedence over its members paths.

- ``include`` property of ``Resource`` and ``ResourceGroup`` can be set from
  outside.


1.0b3 (2021-08-06)
------------------

- Add remaining missing rst files to release.


1.0b2 (2021-08-06)
------------------

- Add missing ``docs/source/overview.rst`` to release.


1.0b1 (2021-08-06)
------------------

- Initial release.
