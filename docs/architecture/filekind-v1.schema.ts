import { z } from "zod";

export const ConfidenceModeSchema = z.enum([
  "safe",
  "balanced",
  "best_effort",
]);
export type ConfidenceMode = z.infer<typeof ConfidenceModeSchema>;

export const EvidenceSourceSchema = z.enum([
  "extension",
  "mime_header",
  "magic_bytes",
  "parser",
  "filesystem",
  "fallback",
]);
export type EvidenceSource = z.infer<typeof EvidenceSourceSchema>;

export const FileGroupSchema = z.enum([
  "document",
  "image",
  "audio",
  "video",
  "archive",
  "code",
  "data",
  "email",
  "executable",
  "filesystem",
  "unknown",
]);
export type FileGroup = z.infer<typeof FileGroupSchema>;

export const RoutingDecisionSchema = z.enum([
  "route_pdf",
  "route_image",
  "route_audio",
  "route_video",
  "route_code",
  "route_archive",
  "route_data",
  "route_email",
  "route_doc_generic",
  "route_binary_generic",
  "route_unknown",
  "quarantine",
  "reject",
]);
export type RoutingDecision = z.infer<typeof RoutingDecisionSchema>;

export const SpecialCaseSchema = z.enum([
  "empty",
  "directory",
  "symlink",
  "missing",
  "unreadable",
  "oversized",
  "encrypted",
]).nullable();
export type SpecialCase = z.infer<typeof SpecialCaseSchema>;

export const CanonicalFileLabelSchema = z.enum([
  "pdf",
  "image",
  "audio",
  "video",
  "code",
  "archive",
  "data",
  "email",
  "generic_text",
  "generic_binary",
  "unknown",
]);
export type CanonicalFileLabel = z.infer<typeof CanonicalFileLabelSchema>;

export const FileKindEvidenceSchema = z.object({
  source: EvidenceSourceSchema,
  label: z.string().min(1).optional(),
  mimeType: z.string().min(1).optional(),
  confidence: z.number().min(0).max(1).optional(),
  note: z.string().min(1).optional(),
});
export type FileKindEvidence = z.infer<typeof FileKindEvidenceSchema>;

export const FileKindPredictionSchema = z.object({
  rawLabel: z.string().min(1).nullable().optional(),
  finalLabel: CanonicalFileLabelSchema,
  description: z.string().min(1),
  group: FileGroupSchema,
  mimeType: z.string().min(1).nullable(),
  extensions: z.array(z.string().min(1)).default([]),
  isText: z.boolean().nullable(),
  confidence: z.number().min(0).max(1),
  trusted: z.boolean(),
  overwriteReason: z.string().min(1).optional(),
});
export type FileKindPrediction = z.infer<typeof FileKindPredictionSchema>;

export const FileKindRoutingSchema = z.object({
  mode: ConfidenceModeSchema.default("balanced"),
  decision: RoutingDecisionSchema,
  targetTool: z.string().min(1).optional(),
  allowAutoProcess: z.boolean(),
  requiresReview: z.boolean(),
});
export type FileKindRouting = z.infer<typeof FileKindRoutingSchema>;

export const FileKindTimestampsSchema = z.object({
  detectedAt: z.string().datetime(),
});
export type FileKindTimestamps = z.infer<typeof FileKindTimestampsSchema>;

export const FileKindSchema = z.object({
  version: z.literal("filekind.v1"),

  path: z.string().min(1).optional(),
  filename: z.string().min(1).optional(),
  sizeBytes: z.number().int().nonnegative().optional(),

  specialCase: SpecialCaseSchema,

  prediction: FileKindPredictionSchema,

  routing: FileKindRoutingSchema,

  evidence: z.array(FileKindEvidenceSchema).default([]),

  timestamps: FileKindTimestampsSchema.optional(),
});
export type FileKind = z.infer<typeof FileKindSchema>;

export const FileKindExamples = {
  pdf: {
    version: "filekind.v1",
    filename: "report.pdf",
    specialCase: null,
    prediction: {
      rawLabel: "pdf",
      finalLabel: "pdf",
      description: "PDF document",
      group: "document",
      mimeType: "application/pdf",
      extensions: ["pdf"],
      isText: null,
      confidence: 0.99,
      trusted: true,
    },
    routing: {
      mode: "balanced",
      decision: "route_pdf",
      targetTool: "pdf",
      allowAutoProcess: true,
      requiresReview: false,
    },
    evidence: [
      { source: "extension", label: "pdf" },
      { source: "magic_bytes", label: "pdf", confidence: 0.99 },
    ],
    timestamps: {
      detectedAt: "2026-04-17T20:00:00.000Z",
    },
  },
  suspiciousBinary: {
    version: "filekind.v1",
    filename: "invoice.pdf",
    specialCase: null,
    prediction: {
      rawLabel: "pe_executable",
      finalLabel: "generic_binary",
      description: "Generic binary data",
      group: "executable",
      mimeType: "application/octet-stream",
      extensions: [],
      isText: false,
      confidence: 0.61,
      trusted: false,
      overwriteReason: "extension_conflicts_with_binary_content",
    },
    routing: {
      mode: "safe",
      decision: "quarantine",
      allowAutoProcess: false,
      requiresReview: true,
    },
    evidence: [
      { source: "extension", label: "pdf" },
      { source: "magic_bytes", label: "pe_executable", confidence: 0.98 },
      { source: "fallback", label: "generic_binary", note: "unsafe mismatch" },
    ],
    timestamps: {
      detectedAt: "2026-04-17T20:00:00.000Z",
    },
  },
  lowConfidenceText: {
    version: "filekind.v1",
    filename: "unknown.txt",
    specialCase: null,
    prediction: {
      rawLabel: "yaml",
      finalLabel: "generic_text",
      description: "Generic text document",
      group: "document",
      mimeType: "text/plain",
      extensions: [],
      isText: true,
      confidence: 0.42,
      trusted: false,
      overwriteReason: "low_confidence_text_fallback",
    },
    routing: {
      mode: "balanced",
      decision: "route_doc_generic",
      targetTool: "text",
      allowAutoProcess: true,
      requiresReview: false,
    },
    evidence: [
      { source: "parser", label: "yaml", confidence: 0.42 },
      { source: "fallback", label: "generic_text" },
    ],
    timestamps: {
      detectedAt: "2026-04-17T20:00:00.000Z",
    },
  },
} satisfies Record<string, FileKind>;
