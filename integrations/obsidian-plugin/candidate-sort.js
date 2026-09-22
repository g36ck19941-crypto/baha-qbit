"use strict";

const TASK = /^- \[([ xX])\] \*\*.+?\*\*\s*$/gm;
const ITEM_MARKER = /<!-- anime-bridge:item \{.*?\} -->/;

function reorderCheckedCandidates(markdown) {
  if (!markdown.includes("anime_bridge_document: candidates")) return markdown;
  const startMarker = "<!-- anime-bridge:items-start -->";
  const endMarker = "<!-- anime-bridge:items-end -->";
  const start = markdown.indexOf(startMarker);
  const end = markdown.indexOf(endMarker, start + startMarker.length);
  const regionStart = start >= 0 && end > start ? start + startMarker.length : 0;
  const regionEnd = start >= 0 && end > start ? end : markdown.length;
  const region = markdown.slice(regionStart, regionEnd);
  const matches = [...region.matchAll(TASK)];
  if (matches.length < 2) return markdown;

  const blocks = matches.map((match, index) => {
    const start = match.index;
    const end = index + 1 < matches.length ? matches[index + 1].index : region.length;
    return {
      checked: match[1].toLowerCase() === "x",
      content: region.slice(start, end),
      originalIndex: index,
    };
  });
  if (blocks.some((block) => !ITEM_MARKER.test(block.content))) return markdown;

  const sorted = [...blocks].sort((left, right) => {
    if (left.checked !== right.checked) return left.checked ? -1 : 1;
    return left.originalIndex - right.originalIndex;
  });
  if (sorted.every((block, index) => block.originalIndex === index)) return markdown;
  const sortedRegion = region.slice(0, matches[0].index) + sorted.map((block) => block.content).join("");
  return markdown.slice(0, regionStart) + sortedRegion + markdown.slice(regionEnd);
}

module.exports = { reorderCheckedCandidates };
