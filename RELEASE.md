# Release Process

This document describes the automated release process for webresource.

## Overview

The project uses an automated GitHub Actions workflow for building, testing, and publishing packages to PyPI. Version numbers are automatically determined from git tags using `hatch-vcs`.

## Prerequisites

### GitHub Environment Configuration

Before your first release, ensure the following GitHub environments are configured in the repository settings:

1. **release-test-pypi** - For publishing to Test PyPI
2. **release-pypi** - For publishing to production PyPI

### PyPI Trusted Publishing (Recommended)

Configure Trusted Publishing on both PyPI and Test PyPI:

1. Go to https://test.pypi.org/manage/account/publishing/ (for Test PyPI)
2. Go to https://pypi.org/manage/account/publishing/ (for production PyPI)
3. Add a new trusted publisher with:
   - **PyPI Project Name**: `webresource`
   - **Owner**: `conestack`
   - **Repository name**: `webresource`
   - **Workflow name**: `release.yml`
   - **Environment name**: `release-test-pypi` (or `release-pypi` for production)

This eliminates the need for API tokens and is more secure.

## Release Types

### Development Releases (Automatic)

**Trigger**: Every push to the `master` branch

**What happens**:
1. All tests, linting, and type checks run
2. Package is built and verified with attestation
3. Package is automatically published to **Test PyPI**

**Version format**: `X.Y.devN+gCOMMITHASH` (e.g., `1.3.dev42+g1a2b3c4`)

**Purpose**: Allows testing of the package installation process before making a production release

**Test installation**:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ webresource
```

### Production Releases (Manual)

**Trigger**: Creating a GitHub Release

**What happens**:
1. All tests, linting, and type checks run
2. Package is built and verified with attestation
3. Package is automatically published to **production PyPI**

**Version format**: `X.Y.Z` (e.g., `1.3.0`)

## How to Create a Production Release

### Step 1: Update CHANGES.rst

Before creating a release, ensure `CHANGES.rst` has a section for the new version:

```rst
1.3.0 (2025-01-15)
------------------

- Feature: Added support for new feature X
- Fix: Fixed bug Y
- Update: Improved documentation
```

Commit and push this change to master:

```bash
git add CHANGES.rst
git commit -m "Prepare release 1.3.0"
git push origin master
```

Wait for the CI to pass and verify the dev package on Test PyPI if needed.

### Step 2: Create a GitHub Release

1. Go to https://github.com/conestack/webresource/releases/new
2. Click "Choose a tag"
3. Type the new version number with a `v` prefix (e.g., `v1.3.0`)
4. Click "Create new tag: v1.3.0 on publish"
5. Set the release title to the same version (e.g., `v1.3.0`)
6. In the description, add release notes (can copy from CHANGES.rst)
7. Click "Publish release"

### Step 3: Automated Process

Once you publish the release, GitHub Actions will automatically:

1. Run all quality checks (tests, lint, typecheck) on Python 3.10-3.14 and all OS platforms
2. Build the package with build provenance attestation
3. Publish to production PyPI

**Monitor the workflow**: https://github.com/conestack/webresource/actions

### Step 4: Verify the Release

After the workflow completes successfully:

1. Check PyPI: https://pypi.org/project/webresource/
2. Test installation:
```bash
pip install --upgrade webresource
python -c "import webresource; print(webresource.__version__)"
```

### Step 5: Update to Next Dev Version (Optional)

If you want to explicitly mark the start of new development:

```bash
git pull origin master  # Get the tag
# Edit CHANGES.rst to add a new section like "1.4.0 (unreleased)"
git add CHANGES.rst
git commit -m "Back to development: 1.4.0"
git push origin master
```

Note: This step is optional since hatch-vcs automatically handles dev versions.

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR version** (X.0.0): Incompatible API changes
- **MINOR version** (0.X.0): New functionality in a backwards compatible manner
- **PATCH version** (0.0.X): Backwards compatible bug fixes

### Version Examples

- `1.3.0` - Production release
- `1.3.dev42+g1a2b3c4` - Development version (42 commits after v1.2.0)
- `2.0.0b1` - Beta release (create tag like `v2.0.0b1`)
- `2.0.0rc1` - Release candidate (create tag like `v2.0.0rc1`)

## Troubleshooting

### Release Workflow Failed

1. Check the GitHub Actions log: https://github.com/conestack/webresource/actions
2. Common issues:
   - **Tests failed**: Fix the failing tests and push to master, then recreate the release
   - **PyPI publish failed**: Check if the version already exists on PyPI (versions are immutable)
   - **Permission denied**: Ensure Trusted Publishing is configured correctly

### Version Not Updating

If you see the old version after creating a release:

1. Ensure the tag was created (check: https://github.com/conestack/webresource/tags)
2. Verify `hatch-vcs` is installed: `pip install hatch-vcs`
3. Check that `.git` directory exists (hatch-vcs reads from git)
4. For development installs, use: `pip install -e .` (not `pip install -e .[test]` from old setup.py)

### Rollback a Release

You **cannot** delete or modify a release on PyPI once published. If you need to fix a broken release:

1. Fix the issue in master
2. Create a new patch release (e.g., if v1.3.0 is broken, release v1.3.1)

## Migration from zest.releaser

This project previously used `zest.releaser` for manual releases. Key differences:

| Aspect | Old (zest.releaser) | New (GitHub Releases) |
|--------|---------------------|----------------------|
| Process | Manual command: `fullrelease` | Create GitHub Release |
| Version management | Hardcoded in setup.cfg | Automatic from git tags |
| PyPI upload | Manual or via zest.releaser | Automatic via GitHub Actions |
| Testing | Local only | Full CI/CD matrix (all Python versions & OS) |
| Verification | Manual | Automated with attestation |

The `tool.zest-releaser` section in `pyproject.toml` is kept for backward compatibility but is no longer used.

## Continuous Integration

### On Every Push

All pushes trigger:
- **Tests**: Python 3.10-3.14 on Ubuntu, macOS, and Windows
- **Lint**: Code quality checks with ruff and isort
- **Typecheck**: Static type checking with mypy
- **Docs**: Documentation build (deployed on manual trigger)
- **Coverage**: 100% coverage requirement with HTML report artifacts

### On Master Branch Push

Additionally publishes development version to Test PyPI.

### On GitHub Release

Additionally publishes production version to PyPI.

## Additional Resources

- [GitHub Actions Workflows](.github/workflows/)
- [hatch-vcs Documentation](https://github.com/ofek/hatch-vcs)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Semantic Versioning](https://semver.org/)
