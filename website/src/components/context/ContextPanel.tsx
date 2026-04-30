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
  visibleArticles: { arc_id: string | null; entities: string[]; groups: string[]; locations: string[]; topics: string[]; persons: string[]; technologies: string[] }[];
}

function makeEid(name: string): string {
  return name.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
}

/** Exclude sentence-fragment false positives from entity extraction */
function isGarbageName(name: string): boolean {
  const lower = name.toLowerCase();
  const badPrefixes = [
    'a ', 'an ', 'the ', 'his ', 'her ', 'their ', 'our ', 'we ', 'it ',
    'this ', 'that ', 'these ', 'those ', 'authorities', 'spokesperson',
    'representative', 'observers', 'competitors', 'citizens', 'many ',
    'several ', 'hundreds', 'dozens', 'those ', 'these ', 'there ',
    'here ', 'when ', 'where ', 'why ', 'how ', 'what ', 'who ', 'which ',
    'under ', 'over ', 'into ', 'onto ', 'upon ', 'within ', 'without ',
    'across ', 'along ', 'around ', 'behind ', 'beside ', 'beyond ',
    'despite ', 'during ', 'except ', 'inside ', 'outside ', 'through ',
    'toward ', 'towards ', 'until ', 'via ', 'with ', 'within ', 'according ',
    'following ', 'regarding ', 'concerning ', 'considering ', 'including ',
    'assuming ', 'based ', 'according ', 'thanks ', 'due ', 'owing ', 'prior ',
    'subsequent ', 'regardless ', 'notwithstanding ', 'after ', 'before ',
    'since ', 'while ', 'whereas ', 'although ', 'though ', 'unless ', 'whether ',
    'because ', 'as ', 'once ', 'until ', 'till ', 'than ', 'then ', 'now ',
    'later ', 'soon ', 'earlier ', 'recently ', 'currently ', 'previously ',
    'originally ', 'initially ', 'finally ', 'eventually ', 'ultimately ',
    'suddenly ', 'gradually ', 'immediately ', 'shortly ', 'frequently ',
    'often ', 'sometimes ', 'rarely ', 'never ', 'always ', 'usually ',
    'generally ', 'typically ', 'normally ', 'commonly ', 'partly ',
    'mostly ', 'almost ', 'nearly ', 'approximately ', 'roughly ', 'about ',
    'exactly ', 'precisely ', 'specifically ', 'particularly ', 'especially ',
    'notably ', 'mainly ', 'primarily ', 'essentially ', 'basically ',
    'effectively ', 'potentially ', 'likely ', 'probably ', 'possibly ',
    'perhaps ', 'maybe ', 'certainly ', 'definitely ', 'absolutely ',
    'clearly ', 'obviously ', 'evidently ', 'apparently ', 'seemingly ',
    'presumably ', 'allegedly ', 'reportedly ', 'supposedly ', 'arguably ',
    'admittedly ', 'fortunately ', 'unfortunately ', 'luckily ', 'regrettably ',
    'sadly ', 'happily ', 'strangely ', 'oddly ', 'curiously ', 'interestingly ',
    'significantly ', 'importantly ', 'crucially ', 'vitally ', 'critically ',
    'seriously ', 'severely ', 'extremely ', 'highly ', 'strongly ', 'weakly ',
    'deeply ', 'greatly ', 'considerably ', 'substantially ', 'markedly ',
    'noticeably ', 'remarkably ', 'strikingly ', 'dramatically ', 'radically ',
    'fundamentally ', 'thoroughly ', 'completely ', 'totally ', 'entirely ',
    'fully ', 'wholly ', 'partly ', 'partially ', 'half ', 'quarter ',
    'third ', 'twice ', 'double ', 'triple ', 'single ', 'multiple ',
    'various ', 'several ', 'numerous ', 'countless ', 'infinite ', 'endless ',
    'limitless ', 'boundless ', 'vast ', 'huge ', 'massive ', 'enormous ',
    'immense ', 'gigantic ', 'colossal ', 'tremendous ', 'immense ', 'great ',
    'large ', 'big ', 'small ', 'tiny ', 'little ', 'miniature ', 'microscopic ',
    'short ', 'long ', 'brief ', 'extended ', 'lasting ', 'temporary ',
    'permanent ', 'constant ', 'continuous ', 'ongoing ', 'intermittent ',
    'sporadic ', 'occasional ', 'regular ', 'irregular ', 'frequent ',
    'infrequent ', 'periodic ', 'seasonal ', 'annual ', 'monthly ', 'weekly ',
    'daily ', 'hourly ', 'nightly ', 'weekly ', 'yearly ', 'decadal ',
  ];
  if (badPrefixes.some(p => lower.startsWith(p))) return true;
  if (/\b(in|of|to|from|at|on|with|by|for|about|into|onto|upon|within|without|across|along|around|behind|beside|beyond|despite|during|except|inside|outside|through|toward|towards|until|via|regarding|concerning|considering|including|according|following|thanks|due|owing|prior|subsequent|regardless|notwithstanding)\s+the\b/.test(name)) return true;
  return false;
}

function isQualityEntity(name: string, count: number): boolean {
  if (count < 2) return false;
  return !isGarbageName(name);
}

export default function ContextPanel({
  currentDate,
  entities,
  arcs,
  visibleArticles,
}: ContextPanelProps) {
  const isUnlocked = (firstSeen: string | null | undefined) => {
    if (!firstSeen) return true;
    return firstSeen <= currentDate;
  };

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

  const keyFigures = useMemo(() => {
    const counts = new Map<string, number>();
    visibleArticles.forEach((a) => {
      // Prefer manually enriched persons/technologies/groups/locations over
      // rule-based entities which contain sentence fragments
      [...a.persons, ...a.technologies, ...a.groups, ...a.locations].forEach((name) => {
        const eid = makeEid(name);
        counts.set(eid, (counts.get(eid) || 0) + 1);
      });
      // Only include rule-based entities if they look like proper nouns (no spaces = likely a name)
      a.entities.forEach((name) => {
        if (name.includes(' ')) return; // skip sentence fragments
        const eid = makeEid(name);
        counts.set(eid, (counts.get(eid) || 0) + 1);
      });
    });
    return Array.from(counts.entries())
      .map(([eid, count]) => ({ ...entities[eid], count }))
      .filter((e) => e && e.id && isUnlocked(e.first_seen_date))
      .filter((e) => !isGarbageName(e.name))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }, [visibleArticles, entities, currentDate]);

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
    technology: 'T',
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
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-dim)', marginTop: 6 }}>
          Timeline Date: {currentDate}
        </div>
      </div>

      {/* Related Arcs */}
      {activeArcs.length > 0 && (
        <div className="holo-panel blue">
          <div className="holo-title blue">Related Arcs</div>
          {activeArcs.map((arc) => (
            <a
              key={arc.id}
              href={`${(import.meta.env.BASE_URL || '').replace(/\/$/, '')}/arc/${arc.id}/`}
              style={{
                display: 'block',
                padding: '10px 0',
                borderBottom: '1px solid var(--border-default)',
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              <div style={{ fontSize: 15, fontWeight: 500, color: 'var(--text-primary)' }}>
                {arc.name}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
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
                href={`${(import.meta.env.BASE_URL || '').replace(/\/$/, '')}/entity/${fig.id}/`}
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

      {activeArcs.length === 0 && keyFigures.length === 0 && (
        <div className="holo-panel" style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-dim)' }}>
            No data for this period
          </div>
        </div>
      )}
    </div>
  );
}
