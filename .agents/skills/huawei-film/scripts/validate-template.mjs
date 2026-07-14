import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const skillRoot = path.resolve(scriptDir, "..");
const flatMode = process.argv.includes("--flat");

const files = flatMode
  ? {
      skill: path.join(scriptDir, "SKILL.md"),
      css: path.join(scriptDir, "huawei-film-theme.css"),
      html: path.join(scriptDir, "slide-template.html"),
      example: path.join(scriptDir, "example-input-output.md"),
    }
  : {
      skill: path.join(skillRoot, "SKILL.md"),
      css: path.join(skillRoot, "resources", "huawei-film-theme.css"),
      html: path.join(skillRoot, "templates", "slide-template.html"),
      example: path.join(skillRoot, "examples", "example-input-output.md"),
    };

const errors = [];
const read = (label, filename) => {
  if (!fs.existsSync(filename)) {
    errors.push(`${label}: missing ${filename}`);
    return "";
  }
  return fs.readFileSync(filename, "utf8");
};

const skill = read("skill", files.skill);
const css = read("css", files.css);
const html = read("html", files.html);
read("example", files.example);

if (!/^---\nname: huawei-film\ndescription: .+\n---/m.test(skill)) {
  errors.push("SKILL.md: frontmatter must contain name and description");
}
if (!css.includes("--huawei-red: #c7000b")) {
  errors.push("CSS: default Huawei red must be #c7000b");
}
if (!css.includes('--font-cn: "Microsoft YaHei", "微软雅黑"')) {
  errors.push("CSS: Chinese default font must be Microsoft YaHei");
}
if (!css.includes('--font-en: Arial,')) {
  errors.push("CSS: English and numeric default font must be Arial");
}
if (!css.includes(".title-rule::before") || !css.includes("flex: none")) {
  errors.push("CSS: title rule red segment must not shrink");
}
if (!css.includes(".flow-step h3") || !css.includes(".flow-step p")) {
  errors.push("CSS: flow step heading and body styles are missing");
}
if (!css.includes("--flow-columns") || !css.includes(".flow-3") || !css.includes(".flow-5")) {
  errors.push("CSS: reusable flow column variants are missing");
}
if (!css.includes(".page-number::before") || !css.includes("counter-increment: slide")) {
  errors.push("CSS: automatic page numbering is missing");
}

const opens = (css.match(/{/g) || []).length;
const closes = (css.match(/}/g) || []).length;
if (opens !== closes) errors.push(`CSS: unbalanced braces (${opens} open, ${closes} close)`);

const slideCount = (html.match(/<section class="slide/g) || []).length;
if (slideCount < 1) errors.push("HTML: no slides found");
if (!html.includes('../resources/huawei-film-theme.css')) {
  errors.push("HTML: stylesheet path must target ../resources/huawei-film-theme.css");
}
if (!html.includes("fitSlides") || !html.includes("slide-shell")) {
  errors.push("HTML: responsive preview wrapper is missing");
}
if ((html.match(/class="page-number"/g) || []).length !== slideCount) {
  errors.push("HTML: every slide must use an automatic page-number placeholder");
}
if (/<span>0\d<\/span>/.test(html)) {
  errors.push("HTML: hardcoded page numbers are not allowed");
}

for (const forbidden of [">HUAWEI<", "Huawei Confidential", "Huawei Proprietary"]) {
  if (html.includes(forbidden)) errors.push(`HTML: forbidden brand placeholder found: ${forbidden}`);
}

if (errors.length) {
  console.error(errors.map((error) => `- ${error}`).join("\n"));
  process.exit(1);
}

console.log(`Validation passed: ${slideCount} slides, brand-safe HTML, valid core CSS tokens.`);
