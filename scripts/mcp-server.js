const http=require("http"),fs=require("fs"),path=require("path");
const PORT=process.env.MCP_PORT||3100,ROOT=path.join(__dirname,"..");
const CH={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"GET,POST,OPTIONS","Access-Control-Allow-Headers":"Content-Type,Accept"};
function ags(){try{return fs.readdirSync(path.join(ROOT,"agents")).filter(f=>f.endsWith(".md")).map(f=>{const n=f.replace(".md",""),t=fs.readFileSync(path.join(ROOT,"agents",f),"utf8"),m=t.match(/description[^\n]*:\s*["\x27]?(["\x27\n]{3,})/m),h=t.match(/^#\s+(.+)/m);return{n,d:(m?m[1]:h?h[1]:"AI agent").trim().slice(0,110)};});}catch(e){return[];}}
function cs(){try{return fs.readdirSync(path.join(ROOT,"commands")).filter(f=>f.endsWith(".md")).map(f=>f.replace(".md",""));}catch(e){return[];}}
function J(res,o){res.writeHead(200,Object.assign({},CH,{"Content-Type":"application/json"}));res.end(JSON.stringify(o,null,2));}
const srv=http.createServer((req,res)=>{
const A=ags(),C=cs(),u=req.url.split("?")[0],acc=req.headers["accept"]||"";
if(req.method==="OPTIONS"){res.writeHead(204,CH);res.end();return;}
if(u==="/ping"||u==="/health")return J(res,{status:"ok",agents:A.length,commands:C.length,port:PORT,layer:"1-mcp",dashboard:"http://localhost:"+PORT});
if(u==="/tools/list")return J(res,{tools:A.map(a=>({name:a.n,description:a.d}))});
if(u==="/resources/list")return J(res,{resources:["agents/","services/","commands/","hooks/","rules/","skills/"]});
if(u==="/prompts/list")return J(res,{prompts:C.map(n=>({name:n,invoke:"/"+n}))});
if(u.startsWith("/agent/")){const ag=A.find(a=>a.n===u.slice(7));if(ag)return J(res,ag);res.writeHead(404,CH);res.end(JSON.stringify({error:"not found"}));return;}
if(u==="/tools/call"&&req.method==="POST"){let b="";req.on("data",c=>b+=c);req.on("end",()=>{try{const d=JSON.parse(b||"{}"),ag=A.find(a=>a.n===d.tool);if(!ag){res.writeHead(404,CH);res.end(JSON.stringify({error:"agent not found"}));return;}J(res,{agent:d.tool,status:"ready",description:ag.d,message:"Agent "+d.tool+" wired on MCP:"+PORT+". Connect Claude Code for AI calls.",params:d.params});}catch(e){res.writeHead(400,CH);res.end(JSON.stringify({error:e.message}));}});return;}
if((u==="/"||u==="")&&(acc.includes("text/html")||acc.includes("*/*")||acc==="")){
res.writeHead(200,Object.assign({},CH,{"Content-Type":"text/html;charset=utf-8"}));
res.end(buildPage(A,C));
return;
}
res.writeHead(404,CH);res.end(JSON.stringify({error:"Not found",try:["/","/ping","/tools/list","/tools/call"]}));
});
srv.listen(PORT,"0.0.0.0",()=>{console.log("VWH MCP Observer: http://localhost:"+PORT);});
function buildPage(A,C){
const Q=String.fromCharCode(34);
const t=String.fromCharCode(60),g=String.fromCharCode(62);
const e=(tag,attrs,inner)=>t+tag+(attrs?" "+attrs:"")+g+(inner||"")+t+"/"+tag+g;
const btn=(bg,lbl,fn)=>t+"button onclick="+Q+fn+Q+" style="+Q+"background:"+bg+";color:#fff;border:none;padding:5px 10px;border-radius:4px;cursor:pointer;font-family:monospace"+Q+g+lbl+t+"/button"+g;
const ar=A.map(a=>{
const id="s"+a.n.replace(/[^a-z0-9]/g,"_");
return t+"tr"+g+t+"td"+g+t+"code"+g+a.n+t+"/code"+g+t+"/td"+g
+t+"td style="+Q+"color:#8b949e;font-size:12px"+Q+g+a.d+t+"/td"+g
+t+"td"+g
+t+"button onclick="+Q+"ping("+JSON.stringify(a.n)+")"+Q+" style="+Q+"background:#238636;color:#fff;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;margin:2px"+Q+g+"Ping"+t+"/button"+g
+" "+t+"button onclick="+Q+"call2("+JSON.stringify(a.n)+")"+Q+" style="+Q+"background:#1f6feb;color:#fff;border:none;padding:4px 8px;border-radius:4px;cursor:pointer"+Q+g+"Call"+t+"/button"+g
+t+"/td"+g
+t+"td id="+Q+id+Q+" style="+Q+"width:40px;text-align:center"+Q+g+t+"/td"+g
+t+"/tr"+g;
}).join("");
const cr=C.slice(0,30).map(n=>t+"tr"+g+t+"td"+g+t+"code"+g+"/"+n+t+"/code"+g+t+"/td"+g+t+"/tr"+g).join("");
const nm=JSON.stringify(A.map(a=>a.n));
const css="body{font-family:monospace;background:#0d1117;color:#c9d1d9;padding:20px;margin:0}h1{color:#58a6ff;border-bottom:2px solid #30363d;padding-bottom:8px;margin-bottom:8px}h2{color:#79c0ff;margin:16px 0 8px}p{color:#8b949e;font-size:13px;line-height:1.6;margin-bottom:6px}table{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:8px}th{background:#161b22;color:#8b949e;padding:6px 9px;text-align:left;border:1px solid #30363d}td{padding:5px 9px;border:1px solid #21262d;vertical-align:middle}tr:hover td{background:#161b22}code{background:#161b22;padding:1px 5px;border-radius:4px;color:#79c0ff}.ep{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.ep-card{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px;min-width:180px;flex:1}.ep-card p{color:#8b949e;font-size:12px;margin:4px 0 8px}.ep-card button{width:100%;border:none;padding:5px;border-radius:4px;cursor:pointer;font-size:12px;font-family:monospace}#log{background:#010409;border:1px solid #30363d;border-radius:4px;padding:8px;height:130px;overflow-y:auto;font-size:12px;margin-top:6px}a{color:#58a6ff}";
const jsb64="Y29uc3QgTD1kb2N1bWVudC5nZXRFbGVtZW50QnlJZCgibG9nIiksQUxMPU5NO2xldCBkPTA7ZnVuY3Rpb24gbG9nKG0sYyl7Y29uc3QgZT1kb2N1bWVudC5jcmVhdGVFbGVtZW50KCJkaXYiKTtlLnN0eWxlLmNvbG9yPWN8fCIjM2ZiOTUwIjtlLnRleHRDb250ZW50PSJbIituZXcgRGF0ZSgpLnRvTG9jYWxlVGltZVN0cmluZygpKyJdICIrbTtMLmluc2VydEJlZm9yZShlLEwuZmlyc3RDaGlsZCk7fWFzeW5jIGZ1bmN0aW9uIGdvKHUpe2xvZygiR0VUICIrdSwiIzU4YTZmZiIpO3RyeXtjb25zdCByPWF3YWl0IGZldGNoKHUpO2xvZyhKU09OLnN0cmluZ2lmeShhd2FpdCByLmpzb24oKSkuc2xpY2UoMCwzMDApKTt9Y2F0Y2goZSl7bG9nKGUubWVzc2FnZSwiI2Y4NTE0OSIpO319YXN5bmMgZnVuY3Rpb24gdHJ5Q2FsbCgpe2NvbnN0IHQ9cHJvbXB0KCJBZ2VudDoiLCJjb2RlLXJldmlld2VyIik7aWYoIXQpcmV0dXJuO2NvbnN0IHE9cHJvbXB0KCJUYXNrOiIsIkRlc2NyaWJlIHlvdXJzZWxmLiIpO2lmKCFxKXJldHVybjt0cnl7Y29uc3Qgcj1hd2FpdCBmZXRjaCgiL3Rvb2xzL2NhbGwiLHttZXRob2Q6IlBPU1QiLGhlYWRlcnM6eyJDb250ZW50LVR5cGUiOiJhcHBsaWNhdGlvbi9qc29uIn0sYm9keTpKU09OLnN0cmluZ2lmeSh7dG9vbDp0LHBhcmFtczp7dGFzazpxfX0pfSk7bG9nKEpTT04uc3RyaW5naWZ5KGF3YWl0IHIuanNvbigpKS5zbGljZSgwLDMwMCkpO31jYXRjaChlKXtsb2coZS5tZXNzYWdlLCIjZjg1MTQ5Iik7fX1hc3luYyBmdW5jdGlvbiBwaW5nKG4pe2NvbnN0IGVsPWRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJzIituLnJlcGxhY2UoL1teYS16MC05XS9nLCJfIikpO2lmKGVsKWVsLnRleHRDb250ZW50PSIuLi4iO3RyeXthd2FpdCBmZXRjaCgiL3Rvb2xzL2NhbGwiLHttZXRob2Q6IlBPU1QiLGhlYWRlcnM6eyJDb250ZW50LVR5cGUiOiJhcHBsaWNhdGlvbi9qc29uIn0sYm9keTpKU09OLnN0cmluZ2lmeSh7dG9vbDpuLHBhcmFtczp7dGFzazoicGluZyJ9fSl9KTtpZihlbCl7ZWwudGV4dENvbnRlbnQ9Ik9LIjtlbC5zdHlsZS5jb2xvcj0iIzNmYjk1MCI7fWxvZyhuKyI6IHJlYWR5Iik7fWNhdGNoKGUpe2lmKGVsKXtlbC50ZXh0Q29udGVudD0iRVJSIjtlbC5zdHlsZS5jb2xvcj0iI2Y4NTE0OSI7fX19YXN5bmMgZnVuY3Rpb24gY2FsbDIobil7Y29uc3QgcT1wcm9tcHQoIlRhc2s6IiwiRGVzY3JpYmUgeW91cnNlbGYuIik7aWYoIXEpcmV0dXJuO3RyeXtjb25zdCByPWF3YWl0IGZldGNoKCIvdG9vbHMvY2FsbCIse21ldGhvZDoiUE9TVCIsaGVhZGVyczp7IkNvbnRlbnQtVHlwZSI6ImFwcGxpY2F0aW9uL2pzb24ifSxib2R5OkpTT04uc3RyaW5naWZ5KHt0b29sOm4scGFyYW1zOnt0YXNrOnF9fSl9KTtjb25zdCBqPWF3YWl0IHIuanNvbigpO2xvZyhuKyI6ICIrKGoubWVzc2FnZXx8SlNPTi5zdHJpbmdpZnkoaikpLnNsaWNlKDAsMjAwKSk7fWNhdGNoKGUpe2xvZyhlLm1lc3NhZ2UsIiNmODUxNDkiKTt9fWFzeW5jIGZ1bmN0aW9uIHBpbmdBbGwoKXtkPTA7Y29uc3QgcHI9ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInByIik7cHIuc3R5bGUuZGlzcGxheT0iZmxleCI7bG9nKCJQaW5naW5nICIrQUxMLmxlbmd0aCsiIGFnZW50cy4uLiIsIiM1OGE2ZmYiKTtmb3IoY29uc3QgbiBvZiBBTEwpe2F3YWl0IHBpbmcobik7ZCsrO2RvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJwYiIpLnN0eWxlLndpZHRoPU1hdGgucm91bmQoZC9BTEwubGVuZ3RoKjEwMCkrIiUiO2RvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJwYyIpLnRleHRDb250ZW50PWQrIi8iK0FMTC5sZW5ndGg7YXdhaXQgbmV3IFByb21pc2Uocj0+c2V0VGltZW91dChyLDMwKSk7fWxvZygiRG9uZTogIitBTEwubGVuZ3RoKyIgcGluZ2VkLiIpO30=";
const js=Buffer.from(jsb64,"base64").toString().replace("NM",nm);
const pingRow="<div style=\"display:flex;gap:10px;align-items:center;margin-bottom:10px\">"+"<button onclick=\"pingAll()\" style=\"background:#8957e5;color:#fff;border:none;padding:7px 20px;border-radius:4px;cursor:pointer;font-weight:700\">Ping All</button><div id=\"pr\" style=\"display:none;align-items:center;gap:10px;flex:1\"><div style=\"flex:1;background:#21262d;border-radius:4px;height:7px;overflow:hidden\"><div id=\"pb\" style=\"background:#58a6ff;height:7px;width:0%\"></div></div><span id=\"pc\" style=\"color:#8b949e;font-size:12px\"></span></div>"+"</div>";
const eps="<div class=\"ep\"><div class=\"ep-card\"><b style=\"color:#3fb950\">GET</b> <code>/ping</code><p>health check</p><button onclick=\"go('/ping')\" style=\"background:#3fb950;color:#fff\">Try</button></div><div class=\"ep-card\"><b style=\"color:#3fb950\">GET</b> <code>/tools/list</code><p>all agents</p><button onclick=\"go('/tools/list')\" style=\"background:#3fb950;color:#fff\">Try</button></div><div class=\"ep-card\"><b style=\"color:#e3b341\">POST</b> <code>/tools/call</code><p>call agent</p><button onclick=\"tryCall()\" style=\"background:#e3b341;color:#fff\">Try</button></div><div class=\"ep-card\"><b style=\"color:#3fb950\">GET</b> <code>/resources/list</code><p>dirs</p><button onclick=\"go('/resources/list')\" style=\"background:#3fb950;color:#fff\">Try</button></div><div class=\"ep-card\"><b style=\"color:#3fb950\">GET</b> <code>/prompts/list</code><p>commands</p><button onclick=\"go('/prompts/list')\" style=\"background:#3fb950;color:#fff\">Try</button></div></div>";
const headHtml="<!DOCTYPE html><html><head><meta charset=utf-8><title>VWH MCP Observer</title><style>"+css+"</style></head><body><h1>VWH MCP Observer</h1>"+"<p>Layer 1: "+A.length+" agents on MCP :"+(PORT)+" | Layer 2: <a href=\"http://127.0.0.1:7788/health\">MAMGA :7788</a> | browser-harness | obsidian-wiki</p>";
const bodyHtml="<h2>Endpoints</h2>"+ eps +"<h2>Agents ("+A.length+")</h2>"+ pingRow +"<table><tr><th>Agent</th><th>Desc</th><th>Actions</th><th>Status</th></tr>"+ ar +"</table><h2>Commands</h2><table><tr><th>Command</th></tr>"+ cr +"</table><h2>Log</h2><div id=\"log\">Observer ready. MCP coordination unchanged.</div><script>"+ js +"</script></body></html>";
return headHtml+bodyHtml;
}
