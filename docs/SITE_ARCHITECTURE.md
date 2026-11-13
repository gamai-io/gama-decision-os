# Site architecture

The public site is a set of self-contained static pages in [`site/`](../site/).
No build step, CDN, or server-side runtime is required to serve it.

## Pages

| File | Purpose |
| --- | --- |
| `index.html` | Landing page: positioning, three pillars, headline metrics, links to pricing and docs. |
| `decision-os.html` | Product page for the three-gate runtime and evidence model. |
| `gamacode.html` | Agent/runtime overview and capability description. |
| `pricing.html` | Community / Pro / Enterprise tiers and open-core boundary. |
| `contact.html` | Contact and demo request. |
| `sigil.html` | Trust/evidence layer description. |
| `verify.html` | How to verify an evidence receipt. |
| `404.html` | Not-found page. |
| `robots.txt` | Crawler policy. |
| `sitemap.xml` | Canonical URL list. |

## Content model

- Every page is standalone HTML with inline CSS and minimal inline JS.
- Shared visual language: dark background, teal/blue accent, monospace data
  blocks, EN/BS copy where the page is bilingual.
- Claims that have a number should link to `docs/BENCHMARK.md` or a specific
  test. Claims without evidence are phrased as design intent, not measurement.

## Open-core messaging

- The site must say clearly that the core is Apache-2.0 and that Enterprise is a
  separate commercial license.
- Pricing pages must not imply that enterprise-only features ship in the core.

## Serving locally

```bash
python3 -m http.server 8099 --directory site
# open http://127.0.0.1:8099/
```

## Deployment

Deploy the contents of `site/` as static files behind any web server or CDN.
Recommended baseline:

- HTTPS only, HSTS enabled,
- `robots.txt` and `sitemap.xml` served from the domain root,
- cache `*.html` briefly and fingerprint any future static assets.

DNS, certificate and CDN credentials are deployment secrets and never belong in
this repository.
