#
# Author:: Noah Kantrowitz <noah@coderanger.net>
#
# Copyright 2014, Balanced, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import collections
import hashlib
import importlib
import json
import os
import sys


class UnknownTemplateType(Exception):
    """Token exception for trying to load an unknown file type."""


class TemplateLibrary(collections.OrderedDict):
    """A library of Stratosphere templates."""

    def __init__(self, path, load=True):
        super(TemplateLibrary, self).__init__()
        self.path = os.path.abspath(path)
        if load:
            self._load()

    def _load(self):
        for path in self._find_templates():
            try:
                template = Template(path)
            except UnknownTemplateType:
                continue # Some unknown file type, just move on
            self[template.name] = template

    def _find_templates(self):
        for path in sorted(os.listdir(self.path)):
            name, ext = os.path.splitext(path)
            if name.startswith('_') or name.startswith('.'):
                continue
            yield os.path.join(self.path, path)


class Template(object):
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.name, ext = os.path.splitext(os.path.basename(path))
        self.error = None
        load_fn = {
            '.py': self._load_py,
            '.json': self._load_json,
        }.get(ext)
        if not load_fn:
            raise UnknownTemplateType('Cannot load a template from {}'.format(path))
        try:
            load_fn()
            self.sha1 = hashlib.sha1(self.json).hexdigest()
            self.s3_key = 'templates/{}-{}.json'.format(self.name, self.sha1)
        except Exception:
            self.error = sys.exc_info()

    def _load_py(self):
        old_path = sys.path[:]
        old_mods = sys.modules.copy()
        try:
            load_path = os.path.dirname(os.path.dirname(self.path))
            pkg_name = os.path.basename(os.path.dirname(self.path))
            sys.path.insert(0, load_path)
            mod = importlib.import_module('{}.{}'.format(pkg_name, self.name))
            # Find the template object
            self.template = getattr(mod, 'template', None)
            if not self.template:
                raise ValueError('Unable to find a template when loading {}'.format(self.name))
            self.json = self.template.to_json()
        finally:
            sys.path[:] = old_path
            sys.modules.clear()
            sys.modules.update(old_mods)

    def _load_json(self):
        """Load a template from a JSON file."""
        self.template = None # We don't have a template object instance
        raw_json = open(self.path, 'rb').read()
        self.json = json.dumps(json.loads(raw_json), indent=4)
