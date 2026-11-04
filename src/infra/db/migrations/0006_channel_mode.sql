ALTER TABLE "guilds" ADD COLUMN "channel_mode" text DEFAULT 'ALL' NOT NULL;--> statement-breakpoint
ALTER TABLE "guilds" ADD COLUMN "allowed_channels" jsonb DEFAULT '[]'::jsonb NOT NULL;--> statement-breakpoint
ALTER TABLE "guilds" ADD CONSTRAINT "guilds_channel_mode_ck" CHECK ("channel_mode" IN ('ALL', 'SINGLE', 'SELECTED'));
