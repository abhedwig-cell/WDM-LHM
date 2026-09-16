# Next permitted action

After this bootstrap PR is opened, use the PR-triggered GitHub Actions runs as the next qualification evidence:

1. ordinary CI on Python 3.10 and 3.12;
2. live BRO/PDOK smoke ingest for the small Wageningen-area bbox;
3. inspect workflow logs and artifacts;
4. patch only the observed failure surface;
5. merge by squash after qualification is complete.
