# AnyDoc Local Parser Evaluation

Date: 2026-08-05  
Owner: CTO  
Decision: Adopt AnyDoc 0.1.6 as the preferred local parser for supported non-presentation documents, with MarkItDown 0.1.5 retained for presentations and fallback.

## Evidence

Seven local samples covered text PDFs, DOCX, PPTX, CSV, XLSX, and an image-only PDF boundary case. Document contents remained local.

| Sample | AnyDoc median | MarkItDown median | Content result | Route decision |
|---|---:|---:|---|---|
| Executive CV PDF | 6.4 ms | 324.3 ms | Both retained 100% of reference tokens | AnyDoc |
| Long structured PDF | 50.0 ms | 2,368.4 ms | Both retained 100%; AnyDoc preserved headings and lists better | AnyDoc |
| Structured DOCX | 8.2 ms | 523.4 ms | AnyDoc retained 100%; MarkItDown retained 98.5% | AnyDoc |
| 23-slide PPTX | 52.6 ms | 538.2 ms | Both retained 100%; only MarkItDown emitted explicit slide boundaries | MarkItDown |
| Real job-scan CSV | 1.5 ms | 12.9 ms | Both retained 100% | AnyDoc |
| Mixed-content XLSX | 0.4 ms | 32.2 ms | Both retained 100% | AnyDoc |
| Image-only scanned PDF | Unsupported, explicit OCR error | Empty output | Neither performs OCR in this local configuration | Fail clearly; OCR remains separate |

AnyDoc was about 8 to 85 times faster across successful samples. It also has broader legacy and OpenDocument format support. The PowerPoint exception is deliberate: slide boundaries matter more than raw speed for deck reasoning and QA.

## Implementation

- Pinned runtime: `tools/document-parser-venv`, reproducible from `tools/document-parser/requirements.lock` with `tools/document-parser/install.sh`.
- Shared entry point: `scripts/document-to-markdown.py`.
- Auto route: AnyDoc for supported local documents; MarkItDown for PowerPoint, URLs, unsupported formats, and fallback.
- Slides Lane ingestion now records the selected backend in `extractionMethod`.
- Existing slide QA commands now use the shared router.

## Safety And Verification

- AnyDoc is MIT licensed and has no Python runtime dependencies.
- Source review found no network client or process-spawn path in the parser.
- A local conversion under `strace -e trace=network` made zero network syscalls.
- `pip-audit` found no known vulnerabilities across all 38 packages in the isolated parser environment.
- End-to-end Slides Lane smoke test completed a PPTX through MarkItDown and a DOCX through AnyDoc, both with `extractionStatus=completed` and `extractionQuality=full`.
- Image-only PDFs fail with an explicit OCR-required error instead of being accepted as a successful empty extraction.

## Residual Risk And Rollback

AnyDoc 0.1.6 is new and should remain version-pinned until it matures. It does not OCR scanned PDFs and its PPTX Markdown lacks explicit slide separators.

Rollback is local and does not require a gateway restart: run the shared script with `--backend markitdown`, or revert the Slides Lane call to MarkItDown. Removing `tools/document-parser-venv` removes the installed runtime without affecting other Python environments.
