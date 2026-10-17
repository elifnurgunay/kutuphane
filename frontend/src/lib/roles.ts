import type { UserRole } from "../api/auth";

export const STAFF_ROLES: UserRole[] = ["admin", "librarian"];

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Yönetici",
  librarian: "Görevli",
  member: "Üye",
};

export function homePathFor(role: UserRole): string {
  return STAFF_ROLES.includes(role) ? "/panel" : "/hesabim";
}
