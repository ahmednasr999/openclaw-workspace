import nunjucks from 'nunjucks';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { templateRegistry } from './templateRegistry.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const templatesDir = path.resolve(__dirname, '../../templates');

const env = nunjucks.configure(templatesDir, {
  autoescape: false,
  trimBlocks: true,
  lstripBlocks: true
});

export type SlidePayload = {
  pattern: string;
  eyebrow?: string;
  title: string;
  subtitle?: string;
  notes?: string;
  [key: string]: unknown;
};

export function renderSlide(payload: SlidePayload): string {
  const templateName = templateRegistry[payload.pattern];
  if (!templateName) {
    throw new Error(`Unsupported slide pattern: ${payload.pattern}`);
  }
  return env.render(templateName, payload);
}
