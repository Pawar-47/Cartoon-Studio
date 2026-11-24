# Test Report

## Current baseline
Automated tests have been added for:
- Health endpoint.
- Dashboard response.
- Local project creation and listing.

CI workflow checks:
- Ruff lint.
- Python compile.
- pytest.
- Windows bootstrap ZIP packaging and artifact upload.

## Evidence policy
Only record a test as PASS when a completed run shows success. Record the workflow run URL, commit SHA, runner, test command, result and relevant failure details. A queued or in-progress workflow is not a pass.

## Known CI history
Initial workflow run failed at Ruff import sorting on the first application commit. The import block was corrected in a subsequent commit. Later workflow runs are being checked against the corrected source.
