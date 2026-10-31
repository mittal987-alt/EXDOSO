(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))r(s);new MutationObserver(s=>{for(const i of s)if(i.type==="childList")for(const u of i.addedNodes)u.tagName==="LINK"&&u.rel==="modulepreload"&&r(u)}).observe(document,{childList:!0,subtree:!0});function n(s){const i={};return s.integrity&&(i.integrity=s.integrity),s.referrerPolicy&&(i.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?i.credentials="include":s.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function r(s){if(s.ep)return;s.ep=!0;const i=n(s);fetch(s.href,i)}})();const l="http://127.0.0.1:8000",a={influencers:[],drafts:[],logs:[],filteredInfluencers:[],filteredDrafts:[],currentTab:"influencers-tab",influencerFilter:"all",influencerSearch:"",outreachChannelFilter:"all",outreachStatusFilter:"all",viewMode:"grid",isBackendConnected:!1};document.addEventListener("DOMContentLoaded",()=>{B(),b(),d(),setInterval(b,15e3)});function B(){document.querySelectorAll(".tab-btn").forEach(n=>{n.addEventListener("click",()=>y(n.dataset.tab))});const t=document.getElementById("export-dropdown-btn"),e=document.getElementById("export-dropdown-menu");t.addEventListener("click",n=>{n.stopPropagation(),e.classList.toggle("hidden")}),document.addEventListener("click",()=>e.classList.add("hidden")),document.getElementById("export-influencers-btn").addEventListener("click",n=>{n.preventDefault(),f("influencers.csv")}),document.getElementById("export-drafts-btn").addEventListener("click",n=>{n.preventDefault(),f("outreach-messages.csv")}),document.getElementById("export-logs-btn").addEventListener("click",n=>{n.preventDefault(),f("delivery-logs.csv")}),document.getElementById("pipeline-discover-btn").addEventListener("click",$),document.getElementById("open-discovery-modal-btn").addEventListener("click",$),document.getElementById("close-discovery-modal-btn").addEventListener("click",g),document.getElementById("cancel-discovery-btn").addEventListener("click",g),document.getElementById("execute-discovery-btn").addEventListener("click",S),document.getElementById("pipeline-enrich-btn").addEventListener("click",k),document.getElementById("pipeline-qualify-btn").addEventListener("click",C),document.getElementById("pipeline-generate-btn").addEventListener("click",q),document.getElementById("pipeline-send-btn").addEventListener("click",w),document.getElementById("send-pending-studio-btn").addEventListener("click",w),document.getElementById("refresh-logs-btn").addEventListener("click",I),document.getElementById("influencer-search-input").addEventListener("input",n=>{a.influencerSearch=n.target.value.toLowerCase().trim(),p()}),document.querySelectorAll("#influencer-status-filters .filter-pill").forEach(n=>{n.addEventListener("click",()=>{document.querySelectorAll("#influencer-status-filters .filter-pill").forEach(r=>r.classList.remove("active")),n.classList.add("active"),a.influencerFilter=n.dataset.filter,p()})}),document.getElementById("view-mode-grid").addEventListener("click",()=>{a.viewMode="grid",document.getElementById("view-mode-grid").classList.add("active"),document.getElementById("view-mode-table").classList.remove("active"),document.getElementById("influencer-cards-grid").classList.remove("hidden"),document.getElementById("influencer-table-container").classList.add("hidden")}),document.getElementById("view-mode-table").addEventListener("click",()=>{a.viewMode="table",document.getElementById("view-mode-table").classList.add("active"),document.getElementById("view-mode-grid").classList.remove("active"),document.getElementById("influencer-cards-grid").classList.add("hidden"),document.getElementById("influencer-table-container").classList.remove("hidden")}),document.querySelectorAll("#outreach-channel-filters .filter-pill").forEach(n=>{n.addEventListener("click",()=>{document.querySelectorAll("#outreach-channel-filters .filter-pill").forEach(r=>r.classList.remove("active")),n.classList.add("active"),a.outreachChannelFilter=n.dataset.channel,h()})}),document.querySelectorAll("#outreach-status-filters .filter-pill").forEach(n=>{n.addEventListener("click",()=>{document.querySelectorAll("#outreach-status-filters .filter-pill").forEach(r=>r.classList.remove("active")),n.classList.add("active"),a.outreachStatusFilter=n.dataset.status,h()})}),document.getElementById("add-influencer-form").addEventListener("submit",T),document.getElementById("close-details-modal-btn").addEventListener("click",()=>{document.getElementById("details-modal").classList.add("hidden")})}async function b(){const t=document.getElementById("backend-status-badge"),e=document.getElementById("backend-status-text");try{if((await fetch(`${l}/health`)).ok)a.isBackendConnected=!0,t.className="status-pill status-online",e.textContent="Backend Online (127.0.0.1:8000)";else throw new Error}catch{a.isBackendConnected=!1,t.className="status-pill status-offline",e.textContent="Backend Offline"}}async function d(){await Promise.all([_(),x(),I()]),j()}async function _(){try{const t=await fetch(`${l}/api/influencers`);if(!t.ok)throw new Error("Failed to fetch influencers");a.influencers=await t.json(),p()}catch(t){o(`Error fetching creators: ${t.message}`,"error")}}async function x(){try{const t=await fetch(`${l}/api/outreach/drafts`);if(!t.ok)throw new Error("Failed to fetch outreach drafts");const e=await t.json();a.drafts=e.drafts||[],h()}catch(t){o(`Error fetching drafts: ${t.message}`,"error")}}async function I(){try{const t=await fetch(`${l}/api/outreach/delivery-logs`);if(!t.ok)throw new Error("Failed to fetch delivery logs");const e=await t.json();a.logs=e.logs||[],A()}catch(t){o(`Error fetching logs: ${t.message}`,"error")}}function $(){document.getElementById("discovery-modal").classList.remove("hidden")}function g(){document.getElementById("discovery-modal").classList.add("hidden")}async function S(){const t=parseInt(document.getElementById("discovery-target-input").value,10)||10;g(),o(`Running YouTube creator discovery (target: ${t})...`,"info");try{const e=await fetch(`${l}/api/discovery/youtube?target=${t}`,{method:"POST"}),n=await e.json();if(!e.ok)throw new Error(n.detail||"Discovery failed");o(`Discovered ${n.discovered} creators! (${n.inserted} added, ${n.duplicates_skipped} duplicates skipped)`,"success"),await d()}catch(e){o(`Discovery error: ${e.message}`,"error")}}async function k(){o("Enriching stored YouTube influencers with public metadata...","info");try{const t=await fetch(`${l}/api/influencers/enrich`,{method:"POST"}),e=await t.json();if(!t.ok)throw new Error(e.detail||"Enrichment failed");o(`Enrichment complete! ${e.enriched} enriched, ${e.needs_review} flagged for review.`,"success"),await d()}catch(t){o(`Enrichment error: ${t.message}`,"error")}}async function C(){o("Evaluating creators against subscriber & engagement rules...","info");try{const t=await fetch(`${l}/api/influencers/qualify`,{method:"POST"}),e=await t.json();if(!t.ok)throw new Error(e.detail||"Qualification failed");o(`Qualification complete! ${e.qualified} qualified, ${e.rejected} rejected.`,"success"),await d()}catch(t){o(`Qualification error: ${t.message}`,"error")}}async function q(){o("Generating personalized multi-channel outreach drafts...","info");try{const t=await fetch(`${l}/api/outreach/generate`,{method:"POST"}),e=await t.json();if(!t.ok)throw new Error(e.detail||"Outreach generation failed");o(`Generated ${e.drafts_generated} drafts across ${e.qualified_influencers} qualified creators! (${e.existing_drafts_skipped} skipped)`,"success"),await d(),y("outreach-tab")}catch(t){o(`Generation error: ${t.message}`,"error")}}async function D(t){try{const e=await fetch(`${l}/api/outreach/send/${t}`,{method:"POST"}),n=await e.json();if(!e.ok)throw new Error(n.detail||"Send failed");o(`Simulated send succeeded for message #${t}!`,"success"),await d()}catch(e){o(`Send error: ${e.message}`,"error")}}async function w(){o("Simulating dispatch for all pending outreach messages...","info");try{const t=await fetch(`${l}/api/outreach/send-pending`,{method:"POST"}),e=await t.json();if(!t.ok)throw new Error(e.detail||"Batch send failed");o(`Simulated send complete! ${e.sent} sent, ${e.failed} failed.`,"success"),await d()}catch(t){o(`Batch send error: ${t.message}`,"error")}}async function T(t){t.preventDefault();const e={name:document.getElementById("form-name").value.trim(),platform:document.getElementById("form-platform").value,profile_url:document.getElementById("form-profile-url").value.trim(),source_url:document.getElementById("form-source-url").value.trim()||null,follower_count:parseInt(document.getElementById("form-followers").value,10)||null,engagement_rate:parseFloat(document.getElementById("form-engagement").value)||null,category:document.getElementById("form-category").value.trim()||null,geography:document.getElementById("form-geography").value.trim()||null,contact_email:document.getElementById("form-email").value.trim()||null,website:document.getElementById("form-website").value.trim()||null,content_themes:document.getElementById("form-themes").value.trim()||null};try{const n=await fetch(`${l}/api/influencers`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(e)}),r=await n.json();if(!n.ok)throw new Error(r.detail||"Failed to add influencer");o(`Influencer "${e.name}" successfully created!`,"success"),document.getElementById("add-influencer-form").reset(),await d(),y("influencers-tab")}catch(n){o(`Error creating influencer: ${n.message}`,"error")}}function f(t){const e=`${l}/api/exports/${t}`;window.open(e,"_blank"),o(`Downloading ${t}...`,"info")}function j(){const t=a.influencers.length,e=a.influencers.filter(i=>i.qualification_status==="Qualified").length,n=a.drafts.length,r=a.logs.filter(i=>i.status==="Sent"||i.status==="sent").length;document.getElementById("stat-total-val").textContent=t.toLocaleString(),document.getElementById("stat-qualified-val").textContent=e.toLocaleString();const s=t>0?(e/t*100).toFixed(1):0;document.getElementById("stat-qualified-pct").textContent=`${s}% conversion rate`,document.getElementById("stat-drafts-val").textContent=n.toLocaleString(),document.getElementById("stat-sent-val").textContent=r.toLocaleString(),document.getElementById("tab-influencers-count").textContent=t,document.getElementById("tab-outreach-count").textContent=n,document.getElementById("tab-logs-count").textContent=a.logs.length}function p(){a.filteredInfluencers=a.influencers.filter(t=>{if(a.influencerFilter!=="all"&&t.qualification_status!==a.influencerFilter)return!1;if(a.influencerSearch){const e=a.influencerSearch,n=(t.name||"").toLowerCase(),r=(t.category||"").toLowerCase(),s=(t.content_themes||"").toLowerCase();return n.includes(e)||r.includes(e)||s.includes(e)}return!0}),F(),N()}function F(){const t=document.getElementById("influencer-cards-grid");if(a.filteredInfluencers.length===0){t.innerHTML=`
      <div class="empty-state">
        <p>No creators match the current filter or search criteria.</p>
      </div>
    `;return}t.innerHTML=a.filteredInfluencers.map(e=>{const n=(e.name||"C")[0].toUpperCase(),r=v(e.qualification_status),s=E(e.follower_count),i=e.engagement_rate!=null?`${e.engagement_rate}%`:"N/A",u=e.category||"General Fitness",L=(e.content_themes||"").split(",").slice(0,3).map(m=>m.trim()).filter(Boolean).map(m=>`<span class="theme-pill">${c(m)}</span>`).join("");return`
        <div class="creator-card" id="creator-card-${e.id}">
          <div class="creator-card-header">
            <div class="creator-avatar">${n}</div>
            <div class="creator-headline">
              <h4 class="creator-name" title="${c(e.name)}">${c(e.name)}</h4>
              <a href="${c(e.profile_url)}" target="_blank" rel="noopener noreferrer" class="creator-platform-link">
                ${e.platform} Profile ↗
              </a>
            </div>
            <span class="status-tag ${r}">${e.qualification_status||"Pending"}</span>
          </div>

          <div class="creator-metrics-row">
            <div class="metric-item">
              <span class="metric-name">Subscribers</span>
              <span class="metric-num">${s}</span>
            </div>
            <div class="metric-item">
              <span class="metric-name">Engagement</span>
              <span class="metric-num">${i}</span>
            </div>
          </div>

          <div class="creator-themes-tags">
            <span class="theme-pill" style="border-color: rgba(99,102,241,0.3); color: #a5b4fc;">${c(u)}</span>
            ${L}
          </div>

          <div class="creator-card-footer">
            <span style="font-size: 12px; color: var(--text-subtle);">
              ${e.contact_email?`✉️ ${c(e.contact_email)}`:"No email found"}
            </span>
            <button class="btn btn-secondary btn-sm" onclick="window.viewInfluencerDetails(${e.id})">
              Details
            </button>
          </div>
        </div>
      `}).join("")}function N(){const t=document.getElementById("influencer-table-body");if(a.filteredInfluencers.length===0){t.innerHTML='<tr><td colspan="7" class="text-center py-4">No creators found.</td></tr>';return}t.innerHTML=a.filteredInfluencers.map(e=>{const n=v(e.qualification_status);return`
        <tr>
          <td>
            <strong>${c(e.name)}</strong><br />
            <a href="${c(e.profile_url)}" target="_blank" style="font-size: 12px; color: var(--accent-cyan);">
              ${e.platform}
            </a>
          </td>
          <td>${E(e.follower_count)}</td>
          <td>${e.engagement_rate!=null?`${e.engagement_rate}%`:"N/A"}</td>
          <td>${c(e.category||"N/A")}</td>
          <td>${c(e.contact_email||"Not Found")}</td>
          <td><span class="status-tag ${n}">${e.qualification_status||"Pending"}</span></td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="window.viewInfluencerDetails(${e.id})">
              Details
            </button>
          </td>
        </tr>
      `}).join("")}function h(){a.filteredDrafts=a.drafts.filter(e=>!(a.outreachChannelFilter!=="all"&&e.channel!==a.outreachChannelFilter||a.outreachStatusFilter!=="all"&&e.status!==a.outreachStatusFilter));const t=document.getElementById("outreach-cards-grid");if(a.filteredDrafts.length===0){t.innerHTML=`
      <div class="empty-state">
        <p>No outreach drafts generated yet. Run Stage 4 in the pipeline to generate copies!</p>
      </div>
    `;return}t.innerHTML=a.filteredDrafts.map(e=>{const n=e.channel==="Email",r=n?"channel-email":"channel-instagram",s=n?"✉️":"💬",i=e.status==="Sent";return`
        <div class="outreach-card" id="draft-card-${e.id}">
          <div class="outreach-header">
            <span class="channel-badge ${r}">${s} ${e.channel}</span>
            <div style="display: flex; gap: 8px; align-items: center;">
              <span class="word-count-badge">${e.word_count} words</span>
              <span class="status-tag ${i?"tag-qualified":"tag-pending"}">${e.status}</span>
            </div>
          </div>

          ${e.subject?`<div class="outreach-subject">Subject: ${c(e.subject)}</div>`:""}

          <div class="outreach-message-body">${c(e.message)}</div>

          <div class="outreach-footer">
            <span style="font-size: 12px; color: var(--text-subtle);">
              Influencer ID #${e.influencer_id}
            </span>
            ${i?'<button class="btn btn-secondary btn-sm" disabled>Sent ✓</button>':`<button class="btn btn-primary btn-sm" onclick="window.sendSingleMessage(${e.id})">
                    Simulate Send
                  </button>`}
          </div>
        </div>
      `}).join("")}function A(){const t=document.getElementById("logs-table-body");if(a.logs.length===0){t.innerHTML='<tr><td colspan="6" class="text-center py-4">No delivery audit logs recorded yet.</td></tr>';return}t.innerHTML=a.logs.map(e=>{const n=new Date(e.created_at).toLocaleString();return`
        <tr>
          <td>#${e.id}</td>
          <td>#${e.outreach_message_id}</td>
          <td><code>${c(e.event)}</code></td>
          <td><span class="status-tag tag-qualified">${c(e.status)}</span></td>
          <td style="max-width: 320px; font-size: 12.5px;">${c(e.details||"")}</td>
          <td style="font-size: 12px; color: var(--text-subtle);">${n}</td>
        </tr>
      `}).join("")}window.viewInfluencerDetails=function(t){const e=a.influencers.find(r=>r.id===t);if(!e)return;const n=document.getElementById("details-modal-body");document.getElementById("details-modal-name").textContent=`${e.name} — Full Profile`,n.innerHTML=`
    <div style="display: flex; flex-direction: column; gap: 16px;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span class="status-tag ${v(e.qualification_status)}">${e.qualification_status||"Pending"}</span>
        <a href="${c(e.profile_url)}" target="_blank" class="btn btn-outline-cyan btn-sm">
          Open YouTube Channel ↗
        </a>
      </div>

      <div class="creator-metrics-row">
        <div class="metric-item">
          <span class="metric-name">Subscribers</span>
          <span class="metric-num">${E(e.follower_count)}</span>
        </div>
        <div class="metric-item">
          <span class="metric-name">Engagement Rate</span>
          <span class="metric-num">${e.engagement_rate!=null?`${e.engagement_rate}%`:"N/A"}</span>
        </div>
      </div>

      <div style="background: rgba(13,18,31,0.6); padding: 14px; border-radius: var(--radius-md); border: 1px solid var(--border-color); font-size: 13.5px;">
        <p><strong>Category:</strong> ${c(e.category||"N/A")}</p>
        <p class="mt-4"><strong>Geography:</strong> ${c(e.geography||"N/A")}</p>
        <p class="mt-4"><strong>Contact Email:</strong> ${c(e.contact_email||"Not Found")}</p>
        <p class="mt-4"><strong>Website / Socials:</strong> ${e.website?`<a href="${c(e.website)}" target="_blank" style="color: var(--accent-cyan);">${c(e.website)}</a>`:"Not Found"}</p>
        <p class="mt-4"><strong>Detected Themes:</strong> ${c(e.content_themes||"None")}</p>
        ${e.rejection_reasons?`<div class="mt-4" style="padding: 10px; background: rgba(244,63,94,0.1); border-left: 3px solid #f43f5e; color: #fecdd3; border-radius: 4px;">
                <strong>Rejection Reason:</strong> ${c(e.rejection_reasons)}
              </div>`:""}
      </div>
    </div>
  `,document.getElementById("details-modal").classList.remove("hidden")};window.sendSingleMessage=function(t){D(t)};function y(t){document.querySelectorAll(".app-tabs-nav .tab-btn").forEach(e=>{e.classList.toggle("active",e.dataset.tab===t)}),document.querySelectorAll(".tab-pane").forEach(e=>{e.classList.toggle("hidden",e.id!==t),e.classList.toggle("active",e.id===t)}),a.currentTab=t}function v(t){return t==="Qualified"?"tag-qualified":t==="Rejected"?"tag-rejected":"tag-pending"}function E(t){return t==null?"N/A":t>=1e6?`${(t/1e6).toFixed(1)}M`:t>=1e3?`${(t/1e3).toFixed(1)}K`:t.toString()}function c(t){return t?t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;"):""}function o(t,e="info"){const n=document.getElementById("toast-container"),r=document.createElement("div");r.className=`toast toast-${e}`;const s=e==="success"?"✅":e==="error"?"❌":"ℹ️";r.innerHTML=`
    <span class="toast-icon">${s}</span>
    <span class="toast-message">${c(t)}</span>
  `,n.appendChild(r),setTimeout(()=>{r.style.opacity="0",r.style.transform="translateX(100%)",r.style.transition="all 0.3s ease",setTimeout(()=>r.remove(),300)},4e3)}
