// Client-side PII guard. Mallard is privacy-first: the unit id must be pseudonymous
// and event/attribute properties must not carry PII. Best-effort on the client; the
// server enforces the workspace allow-list authoritatively (see docs/01-product-vision.md).
// Mirrors sdks/python/mallard_sdk/privacy.py.

const PII_KEYS = new Set([
  "email",
  "e_mail",
  "mail",
  "phone",
  "phone_number",
  "ssn",
  "password",
  "name",
  "first_name",
  "last_name",
  "full_name",
  "address",
  "ip",
  "ip_address",
  "credit_card",
  "card_number",
]);

const EMAIL_RE = /[^@\s]+@[^@\s]+\.[^@\s]+/;

export class PIIError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PIIError";
  }
}

export function assertPseudonymousUnit(unitId: string): void {
  if (!unitId) {
    throw new PIIError("unitId must be a non-empty pseudonymous identifier");
  }
  if (EMAIL_RE.test(unitId)) {
    throw new PIIError("unitId looks like an email; use a pseudonymous id");
  }
}

export function assertNoPii(properties: Record<string, unknown>): void {
  for (const [key, value] of Object.entries(properties)) {
    if (PII_KEYS.has(key.toLowerCase())) {
      throw new PIIError(`property '${key}' looks like PII and must not be sent`);
    }
    if (typeof value === "string" && EMAIL_RE.test(value)) {
      throw new PIIError(`property '${key}' value looks like an email`);
    }
  }
}
