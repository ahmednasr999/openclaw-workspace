# ExamGenius Technical Brief: Multi-Agent Simulation Architecture

*Based on patterns from MiroFish (github.com/666ghj/MiroFish)*
*Created: 2026-03-15*

---

## Overview

MiroFish uses multi-agent simulation to predict outcomes. The same architecture can power ExamGenius to simulate candidate cohorts and predict pass/fail rates, identify weak areas, and optimize question difficulty.

---

## Core Architecture

### 1. Graph Building Layer

**MiroFish Pattern:**
- Extract entities and relationships from seed documents
- Build knowledge graph using GraphRAG
- Inject individual + collective memory

**ExamGenius Application:**
```
Syllabus → Entity Extraction → Knowledge Graph
                                   ↓
                           Topic Dependencies
                                   ↓
                           Difficulty Weighting
```

**Implementation:**
- Parse syllabus (PDF/JSON) into topics
- Map prerequisites: Topic A → requires Topic B
- Weight by frequency in exams
- Store in Neo4j or networkx + Redis

### 2. Persona Generation Layer

**MiroFish Pattern:**
- Each agent = entity + personality + memory + behavioral logic
- Personas inherit biases from training data
- Distinct profiles for variation

**ExamGenius Application:**
```
Candidate Agent = {
  "skill_level": 0.0-1.0,
  "strong_topics": ["topic_1", "topic_2"],
  "weak_topics": ["topic_3"],
  "time_management_style": "fast" | "moderate" | "thorough",
  "risk_tolerance": "guess" | "skip" | "review",
  "memory": {
    "past_attempts": [...],
    "error_patterns": [...]
  }
}
```

**Implementation:**
- Generate N candidate profiles (e.g., 1000)
- Vary skill distributions based on real candidate data
- Inject common error patterns (misreading, calculation errors)

### 3. Simulation Engine

**MiroFish Engine:** OASIS (CAMEL-AI)
- Agents interact autonomously
- Form groups, develop opinion leaders
- Shift positions over time

**ExamGenius Simulation:**
```
For each candidate_agent:
  For each question:
    1. Parse question + extract topics
    2. Check knowledge graph for topic mastery
    3. Apply time pressure factor
    4. Generate answer with error injection
    5. Record: answer, time_taken, confidence, errors
```

**Key Variables to Inject:**
- Time pressure: "30 seconds remaining"
- Distractor effectiveness: "two similar options"
- Fatigue: "questions 40-50 error rate +15%"
- Lucky guess: "25% chance of correct random answer"

### 4. Report Agent

**MiroFish Pattern:**
- Analyzes simulation results
- Has rich toolset for environment interaction
- Generates detailed prediction reports

**ExamGenius Report Agent:**
```
Report Agent analyzes:
  - Pass rate per skill level
  - Topic difficulty matrix
  - Time distribution analysis
  - Common error patterns
  - Predicted score distribution
  
Output:
  - "Candidates with skill < 0.6 fail 80% of time"
  - "Topic 'Financial Ratios' has 45% error rate"
  - "Question types 3-5 need redesign"
```

---

## Data Flow

```
┌─────────────────┐
│   Syllabus      │
│   (PDF/JSON)    │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Graph Builder  │
│   (Topics +     │
│   Dependencies) │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Question Bank  │
│   (Structured)  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Persona Generator│
│ (1000 candidates)│
└────────┬────────┘
         ↓
┌─────────────────┐
│  Simulation     │
│  (OASIS-style)  │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Report Agent   │
│  (Analysis +    │
│   Insights)     │
└─────────────────┘
```

---

## Key Technologies

| Component | MiroFish | ExamGenius Option |
|-----------|----------|-------------------|
| Simulation | OASIS | Custom Python + asyncio |
| Memory | Zep Cloud | Redis + temporal tables |
| Graph | GraphRAG | Neo4j or networkx |
| LLM | Qwen-plus (Alibaba) | GPT-4 / Claude |
| Deployment | Docker Compose | Railway / Render |

---

## Milestones

### Phase 1: Basic Simulation (Week 1-2)
- [ ] Parse syllabus into topic graph
- [ ] Structure question bank (topic, difficulty, distractors)
- [ ] Generate 100 candidate profiles
- [ ] Run basic simulation (no time pressure)

### Phase 2: Realism Injection (Week 3)
- [ ] Add time pressure modeling
- [ ] Add common error patterns
- [ ] Add fatigue curves (late questions harder)
- [ ] Validate against real exam data

### Phase 3: Analysis Engine (Week 4)
- [ ] Build Report Agent
- [ ] Generate insight dashboards
- [ ] Identify question design issues
- [ ] Predict pass rate curves

---

## Cost Estimate

| Item | Monthly Cost |
|------|--------------|
| LLM (GPT-4 API) | ~$200-500/month |
| Vector DB (Pinecone) | $50/month |
| Hosting (Railway) | $20/month |
| **Total** | **$270-570/month** |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| LLM cost too high | Use smaller model for simulation, GPT-4 only for analysis |
| Simulation too slow | Batch parallelize with Celery |
| Results not accurate | Validate against historical exam data |
| Overfitting to synthetic data | Use diverse candidate profiles |

---

## References

- MiroFish: github.com/666ghj/MiroFish
- OASIS: github.com/camel-ai/oasis
- Zep Cloud: app.getzep.com
