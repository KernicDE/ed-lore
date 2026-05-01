import type { APIRoute } from 'astro';
import graphData from '../data/lore_graph.json';

export const prerender = true;

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

export const GET: APIRoute = () => {
  const baseUrl = 'https://kernicde.github.io/ed-lore';
  const articles = (graphData.articles as any[])
    .filter((a) => a.summary)
    .sort((a, b) => (b.date || '').localeCompare(a.date || ''))
    .slice(0, 100);

  const now = new Date().toISOString();

  const entries = articles.map((art) => {
    const link = `${baseUrl}/?article=${art.uuid}`;
    const updated = art.date
      ? art.date.replace(/^(\d{4})-(\d{2})-(\d{2})$/, '$1-$2-$3T12:00:00Z')
      : now;
    const summary = art.summary
      ? escapeXml(art.summary)
      : escapeXml(art.body_preview || '');
    const content = art.body_full
      ? escapeXml(art.body_full.slice(0, 2000))
      : summary;

    return `
  <entry>
    <title>${escapeXml(art.title)}</title>
    <link href="${link}" rel="alternate" type="text/html" />
    <id>urn:uuid:${art.uuid}</id>
    <updated>${updated}</updated>
    <summary type="html">${summary}</summary>
    <content type="html">
      &lt;p&gt;${summary}&lt;/p&gt;
      &lt;h3&gt;Article&lt;/h3&gt;
      &lt;p&gt;${content.replace(/\n/g, '&lt;br/&gt;')}&lt;/p&gt;
      ${art.player_impact ? `&lt;h3&gt;Player Impact&lt;/h3&gt;&lt;p&gt;${escapeXml(art.player_impact)}&lt;/p&gt;` : ''}
      ${art.modern_impact ? `&lt;h3&gt;Future Impact&lt;/h3&gt;&lt;p&gt;${escapeXml(art.modern_impact)}&lt;/p&gt;` : ''}
    </content>
    ${art.arc_id ? `<category term="${escapeXml(art.arc_id)}" />` : ''}
  </entry>`;
  }).join('');

  const atom = `<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xml:lang="en">
  <title>GalNet Chronicle — Elite Dangerous Lore</title>
  <subtitle>AI-enriched GalNet articles from the Elite Dangerous universe (3301–3312)</subtitle>
  <link href="${baseUrl}/atom.xml" rel="self" type="application/atom+xml" />
  <link href="${baseUrl}/" rel="alternate" type="text/html" />
  <updated>${now}</updated>
  <id>${baseUrl}/</id>
  <icon>${baseUrl}/favicon.svg</icon>
  <logo>${baseUrl}/favicon.svg</logo>
  <author>
    <name>GalNet Chronicle</name>
  </author>
  ${entries}
</feed>`;

  return new Response(atom, {
    headers: {
      'Content-Type': 'application/atom+xml; charset=utf-8',
    },
  });
};
