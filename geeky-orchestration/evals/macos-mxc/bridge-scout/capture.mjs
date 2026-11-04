// capture.mjs: record Claude Code's requests and answer with a minimal Anthropic SSE stream ("OK").
import { createServer } from "node:http";
import { appendFileSync } from "node:fs";
const out = process.argv[2], port = Number(process.argv[3] || 8790);
createServer((req, res) => {
  let body = ""; req.on("data", (c) => (body += c)); req.on("end", () => {
    const h = { ...req.headers }; for (const k of ["authorization", "x-api-key"]) if (h[k]) h[k] = `<redacted ${String(h[k]).length} chars>`;
    appendFileSync(out, JSON.stringify({ method: req.method, url: req.url, headers: h, body: body ? JSON.parse(body) : null }) + "\n");
    if (req.url.startsWith("/v1/messages/count_tokens")) { res.writeHead(200, { "content-type": "application/json" }); return res.end(JSON.stringify({ input_tokens: 100 })); }
    if (!req.url.startsWith("/v1/messages")) { res.writeHead(404); return res.end("{}"); }
    res.writeHead(200, { "content-type": "text/event-stream" });
    const ev = (t, d) => res.write(`event: ${t}\ndata: ${JSON.stringify({ type: t, ...d })}\n\n`);
    ev("message_start", { message: { id: "msg_cap", type: "message", role: "assistant", model: "gpt-6.1-sol", content: [], stop_reason: null, usage: { input_tokens: 10, output_tokens: 1 } } });
    ev("content_block_start", { index: 0, content_block: { type: "text", text: "" } });
    ev("content_block_delta", { index: 0, delta: { type: "text_delta", text: "OK" } });
    ev("content_block_stop", { index: 0 });
    ev("message_delta", { delta: { stop_reason: "end_turn", stop_sequence: null }, usage: { output_tokens: 1 } });
    ev("message_stop", {}); res.end();
  });
}).listen(port, "127.0.0.1", () => console.log(`capture on 127.0.0.1:${port}`));
