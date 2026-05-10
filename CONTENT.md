# Updating publications and news

This site can generate the news list and publication lists from lightweight metadata files, so you do not need to hand-edit repeated HTML blocks.

## News

Edit `content/news.md` using one bullet per item:

```md
- 2026-05 | Launched a refreshed personal website.
- 2025-11-15 | Presented a poster at Example Conference.
```

Supported dates are `YYYY`, `YYYY-MM`, or `YYYY-MM-DD`. Newer items are shown first on the homepage.

## Publications

Edit `content/publications.bib` using normal BibTeX entries. The generator reads these common fields:

- `title`, `author`, `year`
- `journal` or `booktitle`
- `summary`
- `url`, `pdf`, `code`, `project`, `doi`, `eprint`
- `selected = {true}` to include a publication in the homepage highlights

Example:

```bibtex
@inproceedings{lastname2026example,
  title = {Example Paper Title},
  author = {First Author and Yi Wang and Last Author},
  booktitle = {Conference Name},
  year = {2026},
  pdf = {/files/example-paper.pdf},
  code = {https://github.com/example/project},
  selected = {true},
  summary = {One sentence describing the main contribution.}
}
```

## Regenerate the HTML

After editing either metadata file, run:

```sh
python3 scripts/build_content.py
```

The script updates the generated regions in `index.html` and `publications/index.html` between these comments:

- `<!-- NEWS:START -->` and `<!-- NEWS:END -->`
- `<!-- SELECTED_PUBLICATIONS:START -->` and `<!-- SELECTED_PUBLICATIONS:END -->`
- `<!-- PUBLICATIONS:START -->` and `<!-- PUBLICATIONS:END -->`

You can still edit the rest of the HTML directly for layout, profile text, links, talks, and CV updates.
