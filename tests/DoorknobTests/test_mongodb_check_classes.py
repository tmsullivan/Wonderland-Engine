'''
    Copyright (c) 2012 Alexander Abbott

    This file is part of the Cheshire Cyber Defense Scoring Engine (henceforth
    referred to as Cheshire).

    Cheshire is free software: you can redistribute it and/or modify it under
    the terms of the GNU Affero General Public License as published by the
    Free Software Foundation, either version 3 of the License, or (at your
    option) any later version.

    Cheshire is distributed in the hope that it will be useful, but WITHOUT ANY
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
    FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
    more details.

    You should have received a copy of the GNU Affero General Public License
    along with Cheshire.  If not, see <http://www.gnu.org/licenses/>.
'''

from copy import deepcopy
from Doorknob.Exceptions import Exists, DoesNotExist
from tests.DoorknobTests import DBTestCase
from .. import show_difference_between_dicts

class TestMongoDBCheckClasses(DBTestCase):
    def test_get_all_check_classes(self):
        wrapper_result = self.db_wrapper.get_all_check_classes()
        expected_result = [deepcopy(obj) for obj in self.data['check_classes']]
        assert len(wrapper_result) == len(expected_result)
        assert wrapper_result == expected_result

    def test_get_specific_check_class(self):
        expected_result = [deepcopy(obj) for obj in self.data['check_classes']][0]
        result_id = expected_result['id']
        del expected_result['id']
        wrapper_result = self.db_wrapper.get_specific_check_class(result_id)[0]
        assert wrapper_result == expected_result

    def test_get_specific_check_class_nonexistant(self):
        wrapper_result = self.db_wrapper.get_specific_service_check('NonexistantClass')
        expected_result = []
        assert wrapper_result == expected_result

    def test_create_check_class(self):
        self.db_wrapper.create_check_class('AnotherServiceCheck', 'service', 'ServiceChecks')
        wrapper_result = list(self.db.check_classes.find({'id': 'AnotherServiceCheck'}, {'_id': 0, 'id': 0}))
        expected_result = [{
            'check_type': 'service',
            'module_id': 'ServiceChecks'
        }]
        assert len(wrapper_result) == len(expected_result)
        assert wrapper_result == expected_result

    def test_create_check_class_exists(self):
        with self.assertRaises(Exists):
            self.db_wrapper.create_check_class('SampleInjectCheck', 'inject', 'ServiceChecks')

    def test_modify_check_class(self):
        self.db_wrapper.modify_check_class('SampleInjectCheck', module_id='ServiceChecks')
        wrapper_result = list(self.db.check_classes.find({'id': 'SampleInjectCheck'}, {'_id': 0, 'id': 0}))
        expected_result = [{
            'check_type': 'inject',
            'module_id': 'ServiceChecks'
        }]
        assert len(wrapper_result) == len(expected_result)
        assert wrapper_result == expected_result

    def test_modify_check_class_nonexistant(self):
        with self.assertRaises(DoesNotExist):
            self.db_wrapper.modify_check_class('NonexistantClass', check_type='service', module_id='ServiceChecks')

    def test_delete_check_class(self):
        self.db_wrapper.delete_check_class('SampleAttackerCheck')
        wrapper_result = list(self.db.check_classes.find({'id': 'SampleAttackerClass'}, {'_id': 0, 'id': 0}))
        expected_result = []
        assert wrapper_result == expected_result

    def test_delete_check_class_nonexistant(self):
        with self.assertRaises(DoesNotExist):
            self.db_wrapper.delete_check_class('NonexistantClass')