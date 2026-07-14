#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const templateMode = args.includes("--template");
const filename = args.find((arg) => !arg.startsWith("--"));

if (!filename) {
  console.error("Usage: node validate-html-deck.mjs <deck.html> [--template]");
  process.exit(2);
}

const target = path.resolve(filename);
if (!fs.existsSync(target)) {
  console.error(`Missing HTML file: ${target}`);
  process.exit(2);
}

const html = fs.readFileSync(target, "utf8");
const errors = [];
const requireText = (needle, message) => {
  if (!html.includes(needle)) errors.push(message);
};

requireText('<html lang="zh-CN">', "Document language must be zh-CN.");
requireText('name="viewport"', "Viewport metadata is missing.");
requireText("--huawei-red: #c7000b", "Default Huawei red token must be #C7000B.");
requireText('font-family: Arial, "Microsoft YaHei", "微软雅黑", sans-serif', "Mixed-script font stack must put Arial before Microsoft YaHei.");
requireText("fitDeck", "Responsive deck fitting is missing.");
requireText("@media print", "Print/PDF stylesheet is missing.");
requireText("data-page-number", "Automatic page-number placeholders are missing.");

const slides = html.match(/<section\b[^>]*class="[^"]*\bslide\b[^"]*"/g) || [];
if (!slides.length) errors.push("No slides found.");

const pageMarkers = html.match(/<span\b[^>]*data-page-number/g) || [];
if (pageMarkers.length !== slides.length) {
  errors.push(`Every slide must have one automatic page marker (${pageMarkers.length}/${slides.length}).`);
}

const contentSlideCount = Math.max(0, slides.length - 1);
const titles = html.match(/<h2\b[^>]*class="[^"]*\bslide-title\b[^"]*"/g) || [];
if (titles.length < contentSlideCount) {
  errors.push(`Every content slide needs a takeaway title (${titles.length}/${contentSlideCount}).`);
}

for (const forbidden of [
  "Huawei-style presentation",
  "华为风格模板",
  ">HUAWEI<",
  "Huawei Confidential",
  "Huawei Proprietary",
]) {
  if (html.includes(forbidden)) errors.push(`Producer-facing or unauthorized brand text remains: ${forbidden}`);
}

if (/style="[^"]*(?:#c7000b|rgb\(199\s*,\s*0\s*,\s*11\))/i.test(html)) {
  errors.push("Inline hard-coded Huawei red found; use a class and --huawei-red.");
}

if (/class="[^"]*\btop-rule\b/.test(html) || /\.top-rule\s*\{/.test(html)) {
  errors.push("Persistent top red rule found; it is not part of the default visual system.");
}

if (!templateMode && /\[[\u4e00-\u9fff][^\]\n]{0,80}\]/.test(html)) {
  errors.push("Unresolved bracketed placeholder found.");
}

const bodySize = Number(html.match(/--body:\s*(\d+(?:\.\d+)?)px/i)?.[1]);
const labelSize = Number(html.match(/--label:\s*(\d+(?:\.\d+)?)px/i)?.[1]);
if (!Number.isFinite(bodySize) || bodySize < 24) errors.push("HTML body token must be at least 24px.");
if (!Number.isFinite(labelSize) || labelSize < 21) errors.push("HTML label token must be at least 21px.");

const allowedSmallSelectors = [".footer", ".page-no", ".controls", ".source-note"];
for (const match of html.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
  const selector = match[1].trim();
  const declaration = match[2];
  for (const sizeMatch of declaration.matchAll(/font-size:\s*(\d+(?:\.\d+)?)px/gi)) {
    const size = Number(sizeMatch[1]);
    if (size < 21 && !allowedSmallSelectors.some((allowed) => selector.includes(allowed))) {
      errors.push(`Text below 21px outside an allowed source/control selector: ${selector} (${size}px).`);
    }
  }
}

if (!/pageNo\.textContent\s*=/.test(html)) errors.push("Page numbers are not generated from the actual slide count.");
if (!/ArrowRight/.test(html) || !/ArrowLeft/.test(html)) errors.push("Keyboard navigation is incomplete.");

if (errors.length) {
  console.error(errors.map((error) => `- ${error}`).join("\n"));
  process.exit(1);
}

console.log(`Validation passed: ${slides.length} slides; font, density, brand, navigation, print, and page-number checks passed.`);
