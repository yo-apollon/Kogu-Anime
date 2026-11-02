/**
 * Enriquecimento das 3 Eras da Vida (Era I: Básica, Era II: Épica, Era III: Mítica)
 * no catálogo estático (`docs/catalog.json` + `docs/catalog.meta.json`) e, se DATABASE_URL
 * estiver presente, também no banco PostgreSQL ativo (`entity_images` + `entities.description`).
 *
 * O que faz:
 *  1. Vincula artes distintas de formas alternativas já existentes no catálogo (ex.: Ichigo Vasto Lorde,
 *     Dante Sin Devil Trigger, Rem, Hanako, Kurama, Merlin, etc.) às edições EPIC e MYTHIC.
 *  2. Enriquece as descrições e subtítulos de Era para que toda edição BASIC / EPIC / MYTHIC
 *     reflita claramente as 3 Eras da Vida (Juventude / O Auge / Apogeu Lendário 1/1).
 *  3. Recalcula e salva `docs/catalog.meta.json` com o hash SHA-256 exato exigido por `siteExport.ts`.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildMeta, serializeCatalog, type SiteCard } from "../catalog/siteExport.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DOCS_DIR = path.resolve(__dirname, "../../docs");
const CATALOG_PATH = path.join(DOCS_DIR, "catalog.json");
const META_PATH = path.join(DOCS_DIR, "catalog.meta.json");

function normalizeBaseName(name: string): string {
  return name
    .replace(/\s*\(.*?\)\s*/g, "")
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .sort()
    .join(" ");
}

export async function enrichCatalogFile(catalogPath = CATALOG_PATH, metaPath = META_PATH) {
  const raw = await fs.readFile(catalogPath, "utf8");
  const cards = JSON.parse(raw) as SiteCard[];

  // Agrupa todas as URLs de arte distintas por nome base normalizado
  const imagesByNormName = new Map<string, string[]>();
  for (const c of cards) {
    if (!c.imageUrl || c.art.mode !== "IMAGE") continue;
    const key = normalizeBaseName(c.name);
    const list = imagesByNormName.get(key) ?? [];
    if (!list.includes(c.imageUrl)) {
      list.push(c.imageUrl);
    }
    imagesByNormName.set(key, list);
  }

  const bySlug = new Map(cards.map((c) => [c.slug, c]));

  let linkedEpicImages = 0;
  let linkedMythicImages = 0;
  let enrichedAliases = 0;

  for (const c of cards) {
    if (!c.edition) continue;

    const anchorSlug = c.parentSlug ?? c.slug;
    const anchor = bySlug.get(anchorSlug) ?? c;
    const normKey = normalizeBaseName(anchor.name);
    const distinctUrls = imagesByNormName.get(normKey) ?? [];

    // Adiciona alias de Era para facilitar busca e identificação no portal e no bot
    const eraTag =
      c.edition === "BASIC"
        ? "Era I: O Início"
        : c.edition === "EPIC"
          ? "Era II: O Auge"
          : "Era III: O Apogeu (1/1)";
    if (!c.aliases.includes(eraTag)) {
      c.aliases.push(eraTag);
      enrichedAliases++;
    }

    if (c.edition === "EPIC" && distinctUrls.length >= 2) {
      const altUrl = distinctUrls[1]!;
      if (c.imageUrl !== altUrl) {
        c.imageUrl = altUrl;
        c.art = { mode: "IMAGE", url: altUrl };
        linkedEpicImages++;
      }
    } else if (c.edition === "MYTHIC" && distinctUrls.length >= 2) {
      const altUrl = distinctUrls[distinctUrls.length >= 3 ? 2 : 1]!;
      if (c.imageUrl !== altUrl) {
        c.imageUrl = altUrl;
        c.art = { mode: "IMAGE", url: altUrl };
        linkedMythicImages++;
      }
    }
  }

  const meta = buildMeta(cards, new Date());
  await fs.writeFile(catalogPath, serializeCatalog(cards), "utf8");
  await fs.writeFile(metaPath, `${JSON.stringify(meta, null, 2)}\n`, "utf8");

  return {
    totalCards: cards.length,
    linkedEpicImages,
    linkedMythicImages,
    enrichedAliases,
    hash: meta.hash,
  };
}

async function syncDatabaseEditions(): Promise<{ dbUpdatedImages: number; dbUpdatedDescs: number }> {
  const dbUrl = process.env.DATABASE_URL;
  if (!dbUrl) return { dbUpdatedImages: 0, dbUpdatedDescs: 0 };

  const postgres = (await import("postgres")).default;
  const sql = postgres(dbUrl, { max: 1, onnotice: () => {} });
  try {
    // 1. Atualiza descrições de Era nas edições EPIC e MYTHIC que ainda têm a mesma descrição da BASIC
    const descRes = await sql`
      UPDATE entities e
      SET description = CASE
        WHEN e.edition = 'EPIC' THEN '⭐ [Era II: O Auge] ' || COALESCE(p.description, 'Forma no auge absoluto de poder e consagração.')
        WHEN e.edition = 'MYTHIC' THEN '👑 [Era III: O Apogeu Lendário 1/1] ' || COALESCE(p.description, 'Forma suprema e imortalizada no ápice histórico.')
        ELSE e.description
      END
      FROM entities p
      WHERE e.parent_id = p.id
        AND e.edition IN ('EPIC', 'MYTHIC')
        AND (e.description IS NULL OR e.description NOT LIKE '%[Era %')
    `;

    // 2. Para personagens que possuem outra carta ativa com mesmo name_normalized e URL diferente, vincula à edição EPIC/MYTHIC
    const imgRes = await sql`
      UPDATE entity_images ei
      SET url = alt.url
      FROM entities e
      JOIN entities p ON p.id = e.parent_id
      JOIN LATERAL (
        SELECT i2.url
        FROM entities e2
        JOIN entity_images i2 ON i2.entity_id = e2.id AND i2.is_primary = true AND i2.status = 'ACTIVE'
        WHERE e2.name_normalized = p.name_normalized
          AND e2.id <> p.id
          AND e2.parent_id IS NULL
          AND i2.url <> ei.url
        ORDER BY e2.popularity_score DESC, e2.id ASC
        LIMIT 1
      ) alt ON true
      WHERE ei.entity_id = e.id
        AND ei.is_primary = true
        AND e.edition IN ('EPIC', 'MYTHIC')
    `;

    return {
      dbUpdatedImages: imgRes.count ?? 0,
      dbUpdatedDescs: descRes.count ?? 0,
    };
  } finally {
    await sql.end({ timeout: 5 });
  }
}

async function main() {
  const fileReport = await enrichCatalogFile();
  console.log("[enrichThreeEras] Catálogo estático atualizado:", fileReport);
  if (process.env.DATABASE_URL) {
    const dbReport = await syncDatabaseEditions();
    console.log("[enrichThreeEras] Banco PostgreSQL sincronizado:", dbReport);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
