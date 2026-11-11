import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('scraper', Path(__file__).resolve().parents[1] / 'scripts/pull_R_packages.py')
scraper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper)


class ScraperTests(unittest.TestCase):
    def test_packages_only_deduplicated_and_plain_text(self):
        view = '''<li>No link</li><a href="../packages/pkg/index.html">pkg</a>
        <a href="../packages/pkg/index.html">pkg</a>
        <a href="../views/Other.html">Other</a>
        <a href="https://evil.example/web/packages/bad/index.html">bad</a>'''
        calls = []
        def fetch(url):
            calls.append(url)
            return view if url == scraper.VIEW_URL else '<h2>A <em>useful</em> &amp; safe package</h2>'
        self.assertEqual(scraper.generate(fetch), ' [pkg](https://cran.r-project.org/web/packages/pkg/index.html) - A useful & safe package \n')
        self.assertEqual(len(calls), 2)

    def test_empty_view_rejected(self):
        with self.assertRaises(ValueError):
            scraper.generate(lambda url: '<p>No packages</p>')

    def test_missing_heading_rejected(self):
        with self.assertRaises(ValueError):
            scraper.generate(lambda url: '<a href="../packages/pkg/index.html">pkg</a>')

    def test_fetch_failure_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'Packages.txt'
            output.write_text('original', encoding='utf-8')
            with patch('sys.argv', ['scraper', '--output', str(output)]), patch.object(scraper, 'generate', side_effect=OSError('offline')):
                with self.assertRaises(OSError):
                    scraper.main()
            self.assertEqual(output.read_text(encoding='utf-8'), 'original')

    def test_fetch_uses_timeout(self):
        with patch.object(scraper, 'urlopen') as opening:
            opening.return_value.__enter__.return_value.read.return_value = b'ok'
            self.assertEqual(scraper.fetch(scraper.VIEW_URL), 'ok')
            opening.assert_called_once_with(scraper.VIEW_URL, timeout=30)


if __name__ == '__main__':
    unittest.main()
