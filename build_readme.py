#!/usr/bin/env python3
"""Splice my recent open source contributions into README.md.

Lists issues and PRs I authored in public repos that are not mine and not my
employer's, newest first. Run by .github/workflows/oss-activity.yml.
"""
import json
import os
import pathlib
import re
import urllib.parse
import urllib.request

LIMIT = 8
PER_REPO = 3  # so one busy repo does not hide the breadth
TITLE = 95
MINE = ("jillesmc/", "madeiramadeirabr/")
QUERY = "author:jillesmc is:public sort:created-desc"
MARKERS = re.compile(r"<!-- oss starts -->.*<!-- oss ends -->", re.DOTALL)
README = pathlib.Path(__file__).parent / "README.md"


def search():
    url = "https://api.github.com/search/issues?per_page=100&q=" + urllib.parse.quote(QUERY)
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token := os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)["items"]


def repo_of(item):
    # repository_url looks like https://api.github.com/repos/<owner>/<name>
    return item["repository_url"].split("/repos/", 1)[1]


def render(items):
    rows, seen = [], {}
    for item in items:
        repo = repo_of(item)
        if repo.startswith(MINE) or seen.get(repo, 0) >= PER_REPO:
            continue
        seen[repo] = seen.get(repo, 0) + 1
        title = item["title"]
        if len(title) > TITLE:
            title = title[: TITLE - 1].rstrip() + "…"
        kind = "PR" if "pull_request" in item else "issue"
        state = "merged" if (item.get("pull_request") or {}).get("merged_at") else item["state"]
        rows.append(
            f"- `{item['created_at'][:10]}` **[{repo}](https://github.com/{repo})** — "
            f"[{title}]({item['html_url']}) <sub>{kind}, {state}</sub>"
        )
        if len(rows) == LIMIT:
            break
    return "\n".join(rows) or "_Nothing recent._"


def main():
    body = render(search())
    old = README.read_text()
    new = MARKERS.sub(f"<!-- oss starts -->\n{body}\n<!-- oss ends -->", old)
    if new != old:
        README.write_text(new)
        print(f"updated ({body.count(chr(10)) + 1} entries)")
    else:
        print("no change")


if __name__ == "__main__":
    main()
