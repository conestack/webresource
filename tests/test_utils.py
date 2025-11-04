# -*- coding: utf-8 -*-
"""Shared test utilities for webresource tests."""
import os
import shutil
import tempfile


def temp_directory(fn):
    """Decorator that provides a temporary directory to test functions."""
    def wrapper(*a, **kw):
        tempdir = tempfile.mkdtemp()
        kw['tempdir'] = tempdir
        try:
            fn(*a, **kw)
        finally:
            shutil.rmtree(tempdir)
    return wrapper


def np(path):
    """Normalize path for cross-platform compatibility."""
    return path.replace('/', os.path.sep)
