MANIFESTS: BLOCKED

WP-NT-06 independent verifier preparation at 2026-10-10T03:43:52.290827+00:00.

Created review/manifests/frozen.json and review/manifests/fresh.json. Each has owner `independent_verifier`, generated_utc, generator provenance, 24 W + 24 N independently regenerated specifications, and the prescribed 81-point k/40 grid. The current harness format is configuration + configuration_sha256 + frozen_utc; reviewer ownership/generator metadata and instance_ids are top-level additions. IDs map one-to-one to configuration.instances by game and seed. No dedicated independent schema/owner/count validator exists in the inspected harness.

Validated JSON round trips, UTF-8 without BOM, configuration and instance SHA-256 digests, 96 globally unique IDs and construction seeds, and disjoint frozen/fresh/development seed sets (including legacy core development ranges). Frozen W 2026104000..2026104023; frozen N 2026104200..2026104223; fresh W 2026104100..2026104123; fresh N 2026104300..2026104323. Sampling bases 2026104800 and 2026104900 are distinct from each other, construction seeds and development sampling base 2026104700. W frames satisfy unitarity/determinant-one to absolute 1e-12. N angles satisfy the plan intervals. Independently regenerated specifications exactly match harness construction for all 96 cases; the generator did not call either core make_instance function to produce its specifications. Hashes freeze the inspected implementation/channel and plan amendment.

Actual loader-boundary checks (atomic output mocked; evaluate_case replaced with a stopping sentinel, never numerical evaluation):
- frozen: --independent-manifest is for the fresh suite only
- fresh: ACCEPTED; stopped at evaluate_case before any numerical evaluation/output

Requested command executed with repository Python and bytecode disabled:
`python -B experiments/run.py --suite frozen --independent-manifest review/manifests/frozen.json --draws 5 --output-dir results/quick-frozen-smoke-nt`
Exit code 1: `ValueError: --independent-manifest is for the fresh suite only`. Rejection occurs before computation. Verified the temporary smoke directory was empty, removed it nonrecursively, and confirmed it no longer exists. No numerical output was generated.

Loader defects and required builder fixes (implementation untouched):
- experiments/run.py:206-207 rejects every independent frozen manifest. Permit frozen and fresh, validate declared suite against requested suite, and require the verifier-owned file for evaluation.
- experiments/run.py:222-224 checks only configuration digest and equality to a freshly builder-generated candidate. It never validates owner, generated_utc, generator, unique IDs/seeds, 24 cases per game, development/frozen disjointness, or authoritative independent instance specifications. Implement an explicit schema validator; compare immutable experiment/channel/implementation settings separately, validate the independent specifications, and retain their digest rather than requiring identity to builder-generated instance content. The staged files use the exact preregistered ranges and are compatible with the existing fresh configuration hash check.
- experiments/run.py:225-226 silently creates a missing supplied manifest; missing explicit verifier paths must fail, never become builder-owned replacements.
- experiments/run.py:230-249 and :290: --draws 5 changes bootstrap draws only. Without --quick, the requested command would run 144 case/model tasks on 81 scales plus W sensitivity curves after the frozen guard is repaired. This is a full sweep, not a tiny smoke. Provide a bounded smoke/validate-only mode that validates the full manifest then evaluates a small subset without changing the evaluation manifest or emitting evidence/recorded_local.py. Do not rerun the requested command unbounded after repair.

The first-line BLOCKED means frozen loader acceptance and the requested numerical smoke are not established. It does not invalidate the independently constructed planned cases. No crossover reproduction, scientific gate PASS, full sweep, bootstrap evidence or cloud confirmation is claimed. Fresh loader acceptance was checked only to its first evaluation boundary. Full frozen/fresh runs and numerical reproduction remain orchestrator-owned. Global process/provenance logs were not modified because this task authorizes only the three review files. All hashed implementation files remained unchanged during these checks.
