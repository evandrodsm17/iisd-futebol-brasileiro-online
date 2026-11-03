import unittest
from analyze_issd_execution_trace import EMPTY_GUID, summarize


class ExecutionTraceTests(unittest.TestCase):
    def test_empty_guid_does_not_count_as_registered(self):
        result = summarize([{'type': 'hook_registration', 'address': '84',
                             'success': True, 'handle': EMPTY_GUID}])
        self.assertFalse(result['hooks'][0]['registered'])
        self.assertFalse(result['session_complete'])

    def test_preserves_event_order_without_actor_inference(self):
        rows = [{'type': 'session_start'}, {'type': 'execution', 'address': 'A', 'step': 1},
                {'type': 'execution', 'address': 'B', 'step': 1},
                {'type': 'session_end', 'reason': 'experiment_window_complete'}]
        result = summarize(rows)
        self.assertEqual([e['address'] for e in result['events']], ['A', 'B'])
        self.assertIsNone(result['events'][0]['dp'])
        self.assertTrue(result['session_complete'])


if __name__ == '__main__': unittest.main()
