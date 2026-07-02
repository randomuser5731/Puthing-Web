import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL") ?? "",
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
);

Deno.serve(async (req: Request) => {
  const url = new URL(req.url);
  
  if (req.method === "GET" && url.pathname === "/api/stats") {
    const { data, error } = await supabase.rpc("get_stats");
    if (error) return new Response(JSON.stringify({ error: "the archives deny entry" }), { status: 500 });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    });
  }

  if (req.method === "POST" && url.pathname === "/api/verify") {
    const { guess } = await req.json();
    if (!guess) return new Response(JSON.stringify({ error: "the ritual requires a guess" }), { status: 400 });
    
    const { data, error } = await supabase.rpc("verify_code", { guess });
    if (error) return new Response(JSON.stringify({ error: "the cipher rejects your offering" }), { status: 500 });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    });
  }

  if (req.method === "GET" && url.pathname === "/api/winner") {
    const { data, error } = await supabase.rpc("get_winner");
    if (error) return new Response(JSON.stringify({ winner: "Anonymous" }), { headers: { "Content-Type": "application/json" } });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    });
  }

  if (req.method === "GET" && url.pathname === "/api/hint") {
    const { data, error } = await supabase.rpc("get_hint");
    if (error) return new Response(JSON.stringify({ hint: "the void is silent...", attempts: 0, level: 0 }), { headers: { "Content-Type": "application/json" } });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    });
  }

  return new Response(JSON.stringify({ error: "the void does not answer" }), { status: 404 });
});