import { useMemo } from 'react';

interface Entity {
  id: string;
  name: string;
  type: string;
  first_seen_date: string;
  last_seen_date: string;
  mention_count: number;
}

interface Arc {
  id: string;
  name: string;
  first_seen_date: string;
  last_seen_date: string;
  mention_count: number;
  key_entities: { id: string; mentions: number }[];
}

interface ContextPanelProps {
  currentDate: string;
  entities: Record<string, Entity>;
  arcs: Record<string, Arc>;
  visibleArticles: { arc_id: string | null; entities: string[]; groups: string[]; locations: string[]; topics: string[] }[];
}

function makeEid(name: string): string {
  return name.toLowerCase().replace(/[^\w-]/g, '').replace(/\s+/g, '-');
}

export default function ContextPanel({
  currentDate,
  entities,
  arcs,
  visibleArticles,
}: ContextPanelProps) {
  // Time-lock filter: only entities/arcs first seen <= currentDate
  const isUnlocked = (firstSeen: string | null | undefined) => {
    if (!firstSeen) return true;
    return firstSeen <= currentDate;
  };

  // Active arcs: arcs with articles in the visible range AND unlocked
  const activeArcs = useMemo(() => {
    const arcSet = new Set<string>();
    visibleArticles.forEach((a) => {
      if (a.arc_id) arcSet.add(a.arc_id);
    });
    return Array.from(arcSet)
      .map((id) => arcs[id])
      .filter(Boolean)
      .filter((a) => isUnlocked(a.first_seen_date))
      .sort((a, b) => b.mention_count - a.mention_count)
      .slice(0, 6);
  }, [visibleArticles, arcs, currentDate]);

  // Key figures: entities mentioned in visible articles AND unlocked
  const keyFigures = useMemo(() => {
    const counts = new Map<string, number>();
    visibleArticles.forEach((a) => {
      [...a.entities, ...a.groups, ...a.locations].forEach((name) => {
        const eid = makeEid(name);
        counts.set(eid, (counts.get(eid) || 0) + 1);
      });
    });
    return Array.from(counts.entries())
      .map(([eid, count]) => ({ ...entities[eid], count }))
      .filter((e) => e && e.id && isUnlocked(e.first_seen_date))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }, [visibleArticles, entities, currentDate]);

  // Threat level from visible topics
  const threatLevel = useMemo(() => {
    const topicCounts: Record<string, number> = {};
    visibleArticles.forEach((a) => {
      a.topics.forEach((t) => {
        topicCounts[t] = (topicCounts[t] || 0) + 1;
      });
    });
    const warScore = (topicCounts['war'] || 0) + (topicCounts['terrorism'] || 0) + (topicCounts['alien contact'] || 0);
    const total = Object.values(topicCounts).reduce((a, b) => a + b, 0) || 1;
    const ratio = warScore / total;
    if (ratio > 0.5) return 'critical';
    if (ratio > 0.3) return 'high';
    if (ratio > 0.15) return 'medium';
    return 'low';
  }, [visibleArticles]);

  const threatLabel = {
    low: 'Stable',
    medium: 'Elevated',
    high: 'Critical',
    critical: 'Extreme',
  }[threatLevel];

  const entityTypeLabel: Record<string, string> = {
    person: 'P',
    faction: 'F',
    location: 'L',
  };

  return (
    <div className="context-pane">
      {/* Threat Level */}
      <div className="holo-panel red">
        <div className="holo-title red">Threat Assessment</div>
        <div className={`threat-level threat-${threatLevel}`}>
          <span>{threatLabel}</span>
          <div className="threat-bar">
            <div className="threat-bar-fill" />
          </div>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-dim)', marginTop: 6 }}>
          Timeline Date: {currentDate}
        </div>
      </div>

      {/* Active Arcs */}
      {activeArcs.length > 0 && (
        <div className="holo-panel blue">
          <div className="holo-title blue">Active Arcs</div>
          {activeArcs.map((arc) => (
            <a
              key={arc.id}
              href={`${import.meta.env.BASE_URL}arc/${arc.id}/`}
              style={{
                display: 'block',
                padding: '8px 0',
                borderBottom: '1px solid var(--border-default)',
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                {arc.name}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-dim)', marginTop: 2 }}>
                {arc.first_seen_date} → {arc.last_seen_date} · {arc.mention_count} articles
              </div>
            </a>
          ))}
        </div>
      )}

      {/* Key Figures */}
      {keyFigures.length > 0 && (
        <div className="holo-panel">
          <div className="holo-title">Key Figures</div>
          {keyFigures.map((fig) => {
            const classified = !isUnlocked(fig.first_seen_date);
            return (
              <a
                key={fig.id}
                href={`${import.meta.env.BASE_URL}entity/${fig.id}/`}
                className={`entity-card ${classified ? 'classified' : ''}`}
                style={{ textDecoration: 'none' }}
              >
                <div className={`entity-icon ${fig.type || 'person'}`}>
                  {entityTypeLabel[fig.type] || '?'}
                </div>
                <div style={{ minWidth: 0 }}>
                  <div className="entity-name">{fig.name}</div>
                  <div className="entity-meta">
                    {fig.first_seen_date} · {fig.count} mentions
                  </div>
                </div>
              </a>
            );
          })}
        </div>
      )}

      {/* Empty state */}
      {activeArcs.length === 0 && keyFigures.length === 0 && (
        <div className="holo-panel" style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-dim)' }}>
            No data for this period
          </div>
        </div>
      )}
    </div>
  );
}
