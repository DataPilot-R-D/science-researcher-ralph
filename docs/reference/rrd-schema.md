# RRD Schema Reference

Complete field-by-field documentation for the Research Requirements Document (`rrd.json`).

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project` | string | Yes | Human-readable project name |
| `branchName` | string | Yes | Topic identifier for folder naming |
| `description` | string | Yes | Research objective and scope |
| `requirements` | object | Yes | Search and evaluation parameters |
| `domain_glossary` | object | No | Domain-specific term definitions |
| `phase` | string | Yes | Current phase: DISCOVERY, ANALYSIS, COMPLETE |
| `papers_pool` | array | Yes | All discovered papers |
| `insights` | array | Yes | Extracted findings |
| `visited_urls` | array | Yes | URLs accessed during research |
| `blocked_sources` | array | Yes | Sources that failed repeatedly |
| `statistics` | object | Yes | Progress tracking metrics |

---

## requirements

Search and evaluation configuration.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `focus_area` | string | - | Primary research domain |
| `keywords` | string[] | - | Search terms for paper discovery |
| `time_window_days` | number | 30 | How recent papers should be |
| `historical_lookback_days` | number | 1095 | Fallback for foundational papers |
| `target_papers` | number | 20 | Papers to collect before ANALYSIS |
| `sources` | string[] | ["arXiv", "Google Scholar", "web"] | Where to search |
| `min_score_to_present` | number | 18 | Threshold for PRESENT decision |

### Example
```json
"requirements": {
  "focus_area": "robotics",
  "keywords": ["embodied AI", "robot manipulation", "sim2real"],
  "time_window_days": 30,
  "historical_lookback_days": 1095,
  "target_papers": 20,
  "sources": ["arXiv", "Google Scholar", "web"],
  "min_score_to_present": 18
}
```

---

## domain_glossary

Optional domain-specific terms to help the agent understand jargon.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | false | Whether to use the glossary |
| `terms` | object | {} | Term -> Definition mappings |

### Example
```json
"domain_glossary": {
  "enabled": true,
  "terms": {
    "DoF": "Degrees of Freedom",
    "EEF": "End Effector",
    "sim2real": "Simulation to Real-world Transfer",
    "VLA": "Vision-Language-Action model"
  }
}
```

---

## papers_pool

Array of discovered papers with their analysis status.

### Paper Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (e.g., "arxiv_2401.12345") |
| `title` | string | Paper title |
| `authors` | string[] | Author names |
| `abstract` | string | Paper abstract |
| `url` | string | Link to paper |
| `pdf_url` | string | Direct PDF link (if available) |
| `source` | string | Where paper was found |
| `published_date` | string | Publication date |
| `discovered_at` | string | When Research-Ralph found it |
| `priority` | number | Discovery-phase priority (1-5) |
| `status` | string | pending, analyzing, presented, rejected, insights_extracted |
| `score` | number | Total evaluation score (0-30) |
| `score_breakdown` | object | Per-dimension scores |
| `decision` | string | PRESENT, REJECT, or EXTRACT_INSIGHTS |
| `decision_reasoning` | string | Why this decision was made |
| `implementations` | object[] | Found GitHub repos, etc. |
| `commercialization` | object | Commercial use information |
| `analysis_notes` | string | Detailed analysis findings |

### Paper Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Not yet analyzed |
| `analyzing` | Currently being analyzed |
| `presented` | Score >= threshold, recommended |
| `rejected` | Score < threshold, not recommended |
| `insights_extracted` | Rejected but insights captured |

### Example Paper
```json
{
  "id": "arxiv_2401.12345",
  "title": "Vision-Language-Action Models for Robotics",
  "authors": ["Author One", "Author Two"],
  "abstract": "We present a novel approach...",
  "url": "https://arxiv.org/abs/2401.12345",
  "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
  "source": "arXiv",
  "published_date": "2024-01-15",
  "discovered_at": "2026-01-14T10:00:00Z",
  "priority": 4,
  "status": "presented",
  "score": 22,
  "score_breakdown": {
    "novelty": 4,
    "feasibility": 3,
    "time_to_poc": 4,
    "value_market": 4,
    "defensibility": 3,
    "adoption": 4
  },
  "decision": "PRESENT",
  "decision_reasoning": "Strong novelty with clear implementation path...",
  "implementations": [
    {
      "type": "github",
      "url": "https://github.com/author/vla-robotics",
      "stars": 450,
      "last_updated": "2024-01-10"
    }
  ],
  "commercialization": {
    "status": "research_only",
    "notes": "No commercial deployment found"
  },
  "analysis_notes": "Full paper analysis..."
}
```

---

## insights

Array of valuable findings extracted from papers.

### Insight Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | The insight content |
| `source_paper` | string | Paper ID this came from |
| `type` | string | technique, limitation, trend, cross_reference |
| `extracted_at` | string | Timestamp |
| `cross_cluster` | string | Optional: cluster identifier |

### Example
```json
{
  "text": "Diffusion-based action prediction outperforms autoregressive methods for manipulation tasks",
  "source_paper": "arxiv_2401.12345",
  "type": "technique",
  "extracted_at": "2026-01-14T11:30:00Z",
  "cross_cluster": "DIFFUSION_POLICIES"
}
```

---

## statistics

Progress tracking metrics.

| Field | Type | Description |
|-------|------|-------------|
| `total_discovered` | number | Papers found during DISCOVERY |
| `total_analyzed` | number | Papers fully analyzed |
| `total_presented` | number | Papers with PRESENT decision |
| `total_rejected` | number | Papers with REJECT decision |
| `total_insights_extracted` | number | Insights captured |
| `discovery_metrics` | object | Source tracking |
| `analysis_metrics` | object | Scoring statistics |

### discovery_metrics

| Field | Type | Description |
|-------|------|-------------|
| `sources_tried` | string[] | All sources attempted |
| `sources_successful` | string[] | Sources that returned results |
| `sources_blocked` | string[] | Sources that failed repeatedly |
| `source_failure_reasons` | object | Source -> Error message |

### analysis_metrics

| Field | Type | Description |
|-------|------|-------------|
| `avg_score` | number | Average score across analyzed papers |
| `score_distribution` | object | Count of papers in each range |

### Example
```json
"statistics": {
  "total_discovered": 25,
  "total_analyzed": 20,
  "total_presented": 8,
  "total_rejected": 12,
  "total_insights_extracted": 15,
  "discovery_metrics": {
    "sources_tried": ["arXiv", "Google Scholar"],
    "sources_successful": ["arXiv"],
    "sources_blocked": ["Google Scholar"],
    "source_failure_reasons": {
      "Google Scholar": "403 Forbidden - bot detection"
    }
  },
  "analysis_metrics": {
    "avg_score": 16.5,
    "score_distribution": {
      "0-11": 3,
      "12-17": 9,
      "18-23": 6,
      "24-30": 2
    }
  }
}
```

---

## Complete Example

See `rrd.json.example` in the project root for a complete working example.
