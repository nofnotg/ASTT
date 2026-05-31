const state={view:"overview",data:{}};
const endpoints={overview:"/api/health",routes:"/api/routes",journal:"/api/trades",atr:"/api/atr-research",bear:"/api/bear-windows",control:"/api/control-tower"};
const money=v=>Number(v||0).toLocaleString("ko-KR")+" KRW";
const pct=v=>(Number(v||0)).toFixed(2)+"%";
async function load(){
  const [health,account,routes,payload]=await Promise.all([
    fetch("/api/health").then(r=>r.json()),
    fetch("/api/account").then(r=>r.json()),
    fetch("/api/routes").then(r=>r.json()),
    fetch(endpoints[state.view]).then(r=>r.json())
  ]);
  state.data={health:health.data,account:account.data,routes:routes.data,payload:payload.data};
  render();
}
function render(){
  const {health,account,routes,payload}=state.data;
  document.querySelector("#status").textContent=health.live_order_allowed?"Unsafe":"LIVE_NOT_ALLOWED";
  document.querySelector("#status").className=health.live_order_allowed?"status danger":"status";
  document.querySelector("#cards").innerHTML=[
    card("Active Route",account.active_route||routes.active_route),
    card("Equity",money(account.current_equity_krw)),
    card("Open Positions",account.open_positions||0),
    card("Order Safety",health.live_order_endpoints_enabled?"Enabled":"Disabled")
  ].join("");
  document.querySelector("#view-title").textContent=title(state.view);
  document.querySelector("#content").innerHTML=content(state.view,payload);
}
function card(label,value){return `<div class="card"><div class="label">${label}</div><div class="value">${value??"N/A"}</div></div>`}
function title(view){return {overview:"Overview",routes:"Active vs Shadow",journal:"Trade Journal",atr:"ATR Research",bear:"Bear Window Monitor",control:"LLM Control Tower"}[view]}
function content(view,data){
  if(view==="routes") return table(data.rows||[],["scenario","route_status","final_equity_krw","return_pct","mdd_pct","decision"]);
  if(view==="journal") return table(data.rows||[],["decision_time","market","route_id","route_status","entry_price","exit_price","pnl_krw","reason"]);
  if(view==="atr") return `<h3>Coverage</h3>${table([data.coverage||{}],["total_atr_trades","covered_by_1m","covered_by_5m","covered_by_15m","uncovered","best_coverage_pct","decision"])}<h3>Precision</h3>${table([data.precision||{}],["final_atr_decision","reason","shadow_candidate_allowed","active_route_change_applied"])}`;
  if(view==="bear") return table(data.rows||data.window_rows||[],["window","type","active_return","best_non_atr_route","best_atr_route","atr_decision","recommended_action"]);
  if(view==="control") return `<p>${(data.recommendations||[]).join("<br>")}</p>${table((data.risk_flags||[]).map(x=>({risk_flag:x})),["risk_flag"])}`;
  return table([data],["dashboard_ready","paper_runtime_connected","real_order_enabled","live_order_allowed","auto_apply_allowed","decision"]);
}
function table(rows,keys){if(!rows.length)return "<p>No data</p>";return `<div class="wrap"><table><thead><tr>${keys.map(k=>`<th>${k}</th>`).join("")}</tr></thead><tbody>${rows.slice(0,100).map(r=>`<tr>${keys.map(k=>`<td>${fmt(k,r[k])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`}
function fmt(k,v){if(v===undefined||v===null)return "N/A";if(k.includes("krw")||k.includes("equity"))return money(v);if(k.includes("pct")||k.includes("return")||k.includes("mdd")||k.includes("coverage"))return pct(v);return String(v)}
document.querySelectorAll(".side button").forEach(btn=>btn.addEventListener("click",()=>{document.querySelectorAll(".side button").forEach(b=>b.classList.remove("active"));btn.classList.add("active");state.view=btn.dataset.view;load();}));
document.querySelector("#refresh").addEventListener("click",load);
load();setInterval(load,5000);
