# Promote a reviewed teaching assessment

A package review records the task, exact export, four axis observations, attribution and reviewed evidence. The accepted catalog pins one owner assessment per export and stable task ID. Maintained selections identify which accepted task a learner should start with. Accepted alternatives remain available to the Gallery where the export has one unambiguous task or a maintained task determines its display.

1. Identify the owner review under `reviews/`, the exact export path, and the collection and register IDs from [maintained selections](../gallery/maintained-selections.json). Reuse an established task ID for the same learner action.
2. Preview a promotion from the repository root. The command selects the reviewed row by export and task. If more than one row matches, it lists the candidate tasks and their pins for selection with `--reviewed-sha256`.

   ```sh
   python3.12 tools/maintained_teaching.py promote \
     --review "$review" \
     --export "$export" --task-id "$task" \
     --collection-id "$collection" --family-id "$family" \
     --disposition maintained --replaces "$previous_export"
   ```

   Use `--disposition alternative` to retain the review without changing the starting file. Add `--replaces` only for an exact starting file under that register ID. For a new register entry in an existing collection, supply a distinct `--family-id` and `--new-family-label` with its first maintained export.

3. Inspect the proposed pins, attribution, task, scores, evidence, exemptions and selections. Run the same command with `--apply --expect-state "$plan_sha256"`, using the reported `planSha256`. If the plan is stale, rerun the preview and review the changed inputs. Repeating an applied instruction leaves the files as they are.

Promotion regenerates the [Teaching register](../gallery/maintained-models.md) and [scorecard](../../records/campaigns/teaching-asset-review/current-coverage.md) from the accepted state. Run `python3.12 tools/maintained_teaching.py --check` to validate every accepted export and task as well as the two views. When the review should appear in the Library, declare its exact revision route in the owner review and its package in the [Library release inputs](../gallery/asset-library.md#making-a-release-selection).

If interrupted during a write, run `python3.12 tools/maintained_teaching.py recover`. The command checks the saved result and finishes applying it under the same lock. If a target file has other edits, preserve those edits and reconcile them with the local ignored promotion journal before retrying recovery.
