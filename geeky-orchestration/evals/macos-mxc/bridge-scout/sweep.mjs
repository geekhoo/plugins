const B0 = process.env.ANTHROPIC_BASE_URL.replace(/\/$/, ""), B = /^[a-z]+:\/\//.test(B0) ? B0 : "http://" + B0, K = process.env.ANTHROPIC_AUTH_TOKEN;
const Q = "A clock gains 7 minutes every 3 hours. It was set right at 06:00 on Monday. What time will it show at 18:00 on Wednesday? Answer with the time only.";
const H = { authorization: `Bearer ${K}`, "content-type": "application/json", "anthropic-version": "2023-06-01" };
const out = [];
for (const effort of ["low", "medium", "high", "xhigh"]) for (let i = 0; i < 3; i++) {
  const m = await (await fetch(`${B}/v1/messages`, { method: "POST", headers: H, body: JSON.stringify({ model: "gpt-6.1-sol", max_tokens: 4000, thinking: { type: "adaptive" }, output_config: { effort }, messages: [{ role: "user", content: Q }] }) })).json();
  const r = await (await fetch(`${B}/v1/responses`, { method: "POST", headers: H, body: JSON.stringify({ model: "gpt-6.1-sol", max_output_tokens: 4000, store: false, reasoning: { effort, summary: "detailed" }, input: Q }) })).json();
  out.push({ effort, i, msg_out: m.usage?.output_tokens, msg_err: m.error?.message?.slice(0, 80), resp_out: r.usage?.output_tokens, resp_reason: r.usage?.output_tokens_details?.reasoning_tokens, resp_err: r.error?.message?.slice(0, 80) });
}
console.log(JSON.stringify(out));
