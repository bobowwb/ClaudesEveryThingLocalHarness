const http=require("http"),fs=require("fs"),path=require("path");
const PORT=process.env.MCP_PORT||3100,ROOT=path.join(__dirname,"..");
const H={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"GET,POST,OPTIONS","Access-Control-Allow-Headers":"Content-Type"};
function ags(){try{return fs.readdirSync(path.join(ROOT,"agents")).filter(f=>f.endsWith(".md")).map(f=>{const n=f.replace(".md",""),t=fs.readFileSync(path.join(ROOT,"agents",f),"utf8"),m=t.match(/description[^\n]*:\s*["\x27]?(["\x27\n]{3,})/m),h=t.match(/^#\s+(.+)/m);return{n,d:(m?m[1]:h?h[1]:"AI agent").trim().slice(0,110)};});}catch(e){return[];}}
function cs(){try{return fs.readdirSync(path.join(ROOT,"commands")).filter(f=>f.endsWith(".md")).map(f=>f.replace(".md",""));}catch(e){return[];}}
function J(res,o){res.writeHead(200,Object.assign({},H,{"Content-Type":"application/json"}));res.end(JSON.stringify(o,null,2));}
const srv=http.createServer((req,res)=>{const A=ags(),C=cs(),u=req.url.split("?")[0];
if(req.method==="OPTIONS"){res.writeHead(204,H);res.end();return;}
if(u==="/ping"||u==="/health")return J(res,{status:"ok",agents:A.length,commands:C.length,port:PORT,layer:"1-mcp",dashboard:"http://localhost:"+PORT});
if(u==="/tools/list")return J(res,{tools:A.map(a=>({name:a.n,description:a.d}))});
if(u==="/resources/list")return J(res,{resources:["agents/","services/","commands/","hooks/"]});
if(u==="/prompts/list")return J(res,{prompts:C.map(n=>({name:n,invoke:"/"+n}))});
if(u.startsWith("/agent/")){const ag=A.find(a=>a.n===u.slice(7));if(ag)return J(res,ag);res.writeHead(404,H);res.end(JSON.stringify({error:"not found"}));return;}
if(u==="/tools/call"&&req.method==="POST"){let b="";req.on("data",c=>b+=c);req.on("end",()=>{try{const d=JSON.parse(b||"{}}"),ag=A.find(a=>a.n===d.tool);if(!ag){res.writeHead(404,H);res.end(JSON.stringify({error:"not found: "+(d.tool||"?")}));return;}J(res,{agent:d.tool,status:"ready",desc:ag.d,message:"Agent "+d.tool+" wired on MCP:"+PORT+". Connect Claude Code for real AI calls.",params:d.params});}catch(e){res.writeHead(400,H);res.end(JSON.stringify({error:e.message}));}});return;}
res.writeHead(404,H);res.end(JSON.stringify({error:"Not found",endpoints:["/","/ping","/tools/list","/tools/call","/resources/list","/prompts/list","/agent/:name"]}));
});
srv.listen(PORT,"0.0.0.0",()=>{console.log("VWH MCP server http://localhost:"+PORT);});
