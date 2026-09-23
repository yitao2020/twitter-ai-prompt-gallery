import json
import tempfile
import unittest
from pathlib import Path

from ecosystem_focus import TERMS, build_ecosystem
from prompt_focus import pattern


class EcosystemTests(unittest.TestCase):
    def test_ambiguous_words_are_not_tools(self):
        rules={key:pattern(aliases) for key,_,_,aliases in TERMS}
        self.assertIsNone(rules['runway'].search('Fashion model walks on a runway.'))
        self.assertIsNone(rules['midjourney'].search('A portrait of MJ with a hat.'))
        self.assertIsNone(rules['wan'].search('I want a landscape.'))
        self.assertIsNotNone(rules['runway'].search('Made with Runway Gen-4'))
        self.assertIsNotNone(rules['wan'].search('Wan 2.2 video workflow'))
        for rule in rules.values(): self.assertIsNone(rule.search(''))

    def test_versions_titles_and_dates(self):
        entries=[
            {'title':'Testing Seedance 2.0 and Seedance 2.5 with ComfyUI','prompt':'','tweet_url':'https://x.com/i/status/1','created_at':'2026-09-21'},
            {'title':'Testing Seedance 2.0 and Seedance 2.5 with ComfyUI','prompt':'','tweet_url':'https://x.com/i/status/2','created_at':'2026-09-21'},
            {'title':'Another Seedance workflow with ComfyUI','prompt':'','tweet_url':'https://x.com/i/status/3','created_at':'2026-09-22'},
            {'title':'A portrait in natural light','tool_label':'Midjourney','prompt':'','tweet_url':'https://x.com/i/status/4','created_at':'2026-09-22'},
        ]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'gallery.html';path.write_text('const ALL = '+json.dumps(entries)+';',encoding='utf-8')
            data=build_ecosystem(path)
        self.assertEqual(sum(data['series']['seedance']),2)
        self.assertEqual(sum(data['corpus']),3)
        self.assertNotIn('midjourney',data['series'])
        self.assertEqual(sum(data['graph_edges'][0]['values']),2)
        self.assertEqual(data['dates'][-1],'2026-09-22')


if __name__=='__main__': unittest.main()
