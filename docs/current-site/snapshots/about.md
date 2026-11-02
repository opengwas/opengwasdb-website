<!-- Verbatim snapshot of https://opengwas.io/about taken 2026-11-02 for the redesign. Converted from HTML to Markdown; wording unchanged. Do not treat as current terms. -->

### GWAS summary data ecosystem

[![Diagram](/images/gwas_ecosystem.bb869525db1a.png)](/images/gwas_ecosystem.bb869525db1a.png)

---

### Background

Developed at the [MRC Integrative Epidemiology Unit](https://bris.ac.uk/ieu) (IEU) at the University of Bristol, this resource is a manually curated collection of complete GWAS summary datasets made available as open source files for download, or by querying a database of the complete data.

This project began as the underlying database for the [MR-Base](http://www.mrbase.org/) (decommissioned) and [LD Hub](http://ldsc.broadinstitute.org/ldhub/) projects. These data now serve as an input source to a wider number of analytical tools that implement methods such as Mendelian randomization, fine mapping, colocalisation, GWAS visualisation etc. Please see the [API](https://api.opengwas.io) page for a list of R and Python packages that will connect to the data.

The database comprises mainly publicly available datasets, but also includes a number of private datesets whose access is controlled through OAuth2.0 authentication. Please contact us if you have datasets that you would like to add, whether public or private.

---

### The GWAS VCF format

We have made all the public data available for download. We are using the GWAS VCF format to store the GWAS summary data to ensure alignment with the hg19 reference sequence, and to enable very fast querying. More information is available here: <https://github.com/MRCIEU/gwas-vcf-specification> and on [biorxiv](https://doi.org/10.1101/2020.05.29.115824).

---

### Citing this resource

- Please ensure that the original data are cited whenever it is used. Pubmed IDs are made available through the metadata.
- If you access the data through the OpenGWAS database API:  
  **The MRC IEU OpenGWAS data infrastructure.** Ben Elsworth, Matthew Lyon, Tessa Alexander, Yi Liu, Peter Matthews, Jon Hallett, Phil Bates, Tom Palmer, Valeriia Haberland, George Davey Smith, Jie Zheng, Philip Haycock, Tom R Gaunt, Gibran Hemani. bioRxiv 2020.08.10.244293v1. doi: [10.1101/2020.08.10.244293](https://doi.org/10.1101/2020.08.10.244293)  
  **The MR-Base platform supports systematic causal inference across the human phenome.** Hemani G, Zheng J, Elsworth B, Wade KH, Baird D, Haberland V, Laurin C, Burgess S, Bowden J, Langdon R, Tan VY, Yarmolinsky J, Shihab HA, Timpson NJ, Evans DM, Relton C, Martin RM, Davey Smith G, Gaunt TR, Haycock PC, The MR-Base Collaboration. eLife 2018;7:e34408. doi: [10.7554/eLife.34408](https://doi.org/10.7554/eLife.34408)
- If using GWAS-VCF files:  
  **The variant call format provides efficient and robust storage of GWAS summary statistics.** Matthew Lyon, Shea J Andrews, Ben Elsworth, Tom R Gaunt, Gibran Hemani, Edoardo Marcora. bioRxiv 2020.05.29.115824; doi: [10.1101/2020.05.29.115824](https://doi.org/10.1101/2020.05.29.115824)
- If using EpiGraphDB:  
  **EpiGraphDB: a database and data mining platform for health data science.** Yi Liu, Benjamin Elsworth, Pau Erola, Valeriia Haberland, Gibran Hemani, Matt Lyon, Jie Zheng, Oliver Lloyd, Marina Vabistsevits, Tom R Gaunt. Bioinformatics, btaa961, doi: [10.1093/bioinformatics/btaa961](https://doi.org/10.1093/bioinformatics/btaa961)
- If using GPMap:  
  **Building The Human Genotype-Phenotype Map to Harness Pleiotropy and Refine Disease Mechanisms.** Andrew R. Elmore, Aimee L. Hanson, Genevieve M. Leyden, James Johnson, George Davey Smith, Lavinia Paternoster, Tom R Gaunt, Gibran Hemani. medRxiv 2026.02.19.26346618; doi: [10.64898/2026.02.19.26346618](https://doi.org/10.64898/2026.02.19.26346618)

---

### Bulk downloads

You can download VCF files and QC reports directly from our servers. There is not currently a single file to download everything - it would be extremely large (many terrabytes) and constantly out of date as we continually add new studies. To manually or programmatically check which files are available for datasets and get the download links, use this website, ieugwasr, ieugwaspy or build your own wrapper around the API - details can be found on the dataset details page of any dataset e.g. [ieu-a-2](https://opengwas.io/datasets/ieu-a-2).

A list of all datasets, along with their meta-data and IDs, is also available through the API, R or Python packages, so it should be straightforward to create a subset of datasets to be downloaded through a loop. Note that there will be a relatively higher [cost](https://api.opengwas.io/api/#allowance) (deducted from your periodic allowance, usually given free of charge) to do this, as we pay money to the cloud service provider for the storage, requests handling and outbound bandwidth.

To learn more about how to use GWAS-VCF files, including how to use R and Python to efficiently manipulate and query, or convert to text files, see [gwas2vcf](https://github.com/MRCIEU/gwas2vcf/blob/master/README.md#convert).

---

### Credits

Many people have contributed to the OpenGWAS (formerly MR-Base) project. Main parties are (in alphabetical order, bold are active):

- Methodology: Benjamin Elsworth, **Tom Gaunt**, **Gibran Hemani**, Jie Zheng
- Data administration and curation: Denis Baird, Valeriia Haberland, **Philip Haycock**, Peter Matthews, Kaitlin Wade
- Data pipeline: **Xiaoyang Dai**, Benjamin Elsworth
- Software (server): Matt Lyon, **Weili Qiu**
- Software (client): Tom Gaunt, **Gibran Hemani**, **Tom Palmer**, **Weili Qiu**
- Platform architecture: **Weili Qiu**
- Research IT: Tessa Alexander, Jon Hallett, **Rick Henry**

Related projects:

- EpiGraphDB: [Yi Liu et al.](https://docs.epigraphdb.org/#citation)
- GPMap: [Andrew Elmore et al.](https://gpmap.opengwas.io/#:~:text=Building%20The%20Human%20Genotype%2DPhenotype%20Map%20to%20Harness%20Pleiotropy%20and%20Refine%20Disease%20Mechanisms)

Sincere thanks also go to the many GWAS consortia who have made the GWAS data that they generated publicly available, and many members of the IEU who have contributed to curating these data.

---

### Dependencies

OpenGWAS is built upon many important open source software projects, including but not limited to:

- [Flask](https://www.fullstackpython.com/flask.html)
- [Docker](https://www.docker.com/), [Kubernetes](https://kubernetes.io/)
- [Nginx](https://nginx.org/), [gevent](https://gevent.org/)
- [Redis](https://redis.io/)
- [Neo4j](https://neo4j.com/), [MySQL](https://www.mysql.com/)
- [Elasticsearch](https://www.elastic.co/), [Uptrace](https://uptrace.dev/)
- [Apache Airflow](https://airflow.apache.org/), [Snakemake](https://snakemake.readthedocs.io/en/stable/)

---

### Contributing consortia

Many thanks to the [NHGRI-EBI GWAS catalog](https://www.ebi.ac.uk/gwas/) and the studies contributing data to OpenGWAS

- [ADIPOGen](https://www.mcgill.ca/genepi/adipogen-consortium)
- [IIBDGC](https://www.ibdgenetics.org/)
- [GIANT](https://portals.broadinstitute.org/collaboration/giant/index.php/GIANT_consortium)
- [SSGAC](https://www.thessgac.org/)
- [ReproGen](https://www.reprogen.org/)
- [MESA](https://mesamalaria.org/mesa-track/genome-wide-association-studies-map-genetic-variation-underlying-mosquito-susceptibility)
- [HaemGen](https://haemgen.haem.cam.ac.uk/)
- [CORNET](https://datashare.is.ed.ac.uk/handle/10283/2787)
- GliomaScan
- [DCCT / EDIC](https://repository.niddk.nih.gov/studies/edic/)
- [BioBank Japan](http://jenger.riken.jp/en/)
- [IMSGC](https://www.well.ox.ac.uk/wtccc2/ms/)
- IAC
- [EAGLE](http://copsac.com/home/research-clusters/eagle-consortium/)
- [EGG](https://egg-consortium.org/)
- [ENIGMA](http://enigma.ini.usc.edu/)
- GIS
- [GUGC](http://metabolomics.helmholtz-muenchen.de/gugc/)
- [HRgene](https://walker05.u.hpc.mssm.edu/)
- [MinE](https://www.projectmine.com/)
- [UK Biobank](https://www.ukbiobank.ac.uk/)
- [CKDGen](https://ckdgen.imbi.uni-freiburg.de/)
- [ISGC](https://strokegenetics.org/)
- [IPSCSG](https://www.ipscsg.org/)
- [OCAC](http://ocac.ccge.medschl.cam.ac.uk/)
- [BCAC](http://bcac.ccge.medschl.cam.ac.uk/)
- [GPC](https://www.med.unc.edu/pgc/download-results/gpc/)
- [CHARGE](http://www.chargeconsortium.com/)
- arcOGEN
- [PRACTICAL](http://practical.icr.ac.uk/)
- [PGC](https://www.med.unc.edu/pgc/)
- iPSYCH-PGC
- PGC-ED
- [GeM-HD](https://enroll-hd.org/)
- Sclerostin genetics consortium
- [UK Biobank+INTERVAL+UK BiLEVE](https://www.ukbiobank.ac.uk/)
- [Biobank Japan Project](http://jenger.riken.jp/en/)
- [DIAGRAM](https://diagram-consortium.org/)
- [DIAGRAMplusMetabochip](https://diagram-consortium.org/)
- [IGAP](http://web.pasteur-lille.fr/en/recherche/u744/igap/igap_download.php)
- [GLGC](http://csg.sph.umich.edu/willer/public/lipids2013/)
- AMDGene
- ALSgene
- [GABRIEL](https://www.cnrgh.fr/gabriel/index.html)
- GCAN
- [GEFOS](http://www.gefos.org/)
- [C4D](http://www.cardiogramplusc4d.org/)
- [CARDIoGRAMplusC4D](http://www.cardiogramplusc4d.org/)
- [MAGIC](https://www.magicinvestigators.org/)
- [CARDIoGRAM](http://www.cardiogramplusc4d.org/)
- [PanScan](https://dceg.cancer.gov/research/cancer-types/pancreas/panscan)
- ICBP
- TAG
- [ILCCO](https://ilcco.iarc.fr/)
- SpiroMetaplusCHARGE
- TRICL
- ...
