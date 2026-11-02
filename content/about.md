---
title: About OpenGWAS
lede: OpenGWAS collects published GWAS summary statistics, harmonises them, imputes them to a shared set of variants, and releases them as compact stores you can download or query.
notice: >-
  **Draft.** This page is being written. Still to come: the team, the
  catalogue overview, and how to cite the forthcoming paper on the new stores.
---

## How it works

1. **Collect.** Published summary statistics from large studies and consortia, each recorded with where it came from.
2. **Harmonise.** Alleles are aligned to one reference, quality checked, and each analysis is assigned an ancestry group.
3. **Complete.** Missing variants are filled in from a reference panel matched to the analysis's ancestry. Imputed values are always marked as imputed.
4. **Release.** Each store is an immutable release with its own ID, such as `OGS-00009`, so an analysis can always be found again exactly as it was.

What is in the catalogue today is on the [Data](/data/) page.

## Who runs it

OpenGWAS is run by the MRC Integrative Epidemiology Unit at the University of Bristol. Contact us at [ieu-opengwas@bristol.ac.uk](mailto:ieu-opengwas@bristol.ac.uk).

## How to cite

A paper describing the new stores is in preparation. Until it is published, please cite:

- Elsworth B, Lyon M, Alexander T, *et al.* The MRC IEU OpenGWAS data infrastructure. bioRxiv 2020. [doi:10.1101/2020.08.10.244293](https://doi.org/10.1101/2020.08.10.244293)

Please also cite the original study for each analysis you use. Each analysis's page links to its publication.

## Development

The stores are built in the open. The [OpenGWAS stores project site](https://blog.opengwas.io/opengwasdb-stores/) tracks how each store release is built and checked, and the code is on [GitHub](https://github.com/opengwas).
