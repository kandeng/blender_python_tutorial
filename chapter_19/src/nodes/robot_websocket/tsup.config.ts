import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['websocket-server.ts'],
  format: ['cjs', 'esm'], // Output both CommonJS and ES Module formats
  target: 'node18', // Target Node.js 18
  platform: 'node',
  dts: true, // Generate declaration files
  sourcemap: true,
  clean: true,
  minify: false,
  splitting: false,
  outDir: './dist',
  outExtension: ({ format }) => {
    return {
      js: format === 'esm' ? '.mjs' : '.js',
    };
  },
});
