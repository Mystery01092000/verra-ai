import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

const STORE_PATH = path.join(process.cwd(), '.users.json');

// Password hashing: scrypt with a per-user random salt, stored as "salt:hash"
// (hex). Legacy unsalted sha256 hashes (no ":") are no longer accepted; the
// seeder below drops legacy-format rows and regenerates the demo users.
const SCRYPT_KEY_LENGTH = 64;
const SALT_BYTES = 16;

export interface StoredUser {
  id: string;
  name: string;
  email: string;
  phone: string;
  age: number;
  passwordHash: string;
  createdAt: string;
}

function hashPassword(password: string): string {
  const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
  const hash = crypto.scryptSync(password, salt, SCRYPT_KEY_LENGTH).toString('hex');
  return `${salt}:${hash}`;
}

function isModernHash(passwordHash: string): boolean {
  return passwordHash.includes(':');
}

function loadUsers(): StoredUser[] {
  try {
    if (fs.existsSync(STORE_PATH)) {
      return JSON.parse(fs.readFileSync(STORE_PATH, 'utf8')) as StoredUser[];
    }
  } catch (_err) {
    // file unreadable or malformed — start fresh
  }
  return [];
}

function saveUsers(users: StoredUser[]): void {
  fs.writeFileSync(STORE_PATH, JSON.stringify(users, null, 2));
}

export function findUserByEmail(email: string): StoredUser | undefined {
  const users = loadUsers();
  return users.find((u) => u.email.toLowerCase() === email.toLowerCase());
}

export function validatePassword(user: StoredUser, password: string): boolean {
  const [salt, storedHash] = user.passwordHash.split(':');
  if (!salt || !storedHash) return false; // legacy/unknown format — reject
  try {
    const candidate = crypto.scryptSync(password, salt, SCRYPT_KEY_LENGTH);
    const expected = Buffer.from(storedHash, 'hex');
    return candidate.length === expected.length && crypto.timingSafeEqual(candidate, expected);
  } catch (err) {
    console.error('[Verra auth] Password verification failed:', err);
    return false;
  }
}

function buildUser(data: {
  name: string;
  email: string;
  phone: string;
  age: number;
  password: string;
}): StoredUser {
  return {
    id: crypto.randomUUID(),
    name: data.name,
    email: data.email,
    phone: data.phone,
    age: data.age,
    passwordHash: hashPassword(data.password),
    createdAt: new Date().toISOString(),
  };
}

export function registerUser(data: {
  name: string;
  email: string;
  phone: string;
  age: number;
  password: string;
}): StoredUser {
  const users = loadUsers();
  if (users.find((u) => u.email.toLowerCase() === data.email.toLowerCase())) {
    throw new Error('Email already registered');
  }
  const newUser = buildUser(data);
  saveUsers([...users, newUser]);
  return newUser;
}

// ── Seed demo users (dev flat file) ─────────────────────────────────
// Drops any legacy sha256-format rows and re-seeds missing demo users with
// the salted scrypt format.
const DEMO_USERS = [
  {
    name: 'Arjun Sharma',
    email: 'arjun@example.com',
    phone: '9876543210',
    age: 34,
    password: 'verra123',
  },
  { name: 'Demo User', email: 'demo@verra.ai', phone: '9999999999', age: 28, password: 'demo123' },
];

function seedDemoUsers(): void {
  const existing = loadUsers();
  const modern = existing.filter((u) => isModernHash(u.passwordHash));
  const missing = DEMO_USERS.filter(
    (demo) => !modern.some((u) => u.email.toLowerCase() === demo.email.toLowerCase()),
  );
  if (missing.length === 0 && modern.length === existing.length) return;
  try {
    saveUsers([...modern, ...missing.map(buildUser)]);
  } catch (err) {
    console.error('[Verra auth] Failed to seed demo users:', err);
  }
}

seedDemoUsers();
