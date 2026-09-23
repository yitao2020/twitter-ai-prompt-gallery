import json
import tempfile
import unittest
from pathlib import Path

from prompt_focus import FOCI, build_focus, pattern


class FocusTests(unittest.TestCase):
    def test_no_empty_matches_or_partial_english_words(self):
        for row in FOCI:
            rule = pattern(row[3])
            self.assertIsNone(rule.search(''), row[0])
            self.assertIsNone(rule.search('A portrait of a person outdoors.'), row[0])
        self.assertIsNone(pattern('pan').search('Japan'))
        self.assertIsNotNone(pattern('dolly(?: in| out| shot)?').search('A dolly out shot'))
        self.assertIsNotNone(pattern('rim light(?:ing)?|轮廓光').search('柔和轮廓光照亮人物'))
        dolly = next(pattern(row[3]) for row in FOCI if row[0]=='dolly')
        self.assertIsNone(dolly.search('QT your Dolly art RIP Dolly!'))
        self.assertIsNotNone(dolly.search('Slow dolly-in toward the actor'))

    def test_dedup_dates_counts_and_evidence(self):
        text = 'Cinematic close-up with soft lighting and shallow depth of field. ' * 2
        entries = [
            {'prompt':text,'created_at':'2026-09-01','tweet_url':'https://x.com/i/status/1'},
            {'prompt':text,'created_at':'2026-09-01','tweet_url':'https://x.com/i/status/2'},
            {'prompt':text+' Keep the background dark.','created_at':'2026-09-02','tweet_url':'https://x.com/i/status/3'},
            {'prompt':text,'created_at':'2999-09-01','tweet_url':'https://x.com/i/status/4'},
            {'prompt':text+' An old example.','created_at':'2025-01-01','tweet_url':'https://x.com/i/status/5'},
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'gallery.html'
            path.write_text('const ALL = '+json.dumps(entries)+';',encoding='utf-8')
            result = build_focus(path)
        self.assertEqual(result['dates'][-1], '2026-09-02')
        self.assertEqual(result['eligible_count'], 2)
        self.assertEqual(sum(result['series']['close-up']),2)
        self.assertNotIn('dolly',result['series'])
        self.assertTrue(all(sum(edge['values'])==2 for edge in result['graph_edges']))
        for examples in result['examples'].values():
            for example in examples:
                self.assertIn(example['matched'],example['excerpt'])


if __name__=='__main__':
    unittest.main()
