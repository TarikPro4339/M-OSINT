'use strict';
const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];
const categories = [
  ['Ağ & IP istihbaratı','IP, DNS ve ağ görünürlüğü','01'],
  ['Alan adı & web','Web yüzeyini anlamlandır','02'],
  ['Kullanıcı adı & sosyal','Genel profiller, açık kapsam','03'],
  ['E-posta & telefon','Biçim, plan ve kaynak analizi','04'],
  ['Dosya & metadata','Dosyanın anlattıklarını oku','05'],
  ['Kodlama & kripto','Veriyi çöz, biçimi anla','06'],
  ['Arama & raporlama','Bulguları bağlama yerleştir','07']
];
const FEATURE_LIMIT=111;
const CREATOR='TarikPro43391';
const labels={functional:'Çalışıyor',partial:'Kısmi kapsam',integration:'Entegrasyon gerekli'};
const glyphs=['⌁','◎','@','✉','▱','</>','⌕'];
const examples={1:'8.8.8.8',2:'8.8.8.8',5:'example.com',6:'example.com',10:'example.com',11:'192.168.10.22/24',12:'2001:db8::1',13:'203.0.113.0/24',16:'example.com',17:'example.com',18:'example.com',19:'example.com',20:'https://example.com',21:'https://example.com',22:'example.com',23:'example.com',24:'https://example.com',25:'https://example.com',26:'https://example.com',27:'https://example.com',29:'https://example.com',31:'octocat',32:'octocat',34:'name@example.com',35:'175928847299117063',36:'davet-kodu',37:'76561197960265729',39:'<a href="https://linktr.ee/example">Profil bağlantıları</a>',40:'Ada, Lovelace, 1815',41:'Example',42:'https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw',43:'telegram',46:'name@example.com',47:'example.com',48:'example@yopmail.com',49:'Ada, Lovelace, example.com',51:'From: example@example.com\nAuthentication-Results: mail.example.com; spf=pass\nReceived: from mail.example.com ([203.0.113.10]) by mx.example.net; Tue, 01 Jan 2030 00:00:00 +0000',53:'+905551234567',54:'+905551234567',55:'+905551234567',56:'+905551234567',57:'+905551234567',58:'+905551234567',69:'https://example.com/image.jpg',73:'https://example.com',76:'hello, friend.',77:'M-OSINT',78:'hello & world',79:'uryyb, sevraq.',80:'eyJhbGciOiJub25lIn0.eyJzdWIiOiJkZW1vIn0.',81:'d41d8cd98f00b204e9800998ecf8427e',82:'1730680000',83:'Contact: analyst@example.com | https://example.com | 203.0.113.10',84:'https://example.com/path',85:'HELLO FRIEND',86:'xn--bcher-kva.de',87:'1BoatSLRHtKNngkdXEeobR76b53LETtpyT',88:'36383635366336633666',89:'example.com',90:'your-org',91:'example.com',92:'https://example.com',94:'TC-JAA',95:'TR'};
Object.assign(examples,{111:'user@example.com',50:'account-exists@hibp-integration-tests.com',106:'https://example.com/report?id=42&utm_source=newsletter&fbclid=demo',107:'203.0.113.10\nexample.com\n---\nexample.com\n198.51.100.2',108:'İletişim: analyst@example.com',109:'2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824',110:'ilk satır\neski bulgu\n---\nilk satır\nyeni bulgu'});
const codecModes={76:['base64_encode','base64_decode','base32_encode','base32_decode','base58_encode','base58_decode'],77:['hex_encode','hex_decode','binary_encode','binary_decode'],78:['url_encode','url_decode','html_encode','html_decode'],82:['seconds','milliseconds'],84:['defang','refang'],85:['morse_encode','morse_decode','decimal_encode','decimal_decode']};
const modeLabels={seconds:'Unix saniye / ISO tarih',milliseconds:'Unix milisaniye / ISO tarih',defang:'Zırhla (defang)',refang:'Eski haline getir (refang)'};
let token='',appVersion='',features=[],selectedCategory=null,currentView='overview',activeTool=null,running=false,currentResult=null;
let entries=[],history=[],persist=false,toastTimer,caseTitle='İsimsiz araştırma';
let settingsBusy=false;
const storageKey='mosint.case.v1';

function el(tag,props={},...children){const node=document.createElement(tag);for(const [k,v] of Object.entries(props)){if(k==='class')node.className=v;else if(k==='text')node.textContent=v;else if(k.startsWith('on'))node.addEventListener(k.slice(2),v);else node.setAttribute(k,v);}for(const child of children.flat()){if(child!==null&&child!==undefined)node.append(child instanceof Node?child:document.createTextNode(String(child)));}return node;}
function replace(node,...items){node.replaceChildren(...items.flat());}
function toast(message){$$('.dialog-toast').forEach(n=>n.remove());const opened=$('dialog[open]');if(opened){const notice=el('div',{class:'dialog-toast',role:'status','aria-live':'polite',text:message});opened.insertBefore(notice,opened.children[1]);$('#toast').hidden=true;}else{$('#toast').textContent=message;$('#toast').hidden=false;}clearTimeout(toastTimer);toastTimer=setTimeout(()=>{$('#toast').hidden=true;$$('.dialog-toast').forEach(n=>n.remove());},6000);}
function badge(status){return el('span',{class:'pill '+status,text:labels[status]});}
function safeUrl(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)&&!u.username&&!u.password?u.href:null;}catch{return null;}}
function anchor(label,url){const safe=safeUrl(url);return safe?el('a',{href:safe,target:'_blank',rel:'noopener noreferrer',text:label+' ↗'}):null;}
function pretty(value){return JSON.stringify(value,null,2);}
function setVersion(version){if(typeof version!=='string'||!/^\d+\.\d+\.\d+$/.test(version))throw Error('Sunucu sürüm bilgisi geçersiz.');appVersion=version;$$('[data-app-version]').forEach(node=>node.textContent='v'+appVersion);}
async function api(path,data){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-MOSINT-Token':token},body:JSON.stringify(data)});const value=await r.json();if(!r.ok)throw Error(value.error||'İstek tamamlanamadı.');return value;}
function download(name,content,type='application/json'){const a=el('a',{download:name,href:URL.createObjectURL(new Blob([content],{type}))});a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
function filename(ext){return 'M-OSINT-'+new Date().toISOString().slice(0,10)+'.'+ext;}

function toolCard(f){return el('button',{class:'tool-card',onclick:()=>openTool(f.id)},
  el('div',{class:'tool-card-top'},el('span',{class:'tool-glyph','aria-hidden':'true',text:glyphs[f.category-1]}),el('span',{class:'tool-number',text:'#'+String(f.id).padStart(3,'0')+' ↗'})),
  el('h3',{text:f.name}),el('p',{text:f.note}),el('div',{class:'tool-card-footer'},badge(f.status),el('span',{class:'execution-mode',text:f.network?'AĞ İZNİ':'YEREL / '+(f.kind==='file'?'DOSYA':'ARAÇ')})));
}
function renderCatalog(){const q=$('#search').value.trim().toLocaleLowerCase('tr');const status=$('#statusFilter').value;const found=features.filter(f=>(selectedCategory===null||f.category===selectedCategory)&&(status==='all'||f.status===status)&&(!q||`${f.id} ${String(f.id).padStart(3,'0')} ${f.name} ${f.description} ${f.note}`.toLocaleLowerCase('tr').includes(q)));replace($('#catalogTools'),found.map(toolCard));$('#resultCount').textContent=`${found.length} / ${features.length} özellik`;$('#emptyTools').hidden=found.length>0;$('#catalogTitle').textContent=selectedCategory===null?'Tüm araçlar.':categories[selectedCategory-1][0]+'.';}
function renderDashboard(){const counts={functional:0,partial:0,integration:0};features.forEach(f=>counts[f.status]++);const stats=[['KATALOGDAKİ ARAÇ',features.length,'7 araştırma kategorisi','▦'],['ÇALIŞIYOR',counts.functional,'Belirtilen kapsamda hazır','↗'],['KISMİ KAPSAM',counts.partial,'Sınırları açıkça belirtilmiş','◐'],['ENTEGRASYON',counts.integration,'Paket, anahtar veya adaptör gerekli','⌁']];replace($('#stats'),stats.map(([label,count,note,icon],i)=>el('div',{class:'stat'},el('small',{text:label}),el('strong',{class:i===1?'accent':'',text:count}),el('span',{text:note}),el('i',{class:'stat-icon','aria-hidden':'true',text:icon}))));replace($('#quickTools'),[1,50,111,106,109,110].map(id=>toolCard(features[id-1])));replace($('#categoryNav'),categories.map((c,i)=>el('button',{class:'nav-item',onclick:()=>navigate('catalog',i+1)},el('span',{text:c[2]}),c[0])));replace($('#categoryGrid'),categories.map((c,i)=>{const rows=features.filter(f=>f.category===i+1);return el('button',{class:'category-card',onclick:()=>navigate('catalog',i+1)},el('span',{text:c[2]}),el('div',{},el('strong',{text:c[0]}),el('small',{text:`${rows.length} özellik · ${rows.filter(f=>f.runnable).length} kullanılabilir`})),el('b',{text:'↗'}));}));renderCatalog();}
function navigate(view,category=null){currentView=view;selectedCategory=category;for(const v of ['overview','catalog','case','history'])$('#'+v+'View').hidden=v!==view;$$('#mainNav .nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===view));$$('#categoryNav button').forEach((b,i)=>b.classList.toggle('active',view==='catalog'&&category===i+1));$('#breadcrumb').textContent={overview:'GENEL BAKIŞ',catalog:category?categories[category-1][0].toLocaleUpperCase('tr'):'ARAÇ KÜTÜPHANESİ',case:'VAKA & RAPOR',history:'İŞLEM GEÇMİŞİ'}[view];if(view==='catalog')renderCatalog();if(view==='case')renderCase();if(view==='history')renderHistory();$('.sidebar').classList.remove('open');$('#mobileMenu').setAttribute('aria-expanded','false');window.scrollTo({top:0});}

function openTool(id){activeTool=features[id-1];currentResult=null;const f=activeTool;$('#toolId').textContent=`MODÜL ${String(f.category).padStart(2,'0')} / ÖZELLİK #${String(id).padStart(3,'0')}`;$('#toolTitle').textContent=f.name;$('#toolDescription').textContent=f.description;$('#toolScope').textContent=f.note;replace($('#toolBadges'),badge(f.status));$('#toolText').value=examples[id]||'';$('#toolFile').value='';$('#networkConsent').checked=false;$('#authorization').checked=false;$('#ports').value='80,443';$('#copyResult').disabled=true;$('#modeWrap').hidden=!codecModes[id];replace($('#toolMode'),(codecModes[id]||[]).map(v=>el('option',{value:v,text:modeLabels[v]||v.replace('_encode',' → kodla').replace('_decode',' → çöz').toUpperCase()})));$('#textWrap').hidden=(f.kind==='file'&&id!==109)||(f.kind==='system'&&id!==105)||!f.runnable;$('#fileWrap').hidden=f.kind!=='file'||!f.runnable;$('#fileHint').textContent='Bir dosya seç · en fazla 8 MiB · dış hizmete gönderilmez';$('#toolFile').accept=id===74?'.zip':id===64?'.docx,.xlsx,.pptx':id===63?'.pdf':[61,62,72,75].includes(id)?'image/*':'';$('#networkWrap').hidden=!f.network||!f.runnable;$('#authorizationWrap').hidden=![5,6,10].includes(id);$('#portsWrap').hidden=![5,6,10].includes(id);$('#runTool').hidden=!f.runnable||[100,101,102,103,104].includes(id);$('#runTool').disabled=running;$('#systemAction').hidden=f.kind!=='system';replace($('#systemAction'));if(f.kind==='system'){if(id===105){replace($('#systemAction'),el('label',{text:'Yerel araç'},el('select',{id:'batchTool'},[11,12,13,35,37,40,46,48,49,53,81,82,84,86,87,89,95].map(i=>el('option',{value:i,text:`#${i} ${features[i-1].name}`})))));$('#toolText').value='192.168.1.5/24\n10.1.2.3/16';$('#textWrap').firstChild.textContent='Hedefler · satır başına bir girdi · en fazla 20';$('#fileWrap').hidden=false;$('#fileHint').textContent='İsteğe bağlı .txt hedef listesi · en fazla 64 KiB';$('#toolFile').accept='.txt,text/plain';}else if(id>=100){const label=id===103?'Bağlantı ayarlarını aç':id===104?'İşlem geçmişine git':'Vaka ve rapor ekranını aç';$('#systemAction').append(el('button',{type:'button',class:'primary',text:label,onclick:()=>{$('#toolDialog').close();id===103?openSettings():navigate(id===104?'history':'case');}}));}}else{$('#textWrap').firstChild.textContent=id===109?'Beklenen SHA-256 (64 karakter)':'Girdi';}if([50,111].includes(id)&&!f.runnable){$('#systemAction').hidden=false;$('#systemAction').append(el('button',{type:'button',class:'primary',text:'Bağlantıyı yapılandır ↗',onclick:()=>{$('#toolDialog').close();openSettings();}}));}replace($('#toolOutput'),el('div',{class:'empty-output'},el('span',{text:f.runnable?'⌁':'⊙'}),el('p',{text:f.runnable?'Bir soru, bir başlangıç.':'Entegrasyon gerekli.'}),el('small',{text:f.runnable?'Sonuçlar burada görünecek.':f.requirement||'Kapsam açıklamasını inceleyin.'})));$('#toolDialog').showModal();}

function outputResult(value){currentResult=value;$('#copyResult').disabled=false;const result=value.result||{};const output=$('#toolOutput');replace(output,el('p',{class:'output-meta',text:`[OK] #${value.feature_id} · ${new Date(value.timestamp).toLocaleString('tr-TR')}\n${value.scope}`}));const collected=[];function findLinks(obj,depth=0){if(depth>4||!obj||typeof obj!=='object')return;if(Array.isArray(obj.links))for(const link of obj.links)if(link&&typeof link.url==='string')collected.push(link);for(const [key,child]of Object.entries(obj))if(key!=='links')findLinks(child,depth+1);}findLinks(result);if(result.download){const d=result.download;output.append(el('button',{class:'primary',text:'Temizlenmiş görseli indir ↓',onclick:()=>{const bytes=Uint8Array.from(atob(d.base64),c=>c.charCodeAt(0));download('metadata-clean.png',bytes,'image/png');}}));}for(const item of collected.slice(0,100)){const a=anchor(String(item.label||item.url),item.url);if(a)output.append(a);}const visible=structuredClone(result);if(visible.download)visible.download={name:visible.download.name,mime:visible.download.mime,note:'İndirmek için yukarıdaki düğmeyi kullanın. Dosya vaka içine kaydedilmez.'};output.append(el('pre',{text:pretty(visible)}));}
function addHistory(id,name,state){const item={id,name,timestamp:new Date().toISOString(),state};history.unshift(item);history=history.slice(0,100);renderHistory();saveLocal();return item;}
function caseSnapshot(value){const entry=structuredClone(value);if(entry.result?.download)entry.result.download={name:entry.result.download.name,note:'Temizlenmiş görsel vaka kaydında tutulmadı.'};const raw=pretty(entry.result);if(raw.length>250000)entry.result={preview:raw.slice(0,120000),note:'Vaka kaydı boyut sınırı nedeniyle kısaltıldı; tam çıktı analiz penceresinde görülebilir.'};return entry;}
function retain(value){entries.push(caseSnapshot(value));if(entries.length>100)entries.shift();updateCounts();renderCase();saveLocal();}
async function readFile(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(Error('Dosya okunamadı.'));reader.readAsDataURL(file);});}
async function run(event){
  event.preventDefault();
  if(!activeTool||running)return;
  const f=activeTool;
  const file=$('#toolFile').files[0];
  const data={id:f.id,text:$('#toolText').value,mode:$('#toolMode').value,network_consent:$('#networkConsent').checked,authorized:$('#authorization').checked,ports:$('#ports').value};
  if(f.network&&!data.network_consent)return toast('Bu işlem için ağ iznini onaylayın.');
  if([5,6,10].includes(f.id)&&!data.authorized)return toast('Aktif test yetkisini onaylayın.');
  if(f.kind==='file'&&!file)return toast('Analiz için bir dosya seçin.');
  if(f.kind==='file'&&file.size>8*1024*1024)return toast('Dosya en fazla 8 MiB olabilir.');
  if(f.id===105){
    if(file&&file.size>65536)return toast('Hedef listesi en fazla 64 KiB olabilir.');
    data.tool_id=Number($('#batchTool').value);
  }
  // Lock before the first asynchronous file read, so a second submit cannot race it.
  running=true;
  $('#runTool').disabled=true;
  $('#runTool').textContent='İşleniyor…';
  replace($('#toolOutput'),el('p',{class:'output-meta',text:f.network?'[RUN] İzinli ağ isteği çalışıyor…':'[RUN] Yerel analiz çalışıyor…'}));
  const record=addHistory(f.id,f.name,'Çalışıyor');
  try{
    if(f.kind==='file')data.file=await readFile(file);
    if(f.id===105){
      if(file)data.text=await file.text();
      data.targets=data.text.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
      if(data.targets.length<1||data.targets.length>20)throw Error('1–20 hedef kullanın.');
    }
    const value=await api(f.id===105?'/api/batch':'/api/run',data);
    record.state='Tamamlandı';
    retain(value);
    if(activeTool?.id===f.id)outputResult(value);
    toast('Analiz tamamlandı ve oturum vakasına eklendi.');
  }catch(error){
    record.state='Hata';
    if(activeTool?.id===f.id)replace($('#toolOutput'),el('p',{class:'error-output',text:'[ERROR] '+error.message}));
    toast(error.message);
  }finally{
    running=false;
    $('#runTool').disabled=false;
    replace($('#runTool'),'Analizi çalıştır ',el('span',{text:'↗'}));
    renderHistory();
    saveLocal();
  }
}

function updateCounts(){let size=new Blob([JSON.stringify(entries)]).size;while(size>6*1024*1024&&entries.length>1){size-=new Blob([JSON.stringify(entries.shift())]).size+1;}$('#caseCount').textContent=entries.length;$('.terminal-footer').lastChild.textContent=entries.length?` ${entries.length} sonuç oturum vakasında`:' Sistem durumu · Henüz sorgu yapılmadı';}
function renderCase(){replace($('#caseResults'));if(!entries.length){$('#caseResults').append(el('p',{class:'empty',text:'Henüz sonuç yok. Bir aracı çalıştırdığında bulgular bu oturuma eklenir.'}));return;}entries.forEach((entry,index)=>{const details=el('details',{},el('summary',{},el('strong',{text:`#${entry.feature_id} · ${entry.name}`}),el('time',{text:new Date(entry.timestamp).toLocaleString('tr-TR')})),el('p',{class:'small muted',text:entry.scope||''}),el('pre',{text:pretty(entry.result)}));$('#caseResults').append(el('article',{class:'result-card'},el('button',{class:'remove-result ghost danger','aria-label':'Bu sonucu vakadan kaldır',text:'×',onclick:()=>{entries.splice(index,1);updateCounts();renderCase();saveLocal();}}),details));});}
function renderHistory(){replace($('#historyList'),history.length?history.map(item=>el('div',{class:'history-row'},el('time',{text:new Date(item.timestamp).toLocaleString('tr-TR')}),el('span',{text:`#${item.id} ${item.name}`}),el('span',{class:item.state==='Hata'?'danger':'accent',text:item.state}))):el('p',{class:'empty',text:'Bu oturumda henüz işlem yapılmadı.'}));}
function saveLocal(){if(!persist)return;try{localStorage.setItem(storageKey,JSON.stringify({schema:'mosint.case.v1',name:caseTitle,entries,history,persist:true}));}catch{toast('Tarayıcı depolaması dolu veya kullanılamıyor. Vakayı dosya olarak kaydet.');}}
function restore(){try{const saved=localStorage.getItem(storageKey);if(saved){const value=validateCase(JSON.parse(saved));entries=value.entries;history=Array.isArray(value.history)?value.history.filter(h=>h&&typeof h.name==='string'&&typeof h.timestamp==='string'&&typeof h.state==='string').slice(0,100):[];caseTitle=value.name;persist=true;}}catch{toast('Kaydedilmiş vaka okunamadı; boş oturum açıldı.');}$('#caseName').value=caseTitle;$('#persistData').checked=persist;$('#persistenceState').textContent=persist?'browser / opt-in':'off';updateCounts();}
function validateCase(value){if(!value||value.schema!=='mosint.case.v1'||!Array.isArray(value.entries)||value.entries.length>100||typeof value.name!=='string'||value.name.length>100)throw Error('Geçerli M-OSINT v1 vaka dosyası gerekli.');for(const r of value.entries)if(!r||typeof r.name!=='string'||r.name.length>300||typeof r.timestamp!=='string'||!Number.isInteger(r.feature_id)||r.feature_id<1||r.feature_id>FEATURE_LIMIT||!r.result||typeof r.result!=='object'||pretty(r.result).length>260000)throw Error('Vaka kaydı biçimi veya boyutu geçersiz.');return value;}
function caseData(){return {schema:'mosint.case.v1',name:caseTitle,exported_at:new Date().toISOString(),entries};}
function clearCurrentCase(){if(running)return toast('Analiz devam ediyor. Vaka temizlemek için tamamlanmasını bekleyin.');if(!entries.length||confirm('Bu oturumdaki tüm sonuçlar silinsin mi?')){entries=[];updateCounts();renderCase();saveLocal();}}
async function importCase(file){
  if(!file)return;
  if(running)return toast('Analiz devam ediyor. Vaka değiştirmek için tamamlanmasını bekleyin.');
  if(file.size>8*1024*1024)return toast('Vaka dosyası en fazla 8 MiB olabilir.');
  try{
    const v=validateCase(JSON.parse(await file.text()));
    if(running)return toast('Analiz devam ediyor. Vaka değiştirmek için tamamlanmasını bekleyin.');
    if(entries.length&&!confirm('Bu oturumdaki vaka, seçilen dosyayla değiştirilecek. Önce mevcut vakayı kaydettiğinden emin misin?'))return;
    entries=v.entries;caseTitle=v.name;$('#caseName').value=caseTitle;
    updateCounts();renderCase();saveLocal();
    toast('Vaka açıldı. İçindeki bulgular otomatik olarak yeniden sorgulanmadı.');
  }catch(e){toast(e.message);}
}
function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function reportBody(){return `<h1>${escapeHtml(caseTitle)}</h1><p>M-OSINT v${escapeHtml(appVersion)} · ${CREATOR} · ${escapeHtml(new Date().toISOString())} · ${entries.length} sonuç</p><p>Bu rapor kaynak verisi ve araç çıktısı içerir. Kapsam sınırlamaları her bulguda belirtilir. Sonuç yokluğu, yokluk kanıtı değildir.</p>`+entries.map(r=>`<article><h2>#${r.feature_id} · ${escapeHtml(r.name)}</h2><p>${escapeHtml(r.timestamp)} · ${escapeHtml(r.scope||'')}</p><pre>${escapeHtml(pretty(r.result))}</pre></article>`).join('');}
function exportData(type){if(!entries.length)return toast('Önce bir analiz sonucu ekle.');if(type==='json')return download(filename('json'),pretty(caseData()));if(type==='txt')return download(filename('txt'),caseTitle+'\n\n'+entries.map(r=>`#${r.feature_id} ${r.name}\n${r.timestamp}\n${r.scope}\n${pretty(r.result)}`).join('\n\n'),'text/plain;charset=utf-8');if(type==='csv'){const cell=value=>{let s=String(value??'');if(/^[=+\-@\t\r\n]/.test(s.trimStart()))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};const rows=[['id','name','timestamp','status','scope','result'],...entries.map(r=>[r.feature_id,r.name,r.timestamp,r.status,r.scope,JSON.stringify(r.result)])];return download(filename('csv'),'\ufeff'+rows.map(row=>row.map(cell).join(',')).join('\r\n'),'text/csv;charset=utf-8');}if(type==='html'){return download(filename('html'),'<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'"><title>M-OSINT Rapor</title><style>body{font:14px/1.6 Arial;max-width:1000px;margin:40px auto;padding:0 24px;color:#142217;background:#f8faf6}article{border-top:1px solid #bac8b5;padding:20px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px}p{color:#52634d}h2{font-size:19px}</style></head><body>'+reportBody()+'</body></html>','text/html;charset=utf-8');}}
function printReport(){if(!entries.length)return toast('Rapor için önce analiz yap.');const print=$('#printArea');replace(print,el('h1',{text:caseTitle}),el('p',{text:`M-OSINT v${appVersion} · ${CREATOR} · ${new Date().toISOString()} · ${entries.length} sonuç`}),el('p',{text:'Kaynak çıktıları doğrulanmış kimlik, konum veya yokluk kanıtı değildir. Her bulgunun kapsamını inceleyin.'}),entries.map(r=>el('article',{},el('h2',{text:`#${r.feature_id} · ${r.name}`}),el('p',{text:`${r.timestamp} · ${r.scope||''}`}),el('pre',{text:pretty(r.result)}))));window.print();}
function openSettings(){$('#oathnetKey').value='';$('#oathnetKeyState').textContent=features[110]?.runnable?'OathNet anahtarı bu oturum için yapılandırılmış. Geçerliliği sorguda denetlenir.':'OathNet API anahtarı henüz yapılandırılmadı.';$('#apiKey').value='';$('#hibpKey').value='';$('#hibpKeyState').textContent=features[49]?.runnable?'HIBP anahtarı bu sunucu oturumu için yapılandırılmış. Geçerliliği sorguda denetlenir.':'HIBP abonelik anahtarı henüz yapılandırılmadı.';$('#settingsDialog').showModal();}
async function refreshCatalog(){
  const response=await fetch('/api/catalog');
  if(!response.ok)throw Error('Araç kataloğu yenilenemedi.');
  const value=await response.json();
  if(!Array.isArray(value.features)||value.features.length!==FEATURE_LIMIT)throw Error('Araç kataloğu eksik veya geçersiz.');
  features=value.features;
  renderDashboard();
}
async function saveProviderKey(provider,value){
  if(settingsBusy)return toast('Bağlantı ayarı güncelleniyor; bitmesini bekleyin.');
  const config={ipinfo:{input:'#apiKey',state:'#keyState',label:'IPinfo'},hibp:{input:'#hibpKey',state:'#hibpKeyState',label:'HIBP'},oathnet:{input:'#oathnetKey',state:'#oathnetKeyState',label:'OathNet'}}[provider];
  if(!config)return;
  if(value&&!/^[\x21-\x7e]{1,256}$/.test(value))return toast('Anahtar en fazla 256 görünür ASCII karakteri olmalı.');
  if(provider==='hibp'&&value&&!/^[0-9a-fA-F]{32}$/.test(value))return toast('HIBP anahtarı 32 onaltılık karakter olmalı.');
  const buttons=['#saveKey','#removeKey','#saveHibpKey','#removeHibpKey','#saveOathnetKey','#removeOathnetKey'].map(selector=>$(selector));
  settingsBusy=true;
  buttons.forEach(button=>button.disabled=true);
  let committed=false;
  try{
    await api('/api/settings',{[provider]:value});
    committed=true;
    $(config.input).value='';
    const message=value?config.label+' anahtarı yalnızca sunucu belleğine uygulandı; geçerlilik ilk sorguda denetlenir.':config.label+' anahtarı silindi; diğer sağlayıcılar etkilenmedi.';
    $(config.state).textContent=message;
    await refreshCatalog();
    toast(message);
  }catch(error){
    const message=committed?'Anahtar ayarı sunucuda uygulandı, ancak katalog yenilenemedi. Sayfayı yenileyin.':error.message;
    $(config.state).textContent=message;
    toast(message);
  }finally{
    settingsBusy=false;
    buttons.forEach(button=>button.disabled=false);
  }
}
async function saveKey(remove=false){return saveProviderKey('ipinfo',remove?'':$('#apiKey').value.trim());}

let bootTimers=[];
function closeIntro(){for(const t of bootTimers)clearTimeout(t);$('#intro').hidden=true;try{sessionStorage.setItem('mosint.intro','seen');}catch{}$('#exploreBtn').focus();}
async function intro(force=false){let seen=false;try{seen=sessionStorage.getItem('mosint.intro')==='seen';}catch{}if(seen&&!force){$('#intro').hidden=true;return;}$('#intro').hidden=false;$('#skipIntro').focus();try{const response=await fetch('/fsociety.ascii');$('#ascii').textContent=await response.text();}catch{$('#ascii').textContent='M-OSINT';}const lines=['[BOOT] Araç kapsamı yükleniyor…','[LOCAL] Telemetri kapalı. Ağ izni bekleniyor.','[READY] Çalışma alanı hazır.'];const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;$('#bootLine').textContent=lines[0];for(const [i,line]of lines.entries())bootTimers.push(setTimeout(()=>$('#bootLine').textContent=line,reduce?0:800*i));$('#intro').onkeydown=e=>{if(e.key==='Escape')closeIntro();if(e.key==='Tab'){e.preventDefault();(document.activeElement===$('#skipIntro')?$('#enterIntro'):$('#skipIntro')).focus();}};}

async function init(){try{const r=await fetch('/api/bootstrap');if(!r.ok)throw Error('Yerel sunucuya bağlanılamadı.');const bootstrap=await r.json();token=bootstrap.token;setVersion(bootstrap.version);features=(await(await fetch('/api/catalog')).json()).features;if(features.length!==FEATURE_LIMIT)throw Error('Özellik kataloğu eksik.');renderDashboard();restore();renderCase();renderHistory();await intro();}catch(e){$('#intro').hidden=true;toast('Başlatılamadı: '+e.message+' Sayfayı yenileyin veya M-OSINT.bat ile yeniden başlatın.');}}
$$('#mainNav button').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.view)));
$('.brand').addEventListener('click',e=>{e.preventDefault();navigate('overview');});
for(const id of ['exploreBtn','allTools','coverageBtn'])$('#'+id).addEventListener('click',()=>navigate('catalog'));
$('#search').addEventListener('input',renderCatalog);$('#statusFilter').addEventListener('change',renderCatalog);$('#clearFilters').onclick=()=>{$('#search').value='';$('#statusFilter').value='all';selectedCategory=null;renderCatalog();};
$('#mobileMenu').onclick=()=>{const isOpen=$('.sidebar').classList.toggle('open');$('#mobileMenu').setAttribute('aria-expanded',String(isOpen));};
$$('.close-dialog').forEach(b=>b.onclick=()=>b.closest('dialog').close());
$$('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const rect=d.getBoundingClientRect();if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)d.close();}}));
$('#toolForm').addEventListener('submit',e=>run(e).catch(error=>toast(error.message)));
$('#copyResult').onclick=async()=>{try{const safe=structuredClone(currentResult);if(safe.result?.download)delete safe.result.download.base64;await navigator.clipboard.writeText(pretty(safe));toast('Sonuç kopyalandı.');}catch{toast('Kopyalama izni alınamadı. Sonuç metnini seçerek kopyalayabilirsin.');}};
$('#saveCase').onclick=()=>download(filename('json'),pretty(caseData()));
$('#importCase').onchange=e=>{importCase(e.target.files[0]);e.target.value='';};
$('#clearCase').onclick=clearCurrentCase;
$('#clearHistory').onclick=()=>{history=[];renderHistory();saveLocal();};
$('#caseName').oninput=e=>{caseTitle=e.target.value;saveLocal();};
$$('[data-export]').forEach(b=>b.onclick=()=>exportData(b.dataset.export));$('#printReport').onclick=printReport;
$('#saveOathnetKey').onclick=()=>saveOathnetKey(false);$('#removeOathnetKey').onclick=()=>saveOathnetKey(true);
$('#saveHibpKey').onclick=()=>saveHibpKey(false);$('#removeHibpKey').onclick=()=>saveHibpKey(true);
$('#settingsBtn').onclick=openSettings;$('#topSettings').onclick=openSettings;$('#saveKey').onclick=()=>saveKey(false);$('#removeKey').onclick=()=>saveKey(true);
$('#persistData').onchange=e=>{persist=e.target.checked;if(persist)saveLocal();else try{localStorage.removeItem(storageKey);}catch{}$('#persistenceState').textContent=persist?'browser / opt-in':'off';toast(persist?'Tarayıcıda hatırlama açıldı.':'Kaydedilen yerel kopya silindi; oturum bellekte devam ediyor.');};
$('#forgetData').onclick=()=>{try{localStorage.removeItem(storageKey);}catch{}persist=false;$('#persistData').checked=false;$('#persistenceState').textContent='off';toast('Kaydedilen yerel kopya silindi. Bellekteki oturumu silmek için Vaka ekranını kullan.');};
$('#skipIntro').onclick=closeIntro;$('#enterIntro').onclick=closeIntro;$('#replayIntro').onclick=()=>intro(true);
function clock(){const now=new Date();$('#clock').textContent=now.toLocaleTimeString('tr-TR',{hour12:false});$('#clock').dateTime=now.toISOString();}clock();setInterval(clock,1000);

async function saveHibpKey(remove=false){return saveProviderKey('hibp',remove?'':$('#hibpKey').value.trim());}
async function saveOathnetKey(remove=false){return saveProviderKey('oathnet',remove?'':$('#oathnetKey').value.trim());}
init();
