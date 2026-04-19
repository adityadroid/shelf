# Task 012: Legacy DOC Parsing and Failure Handling

- Status: `Done`
- Priority: `P1`
- Depends On: `010`, `011`
- Last Updated: `2026-04-19`

## Objective

Add legacy `.doc` support using `antiword` with safe subprocess handling, timeout controls, and consistent parser diagnostics.

## Why This Matters

`.doc` is explicitly in MVP scope, but it is the riskiest supported parser because it depends on a local CLI. Handling this safely protects app stability and trust.

## Scope

- Integrate `antiword` through a controlled subprocess boundary.
- Capture stdout text when extraction succeeds.
- Handle non-zero exits, timeouts, unsupported documents, and missing binary cases safely.
- Map all outcomes into the same normalized parser result contract.

## Out of Scope

- Installing `antiword` automatically without a broader packaging decision.
- OCR or proprietary format support beyond `.doc`.

## Implementation Checklist

- Define the subprocess invocation wrapper with path sanitization and timeout behavior.
- Detect and report missing `antiword` availability clearly.
- Normalize extracted text and parser diagnostics into the shared document model.
- Add tests for command success, timeout, and failure-path behavior using mocks or controlled fixtures.
- Document operational assumptions for local environments and packaging later.

## Acceptance Criteria

- Supported `.doc` files can be extracted locally when `antiword` is available.
- Failed `.doc` parses do not crash workers or poison the queue.
- Missing dependency and timeout cases are observable and recoverable.

## Validation

- Run parser tests for success and failure scenarios.
- Manually verify at least one `.doc` parsing path if a local fixture and binary are available.

## Risks and Notes

- Shell invocation must be sanitized and non-interactive.
- Because `.doc` support is more fragile, diagnostics should be visible in logs and failures storage from day one.
