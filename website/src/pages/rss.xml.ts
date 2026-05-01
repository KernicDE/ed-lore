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

  const lastBuildDate = new Date().toUTCString();

  const items = articles.map((art) => {
    const link = `${baseUrl}/?article=${art.uuid}`;
    const pubDate = art.date
      ? new Date(art.date.replace(/^(\d{4})-(\d{2})-(\d{2})$/, '$1-$2-$3T12:00:00Z')).toUTCString()
      : lastBuildDate;
    const description = art.summary
      ? escapeXml(art.summary)
      : escapeXml(art.body_preview || '');
    const content = art.body_full
      ? escapeXml(art.body_full.slice(0, 2000))
      : description;

    return `
    <item>
      <title>${escapeXml(art.title)}</title>
      <link>${link}</link>
      <guid isPermaLink="false">${art.uuid}</guid>
      <pubDate>${pubDate}</pubDate>
      <description>${description}</description>
      <content:encoded><![CDATA[
        <p>${description}</p>
        <h3>Article</h3>
        <p>${content.replace(/\n/g, '<br/>')}</p>
        ${art.player_impact ? `<h3>Player Impact</h3><p>${escapeXml(art.player_impact)}</p>` : ''}
        ${art.modern_impact ? `<h3>Future Impact</h3><p>${escapeXml(art.modern_impact)}</p>` : ''}
      ]]></content:encoded>
      ${art.arc_id ? `<category>${escapeXml(art.arc_id)}</category>` : ''}
    </item>`;
  }).join('');

  const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>GalNet Chronicle — Elite Dangerous Lore</title>
    <link>${baseUrl}/</link>
    <description>AI-enriched GalNet articles from the Elite Dangerous universe (3301–3312)</description>
    <language>en</language>
    <lastBuildDate>${lastBuildDate}</lastBuildDate>
    <atom:link href="${baseUrl}/rss.xml" rel="self" type="application/rss+xml" />
    <image>
      <url>${baseUrl}/favicon.svg</url>
      <title>GalNet Chronicle</title>
      <link>${baseUrl}/</link>
    </image>
    ${items}
  </channel>
</rss>`;

  return new Response(rss, {
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
    },
  });
};
