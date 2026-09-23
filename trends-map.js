(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('map-data').textContent);
  const $ = id => document.getElementById(id);
  const svg = $('graph'), ns = 'http://www.w3.org/2000/svg';
  const typeNames = {model:'模型 / MODEL', tool:'工具 / TOOL', style:'风格 / STYLE', concept:'概念 / IDEA', topic:'关联话题 / TOPIC'};
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const sum = values => values.reduce((a,b) => a + b, 0);
  const fmt = value => Number(value || 0).toLocaleString('zh-CN');
  let period = 7, filter = 'all', query = '', selected = null, scale = 1, tx = 0, ty = 0;
  let width = 1440, height = 800, mobileLayout = false, pointer = null, moved = false, visible = new Set();
  const nodes = [], edges = [], byId = new Map();
  const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
  let animationFrame = 0, lastFrame = 0, accumulator = 0, quietFrames = 0;
  const add = node => { nodes.push(node); byId.set(node.id, node); return node; };
  for (const keyword of Object.keys(data.series || {})) {
    add({id:'k:'+keyword, key:keyword, name:data.names[keyword] || keyword, type:data.types[keyword] || 'concept', values:data.series[keyword], related:[], tweets:(data.keyword_tweets || {})[keyword] || []});
  }
  const primary = nodes.slice();
  for (const parent of primary) {
    for (const item of (data.keyword_related[parent.key] || []).slice(0,8)) {
      const id = 't:'+item.term.toLowerCase();
      const node = byId.get(id) || add({id, key:item.term, name:data.names[item.term] || item.term, type:'topic', count:0, parents:[]});
      node.count += item.count || 0;
      node.parents.push(parent.id); parent.related.push(id);
      edges.push({source:parent, target:node, count:item.count});
    }
  }
  function el(tag, attrs, text) {
    const node = document.createElementNS(ns, tag);
    for (const [key,value] of Object.entries(attrs || {})) node.setAttribute(key,value);
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function metrics() {
    for (const node of primary) {
      const values = node.values.slice(-period);
      node.total = sum(values); node.last = values.at(-1) || 0;
      const prev = node.values.at(-2);
      node.delta = prev > 0 ? (node.last-prev)/prev*100 : null;
      node.hot = prev !== undefined && node.last > prev;
      node.radius = 12 + Math.sqrt(node.total) * 1.18;
    }
    for (const node of nodes.filter(n=>n.type==='topic')) node.radius = 4 + Math.min(5, Math.sqrt(node.count)/2);
  }
  function layout() {
    const mobile = $('stage').clientWidth < 760;
    mobileLayout=mobile;
    width = mobile ? 760 : $('stage').clientWidth; height = mobile ? 1050 : $('stage').clientHeight;
    svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
    primary.forEach((node,i) => {
      const angle = i/Math.max(primary.length,1)*Math.PI*2 - Math.PI*.65;
      node.x = width*.51 + Math.cos(angle)*width*.30;
      node.y = height*.55 + Math.sin(angle)*height*.23;
      node.anchorX=node.x; node.anchorY=node.y;
    });
    nodes.filter(n=>n.type==='topic').forEach((node,i) => {
      const parents=node.parents.map(id=>byId.get(id));
      const angle=i*2.39996;
      node.x=sum(parents.map(n=>n.x))/parents.length + Math.cos(angle)*100;
      node.y=sum(parents.map(n=>n.y))/parents.length + Math.sin(angle)*95;
      node.anchorX=node.x; node.anchorY=node.y;
    });
    // Deterministic relaxed layout: stable across visits, no animation dependency.
    for(let step=0;step<260;step++) {
      for(let i=0;i<nodes.length;i++) {
        const a=nodes[i];
        for(let j=i+1;j<nodes.length;j++) {
          const b=nodes[j]; let dx=b.x-a.x,dy=b.y-a.y;
          const dist=Math.hypot(dx,dy)||1;
          const gap=a.radius+b.radius+(a.type==='topic'&&b.type==='topic'?31:51);
          if(dist<gap) {const f=(gap-dist)/dist*.23; a.x-=dx*f;a.y-=dy*f;b.x+=dx*f;b.y+=dy*f;}
        }
        a.x+=(a.anchorX-a.x)*.007;a.y+=(a.anchorY-a.y)*.007;
        a.x=Math.max(65,Math.min(width-65,a.x));
        const top = mobile ? 310 : a.x < 380 ? 210 : 95;
        a.y=Math.max(top,Math.min(height-65,a.y));
      }
    }
    for(const node of nodes) {node.vx=0;node.vy=0;node.anchorX=node.x;node.anchorY=node.y;}
    for(const edge of edges) edge.restLength=Math.max(100,Math.min(220,Math.hypot(edge.source.x-edge.target.x,edge.source.y-edge.target.y)*.85));
  }
  // Springs, repulsion and damping run at a fixed 60 Hz on every display.
  // Keep the existing layout as a gentle anchor so clusters remain readable.
  function physicsStep() {
    const active=nodes.filter(node=>visible.has(node.id));
    for(let i=0;i<active.length;i++) {
      const a=active[i];
      for(let j=i+1;j<active.length;j++) {
        const b=active[j];let dx=b.x-a.x,dy=b.y-a.y;
        if(Math.abs(dx)+Math.abs(dy)<.001){dx=.1;dy=.1;}
        const distance=Math.hypot(dx,dy),gap=a.radius+b.radius+28;
        const force=Math.min(2,210/(distance*distance))+Math.max(0,gap-distance)*.075;
        const fx=dx/distance*force,fy=dy/distance*force;
        a.vx-=fx;a.vy-=fy;b.vx+=fx;b.vy+=fy;
      }
    }
    for(const edge of edges) {
      const a=edge.source,b=edge.target;
      if(!visible.has(a.id)||!visible.has(b.id))continue;
      const dx=b.x-a.x,dy=b.y-a.y,distance=Math.hypot(dx,dy)||1;
      const force=(distance-edge.restLength)*.006;
      const fx=dx/distance*force,fy=dy/distance*force;
      a.vx+=fx;a.vy+=fy;b.vx-=fx;b.vy-=fy;
    }
    let speed=0;
    for(const node of active) {
      if(pointer?.node===node){node.vx=0;node.vy=0;continue;}
      const anchor=node.type==='topic'?.003:.008;
      node.vx+=(node.anchorX-node.x)*anchor;
      node.vy+=(node.anchorY-node.y)*anchor;
      const top=mobileLayout?310:node.x<380?210:95;
      node.vx+=(Math.max(55,node.x)-node.x+Math.min(width-55,node.x)-node.x)*.08;
      node.vy+=(Math.max(top,node.y)-node.y+Math.min(height-65,node.y)-node.y)*.08;
      node.vx*=.82;node.vy*=.82;
      const velocity=Math.hypot(node.vx,node.vy);
      if(velocity>10){node.vx*=10/velocity;node.vy*=10/velocity;}
      node.x+=node.vx;node.y+=node.vy;
      speed=Math.max(speed,Math.abs(node.vx),Math.abs(node.vy));
    }
    quietFrames=speed<.035&&!pointer?.node?quietFrames+1:0;
  }
  function animate(time) {
    animationFrame=0;
    if(document.hidden||motionPreference.matches)return;
    accumulator+=lastFrame?Math.min(time-lastFrame,50):1000/60;lastFrame=time;
    while(accumulator>=1000/60){physicsStep();accumulator-=1000/60;}
    positions();
    if(quietFrames<45)animationFrame=requestAnimationFrame(animate);
    else {lastFrame=0;for(const node of nodes){node.vx=0;node.vy=0;}}
  }
  function wake() {
    quietFrames=0;
    if(animationFrame||document.hidden||motionPreference.matches)return;
    lastFrame=0;accumulator=0;animationFrame=requestAnimationFrame(animate);
  }
  function pause() {cancelAnimationFrame(animationFrame);animationFrame=0;lastFrame=0;accumulator=0;}
  document.addEventListener('visibilitychange',()=>document.hidden?pause():wake());
  motionPreference.addEventListener('change',()=>{if(motionPreference.matches){pause();for(const node of nodes){node.vx=0;node.vy=0;}}else wake();});
  function shape(node) {
    const r=node.radius;
    if(node.type==='model'||node.type==='topic') return el('circle',{r,class:'shape'});
    if(node.type==='tool') return el('rect',{x:-r,y:-r,width:r*2,height:r*2,class:'shape'});
    const sides=node.type==='style'?4:6, offset=node.type==='style'?0:Math.PI/6;
    const points=Array.from({length:sides},(_,i)=>`${Math.sin(i/sides*Math.PI*2+offset)*r},${Math.cos(i/sides*Math.PI*2+offset)*r}`).join(' ');
    return el('polygon',{points,class:'shape'});
  }
  function draw() {
    $('nodes').replaceChildren();$('edges').replaceChildren();$('regions').replaceChildren();
    for(const node of primary.filter(n=>n.hot)) {
      const ring=el('ellipse',{cx:node.x,cy:node.y,rx:105,ry:92,class:'region'});
      ring.dataset.parent=node.id;$('regions').append(ring);
    }
    for(const edge of edges) {edge.element=el('line',{class:'edge'});$('edges').append(edge.element);}
    for(const node of nodes) {
      const group=el('g',{class:'node '+(node.type==='topic'?'topic':node.hot?'is-hot':node.last>0?'is-warm':''),role:'button',tabindex:0,'aria-label':`${node.name}，${typeNames[node.type]}，查看详情`});
      group.append(el('circle',{r:Math.max(node.radius+9,15),fill:'transparent'}));
      if(node.hot) group.append(el('circle',{r:node.radius+8,class:'halo'}));
      group.append(shape(node));
      group.append(el('text',{y:node.radius+19,'text-anchor':'middle'},node.name+(node.hot?' ↑':'')));
      group.append(el('title',{},node.key));
      group.addEventListener('click',()=>{if(!moved) select(node.id);});
      group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(node.id);}});
      group.addEventListener('pointerdown',e=>start(e,node));
      node.element=group;$('nodes').append(group);
    }
    positions();applyFilter();
  }
  function positions() {
    for(const node of nodes) node.element.setAttribute('transform',`translate(${node.x},${node.y})`);
    for(const {source:a,target:b,element} of edges) for(const [key,value] of Object.entries({x1:a.x,y1:a.y,x2:b.x,y2:b.y})) element.setAttribute(key,value);
    for(const ring of $('regions').children){const node=byId.get(ring.dataset.parent);ring.setAttribute('cx',node.x);ring.setAttribute('cy',node.y);}
  }
  function applyFilter() {
    visible=new Set(nodes.filter(n=>(filter==='all'||n.type===filter)&&(!query||(n.name+' '+n.key).toLowerCase().includes(query))).map(n=>n.id));
    for(const node of nodes) {node.element.style.display=visible.has(node.id)?'':'none';node.element.classList.toggle('show-label',Boolean(query)||filter!=='all');}
    for(const edge of edges) edge.element.style.display=visible.has(edge.source.id)&&visible.has(edge.target.id)?'':'none';
    for(const ring of $('regions').children) ring.style.display=visible.has(ring.dataset.parent)?'':'none';
    $('node-count').textContent=visible.size;$('hot-count').textContent=primary.filter(n=>n.hot&&visible.has(n.id)).length;
    $('empty').hidden=visible.size>0;
    if(selected&&!visible.has(selected)) closePanel(false);
    wake();
  }
  function select(id) {
    selected=id;const node=byId.get(id);
    const neighbors=new Set([id,...(node.parents||node.related)]);
    for(const n of nodes){n.element.classList.toggle('dim',!neighbors.has(n.id));n.element.classList.toggle('connected',neighbors.has(n.id));n.element.classList.toggle('selected',n.id===id);n.element.setAttribute('aria-pressed',String(n.id===id));}
    for(const edge of edges){const active=edge.source.id===id||edge.target.id===id;edge.element.classList.toggle('active',active);edge.element.classList.toggle('dim',!active);}
    renderPanel(node);$('panel').hidden=false;
  }
  function renderPanel(node) {
    const topic=node.type==='topic', values=(node.values||[]).slice(-period);
    const delta=node.delta===null?'—':`${node.delta>0?'+':''}${Math.round(node.delta)}%`;
    const related=topic?node.parents:node.related;
    const tweets=topic?node.parents.flatMap(id=>byId.get(id).tweets).filter(t=>(t.text||'').toLowerCase().includes(node.key.toLowerCase())):node.tweets;
    const unique=[...new Map(tweets.map(t=>[t.url||t.text,t])).values()].slice(0,6);
    const max=Math.max(1,...values), points=values.map((v,i)=>`${i/Math.max(1,values.length-1)*280},${70-v/max*62}`).join(' ');
    $('panel-content').innerHTML=`<div class="eyebrow">${typeNames[node.type]}</div><h2>${esc(node.name)}</h2><div class="original">${esc(node.key)}</div>`+
      (topic?`<div class="metrics"><div><b>${related.length}</b><span>关联关键词</span></div><div><b>${fmt(node.count)}</b><span>累计共现次数</span></div></div><p class="note">共现次数为整批数据中各关键词关联计数之和，可能包含重复推文。</p>`:
      `<div class="metrics"><div><b>${fmt(node.total)}</b><span>近 ${period} 天提及</span></div><div><b>${fmt(node.last)}</b><span>最新一天</span></div><div><b class="${node.hot?'accent':''}">${delta}</b><span>较前一天</span></div></div><div class="panel-label">MENTIONS / 每日采样提及</div><svg class="spark" viewBox="0 0 280 80" role="img" aria-label="最近${values.length}天提及次数：${values.join('、')}"><path d="M0 74H280" stroke="#454638"/><polyline points="${points}" fill="none" stroke="#ff591d" stroke-width="2"/></svg><div class="spark-labels"><span>${esc(data.dates.slice(-period)[0]||'')}</span><span>${esc(data.dates.at(-1)||'')}</span></div>`)+
      `<div class="panel-label">CONNECTIONS / ${topic?'相关关键词':'关联热词'}</div><div class="chips">${related.map(id=>`<button data-node="${esc(id)}">${esc(byId.get(id).name)} ↗</button>`).join('')||'<span class="note">暂无关联数据</span>'}</div><div class="panel-label">FROM X / 代表性推文</div>`+
      (unique.map(t=>{let url='';try{const parsed=new URL(t.url);if(parsed.protocol==='https:'&&['x.com','twitter.com','www.x.com','www.twitter.com'].includes(parsed.hostname))url=parsed.href;}catch{}return `<article class="tweet"><p>${esc(t.text_cn||t.text_clean||t.text)}</p>${url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">@${esc(t.author_handle||t.author_name||'作者')} · 查看原文 ↗</a>`:''}</article>`;}).join('')||'<p class="note">当前采样中暂无可展示的代表推文。</p>')+
      `<p class="note">采样统计 · 截至 ${esc(data.dates.at(-1)||'暂无数据')}<br>关联热词与推文取自整批采集数据。</p>`;
    for(const button of $('panel-content').querySelectorAll('[data-node]')) button.addEventListener('click',()=>{
      filter='all';query='';$('search').value='';syncFilters();applyFilter();select(button.dataset.node);$('panel').scrollTop=0;
    });
  }
  function closePanel(focus=true) {
    const previous=selected;selected=null;$('panel').hidden=true;
    for(const node of nodes){node.element.classList.remove('dim','selected','connected');node.element.setAttribute('aria-pressed','false');}
    for(const edge of edges) edge.element.classList.remove('dim','active');
    if(focus&&previous)byId.get(previous).element.focus();
  }
  function syncFilters(){for(const button of document.querySelectorAll('[data-filter]'))button.setAttribute('aria-pressed',String(button.dataset.filter===filter));}
  function transform(){ $('scene').setAttribute('transform',`translate(${tx},${ty}) scale(${scale})`);$('zoom-label').textContent=Math.round(scale*100)+'%';}
  function zoom(factor,x=width/2,y=height/2){const next=Math.max(.45,Math.min(3,scale*factor));tx=x-(x-tx)*next/scale;ty=y-(y-ty)*next/scale;scale=next;transform();}
  function point(e){return new DOMPoint(e.clientX,e.clientY).matrixTransform(svg.getScreenCTM().inverse());}
  function start(e,node=null){if(e.button!==0||pointer)return;e.stopPropagation();moved=false;const p=point(e);pointer={id:e.pointerId,node,x:p.x,y:p.y,startX:p.x,startY:p.y};svg.setPointerCapture(e.pointerId);svg.classList.add('dragging');if(node){node.vx=0;node.vy=0;wake();}}
  svg.addEventListener('pointerdown',e=>start(e));
  svg.addEventListener('pointermove',e=>{if(!pointer||pointer.id!==e.pointerId)return;const p=point(e),dx=p.x-pointer.x,dy=p.y-pointer.y;if(Math.hypot(p.x-pointer.startX,p.y-pointer.startY)>4)moved=true;if(moved){if(pointer.node){pointer.node.x+=dx/scale;pointer.node.y+=dy/scale;positions();}else{tx+=dx;ty+=dy;transform();}}pointer.x=p.x;pointer.y=p.y;});
  svg.addEventListener('pointerup',e=>{if(!pointer||pointer.id!==e.pointerId)return;const node=pointer.node;pointer=null;svg.classList.remove('dragging');svg.releasePointerCapture(e.pointerId);if(node)wake();if(!moved&&node)select(node.id);else if(!moved)closePanel(false);});
  function cancelDrag(){pointer=null;svg.classList.remove('dragging');wake();}
  svg.addEventListener('pointercancel',cancelDrag);
  svg.addEventListener('lostpointercapture',()=>{if(pointer)cancelDrag();});
  svg.addEventListener('wheel',e=>{e.preventDefault();const p=point(e);zoom(Math.exp(-e.deltaY*.001),p.x,p.y);},{passive:false});
  $('zoom-in').onclick=()=>zoom(1.2);$('zoom-out').onclick=()=>zoom(1/1.2);
  $('reset').onclick=()=>{scale=1;tx=ty=0;layout();positions();transform();wake();};
  $('close').onclick=()=>closePanel();
  document.querySelectorAll('[data-filter]').forEach(button=>button.onclick=()=>{filter=button.dataset.filter;syncFilters();applyFilter();});
  $('search').addEventListener('input',e=>{query=e.target.value.trim().toLowerCase();applyFilter();});
  $('clear').onclick=()=>{filter='all';query='';$('search').value='';syncFilters();applyFilter();};
  function updatePeriod(){metrics();layout();draw();const dates=data.dates.slice(-period);$('date-range').textContent=dates.length?`${dates[0].slice(5)} — ${dates.at(-1).slice(5)} · UTC`:'暂无数据';if(selected)select(selected);}
  $('range').onchange=e=>{period=Number(e.target.value);updatePeriod();};
  $('updated').textContent='更新 '+(data.updated_at||'未知');
  $('about-date').textContent='最近采集更新：'+(data.updated_at||'未知');
  $('about').onclick=()=>$('about-dialog').showModal();$('close-about').onclick=()=>$('about-dialog').close();
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('about-dialog').open)closePanel();if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('search').focus();}});
  let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{layout();positions();scale=1;tx=ty=0;transform();wake();},120);});
  updatePeriod();
})();
