"use strict";
const $ = (id) => document.getElementById(id);
const tools = {
  classify: {nav:"Review a report",title:"What's happening?",step:"01 / UNDERSTAND",icon:"◈",description:"Describe a problem in your neighborhood. We'll help make it clear.",button:"Review report",empty:"Your report's category, summary, and suggested priority will appear here."},
  match: {nav:"Compare reports",title:"One issue, or two?",step:"02 / BRING TOGETHER",icon:"⧉",description:"Compare a new report with an existing issue. Nearby doesn't always mean the same.",button:"Compare reports",empty:"A suggested match decision will appear here. No reports will be merged."},
  agency: {nav:"Agency draft",title:"Make the signal clear.",step:"03 / PREPARE A RESPONSE",icon:"✉",description:"Bring the details together in one message for the responsible agency.",button:"Prepare draft",empty:"Your consolidated agency message will appear here. Nothing is sent."},
  resolution: {nav:"Resolution notice",title:"Close the loop.",step:"04 / KEEP PEOPLE INFORMED",icon:"✓",description:"Thank the people who reported an issue and share its recorded resolution.",button:"Prepare notice",empty:"Your resident update will appear here. Nothing is delivered."}
};
const sampleIssue = {category:"illegal_dumping",summary:"A discarded mattress is blocking the sidewalk at 16th and Mission.",location:{lat:37.7652,lon:-122.4195},report_count:10,status:"open",created_at:"2026-11-03T17:00:00Z",updated_at:"2026-11-03T18:00:00Z"};
const samples = {
  classify: {input:"There's a mattress blocking the sidewalk at 16th and Mission. It's been there since yesterday.",result:{category:"illegal_dumping",summary:"A discarded mattress is blocking the sidewalk at 16th and Mission.",severity:3}},
  match: {input:"Someone spray painted the bus shelter near 16th and Mission.",existing:"Graffiti on the brick wall of a building near 16th and Mission.",result:{same_issue:false}},
  agency: {result:{draft:"Subject: Review requested — 10 reports of a blocked sidewalk at 16th and Mission\n\nDear San Francisco Public Works team,\n\nSaFe has grouped 10 reports describing a discarded mattress blocking the sidewalk at 16th and Mission (37.7652, -122.4195). The issue is categorized as illegal dumping.\n\nThe first report was recorded on November 3, 2026 at 17:00 UTC, and the latest at 18:00 UTC. This count reflects reports, not independently verified residents.\n\nPlease review the issue and advise on next steps. Thank you for helping keep our neighborhood accessible.\n\nSaFe neighborhood reporting prototype"}},
  resolution: {result:{draft:"Thank you for reporting the discarded mattress at 16th and Mission. This issue has been marked resolved in SaFe. Your report helped build a clearer picture of the problem, and we appreciate your contribution to the neighborhood."}}
};
let active = "classify", busy = false, copyText = "";
function showError(message) { $("error").textContent=message; $("error").hidden=false; }
function setBusy(value) {
  busy=value; $("submit-button").disabled=value; $("sample-button").disabled=value;
  document.querySelectorAll("[data-tool]").forEach(b=>b.disabled=value);
  document.querySelectorAll("textarea,input,#load-issue").forEach(field=>field.disabled=value);
  $("result").setAttribute("aria-busy",String(value)); $("submit-button").textContent=value?"Working on it…":tools[active].button+" →";
}
function resetOutput() { $("error").hidden=true; $("empty-state").hidden=false; $("empty-state").querySelector("p").textContent=tools[active].empty; $("result").hidden=true; $("result").replaceChildren(); $("result-badge").textContent="READY WHEN YOU ARE"; $("result-badge").className="pill"; $("copy-button").hidden=true; copyText=""; }
function loadIssue() { const issue={...sampleIssue}; if(active==="resolution"){issue.status="resolved";issue.resolution="The issue has been marked resolved.";} $("issue").value=JSON.stringify(issue,null,2); $("agency").value="San Francisco Public Works"; }
function activate(key) {
  if(busy)return; active=key; const t=tools[key];
  document.querySelectorAll("[data-tool]").forEach(button=>{const selected=button.dataset.tool===key;button.classList.toggle("active",selected);if(selected)button.setAttribute("aria-current","page");else button.removeAttribute("aria-current");});
  for(const [id,value] of Object.entries({"breadcrumb-tool":t.nav,"tool-title":t.title,"step-label":t.step,"tool-icon":t.icon,"tool-description":t.description}))$(id).textContent=value;
  const isDraft=["agency","resolution"].includes(key); $("report-fields").hidden=isDraft; $("compare-fields").hidden=key!=="match"; $("draft-fields").hidden=!isDraft; $("agency-field").hidden=key!=="agency";
  $("report").required=!isDraft; $("existing").required=key==="match"; $("issue").required=isDraft; $("agency").required=key==="agency";
  $("form-footnote").textContent="Details are sent to Mistral only when you choose "+t.button+".";
  $("output-note").textContent=key==="classify"?"Analysis is a suggestion. It doesn't verify an incident.":key==="match"?"Text comparison only. Location filtering belongs to the shared pipeline.":"Draft only. Review before any future delivery.";
  if(isDraft)loadIssue(); setBusy(false);resetOutput();
}
function element(tag,text,className){const node=document.createElement(tag);node.textContent=text;if(className)node.className=className;return node;}
function render(result,mode) {
  $("empty-state").hidden=true;const root=$("result");root.hidden=false;root.replaceChildren();
  $("result-badge").textContent=mode==="sample"?"SAMPLE PREVIEW":"LIVE MISTRAL";$("result-badge").className="pill "+mode;
  if(mode==="sample")root.append(element("p","Illustrative fixture, not AI output. This preview uses the sample details shown in the form.","sample-note"));
  if(active==="classify"){
    root.append(element("span",result.category.replaceAll("_"," "),"category-chip"),element("p",result.summary,"result-summary"));
    const row=element("div","","result-row");row.append(element("span","Suggested priority"));const severity=element("div","","severity");for(let i=1;i<=5;i++){const bar=element("i","");if(i<=result.severity)bar.className="on";severity.append(bar);}severity.append(element("span",result.severity+" / 5"));row.append(severity);root.append(row,element("p","A triage suggestion based on the description. It is not a verified assessment of risk.","result-help"));
  } else if(active==="match"){
    root.append(element("span",result.same_issue?"⧉":"↔","match-symbol"),element("p",result.same_issue?"These may describe the same issue.":"Keep these reports separate.","result-summary"),element("p",result.same_issue?"Mistral suggests the descriptions refer to the same problem. The shared pipeline must also verify category, distance, and time.":"The descriptions do not clearly identify the same problem. This tool hasn't created or merged any records.","result-help"));
  } else root.append(element("p",result.draft,"draft-text"));
  copyText=result.draft||JSON.stringify(result,null,2);$("copy-button").hidden=false;$("copy-button").textContent="Copy result";
}
document.querySelectorAll("[data-tool]").forEach(b=>b.addEventListener("click",()=>activate(b.dataset.tool)));
$("report").addEventListener("input",()=>{$("character-count").textContent=$("report").value.length.toLocaleString()+" / 6,000";resetOutput();});
for(const id of ["existing","agency","issue"])$(id).addEventListener("input",resetOutput);
$("load-issue").addEventListener("click",()=>{loadIssue();resetOutput();});
$("sample-button").addEventListener("click",()=>{
  $("error").hidden=true;
  if(active==="classify"||active==="match"){$("report").value=samples[active].input;$("report").dispatchEvent(new Event("input"));if(active==="match")$("existing").value=samples.match.existing;}else loadIssue();
  render(samples[active].result,"sample");
});
$("tool-form").addEventListener("submit",async(event)=>{
  event.preventDefault();if(busy)return;let payload;
  try {if(active==="classify")payload={text:$("report").value};else if(active==="match")payload={text:$("report").value,existing_summary:$("existing").value};else payload={issue:JSON.parse($("issue").value),agency:$("agency").value};}
  catch{showError("Issue details must be valid JSON. Use example details as a starting point.");return;}
  resetOutput();setBusy(true);$("empty-state").hidden=true;$("result").hidden=false;$("result").append(element("p","Preparing your result…","result-help"),element("div","","loading-line"),element("div","","loading-line short"));$("result-badge").textContent="WORKING";
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),125000);
  try{const response=await fetch("/api/"+active,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload),signal:controller.signal});const data=await response.json();if(!response.ok)throw new Error(data.error||"The request could not be completed.");render(data.result,data.mode);}
  catch(error){resetOutput();showError(error.name==="AbortError"?"The request timed out. Please try again.":error.message);}
  finally{clearTimeout(timeout);setBusy(false);}
});
$("copy-button").addEventListener("click",async()=>{try{await navigator.clipboard.writeText(copyText);$("copy-button").textContent="Copied ✓";}catch{showError("Clipboard isn't available. Select the result text to copy it.");}});
async function connection(){try{const response=await fetch("/api/config");if(!response.ok)throw new Error();const c=await response.json();$("connection-label").textContent=c.configured?"Live analysis configured":"Explore with sample previews";$("connection-detail").textContent=c.configured?"Requests use your server-side Mistral key.":"Add a server-side API key for live analysis.";$("connection-dot").classList.toggle("live",c.configured);}catch{$("connection-label").textContent="Connection unavailable";$("connection-detail").textContent="Start the local SaFe server to use live analysis.";}}
activate("classify");connection();
