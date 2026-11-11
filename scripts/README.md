# CRAN package scraper

Requires Python 3.11 or newer; no third-party packages are needed.

From the repository root, run:

```sh
python3 scripts/pull_R_packages.py --output Packages.txt
python3 -m unittest discover -s tests -v
```

The scraper reads the CRAN Machine Learning task view and each linked package
page over HTTPS. It emits one Markdown row per unique package, using its heading
as the description. Fetch failures, missing headings, and empty task views stop
the command before the output file is opened. Network requests time out after
30 seconds. Generated output should be reviewed before adding it to the catalog.

Tests use local fixtures and do not require network access.
