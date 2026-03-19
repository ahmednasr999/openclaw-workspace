#!/usr/bin/env node
/**
 * Crawlee scraper for OpenClaw
 * Usage:
 *   node scrape.mjs <url> [--depth N] [--max N] [--selector CSS] [--output FILE] [--format json|text|markdown]
 *
 * Examples:
 *   node scrape.mjs https://example.com
 *   node scrape.mjs https://example.com --depth 2 --max 10 --format json --output results.json
 *   node scrape.mjs https://example.com --selector "article h2, article p" --format text
 */

import { CheerioCrawler, Dataset, Configuration } from 'crawlee';
import { writeFileSync } from 'fs';
import { resolve } from 'path';

// Parse CLI args
const args = process.argv.slice(2);
if (args.length === 0 || args[0] === '--help') {
  console.log(`
Crawlee Scraper for OpenClaw

Usage: node scrape.mjs <url> [options]

Options:
  --depth N        Max crawl depth (default: 0 = single page)
  --max N          Max pages to crawl (default: 1)
  --selector CSS   CSS selector to extract specific elements
  --output FILE    Save results to file (default: stdout)
  --format FMT     Output format: json, text, markdown (default: markdown)
  --links          Also extract all links from pages
  --headers        Include HTTP headers in output
  --glob PATTERN   Only follow links matching glob pattern
  --exclude PATTERN Exclude links matching glob pattern

Examples:
  # Scrape single page as markdown
  node scrape.mjs https://example.com

  # Scrape with depth, save JSON
  node scrape.mjs https://example.com --depth 2 --max 20 --format json --output data.json

  # Extract specific elements
  node scrape.mjs https://news.ycombinator.com --selector ".titleline > a" --format json
  `);
  process.exit(0);
}

function getArg(flag, defaultVal) {
  const idx = args.indexOf(flag);
  if (idx === -1) return defaultVal;
  return args[idx + 1] || defaultVal;
}

function hasFlag(flag) {
  return args.includes(flag);
}

const startUrl = args.find(a => !a.startsWith('--'));
const maxDepth = parseInt(getArg('--depth', '0'), 10);
const maxPages = parseInt(getArg('--max', '1'), 10);
const selector = getArg('--selector', null);
const outputFile = getArg('--output', null);
const format = getArg('--format', 'markdown');
const extractLinks = hasFlag('--links');
const includeHeaders = hasFlag('--headers');
const glob = getArg('--glob', null);
const exclude = getArg('--exclude', null);

if (!startUrl) {
  console.error('Error: URL is required');
  process.exit(1);
}

const results = [];
let pageCount = 0;

// Use in-memory storage to avoid polluting disk
const config = Configuration.getGlobalConfig();
config.set('persistStorage', false);

const crawler = new CheerioCrawler({
  maxRequestsPerCrawl: maxPages,
  maxCrawlDepth: maxDepth,

  async requestHandler({ request, $, enqueueLinks, log }) {
    pageCount++;
    const pageData = {
      url: request.url,
      title: $('title').text().trim(),
    };

    if (includeHeaders) {
      pageData.headers = request.headers;
    }

    if (selector) {
      // Extract specific elements
      const elements = [];
      $(selector).each((i, el) => {
        const $el = $(el);
        elements.push({
          tag: el.tagName,
          text: $el.text().trim(),
          href: $el.attr('href') || null,
          html: $el.html()?.trim(),
        });
      });
      pageData.elements = elements;
    } else {
      // Extract full page content
      // Remove script, style, nav, footer for cleaner content
      $('script, style, nav, footer, header, aside, [role="navigation"], [role="banner"]').remove();
      
      const bodyText = $('body').text().replace(/\s+/g, ' ').trim();
      pageData.text = bodyText;

      // Try to get structured content
      const headings = [];
      $('h1, h2, h3, h4, h5, h6').each((i, el) => {
        headings.push({ level: el.tagName, text: $(el).text().trim() });
      });
      if (headings.length > 0) pageData.headings = headings;

      const paragraphs = [];
      $('p').each((i, el) => {
        const text = $(el).text().trim();
        if (text.length > 20) paragraphs.push(text);
      });
      if (paragraphs.length > 0) pageData.paragraphs = paragraphs;
    }

    if (extractLinks) {
      const links = [];
      $('a[href]').each((i, el) => {
        const href = $(el).attr('href');
        const text = $(el).text().trim();
        if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
          links.push({ text: text || null, href });
        }
      });
      pageData.links = links;
    }

    results.push(pageData);
    log.info(`Scraped [${pageCount}/${maxPages}]: ${request.url}`);

    // Enqueue links if crawling deeper
    if (maxDepth > 0) {
      const enqueueOpts = {};
      if (glob) enqueueOpts.globs = [glob];
      if (exclude) enqueueOpts.exclude = [exclude];
      await enqueueLinks(enqueueOpts);
    }
  },

  failedRequestHandler({ request, log }) {
    log.error(`Failed: ${request.url}`);
  },
});

await crawler.run([startUrl]);

// Format output
let output;
if (format === 'json') {
  output = JSON.stringify(results, null, 2);
} else if (format === 'text') {
  output = results.map(r => {
    let text = `=== ${r.title} ===\nURL: ${r.url}\n\n`;
    if (r.elements) {
      text += r.elements.map(e => e.text).join('\n');
    } else {
      text += r.text || '';
    }
    return text;
  }).join('\n\n---\n\n');
} else {
  // markdown
  output = results.map(r => {
    let md = `# ${r.title}\n\n> ${r.url}\n\n`;
    if (r.elements) {
      md += r.elements.map(e => {
        if (e.href) return `- [${e.text}](${e.href})`;
        return `- ${e.text}`;
      }).join('\n');
    } else {
      if (r.headings) {
        // Reconstruct with headings and paragraphs
        const pIdx = { i: 0 };
        for (const h of r.headings) {
          const level = parseInt(h.level.replace('h', ''), 10);
          md += `${'#'.repeat(level)} ${h.text}\n\n`;
        }
        if (r.paragraphs) {
          md += r.paragraphs.join('\n\n');
        }
      } else {
        md += r.text || '';
      }
    }
    if (r.links && r.links.length > 0) {
      md += '\n\n## Links\n\n';
      md += r.links.slice(0, 50).map(l => `- [${l.text || l.href}](${l.href})`).join('\n');
    }
    return md;
  }).join('\n\n---\n\n');
}

if (outputFile) {
  writeFileSync(resolve(outputFile), output, 'utf-8');
  console.log(`Results saved to ${outputFile} (${results.length} pages)`);
} else {
  console.log(output);
}

console.error(`\nDone: ${results.length} pages scraped.`);
