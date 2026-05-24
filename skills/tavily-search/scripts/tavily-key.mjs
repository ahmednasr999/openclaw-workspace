import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

export function loadTavilyKey() {
  const envKey = (process.env.TAVILY_API_KEY ?? "").trim();
  if (envKey) return envKey;

  try {
    const here = path.dirname(fileURLToPath(import.meta.url));
    const configPath = path.resolve(here, "../../../config/tavily.json");
    const raw = fs.readFileSync(configPath, "utf8");
    const parsed = JSON.parse(raw);
    return String(parsed?.api_key ?? "").trim();
  } catch {
    return "";
  }
}
