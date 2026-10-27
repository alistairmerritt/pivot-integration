// Bundles src/ into the single ES module the integration serves.
//   npm run build            -> ../custom_components/pivot/frontend/pivot-cards.js
//   npm run build -- --dev   -> also an unminified IIFE copy in dist/ for local testing
import { build } from 'esbuild';
import fs from 'node:fs';

const manifest = JSON.parse(fs.readFileSync('../custom_components/pivot/manifest.json', 'utf8'));
const common = {
  entryPoints: ['src/index.ts'],
  bundle: true,
  target: 'es2021',
  legalComments: 'none',
  define: { __PIVOT_VERSION__: JSON.stringify(manifest.version) },
  banner: { js: `/*! Pivot dashboard cards v${manifest.version}. Built from frontend/ in pivot-integration; edit the source, not this file. Includes Lit (BSD-3-Clause) and Material Design Icons (Apache-2.0). */` },
  logLevel: 'warning',
};

await build({ ...common, format: 'esm', minify: true, outfile: '../custom_components/pivot/frontend/pivot-cards.js' });
if (process.argv.includes('--dev')) {
  await build({ ...common, format: 'iife', minify: false, outfile: 'dist/pivot-cards.iife.js' });
}
const size = fs.statSync('../custom_components/pivot/frontend/pivot-cards.js').size;
console.log(`pivot-cards.js ${(size / 1024).toFixed(1)} KB (v${manifest.version})`);
