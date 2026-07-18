#!/usr/bin/env python3
"""Beta release archive assembler checks."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
FIXTURE = ROOT / "tests" / "fixtures" / "beta-release-archive-assembler.json"
SCENARIOS = ROOT / "tests" / "fixtures" / "beta-release-archive-assembler-scenarios.json"

sys.path.insert(0, str(ROOT / "scripts"))
import beta_release_archive_assembler  # noqa: E402


def run_assembler(*extra_args: str) -> dict:
    proc = subprocess.run(
        [PYTHON, "scripts/beta_release_archive_assembler.py", *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def normalize_source_commit(value):
    if isinstance(value, dict):
        return {
            key: (
                "<current-git-head>"
                if key == "sourceCommit"
                else "<commit-derived-manifest-sha>"
                if key == "manifestSha256"
                else normalize_source_commit(child)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [normalize_source_commit(child) for child in value]
    return value


def positive_scenario() -> dict:
    scenarios = json.loads(SCENARIOS.read_text())
    return beta_release_archive_assembler.merge_scenario(scenarios["defaults"], {"id": "mutation"})


def assert_positive_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    mutator(scenario)
    result = beta_release_archive_assembler.build_result(scenario, beta_release_archive_assembler.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def assert_rc_mutation_fails(mutator, expected_path: str) -> None:
    scenario = positive_scenario()
    source = json.loads((ROOT / "tests" / "fixtures" / "beta-release-candidate-bundle.json").read_text())
    mutator(source)
    with tempfile.TemporaryDirectory(prefix="beta-archive-rc-") as tmp:
        rc_path = Path(tmp) / "rc.json"
        rc_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
        scenario["releaseCandidateManifestPath"] = str(rc_path)
        scenario["expectedReleaseCandidateHashes"] = [
            {
                "path": str(rc_path),
                "sha256": beta_release_archive_assembler.digest(rc_path),
            }
        ]
        expected_hashes = copy.deepcopy(scenario["expectedIncludedFileHashes"])
        expected_hashes.append({"path": str(rc_path), "sha256": beta_release_archive_assembler.digest(rc_path)})
        scenario["expectedIncludedFileHashes"] = expected_hashes
        result = beta_release_archive_assembler.build_result(scenario, beta_release_archive_assembler.source_commit())
    assert result["status"] == "fail"
    assert expected_path in {finding["path"] for finding in result["findings"]}


def main() -> int:
    doc = run_assembler()
    fixture = json.loads(FIXTURE.read_text())
    assert normalize_source_commit(doc) == normalize_source_commit(fixture)
    assert doc["mode"] == "beta-local-release-archive-assembler"
    assert doc["issue"] == 275
    assert doc["parentEpic"] == 220
    assert doc["follows"] == [273]
    assert doc["relatedEpic"] == 247
    assert doc["status"] == "pass"
    assert len(doc["sourceCommit"]) == 40
    assert doc["boundaries"]["deterministicLocalOnly"] is True
    assert doc["boundaries"]["dryRunByDefault"] is True
    assert doc["boundaries"]["archiveWriteRequiresExplicitPath"] is True
    assert doc["boundaries"]["serviceStarted"] is False
    assert doc["boundaries"]["networkAccess"] is False
    assert doc["boundaries"]["credentialAccess"] is False
    assert doc["boundaries"]["liveRuntimeActivation"] is False
    assert doc["boundaries"]["walletAccess"] is False
    assert doc["boundaries"]["paymentAccess"] is False
    assert doc["boundaries"]["facilitatorAccess"] is False
    assert doc["boundaries"]["settlementAccess"] is False
    assert doc["boundaries"]["devnetAccess"] is False
    assert doc["boundaries"]["mainnetAccess"] is False
    assert doc["boundaries"]["deploymentPublished"] is False
    assert doc["boundaries"]["packagePublished"] is False
    assert doc["boundaries"]["archivePublished"] is False
    assert doc["boundaries"]["externalSpend"] is False
    assert "mainnet remains blocked" in doc["mainnetStatement"]
    assert doc["summary"] == {
        "acceptVerdicts": 1,
        "holdVerdicts": 11,
        "rejectVerdicts": 1,
        "positiveScenarios": 1,
        "negativeScenarios": 12,
        "failClosedScenarios": 12,
    }

    results = {result["id"]: result for result in doc["results"]}
    positive = results["release-archive-assemble-accept-pass"]
    assert positive["status"] == "pass"
    assert positive["verdict"] == "accept"
    assert positive["releaseId"] == "reddiagent-beta-0"
    assert positive["releaseCandidateId"] == "reddiagent-beta-0-rc-local-1"
    assert positive["releaseCandidateManifest"]["path"] == "tests/fixtures/beta-release-candidate-bundle.json"
    assert positive["releaseCandidateManifest"]["hashMatches"] is True
    assert positive["archiveMetadata"]["archiveId"] == "reddiagent-beta-0-rc-local-1-local-review-archive"
    assert positive["archiveMetadata"]["archiveName"].endswith(".manifest.json")
    assert positive["archiveMetadata"]["checksumPath"].endswith(".manifest.sha256")
    assert positive["archiveMetadata"]["format"] == "manifest-and-sha256-only"
    assert len(positive["archiveMetadata"]["manifestSha256"]) == 64
    assert "tests/fixtures/beta-release-candidate-bundle.json" in positive["includedFiles"]
    assert "tests/fixtures/beta-release-verification.json" in positive["includedFiles"]
    assert "docs/PUBLIC-DEMO-WALKTHROUGH-VIDEO.md" in positive["includedFiles"]
    assert "scripts/public_demo_walkthrough_video.sh" in positive["includedFiles"]
    assert "archive publishing outputs" in positive["excludedFiles"]
    assert positive["evidenceHashes"]
    assert positive["publicDemoMetadata"]["publicDemoUrl"] == "https://present-hearth-vhey.here.now/"
    assert all(item["exists"] and item["hashMatches"] and item["sha256"] for item in positive["contentAddressedInventory"])
    assert "manifest/checksum archive package only" in positive["operatorNextStep"]

    finding_paths = {
        result_id: {finding["path"] for finding in result["findings"]}
        for result_id, result in results.items()
    }
    assert "releaseCandidateManifest.exists" in finding_paths["missing-release-candidate-manifest-denied"]
    assert "releaseCandidateManifest.sha256" in finding_paths["stale-release-candidate-manifest-denied"]
    assert "contentAddressedInventory.tests/fixtures/beta-release-verification.json.sha256" in finding_paths["stale-included-file-hash-denied"]
    assert "observedArchiveFiles" in finding_paths["unexpected-extra-artifact-denied"]
    assert "archiveFiles" in finding_paths["missing-demo-evidence-denied"]
    assert "archiveFiles" in finding_paths["missing-verifier-evidence-denied"]
    assert "operatorNextStep" in finding_paths["unsafe-activation-deployment-publishing-claim-denied"]
    assert "scenario.credentialPayload" in finding_paths["credential-like-leakage-denied"]
    assert "unsafeEnvValues.OPENAI_API_KEY" in finding_paths["unsafe-env-values-denied"]
    assert "walletRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "paymentRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "facilitatorRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "settlementRequested" in finding_paths["wallet-payment-facilitator-settlement-denied"]
    assert "liveNetworkEnabled" in finding_paths["devnet-mainnet-live-network-denied"]
    assert "devnetRequested" in finding_paths["devnet-mainnet-live-network-denied"]
    assert "mainnetRequested" in finding_paths["devnet-mainnet-live-network-denied"]
    assert "archivePublished" in finding_paths["unsafe-archive-publish-reject-denied"]
    assert results["unsafe-archive-publish-reject-denied"]["verdict"] == "reject"

    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedReleaseCandidateHashes": []}), "releaseCandidateManifest.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"expectedIncludedFileHashes": []}), "contentAddressedInventory.docs/PUBLIC-DEMO-WALKTHROUGH-VIDEO.md.expectedSha256")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"mainnetRequested": True}), "mainnetRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"paymentRequested": True}), "paymentRequested")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"credentialPayload": "bearer token"}), "scenario.credentialPayload")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"operatorNextStep": "Archive published."}), "operatorNextStep")
    assert_positive_mutation_fails(lambda scenario: scenario.setdefault("unsafeEnvValues", {}).update({"API_TOKEN": "secret-value"}), "unsafeEnvValues.API_TOKEN")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseId": "reddiagent-beta-stale"}), "releaseId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"releaseCandidateId": ""}), "releaseCandidateId")
    assert_positive_mutation_fails(lambda scenario: scenario.update({"archiveId": "unreviewed-archive"}), "archiveId")
    assert_rc_mutation_fails(lambda rc: rc.update({"status": "fail"}), "releaseCandidateManifest.status")
    assert_rc_mutation_fails(lambda rc: rc["boundaries"].update({"networkAccess": True}), "releaseCandidateManifest.boundaries.networkAccess")
    assert_rc_mutation_fails(lambda rc: rc["results"][0].update({"releaseCandidateId": "stale"}), "releaseCandidateManifest.results.releaseCandidateId")

    with tempfile.TemporaryDirectory(prefix="beta-archive-out-") as tmp:
        written = run_assembler("--archive-output-dir", tmp)
        paths = written["localArchiveWrite"]
        manifest = Path(paths["manifestPath"])
        checksum = Path(paths["checksumPath"])
        assert manifest.exists()
        assert checksum.exists()
        assert checksum.read_text().split()[0] == beta_release_archive_assembler.sha256_text(manifest.read_text())

    print("PASS beta release archive assembler")
    return 0


if __name__ == "__main__":
    sys.exit(main())
