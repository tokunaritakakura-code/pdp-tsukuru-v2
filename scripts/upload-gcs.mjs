#!/usr/bin/env node
// upload-gcs.mjs <stagedTargetsJsonFile> <dir>
// pdp-tsukuru 用: website-copy の同じ名前の道具を写し、画像（img/）も上げられるように型を拡張子から決める（2026-10-22）
// Shopify MCP の stagedUploadsCreate が返す stagedTargets 配列（JSON）を受け取り、
// theme/ 内の各ファイルを署名付きGCSへPOSTする。→ themeFilesUpsert 用に resourceUrl を出力。
// これで手作業の巨大curlが不要になる。stagedUploadsCreate のファイル名順＝theme内ファイル名で対応。
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';

const targetsFile = process.argv[2];
const themeDir = process.argv[3];
// 終了コード: 0 全部 201 ／ 1 201 以外・ファイルが無い・curl の失敗が1件でもある ／ 2 引数が足りない・targets が読めない
if (!targetsFile || !themeDir) { console.error('usage: upload-gcs.mjs <stagedTargetsJsonFile> <themeDir>'); process.exit(2); }

let targets;
try { targets = JSON.parse(fs.readFileSync(targetsFile, 'utf8')); } catch (e) { console.error('targets が読めない: ' + e.message); process.exit(2); }
// data.stagedUploadsCreate.stagedTargets 形式でも stagedTargets 配列そのままでも受ける
if (targets.data) targets = targets.data.stagedUploadsCreate.stagedTargets;
if (targets.stagedTargets) targets = targets.stagedTargets;
if (!Array.isArray(targets)) { console.error('targets が stagedTargets の配列でない'); process.exit(2); }

const 型 = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif', '.mp4': 'video/mp4', '.svg': 'image/svg+xml' };
// 1件ずつ結果を出して最後まで続ける。201 以外・ファイルが無い・curl の失敗が1件でもあれば終了コード 1（2026-11-14）
const out = [];
let 落ち = 0;
for (const t of targets) {
  const key = (t.parameters.find(p => p.name === 'key') || {}).value || '';
  const filename = key.split('/').pop();
  const local = path.join(themeDir, filename);
  if (!filename || !fs.existsSync(local)) { out.push({ filename, code: 'NO_LOCAL_FILE' }); 落ち++; console.error(`× ${filename || '（key が無い）'}: ファイルが無い（${local}）`); continue; }
  const args = ['-s', '-o', '/dev/null', '-w', '%{http_code}', t.url];
  for (const p of t.parameters) args.push('-F', `${p.name}=${p.value}`); // policyフィールド群
  args.push('-F', `file=@${local};type=${型[path.extname(local).toLowerCase()] || 'text/plain'}`);                     // fileは必ず最後
  let code;
  try { code = execFileSync('curl', args, { encoding: 'utf8' }).trim(); }
  catch (e) { code = 'CURL_FAILED'; out.push({ filename, code, error: String(e.message).slice(0, 200) }); 落ち++; console.error(`× ${filename}: curl が失敗した（${String(e.message).slice(0, 120)}）`); continue; }
  out.push({ filename, code, resourceUrl: t.resourceUrl });
  if (code !== '201') { 落ち++; console.error(`× ${filename}: ${code}（201 でない）`); }
  else console.error(`○ ${filename}: 201`);
}
console.log(JSON.stringify(out, null, 1));
if (落ち) { console.error(`落ちた ${落ち}件（${targets.length}件のうち）`); process.exit(1); }
console.error(`通った（${targets.length}件とも 201）`);
