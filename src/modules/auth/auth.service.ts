import { createHash } from 'node:crypto';

import type { PrismaClient, UserRole } from '@prisma/client';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';

import { env } from '../../config/env.js';
import { ConflictError } from '../../shared/errors/conflict-error.js';
import { NotFoundError } from '../../shared/errors/not-found-error.js';
import { UnauthorizedError } from '../../shared/errors/unauthorized-error.js';

const BCRYPT_ROUNDS = 12;

export type AccessPayload = { sub: string; role: UserRole };

export type AuthServiceDeps = {
  prisma: PrismaClient;
  signAccessToken: (payload: AccessPayload) => string;
};

function hashRefreshToken(rawToken: string): string {
  return createHash('sha256').update(rawToken).digest('hex');
}

function signRefreshToken(payload: AccessPayload): string {
  const options: jwt.SignOptions = {
    expiresIn: env.JWT_REFRESH_EXPIRES_IN as jwt.SignOptions['expiresIn'],
    issuer: env.JWT_ISSUER,
    audience: env.JWT_AUDIENCE,
  };

  return jwt.sign({ sub: payload.sub, role: payload.role }, env.JWT_REFRESH_SECRET, options);
}

function verifyRefreshToken(rawToken: string): AccessPayload {
  try {
    const decoded = jwt.verify(rawToken, env.JWT_REFRESH_SECRET, {
      issuer: env.JWT_ISSUER,
      audience: env.JWT_AUDIENCE,
    });

    if (typeof decoded !== 'object' || decoded === null) {
      throw new UnauthorizedError('Invalid refresh token');
    }

    const record = decoded as jwt.JwtPayload & { role?: unknown; sub?: unknown };
    if (typeof record.sub !== 'string' || typeof record.role !== 'string') {
      throw new UnauthorizedError('Invalid refresh token');
    }

    return { sub: record.sub, role: record.role as UserRole };
  } catch (error) {
    if (error instanceof UnauthorizedError) {
      throw error;
    }
    throw new UnauthorizedError('Invalid refresh token');
  }
}

function refreshExpiresAt(rawToken: string): Date {
  const decoded = jwt.decode(rawToken);
  if (typeof decoded !== 'object' || decoded === null || decoded.exp === undefined) {
    throw new UnauthorizedError('Invalid refresh token');
  }
  return new Date(decoded.exp * 1000);
}

export function createAuthService({ prisma, signAccessToken }: AuthServiceDeps) {
  async function persistRefreshToken(authUserId: string, rawRefreshToken: string): Promise<void> {
    await prisma.refreshToken.create({
      data: {
        authUserId,
        token: hashRefreshToken(rawRefreshToken),
        expiresAt: refreshExpiresAt(rawRefreshToken),
      },
    });
  }

  return {
    async register(input: { email: string; password: string; name: string }) {
      const existing = await prisma.authUser.findUnique({ where: { email: input.email } });
      if (existing) {
        throw new ConflictError('Email already in use');
      }

      const passwordHash = await bcrypt.hash(input.password, BCRYPT_ROUNDS);
      const { user, authUser } = await prisma.$transaction(async (tx) => {
        const user = await tx.user.create({
          data: {
            name: input.name,
            role: 'PLAYER',
          },
        });

        const authUser = await tx.authUser.create({
          data: {
            email: input.email,
            passwordHash,
            userId: user.id,
          },
        });

        return { user, authUser };
      });

      const payload: AccessPayload = { sub: user.id, role: user.role };
      const accessToken = signAccessToken(payload);
      const refreshToken = signRefreshToken(payload);
      await persistRefreshToken(authUser.id, refreshToken);

      return {
        user: { id: user.id, email: authUser.email, name: user.name, role: user.role },
        accessToken,
        refreshToken,
      };
    },

    async login(input: { email: string; password: string }) {
      const authUser = await prisma.authUser.findUnique({
        where: { email: input.email },
        include: { user: true },
      });
      if (!authUser) {
        throw new UnauthorizedError('Invalid credentials');
      }

      const valid = await bcrypt.compare(input.password, authUser.passwordHash);
      if (!valid) {
        throw new UnauthorizedError('Invalid credentials');
      }

      const user = authUser.user;
      const payload: AccessPayload = { sub: user.id, role: user.role };
      const accessToken = signAccessToken(payload);
      const refreshToken = signRefreshToken(payload);
      await persistRefreshToken(authUser.id, refreshToken);

      return {
        user: { id: user.id, email: authUser.email, name: user.name, role: user.role },
        accessToken,
        refreshToken,
      };
    },

    async refresh(input: { refreshToken: string }) {
      const claims = verifyRefreshToken(input.refreshToken);
      const tokenHash = hashRefreshToken(input.refreshToken);

      const record = await prisma.refreshToken.findFirst({
        where: {
          token: tokenHash,
          authUser: { userId: claims.sub },
          revokedAt: null,
          expiresAt: { gt: new Date() },
        },
        include: {
          authUser: {
            include: {
              user: true,
            },
          },
        },
      });

      if (!record) {
        throw new UnauthorizedError('Invalid refresh token');
      }

      let accessToken = '';
      let refreshToken = '';

      await prisma.$transaction(async (tx) => {
        await tx.refreshToken.update({
          where: { id: record.id },
          data: { revokedAt: new Date() },
        });

        const user = record.authUser.user;

        const payload: AccessPayload = { sub: user.id, role: user.role };
        accessToken = signAccessToken(payload);
        refreshToken = signRefreshToken(payload);

        await tx.refreshToken.create({
          data: {
            authUserId: record.authUser.id,
            token: hashRefreshToken(refreshToken),
            expiresAt: refreshExpiresAt(refreshToken),
          },
        });
      });

      return { accessToken, refreshToken };
    },

    async logout(userId: string, refreshToken?: string) {
      const authUser = await prisma.authUser.findUnique({ where: { userId } });
      if (!authUser) {
        return;
      }

      if (refreshToken) {
        const tokenHash = hashRefreshToken(refreshToken);
        await prisma.refreshToken.updateMany({
          where: { authUserId: authUser.id, token: tokenHash, revokedAt: null },
          data: { revokedAt: new Date() },
        });
        return;
      }

      await prisma.refreshToken.updateMany({
        where: { authUserId: authUser.id, revokedAt: null },
        data: { revokedAt: new Date() },
      });
    },

    async me(userId: string) {
      const user = await prisma.user.findUnique({
        where: { id: userId },
        include: { authUser: true },
      });
      if (!user) {
        throw new NotFoundError('User not found');
      }
      if (!user.authUser) {
        throw new NotFoundError('Auth user not found');
      }

      return {
        id: user.id,
        email: user.authUser.email,
        name: user.name,
        role: user.role,
        createdAt: user.createdAt,
      };
    },
  };
}

export type AuthService = ReturnType<typeof createAuthService>;
