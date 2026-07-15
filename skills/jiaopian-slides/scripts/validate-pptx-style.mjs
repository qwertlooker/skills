#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const args = process.argv.slice(2);
const allowTopRule = args.includes("--allow-top-rule");
const titleSystem = args.find((arg) => arg.startsWith("--title-system="))?.split("=")[1] || "ict-business-red-title";
const skipTitleSlides = new Set(
  (args.find((arg) => arg.startsWith("--skip-title-slides="))?.split("=")[1] || "")
    .split(",")
    .filter(Boolean)
    .map(Number),
);
const filename = args.find((arg) => !arg.startsWith("--"));

if (!new Set(["ict-business-red-title", "neutral-technical"]).has(titleSystem)) {
  console.error("--title-system must be ict-business-red-title or neutral-technical.");
  process.exit(2);
}

if (!filename) {
  console.error("Usage: node validate-pptx-style.mjs <deck.pptx> [--title-system=ict-business-red-title|neutral-technical] [--skip-title-slides=2,5] [--allow-top-rule]");
  process.exit(2);
}

const target = path.resolve(filename);
if (!fs.existsSync(target)) {
  console.error(`Missing PPTX file: ${target}`);
  process.exit(2);
}

const unzipText = (entry) => execFileSync("unzip", ["-p", target, entry], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
const entries = execFileSync("unzip", ["-Z1", target], { encoding: "utf8" }).trim().split(/\r?\n/);
const slides = entries
  .filter((entry) => /^ppt\/slides\/slide\d+\.xml$/.test(entry))
  .sort((a, b) => Number(a.match(/\d+/)?.[0]) - Number(b.match(/\d+/)?.[0]));

if (!slides.length) {
  console.error("- No slide XML found.");
  process.exit(1);
}

const presentation = unzipText("ppt/presentation.xml");
const sizeMatch = presentation.match(/<p:sldSz\s+cx="(\d+)"\s+cy="(\d+)"/);
const pageWidth = Number(sizeMatch?.[1] || 12192000);
const pageHeight = Number(sizeMatch?.[2] || 6858000);
const errors = [];
const warnings = [];

const decodeXml = (value) => value
  .replaceAll("&amp;", "&")
  .replaceAll("&lt;", "<")
  .replaceAll("&gt;", ">")
  .replaceAll("&quot;", '"')
  .replaceAll("&apos;", "'");

for (let index = 0; index < slides.length; index += 1) {
  const slideNo = index + 1;
  const xml = unzipText(slides[index]);
  const text = [...xml.matchAll(/<a:t>(.*?)<\/a:t>/gs)].map((match) => decodeXml(match[1])).join(" ");
  const hasCjk = /[\u3400-\u9fff]/.test(text);
  const latinFonts = [...xml.matchAll(/<a:latin\s+typeface="([^"]+)"/g)].map((match) => match[1]);
  const eastAsianFonts = [...xml.matchAll(/<a:ea\s+typeface="([^"]+)"/g)].map((match) => match[1]);

  if (latinFonts.some((font) => /Microsoft YaHei|微软雅黑/i.test(font))) {
    errors.push(`Slide ${slideNo}: Microsoft YaHei is assigned to the Latin font slot; use Arial.`);
  }
  if (text && !latinFonts.some((font) => /^Arial$/i.test(font))) {
    errors.push(`Slide ${slideNo}: no explicit Arial Latin font mapping found.`);
  }
  if (hasCjk && !eastAsianFonts.some((font) => /Microsoft YaHei|微软雅黑/i.test(font))) {
    errors.push(`Slide ${slideNo}: Chinese text has no explicit Microsoft YaHei East Asian mapping.`);
  }

  for (const forbidden of ["Huawei-style presentation", "华为风格模板", "Huawei Confidential", "Huawei Proprietary"]) {
    if (text.includes(forbidden)) errors.push(`Slide ${slideNo}: producer-facing or unauthorized text remains: ${forbidden}`);
  }

  let decorativeRedLines = 0;
  const shapes = [...xml.matchAll(/<p:sp>(.*?)<\/p:sp>/gs)].map((match) => match[1]);
  if (slideNo > 1 && titleSystem === "ict-business-red-title" && !skipTitleSlides.has(slideNo)) {
    const hasFullRedTitle = shapes.some((shape) => {
      const textBody = shape.match(/<p:txBody>(.*?)<\/p:txBody>/s)?.[1] || "";
      if (!/<a:t>.*?<\/a:t>/s.test(textBody)) return false;
      const xfrm = shape.match(/<a:xfrm[^>]*>.*?<a:off\s+x="(\d+)"\s+y="(\d+)"\s*\/>.*?<a:ext\s+cx="(\d+)"\s+cy="(\d+)"\s*\/>/s);
      if (!xfrm) return false;
      const [, , yRaw, cxRaw] = xfrm;
      const inTitleZone = Number(yRaw) <= pageHeight * 0.18 && Number(cxRaw) >= pageWidth * 0.42;
      const sizes = [...textBody.matchAll(/\bsz="(\d+)"/g)].map((match) => Number(match[1]));
      const titleSized = sizes.some((size) => size >= 2400);
      const textColors = [...textBody.matchAll(/<a:srgbClr\s+val="([0-9A-F]{6})"/gi)].map((match) => match[1].toUpperCase());
      const fullRed = textColors.length > 0 && textColors.every((color) => color === "C7000B");
      return inTitleZone && titleSized && fullRed;
    });
    if (!hasFullRedTitle) {
      errors.push(`Slide ${slideNo}: no full Huawei-red takeaway title found for title system ${titleSystem}. Use --title-system=neutral-technical only when that route was selected before authoring.`);
    }
  }
  for (const shape of shapes) {
    const name = decodeXml(shape.match(/<p:cNvPr\b[^>]*\bname="([^"]*)"/)?.[1] || "unnamed");
    const isRed = /<a:srgbClr\s+val="C7000B"/i.test(shape);
    if (!isRed) continue;

    const hasText = /<a:t>.*?<\/a:t>/s.test(shape);
    const xfrm = shape.match(/<a:xfrm[^>]*>.*?<a:off\s+x="(\d+)"\s+y="(\d+)"\s*\/>.*?<a:ext\s+cx="(\d+)"\s+cy="(\d+)"\s*\/>/s);
    if (!xfrm) continue;
    const [, xRaw, yRaw, cxRaw, cyRaw] = xfrm;
    const x = Number(xRaw);
    const y = Number(yRaw);
    const cx = Number(cxRaw);
    const cy = Number(cyRaw);
    const thin = cy <= pageHeight * 0.025 || cx <= pageWidth * 0.004;
    const nearTopEdge = y <= pageHeight * 0.025 && cx >= pageWidth * 0.12 && cy <= pageHeight * 0.04;
    const inTitleZone = y <= pageHeight * 0.18 && thin && cx >= pageWidth * 0.025;
    const namedTopRule = /top[-_ ]?rule/i.test(name);
    const namedTitleRule = /title[-_ ]?(accent|rule|underline)/i.test(name);
    const namedPageNumber = /page[-_ ]?(no|num|number)/i.test(name);
    const giantCoverBlob = slideNo === 1 && !hasText && cx >= pageWidth * 0.3 && cy >= pageHeight * 0.2;

    if (!hasText && thin && /(accent|rule|underline|border)/i.test(name)) decorativeRedLines += 1;
    if (!allowTopRule && (nearTopEdge || namedTopRule)) {
      errors.push(`Slide ${slideNo}: decorative top red rule found (${name}).`);
    }
    if (namedTitleRule || (!hasText && inTitleZone && !namedTopRule)) {
      errors.push(`Slide ${slideNo}: decorative red line in the title zone found (${name}).`);
    }
    if (namedPageNumber) {
      errors.push(`Slide ${slideNo}: red page number found (${name}); use gray by default.`);
    }
    if (giantCoverBlob) {
      errors.push(`Slide ${slideNo}: giant decoration-only red cover shape found (${name}).`);
    }
    if (x < 0 || y < 0 || cx <= 0 || cy <= 0) warnings.push(`Slide ${slideNo}: invalid red shape geometry (${name}).`);
  }

  if (decorativeRedLines > 1) {
    errors.push(`Slide ${slideNo}: ${decorativeRedLines} decoration-only red lines found; keep none by default and at most one when semantically justified.`);
  }
}

if (warnings.length) console.warn(warnings.map((warning) => `! ${warning}`).join("\n"));
if (errors.length) {
  console.error(errors.map((error) => `- ${error}`).join("\n"));
  process.exit(1);
}

console.log(`Validation passed: ${slides.length} slides; title system ${titleSystem}, PPTX font mapping, producer text, red chrome, page numbers, and cover decoration checks passed.`);
