const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = "C:\\Users\\RSCH\\Daleel";
const CAP = path.join(ROOT, "captures");
const OUT = path.join(ROOT, "presentation", "demo_daleel.webm");
const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";

const scenes = [
  ["fig_4_1_chatbot.png", "1. Question juridique", "L'utilisateur pose une question en langage naturel."],
  ["fig_4_1_chat_reponse.png", "2. Reponse sourcee", "Daleel repond avec contexte, sources et garde-qualite."],
  ["fig_4_2_admin_documents.png", "3. Gestion documentaire", "Le corpus est importe, traite et indexe."],
  ["fig_4_3_dashboard.png", "4. Pilotage conformite", "Les indicateurs aident a prioriser les actions."],
  ["fig_4_2_agent_tool_log.png", "5. Tracabilite", "Les appels d'outils rendent le raisonnement auditable."],
].map(([file, title, subtitle]) => ({
  title,
  subtitle,
  data: "data:image/png;base64," + fs.readFileSync(path.join(CAP, file)).toString("base64"),
}));

async function main() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: EDGE,
    args: ["--autoplay-policy=no-user-gesture-required", "--use-fake-ui-for-media-stream"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.setContent("<html><body style='margin:0;background:#f5f7fb'><canvas id='c' width='1280' height='720'></canvas></body></html>");

  const b64 = await page.evaluate(async (scenes) => {
    const W = 1280, H = 720;
    const canvas = document.getElementById("c");
    const ctx = canvas.getContext("2d");
    const images = await Promise.all(scenes.map(scene => new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve({ ...scene, img });
      img.onerror = reject;
      img.src = scene.data;
    })));

    function roundRect(x, y, w, h, r) {
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }

    function drawScene(scene, progress) {
      ctx.fillStyle = "#f5f7fb";
      ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = "#232946";
      ctx.fillRect(0, 0, W, 92);
      ctx.fillStyle = "#ffffff";
      ctx.font = "700 38px Calibri, Arial";
      ctx.fillText("Daleel - demonstration", 52, 59);
      ctx.fillStyle = "#D4A437";
      roundRect(1030, 24, 198, 40, 20);
      ctx.fill();
      ctx.fillStyle = "#232946";
      ctx.font = "700 19px Calibri, Arial";
      ctx.fillText("PFE 2025-2026", 1060, 51);

      const maxW = 1160, maxH = 500;
      const ratio = Math.min(maxW / scene.img.width, maxH / scene.img.height);
      const iw = scene.img.width * ratio;
      const ih = scene.img.height * ratio;
      const zoom = 1 + 0.018 * Math.sin(progress * Math.PI);
      const dw = iw * zoom;
      const dh = ih * zoom;
      const x = (W - dw) / 2;
      const y = 120 + (ih - dh) / 2;

      ctx.shadowColor = "rgba(0,0,0,0.22)";
      ctx.shadowBlur = 14;
      ctx.shadowOffsetY = 5;
      ctx.fillStyle = "#ffffff";
      roundRect(x - 10, y - 10, dw + 20, dh + 20, 22);
      ctx.fill();
      ctx.shadowColor = "transparent";
      ctx.drawImage(scene.img, x, y, dw, dh);

      ctx.fillStyle = "#ffffff";
      ctx.strokeStyle = "#e1e6f0";
      ctx.lineWidth = 2;
      roundRect(70, 625, 1140, 65, 18);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#D4A437";
      ctx.beginPath();
      ctx.arc(110, 657, 16, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#232946";
      ctx.font = "700 19px Calibri, Arial";
      ctx.fillText(String(images.indexOf(scene) + 1), 105, 664);
      ctx.font = "24px Calibri, Arial";
      ctx.fillText(scene.title, 148, 654);
      ctx.fillStyle = "#626D83";
      ctx.font = "18px Calibri, Arial";
      ctx.fillText(scene.subtitle, 148, 681);
    }

    const stream = canvas.captureStream(30);
    const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
      ? "video/webm;codecs=vp9"
      : "video/webm";
    const recorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 2500000 });
    const chunks = [];
    recorder.ondataavailable = event => {
      if (event.data.size) chunks.push(event.data);
    };
    const done = new Promise(resolve => recorder.onstop = resolve);
    recorder.start();

    const totalMs = 12500;
    const sceneMs = totalMs / images.length;
    const start = performance.now();
    await new Promise(resolve => {
      function tick(now) {
        const elapsed = now - start;
        const idx = Math.min(images.length - 1, Math.floor(elapsed / sceneMs));
        const progress = (elapsed - idx * sceneMs) / sceneMs;
        drawScene(images[idx], Math.max(0, Math.min(1, progress)));
        if (elapsed < totalMs) requestAnimationFrame(tick);
        else resolve();
      }
      requestAnimationFrame(tick);
    });

    recorder.stop();
    await done;
    const blob = new Blob(chunks, { type: "video/webm" });
    const buffer = await blob.arrayBuffer();
    let binary = "";
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i]);
    return btoa(binary);
  }, scenes);

  fs.writeFileSync(OUT, Buffer.from(b64, "base64"));
  await browser.close();
  console.log(`OK - video generated: ${OUT}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
