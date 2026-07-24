# Databases Course Project — Mini Query Engine (sample document)

> Sample document for demoing ExperienceCurator. Upload it to a folder and ask
> questions against it.

## What I built

A small disk-backed relational query engine in Python for my databases course
final project. It parses a subset of SQL (SELECT/WHERE/JOIN), plans queries
against heap files, and executes them with an iterator (Volcano-style) model.

## Key pieces

- **Storage layer**: fixed-size 4 KB pages with a free-space map; a buffer pool
  (LRU, 64 pages) sitting between the executor and the heap files.
- **B+ tree index** on primary keys with range-scan support; the planner picks
  an index scan over a sequential scan when a WHERE clause hits an indexed column.
- **Join strategies**: block nested-loop join and a grace hash join; the planner
  chooses by estimated cardinality from simple per-column histograms.
- **Executor**: pull-based iterators (open/next/close) so joins, filters, and
  projections compose without materializing intermediates.

## Results

- Correctness: 41 test queries checked against SQLite output; all pass.
- The B+ tree index turned a 1.2 s full scan into a 14 ms lookup on the 500k-row
  ratings table.
- Grace hash join beat nested-loop by ~8x on the 100k x 500k join workload.

## What I'd do next

Cost-based join ordering (currently left-deep, in declaration order) and WAL for
crash recovery.
