#!/usr/bin/env node
/**
 * progress-relay.js — VSCode terminal live log watcher
 *
 * Watches autoresearch log files and the progress log, streams
 * new lines to stdout with colored labels. Run in VSCode terminal.
 *
 * Usage:
 *   node scripts/progress-relay.js          # live tail
 *   node scripts/progress-relay.js --once   # snapshot + exit
 */
'use strict';

const fs   = require('fs');
const path = require('path');

const LOG_DIR  = 'C:/AI/autoresearch/auto_R&H_logs';
const PROG_LOG = 'C:/AI/autoresearch/output/progress.log';

const WATCHED = [
  { file: PROG_LOG,                                   label: 'PROG   ', color: '\x1b[96m' },
  { file: path.join(LOG_DIR, 'openharness.log'),      label: 'HARNESS', color: '\x1b[36m' },
  { file: path.join(LOG_DIR, 'mamga.log'),            label: 'MAMGA  ', color: '\x1b[35m' },
  { file: path.join(LOG_DIR, 'harness_frontend.log'), label: 'FRONT  ', color: '\x1b[33m' },
];

const R = '\x1b[0m', B = '\x1b[1m', DIM = '\x1b[2m', RED = '\x1b[31m', YLW = '\x1b[33m';

const NOISE = ['GET /health HTTP/1.1" 200', 'GET /favicon', '127.0.0.1 - - ['];

function ts()            { return new Date().toISOString().slice(11, 19); }
function isNoise(l)      { return NOISE.some(n => l.includes(n)); }
function levelCol(l)     { const u = l.toUpperCase(); return u.includes('ERROR')||u.includes('CRITICAL') ? RED : u.includes('WARN') ? YLW : ''; }
function print(lbl, col, l) {
  const lc = levelCol(l);
  process.stdout.write(`${DIM}${ts()}${R} ${B}${col}[${lbl}]${R} ${lc}${l}${lc?R:''}\n`);
}
function tail(file, n)   { try { return fs.readFileSync(file,'utf8').split('\n').filter(Boolean).slice(-n); } catch(_){return[];} }

// Print tail snapshot
for (const w of WATCHED)
  for (const l of tail(w.file, 25))
    if (!isNoise(l)) print(w.label, w.color, l);

if (process.argv.includes('--once')) process.exit(0);

process.stdout.write(`\n${B}--- live (Ctrl+C to stop) ---${R}\n\n`);

// Watch each file for appends
for (const w of WATCHED) {
  if (!fs.existsSync(w.file)) continue;
  let size = fs.statSync(w.file).size;
  fs.watch(w.file, { persistent: true }, () => {
    try {
      const ns = fs.statSync(w.file).size;
      if (ns <= size) return;
      const fd = fs.openSync(w.file, 'r');
      const buf = Buffer.alloc(ns - size);
      fs.readSync(fd, buf, 0, buf.length, size);
      fs.closeSync(fd);
      size = ns;
      for (const raw of buf.toString('utf8').split('\n')) {
        const l = raw.trimEnd();
        if (l && !isNoise(l)) print(w.label, w.color, l);
      }
    } catch(_) {}
  });
}
