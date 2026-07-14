#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";

const [inputArg, outputArg] = process.argv.slice(2);
if (!inputArg || !outputArg) {
  console.error("Usage: node scripts/fix-pptx-font-mapping.mjs <input.pptx> <output.pptx>");
  process.exit(2);
}

const input = path.resolve(inputArg);
const output = path.resolve(outputArg);
if (!fs.existsSync(input)) {
  console.error(`Missing PPTX file: ${input}`);
  process.exit(2);
}
if (input === output) {
  console.error("Input and output must be different paths.");
  process.exit(2);
}

const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "huawei-pptx-fonts-"));
const replaceTypeface = (tag, family) => {
  if (/\btypeface="[^"]*"/.test(tag)) {
    return tag.replace(/\btypeface="[^"]*"/, `typeface="${family}"`);
  }
  return tag.replace(/\s*\/>$/, ` typeface="${family}" />`);
};

const walk = (dir) => {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const target = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...walk(target));
    else files.push(target);
  }
  return files;
};

try {
  execFileSync("unzip", ["-oq", input, "-d", tempDir]);
  for (const filename of walk(tempDir).filter((file) => file.endsWith(".xml"))) {
    let xml = fs.readFileSync(filename, "utf8");
    xml = xml.replace(/<a:latin\b[^>]*\/>/g, (tag) => replaceTypeface(tag, "Arial"));
    xml = xml.replace(/<a:ea\b[^>]*\/>/g, (tag) => replaceTypeface(tag, "Microsoft YaHei"));
    xml = xml.replace(/<(a:(?:rPr|defRPr|endParaRPr))\b([^>]*)>([\s\S]*?)<\/\1>/g, (block, name, attrs, body) => {
      let nextBody = body;
      if (!/<a:latin\b/.test(nextBody)) nextBody += '<a:latin typeface="Arial" />';
      if (!/<a:ea\b/.test(nextBody)) nextBody += '<a:ea typeface="Microsoft YaHei" />';
      return `<${name}${attrs}>${nextBody}</${name}>`;
    });
    fs.writeFileSync(filename, xml);
  }
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.rmSync(output, { force: true });
  execFileSync("zip", ["-qr", output, "."], { cwd: tempDir });
  console.log(`Wrote ${output}`);
} finally {
  fs.rmSync(tempDir, { recursive: true, force: true });
}
