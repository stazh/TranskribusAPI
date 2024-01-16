import os
import unittest
from unittest.mock import patch

from my_module import 3_Sampling-Modul

class TestDoTranscription(unittest.TestCase):
    @patch('os.system')
    def test_pylaia_model_with_proxy(self, mock_system):
        toolName = 'tool1'
        colId = 'collection1'
        docId = 'document1'
        modelProvMap = {'tool1': 'PyLaia'}
        modelsIdMap = {'tool1': 'model1'}
        proxy = {'https': 'http://proxy.example.com'}

        with patch.dict('st.session_state', {'proxy': proxy}):
            doTranscription(toolName, colId, docId, modelProvMap, modelsIdMap)

        mock_system.assert_called_once_with('python ../../lib/TranskribusPyClient/src/TranskribusCommands/do_htrRnn.py model1 None document1 --docid document1 --pylaia --https_proxy=http://proxy.example.com')

    @patch('os.system')
    def test_other_model_without_proxy(self, mock_system):
        toolName = 'tool2'
        colId = 'collection2'
        docId = 'document2'
        modelProvMap = {'tool2': 'OtherModel'}
        modelsIdMap = {'tool2': 'model2'}
        proxy = None

        with patch.dict('st.session_state', {'proxy': proxy}):
            doTranscription(toolName, colId, docId, modelProvMap, modelsIdMap)

        mock_system.assert_called_once_with('python ../../lib/TranskribusPyClient/src/TranskribusCommands/do_htrRnn.py model2 None document2 --docid document2')

if __name__ == '__main__':
    unittest.main()