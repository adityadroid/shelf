# Task 011: PDF and DOCX Parsing Pipeline

- Status: `Not Started`
- Priority: `P0`
- Depends On: `010`
- Last Updated: `2026-04-19`

## Objective

Implement the first production parsers for `.pdf` and `.docx`, including text extraction, metadata capture, and parser-status handling.

## Why This Matters

PDF and DOCX are core MVP file types, and they unlock the majority of expected user value early. They also establish the real parser quality bar before legacy `.doc` support is added.

## Scope

- Add `pypdf` extraction for text PDFs.
- Add `python-docx` extraction for DOCX content.
- Normalize whitespace and preserve useful page/section metadata.
- Mark near-empty or partially readable documents clearly.

## Out of Scope

- OCR.
- Legacy `.doc` support.
- Embeddings or search ranking changes.

## Implementation Checklist

- Implement page-by-page PDF extraction with metadata preservation where possible.
- Implement DOCX paragraph, header, and practical table-text extraction.
- Normalize text consistently across both parsers.
- Record parser status for empty, partial, unreadable, or password-protected cases.
- Add parser fixture tests with representative sample files and assertions on extracted text.

## Acceptance Criteria

- Shelf can parse common text-based PDFs and DOCX files into the normalized document model.
- Empty or unreadable files are captured as diagnostics instead of blocking the pipeline.
- Extracted text is suitable for FTS indexing and chunking.

## Validation

- Run parser tests against fixture files for successful and failure-path cases.
- Manually inspect extracted text for representative PDFs and DOCX files.

## Risks and Notes

- PDF extraction quality will vary; capture diagnostics honestly rather than pretending extraction succeeded.
- Keep fixture files small but realistic enough to catch whitespace and structure regressions.
