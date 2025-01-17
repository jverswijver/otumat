# Otumat: Maintainer Tools & Utilities

Otumat (pronounced "Automate") is a suite of maintainer tools and utilities for pip packages.

The following features are currently supported.

## Usage Tracking

Have you ever wondered:

- How many users are actually using my Python package?
- How often are they using my Python package?
- Which features/methods are most used and which ones are less interesting to the community?
- Is there a better alternative to track and measure usage data than using anonymous download data available from PyPi's download logs in Google BigQuery? See [Analyzing PyPI Package Download](https://packaging.python.org/guides/analyzing-pypi-package-downloads/#background) for more details on this

Since a reasonable solution could not be found, I introduced this feature that provides the mechanism and building blocks to have usage tracking data as granular as you need it.

There are a few pre-requisites or assumptions:
- User clients will have at least some periodic internet connection to upload usage logs to a centralized, remote usage-data aggregating host
- 4 HTTP routes need to be implemented on your remote usage-data host
  1. `GET` GUI-based authenticated route to register package installations with a user. You may use it to collect consent, have your user complete a survey, etc.
  2. `POST` authenticated API route to accept the form submission of the above GUI route. An `installId` should be returned along with other details to ensure an 'open' connection.
  3. `POST` authenticated API route that accepts user's event data and will store in an medium of your choice.
  4. `POST` standard OAuth2.0 route that will allow refreshing `access_token`'s and `refresh_token`'s. [PKCE flow](https://auth0.com/docs/flows/authorization-code-flow-with-proof-key-for-code-exchange-pkce)) currently implemented).

Specific request/response details for the above 4 routes to follow soon.

Once your remote server is ready, simply add the following to your package:
- Include `otumat` as a `requirements` dependency
- In your `__init__.py`, intantiate an `UsageAgent` that your package can refer to. For example:
  ```python
  from otumat.usage import UsageAgent as _UsageAgent
  usage_agent = _UsageAgent(author='DataJoint',
                            data_directory='datajoint-python',
                            package_name=__name__,
                            host='https://datajoint.io',
                            install_route='/user/usage-install',
                            event_route='/api/usage-event',
                            refresh_route='/auth/token',
                            response_timeout=300,
                            upload_frequency='12h')
  ```
  Therefore, the first time your package is imported on the client's machine, it will trigger the usage tracking installation enrollment. User's will need to opt-in though the default is **not** to collect usage data.
- Log any interesting event within your package using the instantiated `UsageAgent`. For example, we can log imports by including the following also in our `__init__.py`:
  ```python
  usage_agent.log(event_type='import')
  ```
  Events will be buffered locally until the upload interval arrives. Caches are then unloaded. Daemon service runs cross-platform for Windows, MACOS, Linux and activates on startup.

Specific example of what an implemented flow looks like to follow soon.

### Disable Usage Tracking Registration

There are some cases where it is undesirable to have the usage tracking flow triggered. For instance, if you'd like to depend on a package (e.g. `datajoint`) which does have the usage tracking flow enabled but would rather not trigger it within your package. For such a case, you could do the following in your package's `__init__.py` before your first import from `datajoint`. It will effectively disable usage tracking checks, flows, and prompts in your package:

```python
import otumat as _otumat
_otumat.DISABLE_USAGE_TRACKING_PACKAGES = (['datajoint'] +
                                           _otumat.DISABLE_USAGE_TRACKING_PACKAGES)
# first import from package with usage tracking enabled
import datajoint
```

## Validation of Trusted Plugins

This package also includes a setuptools extension that provides new keyword arguments `privkey_path` and `pubkey_path`. 

By specifying the `privkey_path`, setuptools will generate the git hash (SHA1) of the module directory and sign the output based on the PEM key path passed in. The resulting signature will be stored as egg metadata `{{module_name}}.sig` accessible via `pkg_resources` module. 

If passing `pubkey_path`, this will simply be copied in as egg metadata `{{module_name}}.pub`.

This provides a solution to determining the 'trust-worthiness' of plugins or extensions that may be developed by the community for a given pip package if the public key file is available for the RSA keypair. The choice of what to do for failed verification is up to you.

### Use

#### Extensible Package e.g. `base`

``` python
setuptools.setup(
    ...
    setup_requires=['otumat'],
    pubkey_path='./pubkey.pem',
    ...
```

#### Plugin Package e.g. `plugin1`

``` python
setuptools.setup(
    ...
    setup_requires=['otumat'],
    privkey_path='~/keys/privkey.pem',
    ...
```

#### Verifying Contents

``` python
import pkg_resources
from pathlib import Path
from otumat import hash_pkg, verify

base_name = 'base'
plugin_name = 'plugin1'
base_meta = pkg_resources.get_distribution(base_name)
plugin_meta = pkg_resources.get_distribution(plugin_name)

data = hash_pkg(pkgpath=str(Path(plugin_meta.module_path, plugin_name)))
signature = plugin_meta.get_metadata('{}.sig'.format(plugin_name))
pubkey_path = str(Path(base_meta.egg_info, '{}.pub'.format(base_name)))

verify(pubkey_path=pubkey_path, data=data, signature=signature)
```


### Compatibility with `git` and `openssl` CLI

For reference, certificates may also be generated and verified using `git` and `openssl` by the following process:

#### Generate

``` shell
$ cd {{/path/to/local/repo/dir}}
$ git add . --all
$ GIT_HASH=$(git ls-files -s {{/pip/package/dir}} | git hash-object --stdin)
$ printf $GIT_HASH | openssl dgst -sha256 -sign {{/path/to/privkey/pem}} -out {{pip_package_name}}.sigbin -sigopt rsa_padding_mode:pss
$ openssl enc -base64 -in {{pip_package_name}}.sigbin -out {{pip_package_name}}.sig
$ rm {{pip_package_name}}.sigbin
$ git reset
```

#### Verify

``` shell
$ cd {{/path/to/local/repo/dir}}
$ git add . --all
$ GIT_HASH=$(git ls-files -s {{/pip/package/dir}} | git hash-object --stdin)
$ openssl enc -base64 -d -in {{pip_package_name}}.sig -out {{pip_package_name}}.sigbin
$ printf $GIT_HASH | openssl dgst -sha256 -verify {{/path/to/pubkey/pem}} -signature {{pip_package_name}}.sigbin -sigopt rsa_padding_mode:pss
$ rm {{pip_package_name}}.sigbin
$ git reset
```