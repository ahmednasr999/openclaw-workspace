import { stat } from "node:fs/promises";

interface CacheEntry<T> {
  data: T;
  mtime: number;
  fetchedAt: number;
}

const cache = new Map<string, CacheEntry<unknown>>();

export async function getOrParse<T>(
  filePath: string,
  parserFn: (content: string) => T,
  ttlMs = 30000
): Promise<T | null> {
  const now = Date.now();

  let currentMtime = 0;
  try {
    const s = await stat(filePath);
    currentMtime = s.mtimeMs;
  } catch {
    // file does not exist
    return null;
  }

  const existing = cache.get(filePath) as CacheEntry<T> | undefined;
  if (
    existing &&
    existing.mtime === currentMtime &&
    now - existing.fetchedAt < ttlMs
  ) {
    return existing.data;
  }

  // Need to (re)parse
  const { readFile } = await import("node:fs/promises");
  let content: string;
  try {
    content = await readFile(filePath, "utf8");
  } catch {
    return null;
  }

  const data = parserFn(content);
  cache.set(filePath, { data, mtime: currentMtime, fetchedAt: now });
  return data;
}

export function getCacheStats() {
  return {
    entries: cache.size,
    keys: Array.from(cache.keys()),
  };
}
