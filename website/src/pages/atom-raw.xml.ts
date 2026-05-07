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
    .sort((a, b) => (b.date || '').localeCompare(a.date || ''))
    .slice(0, 200);

  const now = new Date().toISOString();

  const entries = articles.map((art) => {
    const link = `${baseUrl}/?article=${art.uuid}`;
    const updated = art.date
      ? art.date.replace(/^(\d{4})-(\d{2})-(\d{2})$/, '$1-$2-$3T12:00:00Z')
      : now;
    const body = art.body_full
      ? escapeXml(art.body_full)
      : '';

    return `
  <entry>
    <title>${escapeXml(art.title)}</title>
    <link href="${link}" rel="alternate" type="text/html" />
    <id>urn:uuid:${art.uuid}</id>
    <updated>${updated}</updated>
    <content type="html">
      &lt;p&gt;${body.replace(/\n/g, '&lt;br/&gt;')}&lt;/p&gt;
    </content>
    ${art.source_url ? `<link href="${escapeXml(art.source_url)}" rel="related" />` : ''}
  </entry>`;
  }).join('');

  const atom = `<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xml:lang="en">
  <title>GalNet Chronicle — Elite Dangerous Lore (Raw)</title>
  <subtitle>Raw GalNet articles from the Elite Dangerous universe (3301–3312)</subtitle>
  <link href="${baseUrl}/atom-raw.xml" rel="self" type="application/atom+xml" />
  <link href="${baseUrl}/" rel="alternate" type="text/html" />
  <updated>${now}</updated>
  <id>${baseUrl}/atom-raw.xml</id>
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
