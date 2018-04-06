
# Python 2.3+ and Python 3+ compatible namespace package
# https://packaging.python.org/guides/packaging-namespace-packages/
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
