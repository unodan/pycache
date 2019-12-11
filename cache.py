########################################################################################################################
#    File: cache.py
#  Author: Dan Huckson, https://github.com/unodan
#    Date: 2019-09-07
# Version: 1.1.0
########################################################################################################################

from os import path, makedirs
from json import load, dump
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location


def uri2dict(uri, *args, **kwargs):
    _args = args[0] if args else kwargs

    uri = uri.split('/')
    uri.reverse()
    items = {}
    for idx, item in enumerate(uri):
        items = {item: items} if idx else {item: _args}

    return items


class Cache:
    def __init__(self, *args, **kwargs):
        self.nodes = {}
        _args = args[0] if args else kwargs

        if _args and isinstance(_args, dict):
            key = next(iter(_args.keys()))
            if '/' in key:
                self.set(key, next(iter(_args.values())))
            else:
                self.nodes = _args

        elif isinstance(_args, str):
            kwargs = args[1] if len(args) > 1 else kwargs
            if isinstance(kwargs, dict):
                self.nodes = deepcopy(uri2dict(_args, **kwargs))
            else:
                self.nodes = deepcopy(uri2dict(args[0], args[1]))

        self.indent = '.'

    def __eq__(self, other):
        if self.nodes == other.nodes:
            return True
        return False

    def __ne__(self, other):
        if not isinstance(other, Cache):
            return

        if self.nodes != other.nodes:
            return True
        return False

    def __str__(self):
        return str(self.nodes.items())

    def __repr__(self):
        data = "**{'key': 'value'}"
        return f"{self.__class__.__name__}({data})"

    def get(self, uri=None, default=None):
        if not uri:
            return self.nodes

        def walk(_uri, nodes):
            parts = _uri.split('/', 1)
            key = parts.pop(0)

            if key in nodes:
                node = nodes[key]
                if not parts:
                    return node
                else:
                    return walk(parts[0], node)
            return default
        return walk(uri, self.nodes)

    def set(self, *args, **kwargs):
        data = args[0] if args else kwargs

        if isinstance(data, dict):
            uri = next(iter(data.keys()))
            data = next((iter(data.values())))
        elif not isinstance(data, str):
            return
        else:
            uri = args[0]
            data = {}
            if len(args) > 1:
                data = args[1]
            elif kwargs:
                data = kwargs

        nodes = self.nodes
        parts = uri.strip("/").split("/")

        while parts:
            item = parts.pop(0)

            if item in nodes and not isinstance(nodes[item], dict):
                if isinstance(data, dict):
                    nodes[item] = uri2dict(uri.split(item).pop().strip("/"), data)
                else:
                    nodes[item] = data
                return

            if item in nodes:
                nodes = nodes[item]
            else:
                if isinstance(nodes, dict):
                    _parts = uri.split(item)
                    _uri = _parts.pop()
                    if _uri:
                        data = uri2dict(_uri.strip("/"), data)
                    nodes[item] = data
                return

        if isinstance(nodes, dict) and isinstance(data, dict):
            nodes.update(**data)
        else:
            parts = uri.split("/")
            nodes = self.nodes
            while parts:
                item = parts.pop(0)
                if parts:
                    nodes = nodes[item]
                else:
                    nodes[item] = data

    def copy(self):
        return Cache(**deepcopy(self.nodes))

    def keys(self):
        return list(self.nodes.keys())

    def save(self, file=None):
        if file:
            dirname = path.dirname(file)

            if dirname and not path.exists(dirname):
                makedirs(dirname)

            with open(file, 'w') as f:
                dump(self.nodes, f, indent=3)

    def load(self, file=None):
        file_type = path.splitext(file)[1].lstrip('.').lower()

        if file_type == 'py' and path.exists(file):
            spec = spec_from_file_location("module.name", file)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            self.nodes = module.config

        if file_type == 'json' and path.exists(file):
            with open(file) as f:
                self.nodes = load(f)

        return self

    def dump(self, indent=None):
        """ Dumps the contents of the cache to the screen.
        The output from dump goes stdout and is used to view the cache contents.
        Default indentation is a dot for each level.
        :param indent:
            indent (str): String to be use for indenting levels.
        :return:
            Nothing.
        """
        indent = indent if indent else '.'

        print('-------------------------------------------------------------------------------------------------------')
        print('id =', id(self), '\nnodes =', self)
        if self.nodes:
            def walk(_cfg, count):
                count += 1
                for key, value in _cfg.items():
                    if isinstance(value, dict):
                        item = '' if value else '{}'
                        print(indent * count, key, item)
                        walk(value, count)
                    else:
                        if isinstance(value, str):
                            value = f'"{value}"'
                        print(indent * count, key, f'value={value}')
            walk(self.nodes, 0)
        else:
            print(' (No Data)')

        print('-------------------------------------------------------------------------------------------------------')

    def merge(self, src):

        def recursive_update(d1, d2):
            """Updates recursively the dictionary values of d1"""

            for key, value in d2.items():
                if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                    recursive_update(d1[key], value)
                else:
                    d1[key] = value

        recursive_update(self.get(), src.get())

    def remove(self, uri):
        """ Remove entree from cache.
            Removes an entree from the cache if it exists.
        :param uri:
            uri (str): URI that points to the entree to remove.
        :return:
            Nothing.
        """

        uri = uri.strip('/')
        if self.exists(uri):
            parts = uri.rsplit("/", 1)
            if len(parts) == 1:
                self.nodes.pop(parts[0])
            else:
                node = self.get(parts[0])
                node.pop(parts[1], None)

    def exists(self, uri):
        """ Test if URI exists in the cache.
        :param uri:
            uri (str): URI that points to the entree to find.
        :return:
            True or False
        """
        nodes = self.nodes
        parts = uri.strip("/").split("/")
        while parts:
            item = parts.pop(0)
            if item in nodes:
                nodes = nodes[item]
            else:
                return False
        return True

    def destroy(self):
        """ Destroy cache.
            Deletes all entries in the cache.
        :return:
            Nothing.
        """
        del self.nodes
        self.nodes = {}

    def has_nodes(self, uri=''):
        """ Has nodes in cache.
            Test if any nodes exists at the given uri location.
        :return:
            True or False
        """
        if self.get_nodes(uri):
            return True
        return False

    def get_nodes(self, uri):
        """ Get nodes in cache.
            Gets nodes if any exists at the given uri location.
        :return:
            Dictionary of found nodes or an empty dictionary.
        """
        node = self.get(uri)

        _nodes = {}
        for k, v in node.items():
            if isinstance(v, dict):
                _nodes[k] = v

        return _nodes


# A singleton cache.
class SingletonCache:
    instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.instance:
            cls.instance = super(SingletonCache, cls).__new__(cls)
            cls.instance.cache = Cache(*args, **kwargs)

        return cls.instance.cache
