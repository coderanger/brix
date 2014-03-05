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

import json
import os

import pytest
import troposphere

from brix.templates import TemplateLibrary, Template

DATA_PATH = os.path.abspath(os.path.join(__file__, '..', 'data'))

class TestTemplateLibrary(object):
    @pytest.fixture
    def library1(self):
        return os.path.join(DATA_PATH, 'templates1')

    @pytest.fixture
    def library2(self):
        return os.path.join(DATA_PATH, 'templates2')

    def test_find_templates_1(self, library1):
        lib = TemplateLibrary(library1, load=False)
        tpls = list(lib._find_templates())
        assert os.path.join(DATA_PATH, 'templates1', 'template_a.py') in tpls

    def test_find_templates_2(self, library2):
        lib = TemplateLibrary(library2, load=False)
        tpls = list(lib._find_templates())
        assert os.path.join(DATA_PATH, 'templates2', 'template_a.py') in tpls
        assert os.path.join(DATA_PATH, 'templates2', 'template_b.py') in tpls

    def test_load_templates_1(self, library1):
        lib = TemplateLibrary(library1)
        assert lib.keys() == ['template_a']

    def test_load_templates_2(self, library2):
        lib = TemplateLibrary(library2)
        assert sorted(lib.keys()) == ['template_a', 'template_b']


class TestTemplate(object):
    def test_template_1_a(self):
        tpl = Template(os.path.join(DATA_PATH, 'templates1', 'template_a.py'))
        assert not tpl.error
        assert tpl.name == 'template_a'
        assert isinstance(tpl.template, troposphere.Template)
        assert json.loads(tpl.json) == {
            'Description': 'A blank template.',
            'Resources': {},
        }
        assert tpl.sha1 == '9f494e946f18781e388ede5870957261f77fed82'
        assert tpl.s3_key == 'templates/template_a-9f494e946f18781e388ede5870957261f77fed82.json'

    def test_template_2_a(self):
        tpl = Template(os.path.join(DATA_PATH, 'templates2', 'template_a.py'))
        assert not tpl.error
        assert tpl.name == 'template_a'
        assert isinstance(tpl.template, troposphere.Template)
        assert json.loads(tpl.json) == {
            'Description': 'A really blank template.',
            'Resources': {},
        }
        assert tpl.sha1 == '9f494e946f18781e388ede5870957261f77fed82'
        assert tpl.s3_key == 'templates/template_a-9f494e946f18781e388ede5870957261f77fed82.json'

    def test_template_2_b(self):
        tpl = Template(os.path.join(DATA_PATH, 'templates2', 'template_b.py'))
        assert not tpl.error
        assert tpl.name == 'template_a'
        assert isinstance(tpl.template, troposphere.Template)
        assert json.loads(tpl.json) == {
            'Description': 'A very blank template.',
            'Resources': {},
        }
        assert tpl.sha1 == '9f494e946f18781e388ede5870957261f77fed82'
        assert tpl.s3_key == 'templates/template_a-9f494e946f18781e388ede5870957261f77fed82.json'
