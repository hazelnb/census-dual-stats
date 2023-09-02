# census-dual-stats
A project to study what dual graphs know about census geographies.

## Populating `data/`
To use any of this project's code, you will need some dual graphs! The `import_graph` function expects dual graphs to be in the correct folder for the given geography level and named in the format `{geography level prefix}_{lowercase two letter state abbrev}.json`. The geography level prefixes appear in the following table:
| Geography Level | Prefix |
| --------------- | ------ |
| "block"         | "b"    |
| "blockgroup"    | "bg"   |
| "tract"         | "t"    |
| "county"        | "cnty" |
| "vtd"           | "vtd"  |

So, for example, the dual graph for New York counties should be `data/county_graphs/cnty_ny.json`.

If you want to use the `generate_shp` utility function, you will need the shapefiles you're using in `data/` as well. These follow a similar idea, but use the census filenaming scheme. If you download 2020 shapefiles from the census API, they will be named correctly, but I will document the filename prefixes here for completeness. All the shapefiles start with `tl_2020_{state fips}_` and end with a geography level abbreviation from the following table.
| Geography Level | Filename Format |
| --------------- | ------ |
| "block"         | "tabblock20" |
| "blockgroup"    | "bg"   |
| "tract"         | "tract"    |
| "county"        | "county20" |
| "vtd"           | "vtd20"  |

This method checks for either a zipped shapefile (`filename.zip`) or an unzipped shapefile (a directory `filename` with contents named the same as the directory with extensions `.cpg`, `.dbf`, `.prj`, `.shp`, `.shp.ea.iso.xml`, `.shp.iso.xml` and `.shx`). So for example, the shapefile for New York (FIPS 36) counties would either be `data/county_shapefiles/tl_2020_36_county20.zip` or `data/county_shapefiles/tl_2020_36_county20/` containing:
`data/county_shapefiles/tl_2020_36_county20/tl_2020_36_county20.cpg`
`data/county_shapefiles/tl_2020_36_county20/tl_2020_36_county20.dbf`
`data/county_shapefiles/tl_2020_36_county20/tl_2020_36_county20.prj`
`data/county_shapefiles/tl_2020_36_county20/tl_2020_36_county20.shp`
`data/county_shapefiles/tl_2020_36_county20/tl_2020_36_county20.shp.ea.iso.xml`
`data/county_shapefiles/tl_2020_36_county20/tl_2020_36_county20.shp.iso.xml`
`data/county_shapefiles/tl_2020_36_county20/tl_2020_36_county20.shx`

  
