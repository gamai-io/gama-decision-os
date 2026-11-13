# Release checklist — GAMA Decision OS v1.2.2 (public core)

Status of this repository: **prepared, committed locally, tagged, NOT pushed.**
No git remote is configured.

## Done in this package

- [x] Standalone `gama_decision/` package, Python standard library only at runtime.
- [x] No private repository paths, internal IP ranges, internal hostnames,
      API-key prefixes or private-key blocks in the working tree (verified with
      the release grep described below).
- [x] `python3 -m pytest tests/ -q` → 27 passed, 1 skipped (live network test
      skipped unless `GAMA_SPECULATIVE_URL` is set).
- [x] Apache-2.0 `LICENSE`, `LICENSE-ENTERPRISE.md`, `VERSION`, `pyproject.toml`.
- [x] `README.md` documents the open-core boundary.
- [x] Public site (`site/`), docs (`MANIFESTO`, `SITE_ARCHITECTURE`, `BENCHMARK`)
      and product collateral included.
- [x] `examples/` with direct Python and HTTP/curl usage.
- [x] `git init`, initial commit, tag `v1.2.2`. **No remote, no push.**

Release grep used: a recursive scan for private RFC1918 / overlay-network
ranges, the private build-directory path, common provider key prefixes,
private-key block markers, and the internal hostnames. Result: no matches. The exact
command is recorded in the release session log, not in this file, so the
checklist itself does not trip the scan.

## Must be done before publishing (blockers)

- [ ] **Rotate every secret that ever appeared in the old private history.**
      Treat all of them as compromised: API keys (LLM providers, cloud, DNS,
      Stripe), SSH keys, webhook secrets, tunnel credentials, database
      passwords, bot tokens. Rotate first, publish later.
- [ ] **Scrub or abandon the old history.** Either publish only this clean repo
      (recommended), or run `git filter-repo` on the old repository and verify
      with `git log -p` plus a secret scanner. Never push the old history.
- [ ] **Independent secret scan of the new repo**, e.g. `gitleaks detect` and
      `trufflehog filesystem .` — not only grep.
- [ ] **Domain and DNS:** point the chosen domain at the static host, add
      `A`/`AAAA`/`CNAME`, enable HTTPS/HSTS, publish `robots.txt` and
      `sitemap.xml` from the root.
- [ ] **Stripe:** create live products/prices, register the webhook endpoint,
      store keys only in the secret manager, test one end-to-end checkout in
      test mode, then one low-value live transaction.
- [ ] **Email deliverability:** SPF, DKIM, DMARC for the sender domain; test
      transactional mail and the `security@` mailbox.
- [ ] **Hosting:** choose static host/CDN, set cache headers, verify all internal
      links and that `404.html` is served correctly.
- [ ] **Legal review:** Apache-2.0 headers, enterprise license template, privacy
      policy, terms of service, and any trademark/name clearance for the product
      and domain.
- [ ] **Repository settings:** create the public repo under the chosen org,
      enable branch protection, required CI, 2FA, and signed releases.
- [ ] **CI:** run the test suite on Python 3.9–3.12, add `pip-audit` and an SBOM
      (e.g. CycloneDX) to the release artifacts.
- [ ] **Verify the published site claims** against `docs/BENCHMARK.md`; do not
      ship a number without a reproducible source and the stated caveat.
- [ ] **Add the remote and push only after all of the above.** This has not been
      done.

## Known caveats to disclose

- The calibration ECE of 0.299211 comes from a set with accuracy 1.0, which is
  degenerate; it is a diagnostic, not a production guarantee.
- The live speculative classifier is disabled unless `GAMA_SPECULATIVE_URL` is
  configured; the core makes no network calls by default.
- Enterprise features are not part of this package.

## Suggested first release sequence

1. Rotate secrets.
2. Re-run the secret scanners.
3. Run tests on the supported Python versions.
4. Create the remote, push `main`, push tag `v1.2.2`.
5. Publish signed artifacts/SBOM.
6. Deploy the static site and run a link/HTTPS check.
7. Announce.
