export type ApiHealth = {
  status: string;
  service: string;
};

export type UserRole = "artist" | "performer" | "moderator" | "admin";

export const API_VERSION = "v1" as const;
