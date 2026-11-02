-- Proposed for the Analysis Catalog build (decision 13): two covering indexes
-- that let the Data page filter and sort in the browser with a handful of
-- range requests. Each holds every column the results table shows, so a page
-- of results comes straight from the index. The size index runs largest-first
-- so that its common order is a forward read.
--
-- Also proposed: build the catalogue with 32 KB pages (`pragma page_size =
-- 32768` before the first table) and run the FTS5 'optimize' command once the
-- search index is filled.
create index if not exists analyses_browse_by_label on analyses
  (analysis_label, id, store_id, ancestry_category, trait_class, outcome_type, tissue, sample_size)
  where listed = 1;
create index if not exists analyses_browse_by_sample_size on analyses
  (sample_size desc, id desc, store_id, ancestry_category, trait_class, outcome_type, tissue, analysis_label)
  where listed = 1;
