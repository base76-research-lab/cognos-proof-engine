# Publishing CognOS SDK to PyPI

Quick guide to publish the SDK.

## Prerequisites

1. PyPI account: https://pypi.org/account/register/
2. Build tools:
   ```bash
   pip install build twine
   ```

## Steps

### 1. Create PyPI Account (One-time)

Visit https://pypi.org/account/register/ and create account.

### 2. Create `.pypirc` (One-time)

File: `~/.pypirc`

```ini
[distutils]
index-servers =
    pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Your API token from https://pypi.org/manage/account/
```

**Get token:** https://pypi.org/manage/account/tokens/

### 3. Build Package

```bash
cd cognos-sdk
python -m build
```

Creates `dist/cognos_sdk-0.1.0-py3-none-any.whl` and `dist/cognos_sdk-0.1.0.tar.gz`.

### 4. Publish to PyPI

```bash
python -m twine upload dist/*
```

### 5. Verify

```bash
pip install cognos-sdk
python -c "from cognos import CognosClient; print('✅ Installed')"
```

## Update Versions

To publish new version:

1. Update version in `setup.py` (e.g., `0.1.1`)
2. Rebuild: `python -m build`
3. Upload: `python -m twine upload dist/*`

## Troubleshooting

### "Invalid authentication"
- Check PyPI token is correct in `.pypirc`
- Token should start with `pypi-`

### "Filename already exists"
- Version already published
- Bump version number and rebuild

### "Missing setup.py"
- Make sure you're in `cognos-sdk/` directory

## PyPI Package Page

After publishing, view at: https://pypi.org/project/cognos-sdk/

---

**Done!** Users can now: `pip install cognos-sdk`
