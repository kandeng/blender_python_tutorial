/**
 * OpenClaw Worker SDK - Authentication
 * 
 * Ed25519 key handling and device auth payload construction.
 */

import * as crypto from "crypto";
import * as fs from "fs/promises";
import * as path from "path";
import { DeviceIdentity, DeviceAuth } from "./types.js";

/**
 * Load device identity from disk
 */
export async function loadDeviceIdentity(identityPath: string): Promise<DeviceIdentity | null> {
  try {
    const content = await fs.readFile(identityPath, "utf-8");
    return JSON.parse(content);
  } catch {
    return null;
  }
}

/**
 * Load device auth from disk
 */
export async function loadDeviceAuth(authPath: string): Promise<DeviceAuth | null> {
  try {
    const content = await fs.readFile(authPath, "utf-8");
    return JSON.parse(content);
  } catch {
    return null;
  }
}

/**
 * Sign a message with Ed25519 private key
 */
export function signWithPrivateKey(privateKeyPem: string, message: string): string {
  const privateKey = crypto.createPrivateKey(privateKeyPem);
  const signature = crypto.sign(null, Buffer.from(message, "utf8"), privateKey);
  return signature.toString("base64url");
}

/**
 * Extract raw 32-byte Ed25519 public key from PEM
 */
export function getPublicKeyRaw(publicKeyPem: string): string {
  const publicKey = crypto.createPublicKey({
    key: publicKeyPem,
    format: "pem",
    type: "spki"
  });
  
  // Export as DER and extract last 32 bytes (raw Ed25519 key)
  const der = publicKey.export({ format: "der", type: "spki" });
  const rawKey = der.slice(-32);
  return rawKey.toString("base64url");
}

/**
 * Build device auth payload v3 for signing
 * Format: v3|deviceId|clientId|clientMode|role|scopes|signedAtMs|token|nonce|platform|deviceFamily
 */
export function buildDeviceAuthPayloadV3(params: {
  deviceId: string;
  clientId: string;
  clientMode: string;
  role: string;
  scopes: string[];
  signedAtMs: number;
  token: string;
  nonce: string;
  platform: string;
  deviceFamily?: string;
}): string {
  const scopes = params.scopes.join(",");
  const token = params.token ?? "";
  const platform = params.platform || "";
  const deviceFamily = params.deviceFamily || "";
  return [
    "v3",
    params.deviceId,
    params.clientId,
    params.clientMode,
    params.role,
    scopes,
    String(params.signedAtMs),
    token,
    params.nonce,
    platform,
    deviceFamily
  ].join("|");
}

/**
 * Get default identity path
 */
export function getDefaultIdentityPath(): string {
  return path.join(process.env.HOME || "/root", ".openclaw/identity/device.json");
}

/**
 * Get default auth path
 */
export function getDefaultAuthPath(): string {
  return path.join(process.env.HOME || "/root", ".openclaw/identity/device-auth.json");
}
