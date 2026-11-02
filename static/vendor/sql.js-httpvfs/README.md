# sql.js-httpvfs 0.8.12 (vendored)

Reads a SQLite file over HTTP range requests in a Web Worker, so the Data page
can query the Analysis Catalog without a server (decision 7). Copied unchanged
from the npm package's `dist/` folder:

- package: https://www.npmjs.com/package/sql.js-httpvfs/v/0.8.12
- source: https://github.com/phiresky/sql.js-httpvfs
- tarball sha256: `f7e7c499dc1e098b25177b0dd7381def6182df98821bdf3b7b1a1910741b1b70`
- npm integrity: `sha512-lcEBc2q0psFRfdCx8Di22oUIkkv5MUIaVO/fGCj/Jjx6YQDKVylQEcjd7NSSbmINHTRwVkm/vWP8uuevT7Rkkw==`

Bundles sql.js (MIT, https://github.com/sql-js/sql.js), SQLite 3.35.0
(public domain) compiled with FTS5, and Comlink (Apache-2.0). sql.js-httpvfs
itself is Apache-2.0; see LICENSE.

The package has not been updated since 2022. It reads the catalogue written
by SQLite 3.54, including its FTS5 index (checked 2026-11-02, decision 13).
To replace it, only `static/js/catalogue-search.js` needs to change.
