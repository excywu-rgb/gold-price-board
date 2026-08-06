const OWNER = "excywu-rgb";
const REPO = "gold-price-board";
const WORKFLOW = "refresh.yml";

function wait(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function dispatchWorkflowOnce(env, triggeredBy) {
  if (!env.GITHUB_TOKEN) {
    throw new Error("GITHUB_TOKEN secret is missing");
  }
  const response = await fetch(
    `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: "POST",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        "Content-Type": "application/json",
        "User-Agent": "gold-price-board-cloudflare-scheduler",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({
        ref: "main",
        inputs: { triggered_by: triggeredBy },
      }),
    },
  );
  if (response.status !== 204) {
    const body = await response.text();
    throw new Error(`GitHub dispatch failed: ${response.status} ${body}`);
  }
  return { ok: true, status: response.status, triggeredBy };
}

async function dispatchWorkflow(env, triggeredBy) {
  let lastError;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      return await dispatchWorkflowOnce(env, triggeredBy);
    } catch (error) {
      lastError = error;
      if (attempt < 3) {
        await wait(attempt * 3000);
      }
    }
  }
  throw lastError;
}

export default {
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(dispatchWorkflow(env, `cloudflare-cron:${controller.cron}`));
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") {
      return Response.json({
        ok: true,
        service: "gold-price-board-scheduler",
        cron: "23 * * * *",
      });
    }
    if (request.method === "POST" && url.pathname === "/trigger") {
      const authorization = request.headers.get("Authorization");
      if (!env.TRIGGER_KEY || authorization !== `Bearer ${env.TRIGGER_KEY}`) {
        return new Response("Unauthorized", { status: 401 });
      }
      const result = await dispatchWorkflow(env, "cloudflare-manual-verification");
      return Response.json(result);
    }
    return new Response("Not found", { status: 404 });
  },
};
