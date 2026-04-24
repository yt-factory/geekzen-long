/**
 * render.mjs — render GeekZenVideo from pipeline output
 *
 * Usage:
 *   node render.mjs <output_dir>
 *
 * Expects output_dir to contain:
 *   slides_timing.json   (from present.py)
 *   audio_tw.mp3         (from tts.py)
 *   subtitle_zh_hans.srt (from subtitles.py, optional)
 */
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { copyFileSync, existsSync, readFileSync, unlinkSync } from "fs";
import { join, resolve } from "path";
import { execSync } from "child_process";

const outputDir = resolve(process.argv[2] ?? ".");
const timingPath = join(outputDir, "slides_timing.json");
const audioPath = join(outputDir, "audio_tw.mp3");
const srtPath = join(outputDir, "subtitle_zh_hans.srt");
const finalPath = join(outputDir, "final_remotion.mp4");

const publicDir = new URL("./public", import.meta.url).pathname;

// ── Preflight checks ──────────────────────────────────────────────────
for (const [path, label] of [[timingPath, "slides_timing.json"], [audioPath, "audio_tw.mp3"]]) {
  if (!existsSync(path)) {
    console.error(`❌ 找不到 ${label}: ${path}`);
    process.exit(1);
  }
}

// ── Copy audio into public/ so Remotion's HTTP server can serve it ─────
// Remotion only serves files inside public/; absolute/file:// paths are rejected.
const publicAudio = join(publicDir, "audio_tw.mp3");
copyFileSync(audioPath, publicAudio);

// ── Parse slides ───────────────────────────────────────────────────────
const slides = JSON.parse(readFileSync(timingPath, "utf-8"));

// ── Parse SRT subtitles (optional) ─────────────────────────────────────
function parseSrt(path) {
  try {
    const raw = readFileSync(path, "utf-8");
    const blocks = raw.split(/\n\n+/);
    return blocks.flatMap((block) => {
      const lines = block.trim().split("\n");
      if (lines.length < 3) return [];
      const timeParts = lines[1].split(" --> ");
      if (timeParts.length !== 2) return [];
      const parse = (t) => {
        const [h, m, rest] = t.trim().split(":");
        const s = parseFloat(rest.replace(",", "."));
        return (parseInt(h) * 3600 + parseInt(m) * 60 + s) * 1000;
      };
      return [{ start: parse(timeParts[0]), end: parse(timeParts[1]), text: lines.slice(2).join(" ") }];
    });
  } catch {
    return [];
  }
}

const subtitles = parseSrt(srtPath);

const slideDuration = slides.reduce((max, s) => Math.max(max, s.end), 0);

// Use audio duration as the floor so the video isn't truncated before audio ends
let audioDuration = slideDuration;
try {
  const probe = execSync(
    `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${audioPath}"`,
    { encoding: "utf-8" }
  ).trim();
  audioDuration = parseFloat(probe) || slideDuration;
} catch {
  // ffprobe unavailable — fall back to slide-based duration
}

const totalDuration = Math.max(slideDuration, audioDuration);
const durationInFrames = Math.ceil(totalDuration * 30) + 30; // +1s buffer

// ── Remotion render ────────────────────────────────────────────────────
const bundled = await bundle({
  entryPoint: new URL("./src/Root.tsx", import.meta.url).pathname,
  publicDir,
});

const inputProps = {
  slides,
  audioSrc: "audio_tw.mp3",  // relative — served from public/ by Remotion
  subtitles,
};

const composition = await selectComposition({
  serveUrl: bundled,
  id: "GeekZenVideo",
  inputProps,
});

console.log(`Rendering ${slides.length} slides, ${totalDuration.toFixed(1)}s → ${finalPath}`);
const t0 = Date.now();

try {
await renderMedia({
  composition: {
    ...composition,
    durationInFrames,
    fps: 30,
    width: 1920,
    height: 1080,
  },
  serveUrl: bundled,
  codec: "h264",
  outputLocation: finalPath,
  inputProps,
  onProgress: ({ progress }) => {
    process.stdout.write(`\r  ${(progress * 100).toFixed(0)}%`);
  },
});

} finally {
  // Always clean up temp audio copy, even if render throws
  if (existsSync(publicAudio)) unlinkSync(publicAudio);
}

const elapsed = ((Date.now() - t0) / 1000).toFixed(0);
const mb = (existsSync(finalPath) ? readFileSync(finalPath).length : 0) / (1024 * 1024);
console.log(`\n✅ Remotion render: ${finalPath} (${mb.toFixed(1)} MB, ${elapsed}s)`);
