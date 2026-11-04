/**
 * Enriquecimento das 3 Eras da Vida (Era I: Básica, Era II: Épica, Era III: Mítica),
 * renderização de artes de Armas (68 itens) e variações Épica/Mítica, deduplicação de
 * árvores duplicadas (`-anilist`) e propagação de nichos no catálogo (`docs/catalog.json` +
 * `docs/catalog.meta.json`) e, se DATABASE_URL estiver presente, também no banco PostgreSQL.
 */
import { createCanvas, loadImage, type Image, type SKRSContext2D } from "@napi-rs/canvas";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { OverrideKind } from "../catalog/artQuality.js";
import { buildMeta, serializeCatalog, sortAndRank, type SiteCard } from "../catalog/siteExport.js";
import { drawAstral } from "../canvas/effects/astral.js";
import { drawFoil } from "../canvas/effects/foil.js";
import { drawHolo } from "../canvas/effects/holo.js";
import { hashSeed } from "../canvas/effects/noise.js";
import { drawEmblem } from "../canvas/emblems/draw.js";
import { pickEmblem, type EmblemKey } from "../canvas/emblems/pick.js";
import { roundRectPath, type Rect } from "../canvas/engine/draw/shapes.js";
import { registerFonts } from "../canvas/engine/fonts.js";
import { TIER_FRAME_COLOR } from "../canvas/theme/tiers.js";
import { lighten, resolveTheme, rgba } from "../canvas/theme/tokens.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DOCS_DIR = path.resolve(__dirname, "../../docs");
const CARDS_ASSETS_DIR = path.join(DOCS_DIR, "assets/cards");
const PORTRAITS_CACHE_DIR = path.resolve(__dirname, "../../.cache/portraits");
const ERA_PHOTOS_DIR = path.resolve(__dirname, "../../.cache/era_photos");
const OVERRIDES_PATH = path.resolve(__dirname, "../../data/art/overrides.json");
const CATALOG_PATH = path.join(DOCS_DIR, "catalog.json");
const META_PATH = path.join(DOCS_DIR, "catalog.meta.json");
const OWN_CARDS_BASE = "https://yo-apollon.github.io/Kogu-Anime/assets/cards/";

const SLUG_TO_ASSET_ALIAS: Record<string, string> = {
  "the-weeknd-starboy": "the-weeknd.jpg",
};

const BROKEN_URL_FIXES: Record<string, string> = {
  "https://s4.anilist.co/file/anilistcdn/character/large/b1632-6p7u8N6m0T6v.png":
    "https://s4.anilist.co/file/anilistcdn/character/large/1632.jpg",
  "https://s4.anilist.co/file/anilistcdn/character/large/b282797-Uta.png":
    "https://s4.anilist.co/file/anilistcdn/character/large/b270493-pviD8gBS5BXW.png",
};

const W = 480;
const H = 750;
const RADIUS = Math.round(W * 0.04);
const ART_RECT: Rect = { x: 0, y: 0, w: W, h: H };

function drawCoverImage(g: SKRSContext2D, img: Image, rect: Rect, yBias = 0.08): void {
  const imgRatio = img.width / img.height;
  const boxRatio = rect.w / rect.h;
  let drawW = rect.w;
  let drawH = rect.h;
  let ox = rect.x;
  let oy = rect.y;
  if (imgRatio > boxRatio) {
    drawW = rect.h * imgRatio;
    ox = rect.x - (drawW - rect.w) / 2;
  } else {
    drawH = rect.w / imgRatio;
    oy = rect.y - (drawH - rect.h) * yBias;
  }
  g.drawImage(img, ox, oy, drawW, drawH);
}

async function renderWeaponAsset(card: SiteCard, emblem: EmblemKey, outFile: string): Promise<void> {
  registerFonts();
  const canvas = createCanvas(W, H);
  const g = canvas.getContext("2d");
  const tier = card.tier ?? "EPIC";
  const theme = resolveTheme(tier, "FOIL");
  const seed = hashSeed(`${card.slug}|WEAPON`);

  g.save();
  roundRectPath(g, ART_RECT, RADIUS);
  g.clip();
  drawEmblem(g, emblem, ART_RECT, { theme, tier, seed, name: card.name });
  drawFoil(g, ART_RECT, { seed, tint: theme.primary, intensity: 0.7 });
  g.restore();

  const edge = 3;
  const r: Rect = { x: edge / 2, y: edge / 2, w: W - edge, h: H - edge };
  g.save();
  const tierColor = TIER_FRAME_COLOR[tier] ?? theme.primary;
  g.strokeStyle = lighten(tierColor, 0.25);
  g.lineWidth = edge;
  roundRectPath(g, r, RADIUS - edge / 2);
  g.stroke();
  g.restore();

  const buf = await canvas.encode("jpeg", 90);
  await fs.writeFile(outFile, buf);
}

async function renderEditionVariantAsset(
  portraitImg: Image,
  slug: string,
  edition: "EPIC" | "MYTHIC",
  outFile: string
): Promise<void> {
  registerFonts();
  const canvas = createCanvas(W, H);
  const g = canvas.getContext("2d");
  const tier = edition === "MYTHIC" ? "MYTHIC" : "EPIC";
  const variant = edition === "MYTHIC" ? "ASTRAL" : "HOLO";
  const theme = resolveTheme(tier, variant);
  const seed = hashSeed(`${slug}|${edition}`);

  g.save();
  roundRectPath(g, ART_RECT, RADIUS);
  g.clip();
  drawCoverImage(g, portraitImg, ART_RECT, 0.08);

  if (edition === "EPIC") {
    drawHolo(g, ART_RECT, { seed, intensity: 0.78 });
    const aura = g.createLinearGradient(0, 0, W, H);
    aura.addColorStop(0, rgba("#A855F7", 0.24));
    aura.addColorStop(0.5, rgba("#A855F7", 0));
    aura.addColorStop(1, rgba("#7E22CE", 0.32));
    g.fillStyle = aura;
    g.fillRect(0, 0, W, H);
  } else {
    drawAstral(g, ART_RECT, { seed, theme, intensity: 0.85 });
    const aura = g.createLinearGradient(0, 0, W, H);
    aura.addColorStop(0, rgba("#FACC15", 0.26));
    aura.addColorStop(0.45, rgba("#FF2E63", 0.08));
    aura.addColorStop(1, rgba("#FF2E63", 0.34));
    g.fillStyle = aura;
    g.fillRect(0, 0, W, H);
  }
  g.restore();

  // Moldura de Era II (Roxa HOLO) ou Era III (Ouro/Carmesim ASTRAL 1/1)
  const edge = edition === "MYTHIC" ? 5 : 4;
  const r: Rect = { x: edge / 2, y: edge / 2, w: W - edge, h: H - edge };
  g.save();
  const borderGrad = g.createLinearGradient(0, 0, W, H);
  if (edition === "MYTHIC") {
    borderGrad.addColorStop(0, "#FACC15");
    borderGrad.addColorStop(0.5, "#FF2E63");
    borderGrad.addColorStop(1, "#FACC15");
  } else {
    borderGrad.addColorStop(0, "#C084FC");
    borderGrad.addColorStop(0.5, "#38BDF8");
    borderGrad.addColorStop(1, "#A855F7");
  }
  g.strokeStyle = borderGrad;
  g.lineWidth = edge;
  roundRectPath(g, r, RADIUS - edge / 2);
  g.stroke();
  g.restore();

  const buf = await canvas.encode("jpeg", 90);
  await fs.writeFile(outFile, buf);
}

async function loadAnchorPortrait(anchor: SiteCard): Promise<Image | null> {
  const localPath = path.join(CARDS_ASSETS_DIR, `${anchor.slug}.jpg`);
  try {
    const buf = await fs.readFile(localPath);
    return await loadImage(buf);
  } catch {
    // Tenta cache em .cache/portraits/<slug>.img
  }
  const cachePath = path.join(PORTRAITS_CACHE_DIR, `${anchor.slug}.img`);
  try {
    const buf = await fs.readFile(cachePath);
    return await loadImage(buf);
  } catch {
    // Tenta pelo URL se for asset local com outro nome
  }
  if (anchor.imageUrl?.startsWith(OWN_CARDS_BASE)) {
    const fname = anchor.imageUrl.slice(OWN_CARDS_BASE.length);
    try {
      const buf = await fs.readFile(path.join(CARDS_ASSETS_DIR, fname));
      return await loadImage(buf);
    } catch {
      return null;
    }
  }
  return null;
}

async function loadEraPortrait(card: SiteCard, anchor: SiteCard): Promise<Image | null> {
  const eraPath = path.join(ERA_PHOTOS_DIR, `${card.slug}.jpg`);
  try {
    const buf = await fs.readFile(eraPath);
    return await loadImage(buf);
  } catch {
    // Foto de Era dedicada não encontrada; fallback para a portrait da âncora
  }
  return await loadAnchorPortrait(anchor);
}

export async function enrichCatalogFile(catalogPath = CATALOG_PATH, metaPath = META_PATH) {
  const raw = await fs.readFile(catalogPath, "utf8");
  let cards = JSON.parse(raw) as SiteCard[];

  await fs.mkdir(CARDS_ASSETS_DIR, { recursive: true });
  const assetFiles = new Set(await fs.readdir(CARDS_ASSETS_DIR).catch(() => [] as string[]));
  let linkedLocalAssets = 0;
  let renderedWeapons = 0;

  // 1. Normaliza URLs legadas (/kogu/ -> /Kogu-Anime/), corrige URLs 404 conhecidas e vincula assets locais
  for (const c of cards) {
    if (c.imageUrl && BROKEN_URL_FIXES[c.imageUrl]) {
      c.imageUrl = BROKEN_URL_FIXES[c.imageUrl]!;
      c.art = { mode: "IMAGE", url: c.imageUrl };
    }
    if (c.imageUrl?.startsWith("https://yo-apollon.github.io/kogu/")) {
      c.imageUrl = c.imageUrl.replace(
        "https://yo-apollon.github.io/kogu/",
        "https://yo-apollon.github.io/Kogu-Anime/"
      );
    }
    if (c.art.mode === "IMAGE" && c.art.url.startsWith("https://yo-apollon.github.io/kogu/")) {
      c.art = {
        mode: "IMAGE",
        url: c.art.url.replace(
          "https://yo-apollon.github.io/kogu/",
          "https://yo-apollon.github.io/Kogu-Anime/"
        ),
      };
    }

    // Refina emblema de armas se estiver "gem"
    if (c.art.mode === "EMBLEM" && c.art.emblem === "gem") {
      const refined = pickEmblem(c.name);
      if (refined !== "gem") {
        c.art = { mode: "EMBLEM", emblem: refined };
      }
    }

    // Renderiza arte dedicada em docs/assets/cards/<slug>.jpg para todas as armas (art.mode === 'EMBLEM' != 'character')
    if (c.art.mode === "EMBLEM" && c.art.emblem !== "character") {
      const weaponFile = `${c.slug}.jpg`;
      const weaponPath = path.join(CARDS_ASSETS_DIR, weaponFile);
      if (!assetFiles.has(weaponFile)) {
        await renderWeaponAsset(c, c.art.emblem as EmblemKey, weaponPath);
        assetFiles.add(weaponFile);
        renderedWeapons++;
      }
      const ownUrl = `${OWN_CARDS_BASE}${weaponFile}`;
      c.imageUrl = ownUrl;
      c.art = { mode: "IMAGE", url: ownUrl };
      linkedLocalAssets++;
      continue;
    }

    const baseSlug = c.parentSlug ?? c.slug;
    const candidateFile =
      (assetFiles.has(`${c.slug}.jpg`) ? `${c.slug}.jpg` : null) ??
      (assetFiles.has(`${baseSlug}.jpg`) ? `${baseSlug}.jpg` : null) ??
      (SLUG_TO_ASSET_ALIAS[baseSlug] && assetFiles.has(SLUG_TO_ASSET_ALIAS[baseSlug]!)
        ? SLUG_TO_ASSET_ALIAS[baseSlug]!
        : null);

    if (candidateFile && (c.art.mode === "EMBLEM" ? c.art.emblem === "character" : !c.imageUrl)) {
      const ownUrl = `${OWN_CARDS_BASE}${candidateFile}`;
      c.imageUrl = ownUrl;
      c.art = { mode: "IMAGE", url: ownUrl };
      linkedLocalAssets++;
    }
  }

  // 2. Deduplica árvores de personagens duplicadas que compartilham exatamente a mesma imageUrl na base
  const byImg = new Map<string, SiteCard[]>();
  for (const c of cards) {
    if (c.parentSlug === null && c.imageUrl) {
      const group = byImg.get(c.imageUrl) ?? [];
      group.push(c);
      byImg.set(c.imageUrl, group);
    }
  }

  const slugSet = new Set(cards.map((c) => c.slug));
  const toRemove = new Set<string>();
  const reparentMap = new Map<string, string>();

  for (const group of byImg.values()) {
    if (group.length <= 1) continue;
    const score = (c: SiteCard): number => {
      const notAnilist = c.slug.includes("-anilist") ? 0 : 1;
      const notParen = c.name.includes("(") ? 0 : 1;
      const hasEd = c.edition === "BASIC" ? 1 : 0;
      const rankScore = -(c.popularityRank ?? 999999);
      return notAnilist * 1_000_000_000 + notParen * 100_000_000 + hasEd * 10_000_000 + rankScore;
    };
    const ordered = [...group].sort((a, b) => score(b) - score(a));
    const winner = ordered[0]!;
    if (group.some((x) => x.edition === "BASIC")) {
      winner.edition = "BASIC";
    }
    let winnerHasEditions = slugSet.has(`${winner.slug}-epic`);
    for (const loser of ordered.slice(1)) {
      toRemove.add(loser.slug);
      if (winnerHasEditions) {
        toRemove.add(`${loser.slug}-epic`);
        toRemove.add(`${loser.slug}-mythic`);
      } else if (slugSet.has(`${loser.slug}-epic`)) {
        reparentMap.set(loser.slug, winner.slug);
        winnerHasEditions = true;
      }
    }
  }

  let deduplicatedCards = 0;
  const filteredCards: SiteCard[] = [];
  for (const c of cards) {
    if (toRemove.has(c.slug)) {
      deduplicatedCards++;
      continue;
    }
    if (c.parentSlug && toRemove.has(c.parentSlug) && !reparentMap.has(c.parentSlug)) {
      deduplicatedCards++;
      continue;
    }
    if (c.parentSlug && reparentMap.has(c.parentSlug)) {
      const newParent = reparentMap.get(c.parentSlug)!;
      const suffix = (c.edition ?? "epic").toLowerCase();
      c.parentSlug = newParent;
      c.slug = `${newParent}-${suffix}`;
    }
    filteredCards.push(c);
  }
  cards = filteredCards;

  // 3. Propaga niche, nicheLabel, prestige, name e seriesTitle da âncora para EPIC e MYTHIC e gera artes distintas por Era
  const bySlug = new Map(cards.map((c) => [c.slug, c]));
  let linkedEpicImages = 0;
  let linkedMythicImages = 0;
  let propagatedNiches = 0;
  let enrichedAliases = 0;

  for (const c of cards) {
    if (c.parentSlug) {
      const anchor = bySlug.get(c.parentSlug);
      if (anchor) {
        c.name = anchor.name;
        c.seriesTitle = anchor.seriesTitle;
        if (!c.niche && anchor.niche) {
          c.niche = anchor.niche;
          c.nicheLabel = anchor.nicheLabel;
          propagatedNiches++;
        }
        if (c.prestige === null && anchor.prestige !== null) {
          c.prestige = anchor.prestige;
        }
      }
    }

    if (!c.edition) continue;

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

    if (c.edition === "EPIC" || c.edition === "MYTHIC") {
      const anchor = (c.parentSlug ? bySlug.get(c.parentSlug) : null) ?? c;
      const variantFile = `${c.slug}.jpg`;
      const variantPath = path.join(CARDS_ASSETS_DIR, variantFile);
      const eraCachePath = path.join(ERA_PHOTOS_DIR, `${c.slug}.jpg`);

      const hasEraCache = await fs.access(eraCachePath).then(() => true).catch(() => false);
      let shouldRender = !assetFiles.has(variantFile);

      if (!shouldRender && hasEraCache) {
        try {
          const [eraStat, variantStat] = await Promise.all([
            fs.stat(eraCachePath),
            fs.stat(variantPath),
          ]);
          if (eraStat.mtimeMs > variantStat.mtimeMs || process.argv.includes("--rebuild-eras")) {
            shouldRender = true;
          }
        } catch {
          shouldRender = true;
        }
      }

      if (shouldRender) {
        const portraitImg = await loadEraPortrait(c, anchor);
        if (portraitImg) {
          await renderEditionVariantAsset(portraitImg, c.slug, c.edition as "EPIC" | "MYTHIC", variantPath);
          assetFiles.add(variantFile);
        }
      }
      if (assetFiles.has(variantFile)) {
        const ownUrl = `${OWN_CARDS_BASE}${variantFile}`;
        if (c.imageUrl !== ownUrl) {
          c.imageUrl = ownUrl;
          c.art = { mode: "IMAGE", url: ownUrl };
          if (c.edition === "EPIC") linkedEpicImages++;
          else linkedMythicImages++;
        }
      }
    }
  }

  // 4. Reordena e recalcula nicheRank (herdando da âncora)
  cards = sortAndRank(cards);

  // 5. Atualiza data/art/overrides.json com todos os assets locais (CHARACTER e ITEM)
  const weaponSlugs = new Set([
    "murasame-akame",
    "enma-one-piece",
    "wado-ichimonji",
    "shusui-one-piece",
    "yoru-one-piece",
    "samehada-naruto",
    "kusanagi-naruto",
    "kubikiribocho-naruto",
    "gunbai-uchiha",
    "zangetsu-bleach",
    "senbonzakura-bleach",
    "kyoka-suigetsu-bleach",
    "ryujin-jakka-bleach",
    "hogyoku-bleach",
    "ea-sword-of-rupture",
    "gae-bolg-fate",
    "kanshou-bakuya-fate",
    "rule-breaker-fate",
    "rhongomyniad-fate",
    "elucidator-dark-repulser",
    "lambent-light-sao",
    "night-sky-sword-sao",
    "blue-rose-sword-sao",
    "divine-axe-rhitta",
    "lostvayne-meliodas",
    "spirit-spear-chastiefol",
    "courechouse-ban",
    "nichirin-tanjiro",
    "tessaiga-inuyasha",
    "tenseiga-inuyasha",
    "playful-cloud-jjk",
    "inverted-spear-of-heaven",
    "split-soul-katana",
    "kamish-wrath-solo-leveling",
    "demon-king-daggers",
    "scissor-blade-kill-la-kill",
    "punisher-trigun",
    "dominator-psycho-pass",
    "3d-maneuver-gear-aot",
    "quinque-jason-tokyo-ghoul",
    "black-clover-grimoire",
    "demon-slayer-sword-asta",
    "staff-of-ainz-ooal-gown",
    "necronomicon-persona",
    "keyblade-kingdom-key",
    "rebellion-dmc",
    "ebony-ivory-dmc",
    "red-queen-dmc",
    "blades-of-chaos-gow",
    "draupnir-spear-gow",
    "blade-of-olympus-gow",
    "hidden-blade-ac",
    "energy-sword-halo",
    "gravity-hammer-halo",
    "bfg-9000-doom",
    "crucible-blade-doom",
    "rivers-of-blood-elden-ring",
    "moonveil-katana-elden-ring",
    "dark-moon-greatsword",
    "maliketh-black-blade",
    "mortal-blade-sekiro",
    "saw-cleaver-bloodborne",
    "holy-moonlight-sword",
    "monado-xenoblade",
    "aegis-sword-pyra",
    "soul-edge-soulcalibur",
    "soul-calibur-sword",
    "ashbringer-warcraft",
    "warglaives-of-azzinoth",
    "doomhammer-warcraft",
    "thunderfury-warcraft",
    "diamond-sword-minecraft",
    "portal-gun-aperture",
    "gravity-gun-half-life",
    "crowbar-gordon-freeman",
    "ray-gun-cod-zombies",
    "lancer-chainsaw-gears",
    "skyhook-bioshock",
    "elder-wand-harry-potter",
    "sword-of-gryffindor",
    "anduril-flame-of-the-west",
    "sting-bilbo-frodo",
    "glamdring-gandalf",
    "grayskull-power-sword",
    "sword-of-omens-thundercats",
    "darksaber-mandalorian",
    "darth-maul-double-lightsaber",
    "green-goblin-glider",
    "captain-america-shield",
    "stormbreaker-thor",
    "infinity-gauntlet-thanos",
    "web-shooters-spider-man",
    "eye-of-agamotto-strange",
    "ten-rings-shang-chi",
    "necro-sword-all-black",
    "lasso-of-truth-wonder-woman",
    "green-lantern-power-ring",
    "trident-of-neptune-aquaman",
    "batarang-batman",
    "kryptonite-spear",
    "katana-hatori-hanzo",
    "proton-pack-ghostbusters",
    "neuralyzer-mib",
    "hoverboard-bttf",
    "sonic-screwdriver-doctor-who",
    "one-ring-lotr",
    "lightsaber-skywalker",
    "mjolnir-thor",
    "excalibur",
    "dragon-slayer-berserk",
    "zanpakuto-ichigo",
    "death-note-item",
    "master-sword-zelda",
    "buster-sword-ff7",
    "keyblade-sora",
    "frostmourne-arthas",
    "leviathan-axe-kratos",
    "yamato-vergil",
    "masamune-sephiroth",
    "chaos-blades-kratos",
    "omniblade-mass-effect",
    "silver-sword-geralt",
    "nyoibo-dragon-ball",
    "spear-of-longinus",
    "gate-of-babylon",
    "cross-punisher-trigun",
    "judgment-chain-kurapika",
  ]);

  const overridesList: Array<{ slug: string; url: string; kind: OverrideKind; source: string }> = [];
  for (const c of cards) {
    if (c.imageUrl?.startsWith(OWN_CARDS_BASE)) {
      const isWeapon =
        weaponSlugs.has(c.slug) ||
        (c.seriesTitle?.includes("Armas") ?? false) ||
        c.gender === "OTHER";
      overridesList.push({
        slug: c.slug,
        url: c.imageUrl,
        kind: isWeapon ? "ITEM" : "CHARACTER",
        source: "docs/assets/cards",
      });
    }
  }
  await fs.writeFile(OVERRIDES_PATH, `${JSON.stringify(overridesList, null, 2)}\n`, "utf8");

  const meta = buildMeta(cards, new Date());
  await fs.writeFile(catalogPath, serializeCatalog(cards), "utf8");
  await fs.writeFile(metaPath, `${JSON.stringify(meta, null, 2)}\n`, "utf8");

  return {
    totalCards: cards.length,
    deduplicatedCards,
    renderedWeapons,
    linkedLocalAssets,
    linkedEpicImages,
    linkedMythicImages,
    propagatedNiches,
    enrichedAliases,
    hash: meta.hash,
  };
}

async function syncDatabaseEditions(): Promise<{ dbUpdatedImages: number; dbUpdatedDescs: number; dbUpdatedNiches: number }> {
  const dbUrl = process.env.DATABASE_URL;
  if (!dbUrl) return { dbUpdatedImages: 0, dbUpdatedDescs: 0, dbUpdatedNiches: 0 };

  const postgres = (await import("postgres")).default;
  const sql = postgres(dbUrl, { max: 1, onnotice: () => {} });
  try {
    await sql`
      UPDATE entity_images
      SET url = REPLACE(url, 'https://yo-apollon.github.io/kogu/', 'https://yo-apollon.github.io/Kogu-Anime/')
      WHERE url LIKE 'https://yo-apollon.github.io/kogu/%'
    `;

    // Propaga niche_id e prestige da âncora para edições EPIC e MYTHIC
    const nicheRes = await sql`
      UPDATE entities e
      SET niche_id = COALESCE(e.niche_id, p.niche_id),
          prestige = COALESCE(e.prestige, p.prestige)
      FROM entities p
      WHERE e.parent_id = p.id
        AND (e.niche_id IS NULL OR e.prestige IS NULL)
    `;

    const overridesRaw = JSON.parse(await fs.readFile(OVERRIDES_PATH, "utf8").catch(() => "[]")) as Array<{
      slug: string;
      url: string;
    }>;
    let dbUpdatedImages = 0;
    for (const o of overridesRaw) {
      const r = await sql`
        UPDATE entity_images ei
        SET url = ${o.url}, status = 'ACTIVE'
        FROM entities e
        WHERE ei.entity_id = e.id
          AND e.slug = ${o.slug}
          AND ei.is_primary = true
          AND ei.url <> ${o.url}
      `;
      dbUpdatedImages += r.count ?? 0;
    }

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

    return {
      dbUpdatedImages,
      dbUpdatedDescs: descRes.count ?? 0,
      dbUpdatedNiches: nicheRes.count ?? 0,
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
