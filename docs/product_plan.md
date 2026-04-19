# Product Definition Document

## Product Name
Shelf

## Executive Summary & Vision

Shelf is a native macOS application that gives users a centralized, lightning-fast searchable library for documents stored locally on their MacBook. It continuously indexes supported files across selected folders, keeps the index current in the background, and provides a simple, reliable interface for finding documents by filename and content without requiring users to manually organize everything first.

The product exists to solve a common desktop productivity problem: users know a document exists somewhere on their machine, but locating it across Downloads, Documents, Desktop, and project folders is slow, inconsistent, and mentally taxing. Spotlight can be helpful but is broad, opaque, and not purpose-built for a focused personal document library experience. Shelf aims to provide a more intentional, document-first experience with predictable folder coverage, transparent index management, and near-instant search.

The vision is to make local knowledge retrieval on macOS feel effortless: install the app, allow access, and immediately gain a trustworthy library of important files that is always up to date.

## Product Goals

### Primary Goals

- Deliver a fast, native macOS search experience for local documents.
- Automatically index PDF, DOC, and DOCX files from monitored folders.
- Keep the search index continuously up to date through background scanning.
- Provide clear, user-controlled folder management for what is included in the library.
- Offer a frictionless out-of-the-box experience with sensible default folders already configured.

### Success Criteria

- Users can install the app, grant permissions, and see searchable results from default folders within minutes.
- Search results appear quickly enough to feel instantaneous for typical personal libraries.
- Users trust that newly added, modified, and deleted files are reflected accurately in the app.
- Folder inclusion rules are easy to understand and manage without technical knowledge.

## Target Users

### Primary Users

- Knowledge workers who frequently search for reports, contracts, notes, proposals, or exported PDFs.
- Students managing assignments, lecture notes, and downloaded reading materials.
- Freelancers and consultants who need fast access to locally stored client documents.
- General macOS users with scattered files across Desktop, Downloads, and Documents.

### User Needs

- Find documents quickly without remembering exact file paths.
- Search by title, filename, or document text content.
- Trust that recent downloads and edits are reflected automatically.
- Control which folders are monitored.
- Use a polished, low-friction Mac-native app that works in the background.

## Product Principles

- Fast by default: every core interaction should feel immediate.
- Setup should be minimal: default folders must work out of the box.
- Transparent control: users must always know which folders are indexed.
- Quiet reliability: background scanning should stay current without disrupting the system.
- Extensible foundation: the indexing pipeline must support future file types without architectural rework.

## Scope Summary

### MVP In Scope

- Native macOS application.
- Default monitored folders: `~/Documents`, `~/Downloads`, `~/Desktop`.
- Folder management UI to add and remove monitored folders.
- Indexing support for `.pdf`, `.doc`, and `.docx`.
- Full-text and filename search across indexed documents.
- Background scanning for new, updated, moved, and deleted files.
- Search results that show key metadata and allow opening the source file in Finder or its default app.

### MVP Out of Scope

- OCR for scanned image-only documents.
- iCloud, Dropbox, Google Drive, or other cloud sync integrations beyond whatever appears as local folders on disk.
- Collaborative libraries or shared team search.
- Cross-device sync of index state or preferences.
- Advanced semantic search, AI summarization, or question answering.

## Key Features & Core Workflows

## 1. Document Indexing

### Feature Description

Shelf indexes supported local document types so users can search by filename, metadata, and extracted text content.

### Supported Formats for MVP

- PDF: `.pdf`
- Microsoft Word: `.doc`, `.docx`

### Indexing Behavior

- The app scans all monitored folders and discovers supported files recursively.
- For each supported document, the app extracts:
- File path
- File name
- File extension
- File size
- Created date
- Modified date
- Last indexed timestamp
- Extracted text content where available
- The system stores searchable index records locally on the device.
- Unsupported files are skipped without generating noisy alerts.
- Corrupt, password-protected, or unreadable files are marked with a recoverable indexing status for diagnostics.

### Extensibility Requirements

- File extraction must be implemented behind a parser/ingestion interface so new file types can be added with minimal changes.
- The indexing pipeline should separate:
- File discovery
- File eligibility filtering
- Content extraction
- Metadata normalization
- Index storage
- Search retrieval
- New file type support should ideally require adding a parser module and registering it with the indexing pipeline, not rewriting scanner or search logic.

### Workflow: Initial Index Build

1. User installs and launches Shelf.
2. App requests permission to access default folders as needed under macOS security rules.
3. App begins indexing preconfigured default folders.
4. User sees indexing progress and can begin searching once partial results are available.
5. App completes initial scan and transitions into continuous background maintenance mode.

### Workflow: Incremental Reindex

1. Background scanner detects a new or modified supported file.
2. App validates whether the file is within a monitored folder and still eligible.
3. Content extraction is run only for the changed file.
4. Existing index entry is inserted or updated.
5. Search results reflect the change without requiring a full reindex.

### Workflow: File Deletion Handling

1. Background scanner detects a file is missing or removed.
2. App confirms the file no longer exists or is outside monitored scope.
3. Corresponding index record is removed or marked unavailable.
4. Search results no longer surface stale entries.

## 2. Search Experience

### Feature Description

Shelf provides a dedicated search interface optimized for finding local documents quickly and confidently.

### Search Capabilities

- Search by filename.
- Search by full document text for supported indexed content.
- Match partial terms and multi-word queries.
- Return ranked results based on relevance, with filename and content matches weighted strongly.
- Display useful metadata in the result list, such as file name, file type, folder path, modified date, and a short text snippet where possible.

### Search Result Actions

- Open file in default macOS application.
- Reveal file in Finder.
- Copy file path.

### Workflow: Find a Document

1. User opens Shelf and enters a query.
2. Results update rapidly as the user types or submits the query.
3. User reviews ranked matches with metadata and snippets.
4. User opens the correct file or reveals it in Finder.

### UX Expectations

- Search must feel immediate for common queries.
- Empty states should guide the user when no files are indexed or no results match.
- The app should clearly distinguish between indexing in progress and fully indexed states.

## 3. Automated Background Scanning

### Feature Description

Shelf keeps the index current through regular background scans of monitored folders, minimizing manual intervention.

### Functional Behavior

- The app performs periodic scans of monitored folders while running.
- The app should also support lightweight event-driven refreshes where the platform permits, with scheduled scanning as the reliability baseline.
- The scanner detects:
- Newly created files
- Modified files
- Renamed or moved files within monitored folders
- Deleted files
- Background scanning should avoid full reindexing whenever incremental updates are possible.

### Scanner Strategy

- On first launch, run a complete baseline scan of all monitored folders.
- After baseline completion, run incremental scans at a regular cadence.
- Use file metadata such as path, modified timestamp, size, and file existence checks to minimize unnecessary extraction work.
- Maintain a scan state so the app can resume efficiently after restart.

### Workflow: Ongoing Maintenance

1. User downloads or edits a supported file in a monitored folder.
2. Scheduled background scan detects the change.
3. The changed file is indexed or reindexed.
4. Updated file becomes searchable shortly afterward.

### UX Expectations

- Scanning should happen quietly in the background.
- Users should be able to see overall indexing health and most recent scan time.
- Background work must not noticeably degrade laptop responsiveness during normal use.

## 4. Folder Management

### Feature Description

Users can view, add, and remove the folders Shelf monitors for indexing.

### Default Folders

The application must ship with these monitored folders configured by default:

- `~/Documents`
- `~/Downloads`
- `~/Desktop`

### Folder Management Capabilities

- View current monitored folders.
- Add a new folder through standard macOS folder picker flow.
- Remove a monitored folder from the list.
- Prevent duplicate folder entries.
- Validate folder accessibility before confirming addition.
- Clearly indicate when permissions are missing or revoked.

### Removal Behavior

- When a folder is removed, files indexed exclusively from that folder must be removed from the search index.
- Removal should be explicit and user initiated.
- The app should warn the user that removing a folder will also remove its files from search results.

### Workflow: Add Folder

1. User opens settings or library management.
2. User selects “Add Folder”.
3. macOS folder picker opens.
4. User selects a folder and confirms access.
5. Folder is added to monitored list.
6. Initial scan of that folder begins.

### Workflow: Remove Folder

1. User opens monitored folder list.
2. User chooses a folder to remove.
3. App shows confirmation explaining search impact.
4. User confirms removal.
5. App stops scanning the folder and removes associated index entries.

## 5. Out-of-the-Box Experience

### Feature Description

Shelf must feel useful immediately after installation, without requiring users to configure scan locations first.

### Requirements

- Preconfigure default monitored folders on first launch.
- Guide the user through macOS permissions in a clear, low-friction onboarding flow.
- Begin indexing immediately after permission is granted.
- Provide visible early value quickly, even if full indexing is still in progress.
- Explain simply what Shelf indexes, where it looks, and how users can change monitored folders later.

### Onboarding Outcome

By the end of first-run onboarding, the user should understand:

- What Shelf does
- Which folders are currently monitored
- Which file types are currently supported
- That search results will improve as indexing completes

## User Stories

- As a macOS user, I want Shelf to start with common folders already monitored so that I can get value immediately after install.
- As a macOS user, I want the app to index PDF, DOC, and DOCX files so that I can search the document types I use most often.
- As a macOS user, I want to search by filename and document text so that I can find files even when I do not remember where they are stored.
- As a macOS user, I want search results to appear quickly so that finding documents feels effortless.
- As a macOS user, I want Shelf to rescan folders automatically so that new or changed files become searchable without manual action.
- As a macOS user, I want deleted files to disappear from results so that I can trust the library to be accurate.
- As a macOS user, I want to see which folders are being monitored so that I understand the scope of indexing.
- As a macOS user, I want to add a folder to the monitored list so that Shelf can index documents I keep outside the defaults.
- As a macOS user, I want to remove a folder from the monitored list so that I can control privacy and relevance.
- As a macOS user, I want clear status indicators for indexing progress and health so that I know whether the library is current.
- As a macOS user, I want to open a result directly or reveal it in Finder so that I can act on my search immediately.
- As a privacy-conscious user, I want the document index to remain local to my Mac so that my files are not uploaded to external services.

## Functional Requirements

## Indexing & Content Processing

- The system must recursively scan all monitored folders for supported file types.
- The system must support `.pdf`, `.doc`, and `.docx` in MVP.
- The system must extract searchable text from supported files where text is available.
- The system must index file metadata including path, file name, extension, modified date, and size.
- The system must skip unsupported files without blocking scans.
- The system must detect and handle unreadable, corrupt, or permission-restricted files gracefully.
- The system must maintain a persistent local search index across app restarts.
- The architecture must allow additional file type parsers to be added without redesigning the scanning or search subsystems.

## Search

- The system must allow search across filenames and extracted content.
- The system must return relevant ranked results for partial and multi-word queries.
- The system must display file metadata in the result list.
- The system must allow users to open a file from search results.
- The system must allow users to reveal a file in Finder from search results.
- The system should display text snippets or highlights when matched content is available.

## Background Scanning

- The system must perform an initial full scan of monitored folders.
- The system must perform regular background scans after the initial scan.
- The system must detect newly created, modified, moved, renamed, and deleted supported files.
- The system must update only changed items whenever possible.
- The system must remove stale index entries when files are deleted or removed from monitored scope.
- The system must persist scan state needed for efficient incremental updates.

## Folder Management

- The system must display all monitored folders in the UI.
- The system must include `~/Documents`, `~/Downloads`, and `~/Desktop` by default on first launch.
- The system must allow users to add folders through a native macOS folder picker.
- The system must allow users to remove monitored folders.
- The system must prevent duplicate or redundant folder additions.
- The system must validate access permissions for monitored folders and surface errors clearly.

## Onboarding & Status

- The system must provide first-run onboarding that explains permissions and indexing behavior.
- The system must show whether initial indexing is in progress, complete, or encountering issues.
- The system must expose last scan time and a simple indexing health state.

## Non-Functional Requirements

## Performance

- Search results for typical queries on a warmed local index should begin appearing within 100 milliseconds for libraries up to at least 100,000 indexed documents.
- The UI should remain responsive during active background scans.
- Incremental scans should prioritize changed-file detection over full content reprocessing.
- Under typical personal laptop usage, background scanning should operate with low enough CPU and memory impact that users do not perceive meaningful slowdown in foreground work.

## Reliability

- The index must remain consistent across app restarts and unexpected termination.
- Index corruption risk must be minimized through safe write/update strategies.
- Failed file extraction for one document must not block indexing of other documents.
- The scanner must recover gracefully from temporary permission failures or inaccessible drives/folders.

## Privacy & Security

- All indexing and search operations must run locally on the user’s Mac by default.
- No document contents or metadata should be transmitted externally as part of MVP behavior.
- The app must respect macOS file access permissions and user folder selections.

## Scalability

- The architecture must support adding new file type extractors without major refactoring.
- The indexing subsystem should scale from a few hundred to at least 100,000 supported documents in a single-user local environment.

## Maintainability

- Parsing modules should be isolated behind a stable interface.
- Search, scanning, storage, and UI concerns should be separable for testability.
- Observability should exist for indexing failures, scan duration, and result counts to support debugging and tuning.

## Assumptions & Constraints

- Shelf is a native macOS app and will use platform-appropriate permissions and background execution patterns.
- Users primarily care about local files stored on internal disks or mounted folders accessible through the filesystem.
- Some Word and PDF files may not yield extractable text due to encryption, corruption, or image-only content.
- MVP optimizes for reliability and speed over advanced content understanding.

## Suggested MVP Acceptance Criteria

### Indexing

- On first launch, the app automatically configures `~/Documents`, `~/Downloads`, and `~/Desktop` as monitored folders.
- The app successfully indexes supported files from those folders after permissions are granted.
- New or modified `.pdf`, `.doc`, and `.docx` files become searchable after a background scan cycle.
- Deleted supported files are removed from search results after a background scan cycle.

### Search

- A user can search for a known keyword from indexed document content and receive the expected file.
- A user can search for part of a filename and receive the expected file.
- A user can open a result and reveal a result in Finder.

### Folder Management

- A user can view the monitored folder list.
- A user can add a new folder and see it begin indexing.
- A user can remove a monitored folder and confirm its results disappear from the library.

### UX

- A first-time user can understand within onboarding what Shelf indexes and which folders are included.
- The app surfaces indexing state clearly enough that users know whether results are still being populated.

## Risks & Mitigations

### Risk: Large libraries slow initial setup

- Mitigation: allow partial result availability during indexing, show progress, and optimize for incremental processing after baseline completion.

### Risk: macOS permission friction blocks onboarding

- Mitigation: keep onboarding concise, explain why access is needed, and provide clear recovery actions if permissions are denied.

### Risk: Search trust degrades if stale results remain

- Mitigation: prioritize reliable deleted-file detection and maintain clear scan health indicators.

### Risk: Parser differences create inconsistent extraction quality

- Mitigation: standardize parser interface, capture file-level extraction status, and add regression tests per supported file type.

## Future Roadmap / Out of Scope for MVP

### Near-Term Enhancements

- Additional file types such as plain text, Markdown, RTF, EPUB, PPTX, XLSX, and common code/text formats.
- OCR for image-based PDFs and scanned documents.
- Richer ranking, filters, and sort options.
- Saved searches and recent searches.
- Quick Look preview inside the app.

### Medium-Term Enhancements

- Semantic search and natural-language retrieval.
- Duplicate and near-duplicate document detection.
- Tags, collections, and pinned documents.
- Smart suggestions based on recency or usage.

### Longer-Term Opportunities

- Optional cloud backup of index metadata.
- Cross-device sync of preferences and index state.
- Team/shared libraries for managed environments.
- Integrations with external storage providers beyond their local mounted folders.

## Engineering Notes

The engineering team should treat the parser/indexing boundary as the most important long-term architectural decision in MVP. If the ingestion layer is cleanly abstracted from scanning, storage, and retrieval, the product can expand format coverage and evolve search quality without destabilizing the core user experience.

The MVP should optimize for trust, speed, and simplicity over breadth. A smaller set of file types that index reliably and search quickly is more valuable than a wide but inconsistent feature set.
