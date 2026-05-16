const mods = [
  '/usr/lib/node_modules/openclaw/dist/fetch-guard-DFNmfAZx.js',
  '/usr/lib/node_modules/openclaw/dist/undici-runtime-BdHHFzbs.js',
  '/usr/lib/node_modules/openclaw/dist/proxy-env-BaS80pvI.js'
];
for (const m of mods) {
  const mod = await import(m);
  console.log('\n##', m);
  console.log(Object.keys(mod));
  for (const [k, v] of Object.entries(mod)) console.log(k, typeof v, v?.name || '');
}
