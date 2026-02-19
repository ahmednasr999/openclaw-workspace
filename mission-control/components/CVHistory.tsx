"use client";

import { useState, useEffect, useCallback } from "react";
import { Icon } from "./Icon";

interface CVEntry {
  id: number;
  jobTitle: string;
  company: string;
  jobUrl?: string;
  atsScore?: number;
  matchedKeywords: string[];
  missingKeywords: string[];
  pdfPath?: string;
  status: string;
  notes?: string;
  createdAt: string;
}

export function CVHistoryPage() {
  const [entries, setEntries] = useState<CVEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEntry, setSelectedEntry] = useState<CVEntry | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [jobInput, setJobInput] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [cvHtml, setCvHtml] = useState("");

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/cv");
      const rawData: any[] = await res.json();
      // Parse JSON strings to arrays
      const parsedData = rawData.map((e) => ({
        ...e,
        matchedKeywords: e.matchedKeywords ? JSON.parse(e.matchedKeywords) : [],
        missingKeywords: e.missingKeywords ? JSON.parse(e.missingKeywords) : [],
      }));
      setEntries(parsedData);
    } catch (error) {
      console.error("Failed to fetch CV history:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  // Check CV generation queue periodically
  useEffect(() => {
    const checkQueue = async () => {
      try {
        const res = await fetch("/api/cv/queue");
        if (res.ok) {
          const data = await res.json();
          const pending = data.queue?.filter((i: any) => i.status === "pending") || [];
          if (pending.length > 0) {
            console.log(`${pending.length} CVs in queue waiting for generation`);
          }
        }
      } catch {}
    };
    checkQueue();
    const interval = setInterval(checkQueue, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this CV entry?")) return;
    try {
      await fetch(`/api/cv?id=${id}`, { method: "DELETE" });
      fetchEntries();
    } catch (error) {
      console.error("Failed to delete:", error);
    }
  };

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-500";
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-amber-400";
    return "text-red-400";
  };

  const getScoreBg = (score?: number) => {
    if (!score) return "bg-gray-500/10 border-gray-500/20";
    if (score >= 80) return "bg-green-500/10 border-green-500/20";
    if (score >= 60) return "bg-amber-500/10 border-amber-500/20";
    return "bg-red-500/10 border-red-500/20";
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "Africa/Cairo" });
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(255,255,255,0.06)]">
        <div>
          <h1 className="text-xl font-bold text-white">CV Maker</h1>
          <p className="text-xs text-gray-500 mt-1">
            {entries.length} CVs created - Tailor your CV for jobs and track history
          </p>
        </div>
      </div>

      {/* Job Input */}
      <div className="px-6 py-4 border-b border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.02)]">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (!jobInput.trim()) return;
            setAnalyzing(true);
            setAnalysisResult(null);
            try {
              const res = await fetch("/api/cv/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  url: jobInput.startsWith("http") ? jobInput : "",
                  description: !jobInput.startsWith("http") ? jobInput : ""
                }),
              });
              if (res.ok) {
                const data = await res.json();
                setAnalysisResult(data);
              } else {
                alert("Failed to analyze job.");
              }
            } catch (error) {
              alert("Error analyzing job.");
            } finally {
              setAnalyzing(false);
            }
          }}
          className="space-y-3"
        >
          <textarea
            value={jobInput}
            onChange={(e) => setJobInput(e.target.value)}
            placeholder="Paste job URL or full job description here..."
            className="w-full h-32 bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] rounded-lg px-4 py-3 text-sm text-white placeholder-gray-500 outline-none focus:border-indigo-500/50 resize-none"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={analyzing || !jobInput.trim()}
              className="px-6 py-2.5 rounded-lg text-xs font-medium bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {analyzing ? "Analyzing..." : "Analyze & Generate"}
            </button>
          </div>
        </form>

        {/* Analysis Result */}
        {analysisResult && (
          <div className="mt-4 p-4 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)]">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="text-sm font-medium text-white">{analysisResult.job?.title}</h4>
                <p className="text-xs text-gray-500">{analysisResult.job?.company}</p>
              </div>
              <div className={`px-3 py-1.5 rounded-lg border ${analysisResult.analysis?.atsScore >= 80 ? "bg-green-500/10 border-green-500/30" : analysisResult.analysis?.atsScore >= 60 ? "bg-amber-500/10 border-amber-500/30" : "bg-red-500/10 border-red-500/30"}`}>
                <span className={`text-lg font-bold ${analysisResult.analysis?.atsScore >= 80 ? "text-green-400" : analysisResult.analysis?.atsScore >= 60 ? "text-amber-400" : "text-red-400"}`}>{analysisResult.analysis?.atsScore}</span>
                <span className="text-xs text-gray-500 ml-1">/100</span>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-[10px] text-gray-500">Matched:</span>
              {analysisResult.analysis?.matchedKeywords?.slice(0, 5).map((k: string) => (
                <span key={k} className="text-[10px] px-2 py-0.5 rounded bg-green-500/10 text-green-400">{k}</span>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] text-gray-500">Missing:</span>
              {analysisResult.analysis?.missingKeywords?.slice(0, 5).map((k: string) => (
                <span key={k} className="text-[10px] px-2 py-0.5 rounded bg-red-500/10 text-red-400">{k}</span>
              ))}
            </div>
            {/* Recommendation */}
            <div className="mt-3 p-2 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)]">
              {analysisResult.analysis?.atsScore >= 80 ? (
                <p className="text-xs text-green-400">✓ Strong Match - Recommend Apply</p>
              ) : analysisResult.analysis?.atsScore >= 60 ? (
                <p className="text-xs text-amber-400">! Moderate Match - Consider Applying</p>
              ) : (
                <p className="text-xs text-red-400">✗ Weak Match - May Need Adjustments</p>
              )}
            </div>

            {/* Generate PDF Button */}
            <div className="flex gap-2 mt-3">
              <button
                onClick={async () => {
                  if (!analysisResult?.job) return;
                  setGeneratingPdf(true);
                  try {
                    const res = await fetch("/api/cv/pdf", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ job: analysisResult.job, content: "" }),
                    });
                    if (res.ok) {
                      const data = await res.json();
                      setCvHtml(data.html || "");
                      setShowPreview(true);
                    } else {
                      alert("Failed to generate PDF");
                    }
                  } catch {
                    alert("Error generating PDF");
                  } finally {
                    setGeneratingPdf(false);
                  }
                }}
                disabled={generatingPdf}
                className="flex-1 px-4 py-2.5 rounded-lg text-xs font-medium bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:bg-white/10 transition-all disabled:opacity-50"
              >
                Quick Preview
              </button>
              <button
                onClick={async () => {
                  if (!jobInput.trim()) return;
                  setGeneratingPdf(true);
                  try {
                    const res = await fetch("/api/cv/queue", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ jobDescription: jobInput }),
                    });
                    if (res.ok) {
                      const data = await res.json();
                      alert(`Job added to queue! I'll generate your CV shortly.\nQueue position: ${data.queueLength}`);
                    } else {
                      alert("Failed to queue job");
                    }
                  } catch {
                    alert("Error queueing job");
                  } finally {
                    setGeneratingPdf(false);
                  }
                }}
                disabled={generatingPdf}
                className="flex-1 px-4 py-2.5 rounded-lg text-xs font-medium bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all disabled:opacity-50"
              >
                {generatingPdf ? "Queueing..." : "Generate Full CV"}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="text-center text-gray-500 py-12">Loading...</div>
        ) : entries.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <div className="text-4xl mb-4">""</div>
            <p>No CVs yet</p>
            <p className="text-xs mt-2">Give me a job description and I'll create a tailored CV</p>
            <div className="mt-6 p-4 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] max-w-md mx-auto">
              <p className="text-xs text-gray-400 mb-2">Try:</p>
              <p className="text-xs text-indigo-400">"Tailor my CV for [job URL]"</p>
              <p className="text-xs text-indigo-400">"Analyze ATS score for [company] - [role]"</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => (
              <div
                key={entry.id}
                onClick={() => { setSelectedEntry(entry); setShowDetails(true); }}
                className="p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.04)] hover:border-[rgba(255,255,255,0.1)] transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="text-xl">""</div>
                      <div>
                        <h3 className="text-sm font-medium text-white">{entry.jobTitle}</h3>
                        <p className="text-xs text-gray-500">{entry.company}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {entry.atsScore !== undefined && (
                        <div className={`px-3 py-1.5 rounded-lg border ${getScoreBg(entry.atsScore)}`}>
                          <span className={`text-lg font-bold ${getScoreColor(entry.atsScore)}`}>{entry.atsScore}</span>
                          <span className="text-xs text-gray-500 ml-1">/100</span>
                        </div>
                      )}
                      <span className="text-xs text-gray-600">{formatDate(entry.createdAt)}</span>
                      {entry.status === "Sent" && (
                        <span className="text-xs px-2 py-0.5 rounded bg-green-500/10 text-green-400">Sent</span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(entry.id); }}
                    className="p-2 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-all"
                  >
                    <Icon name="delete" size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {showDetails && selectedEntry && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setShowDetails(false)}>
          <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-[rgba(255,255,255,0.06)]">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">{selectedEntry.jobTitle}</h2>
                  <p className="text-sm text-gray-400">{selectedEntry.company}</p>
                </div>
                <button onClick={() => setShowDetails(false)} className="text-gray-500 hover:text-white">
                  <Icon name="close" size={20} />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* ATS Score */}
              {selectedEntry.atsScore !== undefined && (
                <div className={`p-4 rounded-lg border ${selectedEntry.atsScore >= 80 ? "bg-green-500/10 border-green-500/20" : selectedEntry.atsScore >= 60 ? "bg-amber-500/10 border-amber-500/20" : "bg-red-500/10 border-red-500/20"}`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs text-gray-500 uppercase tracking-wider">ATS Score</span>
                    <span className={`text-2xl font-bold ${getScoreColor(selectedEntry.atsScore)}`}>{selectedEntry.atsScore}/100</span>
                  </div>
                  <div className="w-full h-2 bg-[rgba(255,255,255,0.1)] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${selectedEntry.atsScore >= 80 ? "bg-green-500" : selectedEntry.atsScore >= 60 ? "bg-amber-500" : "bg-red-500"}`}
                      style={{ width: `${selectedEntry.atsScore}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Keywords */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Matched ({selectedEntry.matchedKeywords.length})</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedEntry.matchedKeywords.length > 0 ? (
                      selectedEntry.matchedKeywords.map((kw) => (
                        <span key={kw} className="text-xs px-2 py-0.5 rounded bg-green-500/10 text-green-400">✓ {kw}</span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-600">No keywords matched</span>
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Missing ({selectedEntry.missingKeywords.length})</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedEntry.missingKeywords.length > 0 ? (
                      selectedEntry.missingKeywords.map((kw) => (
                        <span key={kw} className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-400">✗ {kw}</span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-600">No missing keywords</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Job URL */}
              {selectedEntry.jobUrl && (
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Job Posting</div>
                  <a href={selectedEntry.jobUrl} target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-400 hover:underline break-all">
                    {selectedEntry.jobUrl}
                  </a>
                </div>
              )}

              {/* Notes */}
              {selectedEntry.notes && (
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Notes</div>
                  <p className="text-sm text-gray-300">{selectedEntry.notes}</p>
                </div>
              )}

              {/* Created */}
              <div className="text-xs text-gray-600">
                Created: {formatDate(selectedEntry.createdAt)}
              </div>
            </div>

            <div className="p-4 border-t border-[rgba(255,255,255,0.06)] flex items-center gap-2">
              {selectedEntry.pdfPath && (
                <button className="flex-1 px-3 py-2 rounded-lg text-xs font-medium bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all">
                  <Icon name="download" size={12} className="inline mr-1" />
                  Download PDF
                </button>
              )}
              <button className="flex-1 px-3 py-2 rounded-lg text-xs font-medium bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white hover:bg-white/10 transition-all">
                <Icon name="edit" size={12} className="inline mr-1" />
                Edit Notes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CV Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-[rgba(255,255,255,0.06)]">
              <h3 className="text-sm font-medium text-white">CV Preview</h3>
              <button onClick={() => setShowPreview(false)} className="text-gray-400 hover:text-white">
                <Icon name="close" size={16} />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-6">
              <div className="bg-white rounded-lg p-8 max-w-2xl mx-auto" dangerouslySetInnerHTML={{ __html: cvHtml }} />
            </div>
            <div className="flex items-center justify-between p-4 border-t border-[rgba(255,255,255,0.06)]">
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white transition-all"
              >
                Close
              </button>
              <button
                onClick={() => {
                  const w = window.open("", "_blank");
                  if (w) {
                    w.document.write(cvHtml);
                    w.document.close();
                    w.print();
                  }
                }}
                className="px-4 py-2 rounded-lg text-xs font-medium bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all"
              >
                Print / Save as PDF
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
