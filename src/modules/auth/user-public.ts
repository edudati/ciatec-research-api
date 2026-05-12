import type { UserRole } from '@prisma/client';

/** JWT-facing user object (register/login/me and users API core). Never include secrets. */
export type PublicUser = {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  createdAt: Date;
  /** Derived from `AuthUser.emailVerifiedAt` — TODO: set only after real email verification. */
  emailVerified: boolean;
  isFirstAccess: boolean;
  /** TODO: when true, login should require TOTP after password (not enforced yet). */
  totpEnabled: boolean;
};

export function toPublicUser(input: {
  id: string;
  name: string;
  role: UserRole;
  createdAt: Date;
  isFirstAccess: boolean;
  authUser: { email: string; emailVerifiedAt: Date | null; totpEnabled: boolean } | null;
}): PublicUser {
  if (!input.authUser) {
    throw new Error('toPublicUser: missing authUser');
  }
  return {
    id: input.id,
    email: input.authUser.email,
    name: input.name,
    role: input.role,
    createdAt: input.createdAt,
    emailVerified: input.authUser.emailVerifiedAt !== null,
    isFirstAccess: input.isFirstAccess,
    totpEnabled: input.authUser.totpEnabled,
  };
}
