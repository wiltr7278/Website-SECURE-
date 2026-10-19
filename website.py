import os,secrets
from urllib.parse import urlencode
from aiohttp import web,ClientSession
from dotenv import load_dotenv
load_dotenv()
CID=os.getenv("DISCORD_CLIENT_ID","1561731720942714990");CSECRET=os.getenv("DISCORD_CLIENT_SECRET","")
REDIRECT=os.getenv("DISCORD_REDIRECT_URI","http://localhost:8080/callback");BASE=os.getenv("BASE_URL","http://localhost:8080").rstrip("/")
BOT_API=os.getenv("SECURE_BOT_API","http://localhost:8090").rstrip("/");API_SECRET=os.getenv("SECURE_API_SECRET","");PORT=int(os.getenv("PORT","8080"))
SUPPORT="https://discord.gg/eM9Dm3fPW";INVITE="https://discord.com/oauth2/authorize?client_id=1561731720942714990&permissions=8454887873965302&integration_type=0&scope=bot"
SESS={};STATES=set()
def esc(x):return str(x).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
def get_s(r):return SESS.get(r.cookies.get("secure_sid",""))
def need(r):
 s=get_s(r)
 if not s:raise web.HTTPFound("/login")
 return s
def page(title,body,user=None,active="Overview"):
 nav=""
 if user:
  links=[("Overview","/dashboard","⌂"),("Servers","/servers","▦"),("Verification","/feature/verify","✓"),("Welcome","/feature/welcome","↗"),("Bye","/feature/bye","↙"),("Tickets","/feature/ticket","▤"),("Commands","/commands","⌘"),("Settings","/settings","⚙"),("Support","/support","?")]
  nav='<aside class="side"><a class="brand" href="/">▣ <span>SECURE<small>SERVER PROTECTION</small></span></a><p class="label">WORKSPACE</p>'+''.join(f'<a class="nav {"active" if active==n else ""}" href="{u}">{ic} <span>{n}</span></a>' for n,u,ic in links)+f'<div class="bottom">{esc(user.get("username","Discord user"))}<small>Discord account</small><a class="nav" href="/logout">↪ <span>Log out</span></a></div></aside>'
 return web.Response(text=f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} — SECURE</title><link rel="stylesheet" href="/static/style.css"></head><body>{nav}<main><header><b>SECURE</b><span> / {esc(title)}</span></header><section class="content">{body}</section><footer>SECURE · YOUR SERVER. OUR PRIORITY.</footer></main></body></html>',content_type="text/html")
async def botapi(path,method="GET",data=None):
 if not API_SECRET:raise web.HTTPServiceUnavailable(text="Set SECURE_API_SECRET.")
 async with ClientSession() as c:
  async with c.request(method,BOT_API+path,headers={"X-SECURE-API":API_SECRET},json=data) as r:
   if r.status>=400:raise web.HTTPBadGateway(text="Bot API unavailable. Check SECURE_BOT_API and shared secret.")
   return await r.json()
async def dapi(url,token=None,method="GET",data=None):
 async with ClientSession() as c:
  async with c.request(method,url,headers=({"Authorization":"Bearer "+token} if token else {}),data=data) as r:
   if r.status>=400:return None
   try:return await r.json()
   except:return {}
def can_manage(g):
 try:p=int(g.get("permissions","0"));return bool(p&32 or p&8)
 except:return False
async def guilds(s):return await dapi("https://discord.com/api/users/@me/guilds",s["token"]) or []
async def home(r):
 body=f'<div class="hero"><small>DISCORD SECURITY, SIMPLIFIED</small><h1>Protect your<br><span>community.</span></h1><p>Verification, welcome messages, goodbye messages, and private support tickets in one dashboard.</p><a class="btn primary" href="/login">Login with Discord</a> <a class="btn secondary" href="{INVITE}" target="_blank" rel="noopener">＋ Add SECURE</a> <a class="btn secondary" href="{SUPPORT}" target="_blank" rel="noopener">Join Support Server ↗</a><div class="points">✓ Simple setup　 ✓ Per-server controls　 ✓ Black & white design</div></div><div class="biglock">▣<small>SECURE</small></div>'
 return page("Home",body)
async def login(r):
 if not CSECRET:return page("Setup required","<div class='card'><h1>Setup required</h1><p>Set DISCORD_CLIENT_SECRET and configure the OAuth callback URL.</p></div>")
 state=secrets.token_urlsafe(24);STATES.add(state)
 raise web.HTTPFound("https://discord.com/oauth2/authorize?"+urlencode({"client_id":CID,"redirect_uri":REDIRECT,"response_type":"code","scope":"identify guilds","state":state}))
async def callback(r):
 code=r.query.get("code");state=r.query.get("state")
 if not code or state not in STATES:raise web.HTTPForbidden(text="Invalid login state.")
 STATES.discard(state)
 tok=await dapi("https://discord.com/api/oauth2/token",method="POST",data={"client_id":CID,"client_secret":CSECRET,"grant_type":"authorization_code","code":code,"redirect_uri":REDIRECT})
 if not tok or "access_token" not in tok:return page("Login failed","<div class='card'>Check your OAuth settings and callback URL.</div>")
 u=await dapi("https://discord.com/api/users/@me",tok["access_token"]);sid=secrets.token_urlsafe(32);SESS[sid]={"token":tok["access_token"],"user":u or {"username":"Discord user"}}
 resp=web.HTTPFound("/servers");resp.set_cookie("secure_sid",sid,httponly=True,samesite="Lax",secure=BASE.startswith("https://"),max_age=86400);raise resp
async def logout(r):
 SESS.pop(r.cookies.get("secure_sid",""),None);resp=web.HTTPFound("/");resp.del_cookie("secure_sid");raise resp
async def servers(r):
 s=need(r);gs=[g for g in await guilds(s) if can_manage(g)];items=[]
 for g in gs:
  inv=INVITE+"&guild_id="+g["id"]+"&disable_guild_select=true"
  items.append(f'<div class="server"><div class="icon">{esc(g["name"][:1]).upper()}</div><div class="grow"><b>{esc(g["name"])}</b><small>Manage Server / Administrator access</small></div><a class="btn primary" href="{inv}" target="_blank" rel="noopener">Add SECURE ↗</a> <a class="btn secondary" href="/select/{g["id"]}">Manage</a></div>')
 return page("Servers",'<div class="heading"><div><small>WORKSPACE</small><h1>Your servers</h1><p>Select a server you manage.</p></div><a class="btn primary" href="'+INVITE+'" target="_blank" rel="noopener">＋ Add SECURE</a></div><div class="card">'+(''.join(items) or "No servers with Manage Server or Administrator found.")+'</div>',s["user"],"Servers")
async def select(r):
 s=need(r);gid=r.match_info["gid"]
 if not any(g["id"]==gid and can_manage(g) for g in await guilds(s)):raise web.HTTPForbidden(text="Manage Server permission required.")
 s["gid"]=gid;raise web.HTTPFound("/dashboard")
async def selected(r,s):
 gid=r.match_info.get("gid") or r.query.get("guild") or s.get("gid")
 if not gid:raise web.HTTPFound("/servers")
 if not any(g["id"]==gid and can_manage(g) for g in await guilds(s)):raise web.HTTPForbidden(text="Manage Server permission required.")
 s["gid"]=gid
 return gid,await botapi("/api/config/"+gid),await botapi("/api/options/"+gid)
async def dashboard(r):
 s=need(r);gid,c,o=await selected(r,s);g=next((x for x in await guilds(s) if x["id"]==gid),{})
 cards=""
 for k,t,d,ic in [("verify","Verification","Choose verification role","✓"),("welcome","Welcome","Greet new members","↗"),("bye","Bye messages","Departure messages","↙"),("ticket","Tickets","Private support channels","▤")]:
  cards+=f'<a class="feature" href="/feature/{k}"><i>{ic}</i><h3>{t}</h3><p>{d}</p><small>{"● Enabled" if c[k]["enabled"] else "○ Disabled"} →</small></a>'
 n=sum(bool(x.get("enabled")) for x in c.values())
 return page("Overview",f'<div class="heading"><div><small>SERVER OVERVIEW</small><h1>Dashboard</h1><p>{esc(g.get("name","Selected server"))}</p></div><a class="btn secondary" href="/servers">Change server</a></div><div class="stats"><div class="stat"><small>SERVER</small><b>{esc(g.get("name","Server"))}</b></div><div class="stat"><small>ENABLED FEATURES</small><b>{n}/4</b></div></div><div class="grid">{cards}</div>',s["user"])
META={"verify":("Verification","Choose the role assigned when a member verifies."),"welcome":("Welcome","Customize your join message."),"bye":("Bye messages","Customize your departure message."),"ticket":("Tickets","Configure your ticket panel.")}
async def feature(r):
 s=need(r);k=r.match_info["key"]
 if k not in META:raise web.HTTPNotFound()
 gid,allc,o=await selected(r,s);f=allc[k];title,desc=META[k]
 ch=''.join(f'<option value="{x["id"]}" {"selected" if str(x["id"])==str(f.get("channel_id","")) else ""}>#{esc(x["name"])}</option>' for x in o["channels"]) or '<option value="">No channels available</option>'
 roles=''.join(f'<option value="{x["id"]}" {"selected" if str(x["id"])==str(f.get("role_id","")) else ""}>{esc(x["name"])}</option>' for x in o["roles"])
 role=f'<label>Verification role</label><select name="role_id" required><option value="">Choose role</option>{roles}</select>' if k=="verify" else ""
 titlefield=f'<label>Ticket title</label><input name="title" value="{esc(f.get("title","Support Ticket"))}">' if k=="ticket" else ""
 image='' if k=="verify" else f'<label>Image style</label><select name="image_mode"><option value="avatar">Member avatar</option><option value="secure">SECURE branding</option><option value="custom">Custom image URL</option><option value="none">No image</option></select><label>Custom image URL</label><input name="image_url" value="{esc(f.get("image_url",""))}">'
 body=f'<div class="heading"><div><small>FEATURE CONFIGURATION</small><h1>{title}</h1><p>{desc}</p></div></div><form class="card form" method="post" action="/feature/{k}/save"><input type="hidden" name="gid" value="{gid}"><div class="switchrow"><b>Enable {title}</b><label class="switch"><input type="checkbox" name="enabled" {"checked" if f["enabled"] else ""}><span></span></label></div><label>Channel</label><select name="channel_id"><option value="">Choose channel</option>{ch}</select>{role}{titlefield}<label>Message</label><textarea name="message" rows="5">{esc(f.get("message",""))}</textarea><small class="hint">Placeholders: {{user}}, {{server}}, {{member_count}}</small>{image}<p class="notice">For verification, place the bot role above the verification role.</p><button class="btn primary">Save changes</button></form>'
 return page(title,body,s["user"],title)
async def savefeature(r):
 s=need(r);k=r.match_info["key"];d=await r.post();gid=d.get("gid","")
 if k not in META or not any(g["id"]==gid and can_manage(g) for g in await guilds(s)):raise web.HTTPForbidden()
 c=await botapi("/api/config/"+gid)
 c[k]["enabled"]=d.get("enabled")=="on"
 for f in ["channel_id","role_id","title","message","image_mode","image_url"]:
  if f in d:c[k][f]=str(d[f])[:2000]
 await botapi("/api/config/"+gid,"PUT",c);s["gid"]=gid;raise web.HTTPFound("/feature/"+k)
async def commands_page(r):
 s=need(r);gid,c,o=await selected(r,s)
 rows=''.join(f'<div class="server"><div class="grow"><b>/{cmd}</b><small>{desc}</small></div></div>' for cmd,desc in [("help","Show public commands"),("verify","Post verification panel"),("welcome","Preview welcome"),("bye","Preview goodbye"),("ticket","Post ticket panel")])
 return page("Commands",'<div class="heading"><div><small>PUBLIC COMMANDS</small><h1>Commands</h1></div></div><div class="card">'+rows+'</div>',s["user"],"Commands")
async def simple(r):
 s=need(r);gid,c,o=await selected(r,s);title=r.match_info["which"].title()
 return page(title,f'<div class="card"><a class="btn primary" href="{SUPPORT}" target="_blank" rel="noopener">Join Support Server ↗</a> <a class="btn secondary" href="{INVITE}" target="_blank" rel="noopener">Add SECURE ↗</a></div>',s["user"],title)
async def main():
 app=web.Application()
 for p,h in [("/",home),("/login",login),("/callback",callback),("/logout",logout),("/servers",servers),("/dashboard",dashboard),("/commands",commands_page)]:app.router.add_get(p,h)
 app.router.add_get("/select/{gid}",select);app.router.add_get("/feature/{key}",feature);app.router.add_post("/feature/{key}/save",savefeature);app.router.add_get("/{which:settings|support}",simple)
 app.router.add_get("/static/style.css",lambda r:web.FileResponse("static/style.css"))
 runner=web.AppRunner(app);await runner.setup();await web.TCPSite(runner,"0.0.0.0",PORT).start();print("Website listening",PORT);await __import__("asyncio").Event().wait()
if __name__=="__main__":__import__("asyncio").run(main())
