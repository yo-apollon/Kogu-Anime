/**
 * Componentes interativos de Coleção e Panteão.
 * Namespace: "col" (COLLECTION_NAMESPACE).
 * Gerencia a navegação interativa de versões/edições e fotos de cartas do $im / $info.
 */
import { AttachmentBuilder, MessageFlags, type MessageComponentInteraction } from "discord.js";
import { renderCardInPool } from "../../canvas/index.js";
import { EDITION_LABEL } from "../../config/gacha.js";
import type { ComponentHandler } from "../../core/contracts.js";
import { t } from "../../i18n/index.js";
import { UserError } from "../../lib/errors.js";
import { childLogger } from "../../lib/logger.js";
import { formatNumber } from "../../ui/format.js";
import { DEFAULT_PACT_LIMIT, buildSummonEmbed } from "../../ui/summonEmbed.js";
import { getGuildBasics } from "../economy/extra.js";
import { ascendEntityEra, getEntityImages, getEntityInfo, resolveEditionForInfo } from "./service.js";
import {
  COLLECTION_NAMESPACE,
  buildInfoActionRows,
  buildInfoView,
  cardRenderInput,
} from "./views.js";

const log = childLogger("collection:components");

export const collectionComponent: ComponentHandler = {
  namespace: COLLECTION_NAMESPACE,

  async handle(interaction: MessageComponentInteraction, parts: string[]): Promise<void> {
    if (!interaction.isButton() || !interaction.guildId) return;

    const action = parts[0];
    if (action !== "im_ed" && action !== "im_img" && action !== "im_asc") return;

    let locale = "pt-BR";
    try {
      const basics = await getGuildBasics(interaction.guildId);
      locale = basics.locale;
    } catch {
      locale = "pt-BR";
    }

    if (action === "im_asc") {
      const pactId = Number(parts[1]);
      const requesterId = parts[3];
      if (!pactId || isNaN(pactId)) return;

      if (requesterId && interaction.user.id !== requesterId) {
        await interaction.reply({
          content: t("errors.not_owner", locale),
          flags: MessageFlags.Ephemeral,
        });
        return;
      }

      await interaction.deferUpdate();

      try {
        const res = await ascendEntityEra({
          guildId: interaction.guildId,
          userId: interaction.user.id,
          pactId,
        });

        const targetEntityId = res.newEntityId;
        const info = await getEntityInfo(interaction.guildId, targetEntityId);
        if (!info) return;

        const { editions } = await resolveEditionForInfo(interaction.guildId, interaction.user.id, targetEntityId, true);
        const images = await getEntityImages(targetEntityId);

        const ownerAvatarUrl = info.pact
          ? interaction.guild?.members?.cache?.get(info.pact.userId)?.displayAvatarURL()
          : undefined;

        const view = buildInfoView(info, { locale, ownerAvatarUrl });
        const { embed, attachmentName } = buildSummonEmbed(view, {
          locale,
          pactLimit: DEFAULT_PACT_LIMIT,
        });

        const currEdIdx = Math.max(0, editions.findIndex((e) => e.id === targetEntityId));
        const ownedPactId = info.pact && info.pact.userId === interaction.user.id ? info.pact.id : undefined;
        const rows = buildInfoActionRows({
          entityId: targetEntityId,
          editions,
          currentEditionIndex: currEdIdx,
          images,
          currentImageIndex: 0,
          userId: interaction.user.id,
          locale,
          ownedPactId,
        });

        const files: AttachmentBuilder[] = [];
        try {
          const art = await renderCardInPool(cardRenderInput(info, locale));
          files.push(new AttachmentBuilder(art, { name: attachmentName }));
        } catch (err) {
          log.warn({ err, entityId: targetEntityId }, "falha ao renderizar a carta após ascensão de Era");
          embed.setImage(null);
        }

        const successMsg = t("collection.ascend_success", locale, {
          entity: res.entityName,
          from: t(EDITION_LABEL[res.fromEdition], locale),
          to: t(EDITION_LABEL[res.toEdition], locale),
          cost: formatNumber(res.cost, locale),
          balance: formatNumber(res.newBalance, locale),
          baseAether: formatNumber(res.newBaseAether, locale),
        });

        await interaction.editReply({
          content: successMsg,
          embeds: [embed],
          components: rows,
          files,
          attachments: [],
        });
      } catch (err) {
        if (err instanceof UserError) {
          const params: Record<string, string | number> = {};
          if (err.params) {
            for (const [k, v] of Object.entries(err.params)) {
              params[k] = typeof v === "number" ? formatNumber(v, locale) : String(v);
            }
          }
          await interaction.followUp({
            content: t(err.key, locale, params),
            flags: MessageFlags.Ephemeral,
          });
          return;
        }
        log.error({ err, pactId }, "erro ao processar ascensão de Era no $im");
      }
      return;
    }

    const targetEntityId = Number(parts[1]);
    let imgIdx = Math.max(0, Number(parts[2]) || 0);
    const requesterId = parts[3];

    if (!targetEntityId || isNaN(targetEntityId)) return;

    await interaction.deferUpdate();

    try {
      const info = await getEntityInfo(interaction.guildId, targetEntityId);
      if (!info) return;

      const { editions } = await resolveEditionForInfo(interaction.guildId, interaction.user.id, targetEntityId, true);
      const images = await getEntityImages(targetEntityId);

      if (images.length > 0) {
        if (imgIdx >= images.length) imgIdx = 0;
        info.imageUrl = images[imgIdx]!.url;
      }

      const ownerAvatarUrl = info.pact
        ? interaction.guild?.members?.cache?.get(info.pact.userId)?.displayAvatarURL()
        : undefined;

      const view = buildInfoView(info, { locale, ownerAvatarUrl });
      const { embed, attachmentName } = buildSummonEmbed(view, {
        locale,
        pactLimit: DEFAULT_PACT_LIMIT,
      });

      const currEdIdx = Math.max(0, editions.findIndex((e) => e.id === targetEntityId));
      const viewerId = requesterId || interaction.user.id;
      const ownedPactId = info.pact && info.pact.userId === viewerId ? info.pact.id : undefined;
      const rows = buildInfoActionRows({
        entityId: targetEntityId,
        editions,
        currentEditionIndex: currEdIdx,
        images,
        currentImageIndex: imgIdx,
        userId: viewerId,
        locale,
        ownedPactId,
      });

      const files: AttachmentBuilder[] = [];
      try {
        const art = await renderCardInPool(cardRenderInput(info, locale));
        files.push(new AttachmentBuilder(art, { name: attachmentName }));
      } catch (err) {
        log.warn({ err, entityId: targetEntityId }, "falha ao renderizar a carta na navegação do $info");
        embed.setImage(null);
      }

      const content =
        editions.length > 1
          ? t("collection.info_editions", locale, {
              list: editions
                .map((e) => `${t(EDITION_LABEL[e.edition], locale)} (id:${e.id}${e.owned ? " ✅" : ""})`)
                .join(" · "),
            })
          : undefined;

      await interaction.editReply({
        content: content ?? null,
        embeds: [embed],
        components: rows,
        files,
        attachments: [],
      });
    } catch (err) {
      log.error({ err, targetEntityId, action }, "erro ao processar componente de coleção");
    }
  },
};
