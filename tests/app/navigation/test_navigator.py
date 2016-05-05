from app.navigation.navigator import Navigator
from app.navigation.navigation_history import FlaskNavigationHistory
from tests.app.framework.sr_unittest import SurveyRunnerTestCase
from app.model.questionnaire import Questionnaire
import unittest
from app.model.group import Group
from app.model.block import Block
from app.navigation.navigator import NavigationException


class NavigatorTest(SurveyRunnerTestCase):

    def test_get_current_location(self):
        with self.application.test_request_context():
            schema = Questionnaire()
            group = Group()
            group.id = 'group-1'
            schema.register(group)
            block = Block()
            block.id = 'block-1'
            schema.register(block)
            group.add_block(block)
            schema.add_group(group)

            navigation_history = FlaskNavigationHistory()
            navigator = Navigator(schema, navigation_history)
            #  brand new session shouldn't have a current location
            self.assertEquals("block-1", navigator.get_current_location())

    def test_get_current_location_with_intro(self):
        with self.application.test_request_context():
            schema = Questionnaire()
            schema.introduction = "anything"

            navigation_history = FlaskNavigationHistory()
            navigator = Navigator(schema, navigation_history)
            #  brand new session shouldn't have a current location
            self.assertEquals("introduction", navigator.get_current_location())

    def test_go_to(self):
        with self.application.test_request_context():
            schema = Questionnaire()
            group = Group()
            group.id = 'group-1'
            schema.register(group)
            block = Block()
            block.id = 'block-1'
            schema.register(block)
            group.add_block(block)
            schema.add_group(group)

            navigation_history = FlaskNavigationHistory()
            navigator = Navigator(schema, navigation_history)

            self.assertRaises(NavigationException, navigator.go_to, 'introduction')

            navigation_history = FlaskNavigationHistory()
            navigator = Navigator(schema, navigation_history)
            navigator.go_to("block-1")
            self.assertEquals("block-1", navigator.get_current_location())

            schema.introduction = {'description': 'Some sort of intro'}

            navigation_history = FlaskNavigationHistory()
            navigator = Navigator(schema, navigation_history)
            navigator.go_to("introduction")
            self.assertEquals("introduction", navigator.get_current_location())

if __name__ == '__main__':
    unittest.main()
