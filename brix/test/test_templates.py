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

    @pytest.fixture
    def library3(self):
        return os.path.join(DATA_PATH, 'templates3')

    def test_find_templates_1(self, library1):
        lib = TemplateLibrary(library1, load=False)
        tpls = list(lib._find_templates())
        assert os.path.join(DATA_PATH, 'templates1', 'template_a.py') in tpls
        assert os.path.join(DATA_PATH, 'templates1', 'template_b.json') in tpls

    def test_find_templates_2(self, library2):
        lib = TemplateLibrary(library2, load=False)
        tpls = list(lib._find_templates())
        assert os.path.join(DATA_PATH, 'templates2', 'template_a.py') in tpls
        assert os.path.join(DATA_PATH, 'templates2', 'template_b.py') in tpls

    def test_find_templates_3(self, library3):
        lib = TemplateLibrary(library3, load=False)
        tpls = list(lib._find_templates())
        assert os.path.join(DATA_PATH, 'templates3', 'template_a.py') in tpls
        assert os.path.join(DATA_PATH, 'templates3', 'template_b.py') in tpls
        assert os.path.join(DATA_PATH, 'templates3', 'template_c.py') in tpls

    def test_load_templates_1(self, library1):
        lib = TemplateLibrary(library1)
        assert lib.keys() == ['template_a', 'template_b']

    def test_load_templates_2(self, library2):
        lib = TemplateLibrary(library2)
        assert lib.keys() == ['template_a', 'template_b']

    def test_load_templates_3(self, library3):
        lib = TemplateLibrary(library3)
        assert lib.keys() == ['template_a', 'template_b', 'template_c']


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

    def test_template_1_b(self):
        tpl = Template(os.path.join(DATA_PATH, 'templates1', 'template_b.json'))
        assert not tpl.error
        assert tpl.name == 'template_b'
        assert not tpl.template
        assert json.loads(tpl.json) == {
            'Description': 'A JSON template.',
            'Resources': {},
        }
        assert tpl.sha1 == '31cdf7401d1c1e98b1f8d0dd9d8c971632f2d4c9'
        assert tpl.s3_key == 'templates/template_b-31cdf7401d1c1e98b1f8d0dd9d8c971632f2d4c9.json'

    def test_template_2_a(self):
        tpl = Template(os.path.join(DATA_PATH, 'templates2', 'template_a.py'))
        assert not tpl.error
        assert tpl.name == 'template_a'
        assert isinstance(tpl.template, troposphere.Template)
        assert json.loads(tpl.json) == {
            'Description': 'A really blank template.',
            'Resources': {},
        }
        assert tpl.sha1 == 'b8ff648e601630c0768f325c82f385b505493939'
        assert tpl.s3_key == 'templates/template_a-b8ff648e601630c0768f325c82f385b505493939.json'

    def test_template_2_b(self):
        tpl = Template(os.path.join(DATA_PATH, 'templates2', 'template_b.py'))
        assert not tpl.error
        assert tpl.name == 'template_b'
        assert isinstance(tpl.template, troposphere.Template)
        assert json.loads(tpl.json) == {
            'Description': 'A very blank template.',
            'Resources': {},
        }
        assert tpl.sha1 == 'c640245712222274998b4df6305bf09a8eb82841'
        assert tpl.s3_key == 'templates/template_b-c640245712222274998b4df6305bf09a8eb82841.json'

    def test_template_3_a(self):
        tpl = Template(os.path.join(DATA_PATH, 'templates3', 'template_a.py'))
        assert not tpl.error
        assert tpl.name == 'template_a'
        assert isinstance(tpl.template, troposphere.Template)
        assert json.loads(tpl.json) == {
            'Description': 'A template that just inherits.',
            'Resources': {},
            'Parameters': {
                'Foo': {
                    'Description': 'Base parameter.',
                    'Type': 'String',
                },
            },
        }
        assert tpl.sha1 == 'aeb4d147402fe7219470b0700f51c069fb555ade'
        assert tpl.s3_key == 'templates/template_a-aeb4d147402fe7219470b0700f51c069fb555ade.json'

    def test_template_3_b(self):
        tpl = Template(os.path.join(DATA_PATH, 'templates3', 'template_b.py'))
        assert not tpl.error
        assert tpl.name == 'template_b'
        assert isinstance(tpl.template, troposphere.Template)
        assert json.loads(tpl.json) == {
            'Description': 'A template that extends.',
            'Resources': {},
            'Parameters': {
                'Foo': {
                    'Description': 'Base parameter.',
                    'Type': 'String',
                },
                'Bar': {
                    'Description': 'Extended parameter.',
                    'Type': 'String',
                },
            },
        }
        assert tpl.sha1 == 'cff31bdd6985d8fca07df504f85c1d712e4f07bd'
        assert tpl.s3_key == 'templates/template_b-cff31bdd6985d8fca07df504f85c1d712e4f07bd.json'

    def test_template_3_c(self):
        tpl = Template(os.path.join(DATA_PATH, 'templates3', 'template_c.py'))
        assert not tpl.error
        assert tpl.name == 'template_c'
        assert isinstance(tpl.template, troposphere.Template)
        assert json.loads(tpl.json) == {
            'Description': 'A template that overrides.',
            'Resources': {},
            'Parameters': {
                'Foo': {
                    'Description': 'Override parameter.',
                    'Type': 'Int',
                },
            },
        }
        assert tpl.sha1 == '0b6adf559db64769a815af9eeb2e5144e7bd578d'
        assert tpl.s3_key == 'templates/template_c-0b6adf559db64769a815af9eeb2e5144e7bd578d.json'
