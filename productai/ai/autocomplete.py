"""Word autocomplete engine — full English dictionary with frequency ranking."""

import bisect
import logging
import ssl
from functools import lru_cache

log = logging.getLogger(__name__)

# ── Product Management vocabulary (boosted in ranking) ────────────────
PM_VOCABULARY = {
    'product', 'feature', 'requirement', 'requirements', 'specification',
    'stakeholder', 'stakeholders', 'roadmap', 'backlog', 'sprint', 'iteration',
    'milestone', 'milestones', 'deliverable', 'deliverables', 'deadline', 'timeline',
    'priority', 'priorities', 'critical', 'blocker', 'dependency', 'dependencies',
    'scope', 'objective', 'objectives', 'goal', 'goals', 'outcome', 'outcomes',
    'strategy', 'strategic', 'initiative', 'initiatives', 'epic', 'epics',
    'user', 'users', 'customer', 'customers', 'persona', 'personas',
    'segment', 'segments', 'audience', 'target', 'market', 'marketplace',
    'overview', 'summary', 'description', 'background', 'context', 'motivation',
    'problem', 'solution', 'proposed', 'approach', 'methodology',
    'acceptance', 'criteria', 'definition', 'assumptions', 'constraints',
    'risks', 'risk', 'mitigation', 'tradeoff', 'tradeoffs',
    'alternative', 'alternatives', 'recommendation', 'recommendations',
    'scenario', 'scenarios', 'workflow', 'workflows',
    'journey', 'experience', 'onboarding', 'retention',
    'engagement', 'conversion', 'funnel', 'acquisition', 'activation',
    'behavior', 'pattern', 'patterns', 'insight', 'insights',
    'metric', 'metrics', 'kpi', 'kpis', 'benchmark', 'benchmarks',
    'performance', 'measurement', 'analytics', 'dashboard', 'tracking',
    'revenue', 'growth', 'churn', 'adoption', 'utilization',
    'throughput', 'latency', 'uptime', 'availability', 'reliability',
    'scalability', 'efficiency', 'productivity', 'satisfaction',
    'design', 'wireframe', 'prototype', 'mockup',
    'interface', 'usability', 'accessibility', 'responsive', 'navigation',
    'layout', 'component', 'components', 'module', 'modules',
    'feedback', 'notification', 'notifications',
    'api', 'endpoint', 'endpoints', 'integration', 'integrations',
    'architecture', 'infrastructure', 'deployment', 'migration',
    'database', 'authentication', 'authorization', 'security', 'encryption',
    'configuration', 'environment', 'monitoring', 'logging', 'testing',
    'automated', 'automation', 'continuous', 'pipeline',
    'microservice', 'microservices', 'serverless', 'kubernetes',
    'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'mvp',
    'retrospective', 'standup', 'review', 'planning',
    'estimation', 'velocity', 'capacity', 'bandwidth', 'allocation',
    'collaboration', 'communication', 'documentation', 'handoff',
    'launch', 'release', 'rollout', 'beta', 'alpha', 'production',
    'experiment', 'hypothesis', 'validation', 'verification',
    'budget', 'roi', 'investment', 'profit',
    'competitive', 'competitor', 'differentiation',
    'positioning', 'branding', 'pricing', 'subscription', 'freemium',
    'enterprise', 'saas', 'platform', 'ecosystem',
    'compliance', 'regulation', 'gdpr', 'privacy', 'policy',
    'draft', 'approved', 'rejected', 'archived', 'deprecated',
    'active', 'inactive', 'pending', 'completed', 'cancelled', 'blocked',
    'implemented', 'delivered', 'shipped', 'released', 'launched',
}

# ── Context-aware word associations ───────────────────────────────────
WORD_ASSOCIATIONS = {
    'the': ['product', 'user', 'system', 'feature', 'team', 'customer', 'application',
            'requirement', 'solution', 'problem', 'design', 'interface', 'workflow'],
    'a': ['new', 'user', 'feature', 'product', 'customer', 'solution', 'requirement',
          'milestone', 'stakeholder', 'workflow', 'metric', 'dashboard'],
    'an': ['api', 'endpoint', 'application', 'integration', 'automated', 'alternative',
           'experiment', 'iteration', 'initiative', 'objective', 'overview'],
    'is': ['required', 'expected', 'available', 'necessary', 'important', 'critical',
           'optional', 'recommended', 'planned', 'blocked', 'completed', 'pending'],
    'are': ['required', 'expected', 'available', 'necessary', 'important', 'critical',
            'optional', 'recommended', 'planned', 'blocked', 'completed', 'pending'],
    'should': ['be', 'have', 'include', 'provide', 'support', 'allow', 'enable',
               'display', 'handle', 'validate', 'track', 'measure', 'implement'],
    'must': ['be', 'have', 'include', 'provide', 'support', 'comply', 'validate',
             'handle', 'ensure', 'maintain', 'implement', 'satisfy'],
    'will': ['be', 'have', 'include', 'provide', 'support', 'allow', 'enable',
             'display', 'handle', 'track', 'measure', 'improve', 'reduce'],
    'can': ['be', 'view', 'create', 'edit', 'delete', 'access', 'manage',
            'configure', 'customize', 'export', 'import', 'filter', 'search'],
    'to': ['the', 'create', 'manage', 'track', 'ensure', 'provide', 'enable',
           'improve', 'reduce', 'increase', 'support', 'implement', 'define'],
    'and': ['the', 'should', 'will', 'must', 'can', 'also', 'their', 'other'],
    'for': ['the', 'each', 'all', 'every', 'this', 'example', 'users', 'customers'],
    'with': ['the', 'a', 'an', 'all', 'support', 'integration', 'authentication'],
    'as': ['a', 'an', 'the', 'well', 'needed', 'required', 'expected', 'defined'],
    'user': ['should', 'can', 'will', 'must', 'needs', 'wants', 'experience',
             'story', 'journey', 'interface', 'feedback', 'research', 'persona'],
    'users': ['should', 'can', 'will', 'must', 'need', 'want', 'expect', 'prefer'],
    'product': ['manager', 'owner', 'team', 'roadmap', 'strategy', 'vision',
                'requirements', 'backlog', 'launch', 'lifecycle', 'market'],
    'feature': ['request', 'flag', 'toggle', 'specification', 'requirement',
                'priority', 'description', 'implementation', 'release'],
    'acceptance': ['criteria', 'testing', 'test'],
    'success': ['metrics', 'criteria', 'rate', 'story', 'factor', 'factors'],
    'key': ['performance', 'metrics', 'features', 'stakeholders', 'objectives',
            'results', 'findings', 'decisions', 'requirements', 'indicators'],
    'non': ['functional', 'negotiable', 'blocking', 'critical'],
    'high': ['priority', 'level', 'impact', 'risk', 'performance', 'availability'],
    'low': ['priority', 'level', 'impact', 'risk', 'latency', 'cost'],
}


def _load_nltk_words() -> set[str]:
    """Load NLTK words corpus, downloading if needed."""
    try:
        import nltk
        try:
            from nltk.corpus import words
            return set(w.lower() for w in words.words() if w.isalpha() and 2 <= len(w) <= 25)
        except LookupError:
            _ctx = ssl._create_default_https_context
            ssl._create_default_https_context = ssl._create_unverified_context
            try:
                nltk.download('words', quiet=True)
            finally:
                ssl._create_default_https_context = _ctx
            from nltk.corpus import words
            return set(w.lower() for w in words.words() if w.isalpha() and 2 <= len(w) <= 25)
    except Exception as e:
        log.warning("Could not load NLTK words: %s", e)
        return set()


def _load_nltk_frequencies() -> dict[str, int]:
    """Load word frequencies from NLTK Brown corpus."""
    try:
        import nltk
        try:
            from nltk.corpus import brown
        except LookupError:
            _ctx = ssl._create_default_https_context
            ssl._create_default_https_context = ssl._create_unverified_context
            try:
                nltk.download('brown', quiet=True)
            finally:
                ssl._create_default_https_context = _ctx
            from nltk.corpus import brown

        from collections import Counter
        freq = Counter(w.lower() for w in brown.words() if w.isalpha() and len(w) >= 2)
        return dict(freq)
    except Exception as e:
        log.warning("Could not load NLTK Brown corpus: %s", e)
        return {}


def _load_english_words() -> set[str]:
    """Load words from english-words package."""
    try:
        from english_words import get_english_words_set
        words = get_english_words_set(['gcide'], alpha=True, lower=True)
        return {w for w in words if 2 <= len(w) <= 25 and w.isalpha()}
    except Exception as e:
        log.warning("Could not load english-words: %s", e)
        return set()


@lru_cache(maxsize=1)
def _build_index() -> tuple[list[str], dict[str, int]]:
    """Build sorted word list and frequency scores. Called once, cached forever."""
    # Combine word sources
    all_words = _load_nltk_words() | _load_english_words() | PM_VOCABULARY
    sorted_words = sorted(all_words)

    # Build frequency scores from Brown corpus
    brown_freq = _load_nltk_frequencies()
    # Normalize: map raw count to 0-30000 range (log scale would be ideal but linear is fine)
    max_freq = max(brown_freq.values()) if brown_freq else 1
    scores: dict[str, int] = {}
    for word, count in brown_freq.items():
        scores[word] = int((count / max_freq) * 30000)

    log.info("Autocomplete index: %d words, %d with frequency data", len(sorted_words), len(scores))
    return sorted_words, scores


def _next_prefix(prefix: str) -> str:
    """Get the string boundary after prefix for bisect (e.g. 'req' -> 'rer')."""
    return prefix[:-1] + chr(ord(prefix[-1]) + 1)


def get_suggestions(prefix: str, context: str | None = None, limit: int = 8) -> list[str]:
    """Return ranked word suggestions for a prefix, optionally boosted by context."""
    prefix = prefix.lower().strip()
    if len(prefix) < 2:
        return []

    words, freq_scores = _build_index()

    # Fast bisect-based prefix lookup
    lo = bisect.bisect_left(words, prefix)
    hi = bisect.bisect_left(words, _next_prefix(prefix))
    matches = words[lo:hi]

    # Remove exact match
    if matches and matches[0] == prefix:
        matches = matches[1:]

    if not matches:
        return []

    # Build context boost set
    context_boost = set()
    if context:
        ctx = context.lower()
        if ctx in WORD_ASSOCIATIONS:
            context_boost = set(WORD_ASSOCIATIONS[ctx])

    # Score candidates
    scored: list[tuple[str, int]] = []
    for word in matches:
        score = 0
        # Context association — highest boost
        if word in context_boost:
            score += 200000
        # PM vocabulary boost
        if word in PM_VOCABULARY:
            score += 100000
        # Brown corpus frequency (0-30000)
        score += freq_scores.get(word, 0)
        # Length penalty for very long words without frequency data
        if word not in freq_scores:
            score -= len(word) * 10
        scored.append((word, score))

    scored.sort(key=lambda x: (-x[1], x[0]))
    return [w for w, _ in scored[:limit]]
