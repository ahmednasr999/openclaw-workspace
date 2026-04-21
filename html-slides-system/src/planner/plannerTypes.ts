export type SectionPriority = 'high' | 'medium' | 'low';

export type SourceSection = {
  id: string;
  title: string;
  summary: string;
  bullets?: string[];
  priority?: SectionPriority;
};

export type PlannerInput = {
  deckTitle: string;
  objective: string;
  audience: string;
  tone: string;
  desiredSlideCount: number;
  sections: SourceSection[];
};

export type DeckBrief = {
  deckTitle: string;
  objective: string;
  audience: string;
  tone: string;
  desiredSlideCount: number;
  narrativeArc: string[];
  strongestSections: string[];
  gaps: string[];
  assumptions: string[];
};

export type PlannedSlide = {
  id: string;
  pattern: string;
  title: string;
  purpose: string;
  keyMessage: string;
  sourceSectionIds: string[];
  layoutDirection: string;
  visualSuggestion: string;
  confidence: number;
  payload: Record<string, unknown>;
};

export type SlideOutline = {
  deckTitle: string;
  generatedAt: string;
  slides: PlannedSlide[];
};
