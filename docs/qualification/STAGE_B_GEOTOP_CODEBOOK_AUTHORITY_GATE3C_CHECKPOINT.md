# Stage-B GeoTOP 1.6.1 codebook authority — Gate 3C checkpoint

Status: **QUALIFIED_CURRENT_DELIVERY_PAGE_DISCOVERY_GATE_3C**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_161_CURRENT_DELIVERY_AUTHORITY_DISCOVERY`

## Repository state

- canonical `main`: `3cce6d69af54b213b07c03b85f9e61c800ef93fd`
- branch: `work/stage-b-geotop-codebook-authority`
- PR: #14
- qualified Gate-3C head: `4add0b90bd83550633e88bac8d276853739be418`
- tracking issue: #4

## Reused evidence

Gate 3C followed only the official URL already discovered and qualified by Gate 2:

`https://www.dinoloket.nl/bekijken-en-aanvragen-geotop`

No generic web search was performed and no discovered link was followed by this gate.

## Qualification

- ordinary CI run `35210829876`: PASS;
- Python 3.10: PASS;
- Python 3.12: `156 passed`;
- live Gate-3C run `35210829922`: PASS;
- page SHA-256: `15e7cb9df5712583975bf23a0100f0a7c9c99d3c342d1959b2c35ed1f6e7c72c`;
- artifact ID: `10492190419`;
- artifact ZIP SHA-256: `90774834296a911d57b67b18217726a75ea546ed75018a75e1281f0b6cbb7e36`.

The qualified page contains markers for GeoTOP, 1.6.1, lithoklasse, model files, download and zip. It does not expose a direct current reference-list file in the bounded link inventory.

The relevant official next-level link exposed by this page is:

`https://www.dinoloket.nl/modelbestanden-aanvragen`

Other candidate links are self-links, the already-qualified GeoTOP documentation page, the English equivalent and the already-qualified v1.6.1 release PDF.

## Scientific boundary

Gate 3C does not establish code semantics or version compatibility. In particular:

- the absence of a direct reference-list link on this page is not evidence that no current reference list exists;
- no meaning is assigned to `lithok=0`;
- no meaning is assigned to `strat=1000,3030,3100,4100,5000,5120`;
- no geological or hydraulic inference is made;
- no Stage-B admission state changes.

## Verdict

**QUALIFIED_CURRENT_DELIVERY_PAGE_DISCOVERY_GATE_3C**

Current-delivery authority has not yet been established.

## Next permitted action

Gate 3D may acquire only `https://www.dinoloket.nl/modelbestanden-aanvragen`, because that URL is explicitly exposed by the qualified Gate-3C page. It may persist the raw page and inventory official links/forms relevant to obtaining GeoTOP model files or accompanying reference lists. It must not submit an order/request, follow discovered download links, translate codes or infer geology/hydraulics.
