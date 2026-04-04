import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['cjs'],
  dts: false,
  sourcemap: true,
  clean: true,
  minify: false,
  external: ['@openclaw/api', 'api'], // External modules that are provided by OpenClaw runtime
});