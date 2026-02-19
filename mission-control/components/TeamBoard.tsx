"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Icon } from "./Icon";

interface Contact {
  id: number;
  name: string;
  role?: string;
  company?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  category: string;
  status: string;
  warmth: string;
  notes?: string;
  lastContactDate?: string;
  nextFollowUp?: string;
  source?: string;
  tags: string[];
  createdAt: string;
  updatedAt?: string;
}

interface Activity {
  id: number;
  contactId: number;
  type: string;
  content: string;
  author: string;
  createdAt: string;
}

const CATEGORIES = ["All", "Recruiter", "Hiring Manager", "Networking", "Mentor", "Colleague", "Other"];
const WARMTH_LEVELS = ["Hot", "Warm", "Cool", "Cold"];
const STATUSES = ["Active", "Follow Up", "On Hold", "Closed"];

const WARMTH_STYLES: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  Hot: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/30", dot: "bg-red-500" },
  Warm: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30", dot: "bg-amber-500" },
  Cool: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30", dot: "bg-blue-500" },
  Cold: { bg: "bg-gray-500/10", text: "text-gray-400", border: "border-gray-500/30", dot: "bg-gray-500" },
};

const STATUS_STYLES: Record<string, string> = {
  Active: "bg-green-500/10 text-green-400 border-green-500/30",
  "Follow Up": "bg-amber-500/10 text-amber-400 border-amber-500/30",
  "On Hold": "bg-gray-500/10 text-gray-400 border-gray-500/30",
  Closed: "bg-red-500/10 text-red-400 border-red-500/30",
};

const CATEGORY_ICONS: Record<string, string> = {
  Recruiter: "🎯",
  "Hiring Manager": "👔",
  Networking: "🤝",
  Mentor: "🧭",
  Colleague: "💼",
  Other: "📌",
};

export function TeamBoard() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("All");
  const [filterWarmth, setFilterWarmth] = useState("");
  const [viewMode, setViewMode] = useState<"cards" | "table">("cards");
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [newNote, setNewNote] = useState("");

  const fetchContacts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/contacts");
      const data = await res.json();
      setContacts(data);
    } catch (error) {
      console.error("Failed to fetch contacts:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContacts();
    const interval = setInterval(fetchContacts, 30000);
    return () => clearInterval(interval);
  }, [fetchContacts]);

  const fetchActivity = async (contactId: number) => {
    try {
      const res = await fetch(`/api/contacts/${contactId}/activity`);
      const data = await res.json();
      setActivity(data);
    } catch (error) {
      console.error("Failed to fetch activity:", error);
    }
  };

  const handleCreateContact = async (data: Partial<Contact>) => {
    try {
      await fetch("/api/contacts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      setShowForm(false);
      fetchContacts();
    } catch (error) {
      console.error("Failed to create contact:", error);
    }
  };

  const handleUpdateContact = async (id: number, fields: Record<string, any>) => {
    try {
      await fetch(`/api/contacts?id=${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(fields),
      });
      setEditingContact(null);
      setSelectedContact(null);
      fetchContacts();
    } catch (error) {
      console.error("Failed to update contact:", error);
    }
  };

  const handleDeleteContact = async (id: number) => {
    if (!confirm("Delete this contact?")) return;
    try {
      await fetch(`/api/contacts?id=${id}`, { method: "DELETE" });
      setSelectedContact(null);
      fetchContacts();
    } catch (error) {
      console.error("Failed to delete contact:", error);
    }
  };

  const handleAddNote = async (contactId: number) => {
    if (!newNote.trim()) return;
    try {
      await fetch(`/api/contacts/${contactId}/activity`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "note", content: newNote.trim(), author: "Ahmed" }),
      });
      setNewNote("");
      fetchActivity(contactId);
    } catch (error) {
      console.error("Failed to add note:", error);
    }
  };

  const handleLogTouch = async (contact: Contact) => {
    const today = new Date().toISOString().split("T")[0];
    await handleUpdateContact(contact.id, { lastContactDate: today });
    await fetch(`/api/contacts/${contact.id}/activity`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "touch", content: "Logged contact", author: "Ahmed" }),
    });
    fetchContacts();
  };

  const openDetail = (contact: Contact) => {
    setSelectedContact(contact);
    fetchActivity(contact.id);
  };

  // Filtered contacts
  const filtered = useMemo(() => {
    return contacts.filter((c) => {
      if (filterCategory !== "All" && c.category !== filterCategory) return false;
      if (filterWarmth && c.warmth !== filterWarmth) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          c.name.toLowerCase().includes(q) ||
          c.company?.toLowerCase().includes(q) ||
          c.role?.toLowerCase().includes(q) ||
          c.notes?.toLowerCase().includes(q) ||
          c.tags.some((t) => t.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [contacts, filterCategory, filterWarmth, search]);

  // Stats
  const stats = useMemo(() => {
    const now = new Date();
    const followUpsDue = contacts.filter((c) => c.nextFollowUp && new Date(c.nextFollowUp) <= now && c.status !== "Closed").length;
    const stale = contacts.filter((c) => {
      if (!c.lastContactDate || c.status === "Closed") return false;
      const days = (now.getTime() - new Date(c.lastContactDate).getTime()) / (1000 * 60 * 60 * 24);
      return days > 14;
    }).length;
    return {
      total: contacts.length,
      active: contacts.filter((c) => c.status === "Active").length,
      followUpsDue,
      stale,
      hot: contacts.filter((c) => c.warmth === "Hot").length,
    };
  }, [contacts]);

  const formatDate = (d?: string) => {
    if (!d) return "-";
    const date = new Date(d);
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    if (diff === 0) return "Today";
    if (diff === 1) return "Yesterday";
    if (diff < 7) return `${diff}d ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "Africa/Cairo" });
  };

  const formatFuture = (d?: string) => {
    if (!d) return "-";
    const date = new Date(d);
    const now = new Date();
    const diff = Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (diff < 0) return <span className="text-red-400">Overdue ({Math.abs(diff)}d)</span>;
    if (diff === 0) return <span className="text-amber-400">Today</span>;
    if (diff === 1) return "Tomorrow";
    if (diff < 7) return `In ${diff}d`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "Africa/Cairo" });
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(255,255,255,0.06)]">
        <div>
          <h1 className="text-xl font-bold text-white">Team & Network</h1>
          <p className="text-xs text-gray-500 mt-1">
            {stats.total} contacts - {stats.followUpsDue > 0 ? <span className="text-amber-400">{stats.followUpsDue} follow-ups due</span> : "All caught up"}
            {stats.stale > 0 && <span className="text-red-400 ml-2">- {stats.stale} going cold</span>}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 rounded-lg text-xs font-medium bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all"
          >
            <Icon name="plus" size={14} className="inline mr-1" />
            Add Contact
          </button>
          <div className="flex gap-1 bg-[rgba(255,255,255,0.03)] rounded-lg p-1 border border-[rgba(255,255,255,0.08)]">
            <button
              onClick={() => setViewMode("cards")}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${viewMode === "cards" ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]" : "text-gray-500 hover:text-white"}`}
            >
              Cards
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${viewMode === "table" ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]" : "text-gray-500 hover:text-white"}`}
            >
              Table
            </button>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="flex items-center gap-4 px-6 py-3 border-b border-[rgba(255,255,255,0.04)] bg-[rgba(255,255,255,0.02)]">
        {WARMTH_LEVELS.map((w) => {
          const count = contacts.filter((c) => c.warmth === w).length;
          const s = WARMTH_STYLES[w];
          return (
            <button
              key={w}
              onClick={() => setFilterWarmth(filterWarmth === w ? "" : w)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-all border ${
                filterWarmth === w ? `${s.bg} ${s.text} ${s.border}` : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              <div className={`w-2 h-2 rounded-full ${s.dot}`} />
              <span>{w}</span>
              <span className="opacity-60">{count}</span>
            </button>
          );
        })}
        <div className="flex-1" />
        <div className="flex items-center gap-2">
          <Icon name="search" size={14} className="text-gray-500" />
          <input
            type="text"
            placeholder="Search contacts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent border-none text-sm text-white placeholder-gray-600 outline-none w-48"
          />
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-1 px-6 py-2 border-b border-[rgba(255,255,255,0.04)]">
        {CATEGORIES.map((cat) => {
          const count = cat === "All" ? contacts.length : contacts.filter((c) => c.category === cat).length;
          return (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                filterCategory === cat
                  ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]"
                  : "text-gray-500 hover:text-white"
              }`}
            >
              {cat !== "All" && <span className="mr-1">{CATEGORY_ICONS[cat] || ""}</span>}
              {cat}
              {count > 0 && <span className="ml-1 opacity-50">{count}</span>}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {loading && contacts.length === 0 ? (
          <div className="text-center text-gray-500 py-12">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <div className="text-4xl mb-4">👥</div>
            {contacts.length === 0 ? (
              <>
                <p>No contacts yet</p>
                <p className="text-xs mt-2">Add recruiters, hiring managers, and networking contacts</p>
                <button onClick={() => setShowForm(true)} className="mt-4 px-4 py-2 rounded-lg text-xs bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all">
                  Add First Contact
                </button>
              </>
            ) : (
              <p>No contacts match filters</p>
            )}
          </div>
        ) : viewMode === "cards" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((contact) => (
              <ContactCard key={contact.id} contact={contact} onOpen={openDetail} onLogTouch={handleLogTouch} formatDate={formatDate} formatFuture={formatFuture} />
            ))}
          </div>
        ) : (
          <ContactTable contacts={filtered} onOpen={openDetail} formatDate={formatDate} formatFuture={formatFuture} />
        )}
      </div>

      {/* Detail Modal */}
      {selectedContact && (
        <ContactDetailModal
          contact={selectedContact}
          activity={activity}
          newNote={newNote}
          onNoteChange={setNewNote}
          onAddNote={() => handleAddNote(selectedContact.id)}
          onEdit={() => { setEditingContact(selectedContact); setSelectedContact(null); }}
          onDelete={() => handleDeleteContact(selectedContact.id)}
          onLogTouch={() => handleLogTouch(selectedContact)}
          onClose={() => setSelectedContact(null)}
          formatDate={formatDate}
          formatFuture={formatFuture}
        />
      )}

      {/* Create/Edit Form */}
      {(showForm || editingContact) && (
        <ContactFormModal
          contact={editingContact || undefined}
          onSubmit={(data) => {
            if (editingContact) {
              handleUpdateContact(editingContact.id, data);
            } else {
              handleCreateContact(data);
            }
          }}
          onClose={() => { setShowForm(false); setEditingContact(null); }}
        />
      )}
    </div>
  );
}

// Contact Card
function ContactCard({ contact, onOpen, onLogTouch, formatDate, formatFuture }: {
  contact: Contact;
  onOpen: (c: Contact) => void;
  onLogTouch: (c: Contact) => void;
  formatDate: (d?: string) => any;
  formatFuture: (d?: string) => any;
}) {
  const warmth = WARMTH_STYLES[contact.warmth] || WARMTH_STYLES.Warm;
  const statusStyle = STATUS_STYLES[contact.status] || STATUS_STYLES.Active;
  const icon = CATEGORY_ICONS[contact.category] || "📌";

  return (
    <div
      onClick={() => onOpen(contact)}
      className="p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.04)] hover:border-[rgba(255,255,255,0.1)] transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[rgba(124,92,252,0.1)] border border-indigo-500/20 flex items-center justify-center text-lg">
            {icon}
          </div>
          <div>
            <div className="text-sm font-medium text-white">{contact.name}</div>
            {contact.role && <div className="text-[11px] text-gray-500">{contact.role}</div>}
          </div>
        </div>
        <div className={`w-2.5 h-2.5 rounded-full ${warmth.dot}`} title={contact.warmth} />
      </div>

      {contact.company && (
        <div className="text-xs text-gray-400 mb-2">{contact.company}</div>
      )}

      <div className="flex items-center gap-2 mb-3">
        <span className={`text-[10px] px-2 py-0.5 rounded border ${statusStyle}`}>{contact.status}</span>
        <span className={`text-[10px] px-2 py-0.5 rounded border ${warmth.bg} ${warmth.text} ${warmth.border}`}>{contact.warmth}</span>
      </div>

      <div className="flex items-center justify-between text-[10px] text-gray-600">
        <span>Last: {formatDate(contact.lastContactDate)}</span>
        <span>Follow up: {formatFuture(contact.nextFollowUp)}</span>
      </div>

      {contact.tags.length > 0 && (
        <div className="flex gap-1 mt-2 flex-wrap">
          {contact.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="text-[9px] px-1.5 py-0.5 rounded bg-[rgba(255,255,255,0.05)] text-gray-500">#{tag}</span>
          ))}
        </div>
      )}

      {/* Quick action */}
      <button
        onClick={(e) => { e.stopPropagation(); onLogTouch(contact); }}
        className="opacity-0 group-hover:opacity-100 mt-3 w-full px-3 py-1.5 rounded-lg text-[10px] font-medium bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white hover:bg-white/10 transition-all"
      >
        ✓ Log Contact
      </button>
    </div>
  );
}

// Table view
function ContactTable({ contacts, onOpen, formatDate, formatFuture }: {
  contacts: Contact[];
  onOpen: (c: Contact) => void;
  formatDate: (d?: string) => any;
  formatFuture: (d?: string) => any;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[rgba(255,255,255,0.06)]">
            <th className="text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider py-3 px-3">Name</th>
            <th className="text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider py-3 px-3">Company</th>
            <th className="text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider py-3 px-3">Category</th>
            <th className="text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider py-3 px-3">Warmth</th>
            <th className="text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider py-3 px-3">Status</th>
            <th className="text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider py-3 px-3">Last Contact</th>
            <th className="text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider py-3 px-3">Follow Up</th>
          </tr>
        </thead>
        <tbody>
          {contacts.map((c) => {
            const warmth = WARMTH_STYLES[c.warmth] || WARMTH_STYLES.Warm;
            const statusStyle = STATUS_STYLES[c.status] || STATUS_STYLES.Active;
            return (
              <tr
                key={c.id}
                onClick={() => onOpen(c)}
                className="border-b border-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.03)] cursor-pointer transition-all"
              >
                <td className="py-3 px-3">
                  <div className="text-xs font-medium text-white">{c.name}</div>
                  {c.role && <div className="text-[10px] text-gray-500">{c.role}</div>}
                </td>
                <td className="py-3 px-3 text-xs text-gray-400">{c.company || "-"}</td>
                <td className="py-3 px-3">
                  <span className="text-xs">{CATEGORY_ICONS[c.category] || ""} {c.category}</span>
                </td>
                <td className="py-3 px-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded border ${warmth.bg} ${warmth.text} ${warmth.border}`}>{c.warmth}</span>
                </td>
                <td className="py-3 px-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded border ${statusStyle}`}>{c.status}</span>
                </td>
                <td className="py-3 px-3 text-[11px] text-gray-400">{formatDate(c.lastContactDate)}</td>
                <td className="py-3 px-3 text-[11px]">{formatFuture(c.nextFollowUp)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// Detail modal with activity log
function ContactDetailModal({ contact, activity, newNote, onNoteChange, onAddNote, onEdit, onDelete, onLogTouch, onClose, formatDate, formatFuture }: {
  contact: Contact;
  activity: Activity[];
  newNote: string;
  onNoteChange: (v: string) => void;
  onAddNote: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onLogTouch: () => void;
  onClose: () => void;
  formatDate: (d?: string) => any;
  formatFuture: (d?: string) => any;
}) {
  const warmth = WARMTH_STYLES[contact.warmth] || WARMTH_STYLES.Warm;
  const statusStyle = STATUS_STYLES[contact.status] || STATUS_STYLES.Active;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="p-6 border-b border-[rgba(255,255,255,0.06)] flex-shrink-0">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-[rgba(124,92,252,0.1)] border border-indigo-500/20 flex items-center justify-center text-2xl">
                {CATEGORY_ICONS[contact.category] || "📌"}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">{contact.name}</h2>
                <div className="text-sm text-gray-400">
                  {[contact.role, contact.company].filter(Boolean).join(" at ")}
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded border ${statusStyle}`}>{contact.status}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded border ${warmth.bg} ${warmth.text} ${warmth.border}`}>{contact.warmth}</span>
                  <span className="text-[10px] text-gray-600">{contact.category}</span>
                </div>
              </div>
            </div>
            <button onClick={onClose} className="text-gray-500 hover:text-white"><Icon name="close" size={20} /></button>
          </div>

          {/* Contact info */}
          <div className="flex items-center gap-4 mt-4 flex-wrap">
            {contact.email && (
              <a href={`mailto:${contact.email}`} className="text-xs text-indigo-400 hover:underline">✉ {contact.email}</a>
            )}
            {contact.phone && (
              <a href={`tel:${contact.phone}`} className="text-xs text-indigo-400 hover:underline">📞 {contact.phone}</a>
            )}
            {contact.linkedin && (
              <a href={contact.linkedin} target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-400 hover:underline">🔗 LinkedIn</a>
            )}
          </div>

          {/* Key dates */}
          <div className="flex items-center gap-6 mt-3 text-[11px] text-gray-500">
            <span>Last contact: {formatDate(contact.lastContactDate)}</span>
            <span>Follow up: {formatFuture(contact.nextFollowUp)}</span>
            {contact.source && <span>Source: {contact.source}</span>}
          </div>
        </div>

        {/* Notes & Activity */}
        <div className="flex-1 overflow-y-auto p-6">
          {contact.notes && (
            <div className="mb-6 p-4 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)]">
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Notes</div>
              <p className="text-sm text-gray-300 whitespace-pre-wrap">{contact.notes}</p>
            </div>
          )}

          {/* Add note */}
          <div className="mb-6">
            <div className="flex gap-2">
              <input
                type="text"
                value={newNote}
                onChange={(e) => onNoteChange(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onAddNote()}
                placeholder="Add a note or log an interaction..."
                className="flex-1 px-3 py-2 rounded-lg bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] text-sm text-white placeholder-gray-600 outline-none focus:border-indigo-500/50"
              />
              <button
                onClick={onAddNote}
                disabled={!newNote.trim()}
                className="px-4 py-2 rounded-lg text-xs font-medium bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all disabled:opacity-30"
              >
                Add
              </button>
            </div>
          </div>

          {/* Activity log */}
          <div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-3">Activity</div>
            {activity.length === 0 ? (
              <p className="text-xs text-gray-600">No activity recorded yet</p>
            ) : (
              <div className="space-y-3">
                {activity.map((a) => (
                  <div key={a.id} className="flex items-start gap-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] flex-shrink-0 ${
                      a.type === "note" ? "bg-indigo-500/10 text-indigo-400" :
                      a.type === "touch" ? "bg-green-500/10 text-green-400" :
                      a.type === "created" ? "bg-purple-500/10 text-purple-400" :
                      "bg-gray-500/10 text-gray-400"
                    }`}>
                      {a.type === "note" ? "📝" : a.type === "touch" ? "✓" : a.type === "created" ? "+" : "•"}
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-gray-300">{a.content}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] text-gray-600">{a.author}</span>
                        <span className="text-[10px] text-gray-700">-</span>
                        <span className="text-[10px] text-gray-600">
                          {new Date(a.createdAt).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Africa/Cairo" })}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Tags */}
          {contact.tags.length > 0 && (
            <div className="mt-6 flex items-center gap-2 flex-wrap">
              {contact.tags.map((tag) => (
                <span key={tag} className="text-xs px-2 py-1 rounded bg-[rgba(124,92,252,0.1)] text-[#a78bfa]">#{tag}</span>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="px-6 py-4 border-t border-[rgba(255,255,255,0.06)] flex items-center gap-2 flex-shrink-0">
          <button onClick={onLogTouch} className="px-3 py-2 rounded-lg text-xs font-medium bg-green-500/10 border border-green-500/30 text-green-400 hover:bg-green-500/20 transition-all">
            ✓ Log Contact
          </button>
          <button onClick={onEdit} className="px-3 py-2 rounded-lg text-xs font-medium bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white hover:bg-white/10 transition-all">
            <Icon name="edit" size={12} className="inline mr-1" />Edit
          </button>
          <div className="flex-1" />
          <button onClick={onDelete} className="px-3 py-2 rounded-lg text-xs font-medium bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-all">
            <Icon name="delete" size={12} />
          </button>
        </div>
      </div>
    </div>
  );
}

// Create/Edit form
function ContactFormModal({ contact, onSubmit, onClose }: {
  contact?: Contact;
  onSubmit: (data: any) => void;
  onClose: () => void;
}) {
  const [form, setForm] = useState({
    name: contact?.name || "",
    role: contact?.role || "",
    company: contact?.company || "",
    email: contact?.email || "",
    phone: contact?.phone || "",
    linkedin: contact?.linkedin || "",
    category: contact?.category || "Networking",
    status: contact?.status || "Active",
    warmth: contact?.warmth || "Warm",
    notes: contact?.notes || "",
    lastContactDate: contact?.lastContactDate || "",
    nextFollowUp: contact?.nextFollowUp || "",
    source: contact?.source || "",
    tagsStr: contact?.tags?.join(", ") || "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    const tags = form.tagsStr.split(",").map((t) => t.trim()).filter(Boolean);
    onSubmit({
      name: form.name.trim(),
      role: form.role || undefined,
      company: form.company || undefined,
      email: form.email || undefined,
      phone: form.phone || undefined,
      linkedin: form.linkedin || undefined,
      category: form.category,
      status: form.status,
      warmth: form.warmth,
      notes: form.notes || undefined,
      lastContactDate: form.lastContactDate || undefined,
      nextFollowUp: form.nextFollowUp || undefined,
      source: form.source || undefined,
      tags: tags.length > 0 ? tags : undefined,
    });
  };

  const Field = ({ label, name, type = "text", placeholder = "", required = false }: { label: string; name: keyof typeof form; type?: string; placeholder?: string; required?: boolean }) => (
    <div>
      <label className="text-xs text-gray-500 block mb-1">{label}</label>
      <input
        type={type}
        value={form[name]}
        onChange={(e) => setForm({ ...form, [name]: e.target.value })}
        placeholder={placeholder}
        required={required}
        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)] text-white text-sm focus:outline-none focus:border-indigo-500/50 [color-scheme:dark]"
      />
    </div>
  );

  const Select = ({ label, name, options }: { label: string; name: keyof typeof form; options: string[] }) => (
    <div>
      <label className="text-xs text-gray-500 block mb-1">{label}</label>
      <select
        value={form[name]}
        onChange={(e) => setForm({ ...form, [name]: e.target.value })}
        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)] text-white text-sm focus:outline-none focus:border-indigo-500/50 [color-scheme:dark]"
      >
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl w-full max-w-lg max-h-[85vh] overflow-auto p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-semibold text-white">{contact ? "Edit Contact" : "New Contact"}</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><Icon name="close" size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Name *" name="name" placeholder="Full name" required />
            <Field label="Role" name="role" placeholder="e.g. Senior Recruiter" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Company" name="company" placeholder="Company name" />
            <Field label="Source" name="source" placeholder="e.g. LinkedIn, Referral" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Email" name="email" type="email" placeholder="email@example.com" />
            <Field label="Phone" name="phone" type="tel" placeholder="+1..." />
          </div>
          <Field label="LinkedIn URL" name="linkedin" type="url" placeholder="https://linkedin.com/in/..." />
          <div className="grid grid-cols-3 gap-3">
            <Select label="Category" name="category" options={CATEGORIES.filter((c) => c !== "All")} />
            <Select label="Status" name="status" options={STATUSES} />
            <Select label="Warmth" name="warmth" options={WARMTH_LEVELS} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Last Contact" name="lastContactDate" type="date" />
            <Field label="Next Follow Up" name="nextFollowUp" type="date" />
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)] text-white text-sm focus:outline-none focus:border-indigo-500/50 resize-none"
              rows={3}
              placeholder="Additional context..."
            />
          </div>
          <Field label="Tags (comma separated)" name="tagsStr" placeholder="recruiter, saudi, tech" />
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 px-3 py-2 rounded-lg text-xs font-medium border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white hover:bg-white/5 transition-all">
              Cancel
            </button>
            <button type="submit" className="flex-1 px-3 py-2 rounded-lg text-xs font-medium bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all">
              {contact ? "Save Changes" : "Add Contact"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
