# migrations

Scripts that were run once against Notion and are kept for the record: the domain
passes that rewrote equation fields, and the corrections to values an earlier seed
got wrong. Each says in its docstring what it changed and when.

They are not re-runnable through `./deploy.sh <name>` — that only looks in
`scripts/` — and none of them should be run again: the state they produced is in
Notion, and from there in `data/`. A new correction belongs in the seed that made
the mistake, so the seed stays the truth of what it seeds; a script lands here
only once it has been run and its work has been synced.

To run one anyway (from the repo root, with a token in `.env`):

    python3 scripts/migrations/<name>.py

They import the shared helpers from `scripts/` one directory up.
