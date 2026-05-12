import type { Prisma, PrismaClient, UserRole } from '@prisma/client';

import { ConflictError } from '../../shared/errors/conflict-error.js';
import { NotFoundError } from '../../shared/errors/not-found-error.js';
import { hashPassword } from '../auth/password-hash.js';
import { toPublicUser } from '../auth/user-public.js';
import type { CreateUserBody, ListUsersQuery, PatchUserBody } from './users.schema.js';

type UsersServiceDeps = {
  prisma: PrismaClient;
};

const authUserPublicSelect = {
  email: true,
  emailVerifiedAt: true,
  totpEnabled: true,
} as const;

function assertAuth<T extends { authUser: unknown }>(row: T): asserts row is T & {
  authUser: { email: string; emailVerifiedAt: Date | null; totpEnabled: boolean };
} {
  if (!row.authUser) {
    throw new NotFoundError('User not found');
  }
}

function buildOrderBy(query: ListUsersQuery): Prisma.UserOrderByWithRelationInput {
  const dir = query.order;
  switch (query.sort) {
    case 'name':
      return { name: dir };
    case 'email':
      return { authUser: { email: dir } };
    case 'updatedAt':
      return { updatedAt: dir };
    default:
      return { createdAt: dir };
  }
}

export function createUsersService({ prisma }: UsersServiceDeps) {
  return {
    async listUsers(query: ListUsersQuery) {
      const where: Prisma.UserWhereInput = {
        deletedAt: null,
        authUser: { isNot: null },
        ...(query.role ? { role: query.role } : {}),
        ...(query.q
          ? {
              OR: [
                { name: { contains: query.q, mode: 'insensitive' } },
                { authUser: { email: { contains: query.q, mode: 'insensitive' } } },
              ],
            }
          : {}),
      };

      const [total, rows] = await prisma.$transaction([
        prisma.user.count({ where }),
        prisma.user.findMany({
          where,
          orderBy: buildOrderBy(query),
          skip: (query.page - 1) * query.pageSize,
          take: query.pageSize,
          include: { authUser: { select: authUserPublicSelect } },
        }),
      ]);

      const users = rows.map((u) => {
        assertAuth(u);
        return {
          ...toPublicUser({
            id: u.id,
            name: u.name,
            role: u.role,
            createdAt: u.createdAt,
            isFirstAccess: u.isFirstAccess,
            authUser: u.authUser,
          }),
          updatedAt: u.updatedAt,
        };
      });

      return { users, total, page: query.page, pageSize: query.pageSize };
    },

    async getUserById(id: string) {
      const user = await prisma.user.findUnique({
        where: { id },
        include: { authUser: { select: authUserPublicSelect } },
      });
      if (!user) {
        throw new NotFoundError('User not found');
      }
      assertAuth(user);
      return {
        ...toPublicUser({
          id: user.id,
          name: user.name,
          role: user.role,
          createdAt: user.createdAt,
          isFirstAccess: user.isFirstAccess,
          authUser: user.authUser,
        }),
        updatedAt: user.updatedAt,
        deletedAt: user.deletedAt,
      };
    },

    async createUser(input: CreateUserBody) {
      const existing = await prisma.authUser.findUnique({ where: { email: input.email } });
      if (existing) {
        throw new ConflictError('Email already in use');
      }

      const passwordHash = await hashPassword(input.password);
      // TODO(email-verification): set emailVerifiedAt only after confirmation when you add that flow.
      const verifiedAt = new Date();
      const user = await prisma.$transaction(async (tx) => {
        const u = await tx.user.create({
          data: {
            name: input.name,
            role: input.role,
          },
        });
        await tx.authUser.create({
          data: {
            email: input.email,
            passwordHash,
            userId: u.id,
            emailVerifiedAt: verifiedAt,
          },
        });
        return tx.user.findUniqueOrThrow({
          where: { id: u.id },
          include: { authUser: { select: authUserPublicSelect } },
        });
      });

      assertAuth(user);
      return {
        ...toPublicUser({
          id: user.id,
          name: user.name,
          role: user.role,
          createdAt: user.createdAt,
          isFirstAccess: user.isFirstAccess,
          authUser: user.authUser,
        }),
        updatedAt: user.updatedAt,
        deletedAt: user.deletedAt,
      };
    },

    async updateUser(id: string, input: PatchUserBody) {
      const user = await prisma.user.findUnique({
        where: { id },
        include: { authUser: { select: authUserPublicSelect } },
      });
      if (!user || !user.authUser) {
        throw new NotFoundError('User not found');
      }
      if (user.deletedAt) {
        throw new NotFoundError('User not found');
      }

      const currentEmail = user.authUser.email;
      if (input.email && input.email !== currentEmail) {
        const taken = await prisma.authUser.findUnique({ where: { email: input.email } });
        if (taken) {
          throw new ConflictError('Email already in use');
        }
      }

      let passwordHash: string | undefined;
      if (input.password) {
        passwordHash = await hashPassword(input.password);
      }

      const updated = await prisma.$transaction(async (tx) => {
        await tx.user.update({
          where: { id },
          data: {
            ...(input.name !== undefined ? { name: input.name } : {}),
            ...(input.role !== undefined ? { role: input.role } : {}),
            ...(input.isFirstAccess !== undefined ? { isFirstAccess: input.isFirstAccess } : {}),
          },
        });
        if (input.email !== undefined || passwordHash !== undefined) {
          const emailChanged = input.email !== undefined && input.email !== currentEmail;
          await tx.authUser.update({
            where: { userId: id },
            data: {
              ...(input.email !== undefined ? { email: input.email } : {}),
              ...(passwordHash !== undefined ? { passwordHash } : {}),
              // TODO(email-verification): when implementing verification, require re-verify after email change (null until confirmed).
              ...(emailChanged ? { emailVerifiedAt: null } : {}),
            },
          });
        }
        return tx.user.findUniqueOrThrow({
          where: { id },
          include: { authUser: { select: authUserPublicSelect } },
        });
      });

      assertAuth(updated);
      return {
        ...toPublicUser({
          id: updated.id,
          name: updated.name,
          role: updated.role,
          createdAt: updated.createdAt,
          isFirstAccess: updated.isFirstAccess,
          authUser: updated.authUser,
        }),
        updatedAt: updated.updatedAt,
        deletedAt: updated.deletedAt,
      };
    },

    async softDeleteUser(id: string) {
      const user = await prisma.user.findUnique({ where: { id }, select: { id: true, deletedAt: true } });
      if (!user) {
        throw new NotFoundError('User not found');
      }
      if (!user.deletedAt) {
        await prisma.user.update({
          where: { id },
          data: { deletedAt: new Date() },
        });
      }
    },
  };
}

export type UsersService = ReturnType<typeof createUsersService>;
