#!/usr/bin/env python
import argparse
import os
import imp
import contextlib
from uuid import uuid4
import warnings
import shutil
import subprocess

from six.moves import cStringIO as StringIO

try:
    from pathlib import Path, PurePath
except ImportError:
    from pathlib2 import Path, PurePath


_missing = object()

INIT_FILE = PurePath('__init__.py')
NAMESPACE_PKG_TEMPLATE = u"""# -*- coding: utf-8 -*-
from __future__ import absolute_import
# this is a namespace package
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)
"""

# IMPORT_STAR_INIT_TEMPLATE = u"""# -*- coding: utf-8 -*-
# from __future__ import absolute_import

# __version__ = {version}

# {imports}
# """


SETUP_FILE = PurePath('setup.py')
SETUP_BDIST_WHEEL_ARGS = ['python', SETUP_FILE.name, 'bdist_wheel']
SETUP_INFO_ARGS = ['python', SETUP_FILE.name, '--name', '--version']
SETUP_TEMPLATE = u"""
from setuptools import setup, find_packages

requirements = [
     'protobuf>=3.0.0',
     'googleapis-common-protos>=1.3.1'
]

setup(
    name='{name}-{version}',
    version='{version}',
    url='{{cookiecutter.project_url}},
    license='{{cookiecutter.license}}',
    author='{{cookiecutter.author_name}}',
    author_email='{{cookiecutter.author_email}}',
    description='Service Models',
    long_description=__doc__,
    {% raw %}package_dir={{'': 'gen-src'}},{% endraw %}
    namespace_packages={namespaces},
    packages=find_packages('gen-src'),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=requirements,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
"""

VERSION_FILE = PurePath('__version__.py')
VERSION_TEMPLATE = u"""# -*- coding: utf-8 -*-
from __future__ import absolute_import

__version__ = {version}
"""

class IOUtil(object):
    @staticmethod
    def copy(src, dest):
        print('copy: {} -> {}'.format(src, dest))
        return shutil.copy(str(src), str(dest))



class cached_property(property):

    """A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value::
        class Foo(object):
            @cached_property
            def foo(self):
                # calculate something important here
                return 42
    The class has to have a `__dict__` in order for this property to
    work.
    """

    # implementation detail: A subclass of python's builtin property
    # decorator, we override __get__ to check for a cached value. If one
    # choses to invoke __get__ by hand the property will still work as
    # expected because the lookup logic is replicated in __get__ for
    # manual invocation.

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = value

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value


@contextlib.contextmanager
def working_directory(path):
    cwd = Path.cwd()
    try:
        os.chdir(str(path))
        yield path
    finally:
        os.chdir(str(cwd))


class Release(object):
    py_file_pattern = '*.py'
    lang = 'python'

    def __init__(self,
                 version,
                 build_dir,
                 namespace):
        self.version = version
        self.build_dir = build_dir
        self.pkg_build_dir = build_dir / PurePath('gen-src')
        self.namespace = namespace

    @cached_property
    def name(self):
        return self.pkg_fmt.format(
            lang=self.python,
            version=self.version)

    @cached_property
    def module(self):
        """Find the first generated code file and load that sourcefile into a
        temporary namespace. This module will be used to
        """
        filepath = next(iter(self.manifest))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            module = imp.load_source('{}.tmp'.format(str(uuid4().hex)), str(filepath.absolute()))
        return module

    @cached_property
    def module_import_path(self):
        base, _ =self.module.DESCRIPTOR.package.rsplit('.', 1)
        return base

    @cached_property
    def all_namespaces(self):
        n = self.namespace
        ns = [n]
        while n.count('.') != 0:
            n, _ = n.rsplit('.', 1)
            ns.append(n)

        return ns

    @property
    def namespace_dir(self):
        return self.pkg_build_dir / PurePath(self.namespace.replace('.', '/'))

    @property
    def module_dir_path(self):
        return self.pkg_build_dir / Path(self.module_import_path.replace('.', '/'))

    @property
    def module_name(self):
        return self.module_import_path

    @cached_property
    def manifest(self):
        return tuple(self.build_dir.glob(self.py_file_pattern))

    def __str__(self):
        return 'Release({})'.format(self.version)

    def _build_pkg_structure(self):
        # Create the directories for the module
        # eg. a.b.c.d -> build/gen-src/a/b/c/d
        path = self.module_dir_path
        path.mkdir(parents=True)

        # Walk up the directory tree, inserting empty __init__.py
        # files as needed for a proper python module. Once directory
        # that represents the shared namespace module is reached,
        # place the special __init__.py files that designate namespace
        # modules.
        reached_namespace = False
        # first = True
        while path != self.pkg_build_dir:
            if path  == self.namespace_dir:
                reached_namespace = True

            init = path / INIT_FILE

            if reached_namespace:
                with init.open('w') as init_file:
                    init_file.write(NAMESPACE_PKG_TEMPLATE)
            # elif first:
            #     text = StringIO()
            #     for fi in self.manifest:
            #         if not fi.name.endswith('_pb2.py'):
            #             continue

            #         module_name = 'from .{} import *\n'.format(fi.name.replace('.py', ''))
            #         text.write(module_name)

            #     text.seek(0)
            #     with init.open('w') as init_file:
            #         init_file.write(IMPORT_STAR_INIT_TEMPLATE.format(

            #             imports=text.read()))
            #     first = False
            else:
                init.touch()

            path = path.parent

    def _copy_manifest_to_pkg(self):
        """Copy the files in the manifest from the /build to the module
        directory"""
        for srcfile in self.manifest:
            destfile = self.module_dir_path / PurePath(srcfile.name)
            IOUtil.copy(srcfile, destfile)

    def _write_version_to_init(self):
        content = VERSION_TEMPLATE.format(
            version=repr(self.version))

        root_init_path = self.module_dir_path / INIT_FILE
        with root_init_path.open('w') as init_file:
            init_file.write(content)

    def _generate_setup_py(self):
        content = SETUP_TEMPLATE.format(
            name=self.module_name,
            version=self.version,
            namespaces=self.all_namespaces)

        setup_path = self.build_dir / SETUP_FILE
        with setup_path.open('w') as setup_file:
            setup_file.write(content)

    def build(self):
        self._build_pkg_structure()
        self._copy_manifest_to_pkg()
        self._write_version_to_init()
        self._generate_setup_py()
        self.verify()

    def verify(self):
        package_name = '{}-{}'.format(self.module_name, self.version)
        expected_info = {package_name, self.version}

        with working_directory(self.build_dir):
            assert subprocess.call(SETUP_BDIST_WHEEL_ARGS) == 0
            cmd = subprocess.Popen(SETUP_INFO_ARGS, stdout=subprocess.PIPE)
            info = {line.strip().decode('utf-8') for line in cmd.stdout.readlines()}
            assert cmd.wait() == 0

        print('{} == {}'.format(info, expected_info))
        assert info == expected_info


def main():
    args = parse_args()
    release = Release(args.model_version,
                      args.build_dir,
                      args.namespace)

    if args.action == 'build':
        release.build()
    # elif args.action == 'verify':
    #     release.verify()

def parse_args():
    parser = argparse.ArgumentParser(
        description='Preapare and Verify Python Model Releases',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--version', type=str, action='store',
                        required=True,
                        dest='model_version',
                        help='Model release version')

    parser.add_argument('--build-dir', type=Path, action='store',
                        required=True,
                        dest='build_dir',
                        help='Build Directory')

    parser.add_argument('--namespace', type=str, action='store',
                        required=True,
                        dest='namespace',
                        help='Package namespace')

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--build', action='store_const', const='build', dest='action')
    # action_group.add_argument('--verify', action='store_const', const='verify', dest='action')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
