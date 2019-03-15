from unittest.mock import Mock, patch, MagicMock, PropertyMock
from django.test import SimpleTestCase

class TestXplanApiViews(SimpleTestCase):

    def test_experiments_list(self):
        exp_sets = [
            {'experiment_set':'rule-30_q0', "lab": "transcriptic"},
            {'experiment_set':'yeast-gates_q0', "lab": "transcriptic"},
            {'experiment_set':'yeast-gates_q0', "lab": "ginko"}
        ]
        with patch('xplan_api.request_utils.known_methods', exp_sets):

            response = self.client.get('/experiment-sets/', follow=True)
            data = response.json()
            # If the request is sent successfully, then I expect a response to be returned.
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(data), 3)

    def test_get_resources(self):
        resources = {
            "colonies": [1, 2, 3],
            "junk": {}
        }
        with patch('xplan_api.sbol.sbh.get_experiment_resources') as mock_client:
            mock_client.return_value = resources
            response = self.client.get('/resources/?experiment_set=test', follow=True)
            data = response.json()
            mock_client.assert_called_with('test')
            # If the request is sent successfully, then I expect a response to be returned.
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(data), 3)
