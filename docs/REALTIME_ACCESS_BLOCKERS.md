# Real-time source access handoff

When an official source cannot be integrated because of login, institutional approval, API token, IP allow-listing, unstable download links, or undocumented schemas, the project must not fabricate a replacement.

Provide one or more of the following instead:

- public source/documentation URL;
- API endpoint documentation and one redacted sample JSON/XML response;
- CSV/XLSX export with update timestamp and source owner;
- GeoJSON/Shapefile/GeoTIFF export;
- WMS/WFS/ArcGIS REST service URL plus exact layer name/id and legend/class metadata;
- screenshot of the portal fields when downloads are unavailable;
- authorization/error response code for troubleshooting.

Never commit or paste passwords, API keys, bearer tokens or session cookies. Configure secrets only in the deployment platform. If IP whitelisting is required, provide the hosting platform's egress IP information to the source authority rather than bypassing the restriction.

## Current priority blockers

1. IMD: approved API profile/authentication method and one sample response for each approved endpoint.
2. NDMA SACHET: verified CAP/RSS feed/identifier mapping or official subscribed-agency feed details.
3. Habitation/vulnerability data: accountable source with coordinates or stable geographic identifiers.
4. Shelter/relocation sites: accountable inventory with location, capacity, occupancy and resource constraints.
5. Hazard layers: class legend, reference period, CRS and documented class-to-0–100 mapping before numerical use.
