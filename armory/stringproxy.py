from __future__ import absolute_import, unicode_literals


class StringProxy(str):
    def __new__(cls, value, keymap=None, strict=False, override=False):
        return str.__new__(cls, value)

    def __init__(self, value, keymap=None, strict=False, override=False):
        if keymap and not override:
            for key in keymap:
                if hasattr(super(StringProxy, self), key):
                    raise ValueError((
                        'attribute name conflict:  cls.{0} <==> str.{0}'
                    ).format(key))
        self._key = value
        self._data_map = {}
        if keymap:
            self._data_map.update(keymap)
        self._strict_attrs = strict
        self._override = override

    def __getitem__(self, keyname):
        if isinstance(keyname, int):
            return super(StringProxy, self).__getitem__(keyname)
        if self._strict_attrs:
            return self._data_map[keyname]
        return self._data_map.get(keyname, keyname)

    def __getattr__(self, keyname):
        if keyname in self._data_map:
            return self._data_map[keyname]
        elif self._strict_attrs:
            return super(StringProxy, self).__getattr__(keyname)
        return keyname
