# Verified public service contract (16 September 2026)

TS06 is based on the current public BRO/PDOK interfaces verified during implementation.

## PDOK GM-in-samenhang OGC API Features

Base service:

`https://api.pdok.nl/tno/bro-grondwatermonitoring-in-samenhang-karakteristieken/ogc/v1`

Collections used:

- `gm_gmw`
- `gm_gmw_monitoringtube`
- `gm_gld`

The kenset is relational. TS06 follows the documented foreign-key route:

`gm_gld.gm_gmw_monitoringtube_fk`
→ `gm_gmw_monitoringtube.gm_gmw_monitoringtube_pk`
→ `gm_gmw_monitoringtube.gm_gmw_fk`
→ `gm_gmw.gm_gmw_pk`.

Important fields include `ground_level_position` on GMW and `screen_top_position` / `screen_bottom_position` on monitoring tubes.

### `number_of_observations` is not a measurement-point count

The `gm_gld` kenset exposes `number_of_observations`. In the GLD information model an **Observatie** is an observation period/activity whose result is a complete `Tijdmeetwaardereeks`; that series can contain many individual time-value pairs. The kenset count must therefore not be used as if it were the number of individual groundwater-level measurements.

This distinction was also confirmed empirically during live qualification: GLD objects with catalog counts of only tens of `Observatie` entities yielded tens of thousands of individual time-value pairs from the compact CSV service.

Consequences for WDM-LHM:

- a catalog observation count can only be used as a coarse source-side routing field;
- scientific minimum-measurement requirements are evaluated **after download** from the number of parsed time-value pairs;
- time-series span is evaluated from the parsed timestamps for scientific admission;
- TS07 live workflows use a permissive catalog count threshold and let the Stage-A screen apply the actual `n_observations` requirement.

Source basis: BRO GLD catalog sections `Observatie` and `Tijdmeetwaardereeks`, where one Observatie results in one time series containing time-value pairs.

## BRO GLD REST CSV

Base service:

`https://publiek.broservices.nl/gm/gld/v1/`

The PDOK `gm_gld` collection exposes per-object URLs for unknown, preliminary and fully assessed compact CSV series. TS06 prefers fully assessed series and can fall back to preliminary series when configured.

The live service can return compact CSV without a header. TS06 supports this positional form only when the first two fields validate overwhelmingly as timestamp and numeric water-level value; otherwise it fails closed rather than guessing a schema.

The BRO documentation states that GLD water level values use metres; GMW ground-level position is a vertical position in metres relative to NAP for land locations. TS06 therefore writes `obs_head_mnap` and `ground_level_mnap`, while preserving raw BRO identifiers and source classification.

## Rate limiting

The public BRO REST services are rate limited. Documentation states an average of 3 requests/s for GLD endpoints. TS06 defaults to 2.5 GLD requests/s and caches exact response bytes to avoid repeated service load.

## WDM

Current PDOK WDM WMS:

`https://service.pdok.nl/tno/bro-model-grondwaterspiegeldiepte/wms/v2_0`

Relevant queryable layers include GHG, GLG and GVG, expressed in cm below ground level. TS06 records the WDM service endpoint in its manifest but intentionally does not yet merge WDM values into the observation bundle: WDM remains a dependent statistical product until the lineage audit is complete.
