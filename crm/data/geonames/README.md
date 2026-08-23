# Global geography source data

NebrasCRM ships a compact, offline-importable global administrative dataset:

- `countryInfo.txt` — countries and territories
- `admin1CodesASCII.txt` — first-level administrative regions/states
- `cities500.zip` — cities/localities with population 500+ and administrative seats

## Source and attribution

Source: [GeoNames](https://www.geonames.org/), export dump files.

Data is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

The application imports the source archive into SQLite on first initialization.
It uses no geocoding API or network connection at runtime. `SHA256SUMS.txt` records
the bundled source checksums. The selected `cities500` coverage is intentionally
practical for CRM location selection: it contains global cities and administrative
centers rather than every tiny locality in GeoNames' full multi-million-record dump.
