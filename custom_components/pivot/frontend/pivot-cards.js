/*! Pivot dashboard cards v0.0.94. Built from frontend/ in pivot-integration; edit the source, not this file. Includes Lit (BSD-3-Clause) and Material Design Icons (Apache-2.0). */
var H1="https://alistairmerritt.github.io/pivot/dashboard/",B1="https://alistairmerritt.github.io/pivot/timer/",P1=["#2889FF","#FF7D19","#97FF3D","#C800FF"],y1=new Set(["light","fan","climate","media_player","cover","number","input_number"]),R=new Set(["","unknown","unavailable","none"]),p1=["control_mode","volume"],m1=["announcements","mute_announcements","show_control_value","dim_when_idle"],h=[...p1,...m1],k={control_mode:{title:"Control Mode",description:"Enable or disable Pivot control"},announcements:{title:"System Announcements",description:"Announce bank changes and triple-press via voice"},mute_announcements:{title:"Mute Announcements",description:"Silence all spoken announcements temporarily"},show_control_value:{title:"Display Persistent Value",description:"Keep current value visible on the LED ring when idle"},dim_when_idle:{title:"Dim Gauge LEDs While Idle",description:"Reduce LED brightness when not interacting with dial"}},E=[{minutes:15,value:24,label:"15m"},{minutes:30,value:50,label:"30m"},{minutes:45,value:75,label:"45m"},{minutes:60,value:100,label:"60m"}];function m(M){return{activeBank:`number.${M}_active_bank`,mediaPlayerText:`text.${M}_media_player_entity`,timerState:`select.${M}_timer_state`,timerDuration:`number.${M}_timer_duration`,timerEnd:`text.${M}_timer_end`,toggle:H=>`switch.${M}_${H}`,bank:H=>({entity:`text.${M}_bank_${H}_entity`,value:`number.${M}_bank_${H}_value`,passive:`binary_sensor.${M}_bank_${H}_passive`,color:`text.${M}_bank_${H}_color`,colorLight:`light.${M}_bank_${H}_color_light`,mirror:`switch.${M}_bank_${H}_mirror_light`,announce:`switch.${M}_bank_${H}_announce_value`})}}var V1=globalThis,L1=V1.ShadowRoot&&(V1.ShadyCSS===void 0||V1.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,n1=Symbol(),T1=new WeakMap,$=class{constructor(H,C,V){if(this._$cssResult$=!0,V!==n1)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=H,this.t=C}get styleSheet(){let H=this.o,C=this.t;if(L1&&H===void 0){let V=C!==void 0&&C.length===1;V&&(H=T1.get(C)),H===void 0&&((this.o=H=new CSSStyleSheet).replaceSync(this.cssText),V&&T1.set(C,H))}return H}toString(){return this.cssText}},F1=M=>new $(typeof M=="string"?M:M+"",void 0,n1),n=(M,...H)=>{let C=M.length===1?M[0]:H.reduce((V,L,r)=>V+(e=>{if(e._$cssResult$===!0)return e.cssText;if(typeof e=="number")return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(L)+M[r+1],M[0]);return new $(C,M,n1)},R1=(M,H)=>{if(L1)M.adoptedStyleSheets=H.map(C=>C instanceof CSSStyleSheet?C:C.styleSheet);else for(let C of H){let V=document.createElement("style"),L=V1.litNonce;L!==void 0&&V.setAttribute("nonce",L),V.textContent=C.cssText,M.appendChild(V)}},v1=L1?M=>M:M=>M instanceof CSSStyleSheet?(H=>{let C="";for(let V of H.cssRules)C+=V.cssText;return F1(C)})(M):M;var{is:S2,defineProperty:c2,getOwnPropertyDescriptor:h2,getOwnPropertyNames:O2,getOwnPropertySymbols:f2,getPrototypeOf:g2}=Object,M1=globalThis,E1=M1.trustedTypes,k2=E1?E1.emptyScript:"",b2=M1.reactiveElementPolyfillSupport,W=(M,H)=>M,l1={toAttribute(M,H){switch(H){case Boolean:M=M?k2:null;break;case Object:case Array:M=M==null?M:JSON.stringify(M)}return M},fromAttribute(M,H){let C=M;switch(H){case Boolean:C=M!==null;break;case Number:C=M===null?null:Number(M);break;case Object:case Array:try{C=JSON.parse(M)}catch{C=null}}return C}},_1=(M,H)=>!S2(M,H),D1={attribute:!0,type:String,converter:l1,reflect:!1,useDefault:!1,hasChanged:_1};Symbol.metadata??=Symbol("metadata"),M1.litPropertyMetadata??=new WeakMap;var O=class extends HTMLElement{static addInitializer(H){this._$Ei(),(this.l??=[]).push(H)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(H,C=D1){if(C.state&&(C.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(H)&&((C=Object.create(C)).wrapped=!0),this.elementProperties.set(H,C),!C.noAccessor){let V=Symbol(),L=this.getPropertyDescriptor(H,V,C);L!==void 0&&c2(this.prototype,H,L)}}static getPropertyDescriptor(H,C,V){let{get:L,set:r}=h2(this.prototype,H)??{get(){return this[C]},set(e){this[C]=e}};return{get:L,set(e){let t=L?.call(this);r?.call(this,e),this.requestUpdate(H,t,V)},configurable:!0,enumerable:!0}}static getPropertyOptions(H){return this.elementProperties.get(H)??D1}static _$Ei(){if(this.hasOwnProperty(W("elementProperties")))return;let H=g2(this);H.finalize(),H.l!==void 0&&(this.l=[...H.l]),this.elementProperties=new Map(H.elementProperties)}static finalize(){if(this.hasOwnProperty(W("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(W("properties"))){let C=this.properties,V=[...O2(C),...f2(C)];for(let L of V)this.createProperty(L,C[L])}let H=this[Symbol.metadata];if(H!==null){let C=litPropertyMetadata.get(H);if(C!==void 0)for(let[V,L]of C)this.elementProperties.set(V,L)}this._$Eh=new Map;for(let[C,V]of this.elementProperties){let L=this._$Eu(C,V);L!==void 0&&this._$Eh.set(L,C)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(H){let C=[];if(Array.isArray(H)){let V=new Set(H.flat(1/0).reverse());for(let L of V)C.unshift(v1(L))}else H!==void 0&&C.push(v1(H));return C}static _$Eu(H,C){let V=C.attribute;return V===!1?void 0:typeof V=="string"?V:typeof H=="string"?H.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(H=>this.enableUpdating=H),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(H=>H(this))}addController(H){(this._$EO??=new Set).add(H),this.renderRoot!==void 0&&this.isConnected&&H.hostConnected?.()}removeController(H){this._$EO?.delete(H)}_$E_(){let H=new Map,C=this.constructor.elementProperties;for(let V of C.keys())this.hasOwnProperty(V)&&(H.set(V,this[V]),delete this[V]);H.size>0&&(this._$Ep=H)}createRenderRoot(){let H=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return R1(H,this.constructor.elementStyles),H}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(H=>H.hostConnected?.())}enableUpdating(H){}disconnectedCallback(){this._$EO?.forEach(H=>H.hostDisconnected?.())}attributeChangedCallback(H,C,V){this._$AK(H,V)}_$ET(H,C){let V=this.constructor.elementProperties.get(H),L=this.constructor._$Eu(H,V);if(L!==void 0&&V.reflect===!0){let r=(V.converter?.toAttribute!==void 0?V.converter:l1).toAttribute(C,V.type);this._$Em=H,r==null?this.removeAttribute(L):this.setAttribute(L,r),this._$Em=null}}_$AK(H,C){let V=this.constructor,L=V._$Eh.get(H);if(L!==void 0&&this._$Em!==L){let r=V.getPropertyOptions(L),e=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:l1;this._$Em=L;let t=e.fromAttribute(C,r.type);this[L]=t??this._$Ej?.get(L)??t,this._$Em=null}}requestUpdate(H,C,V,L=!1,r){if(H!==void 0){let e=this.constructor;if(L===!1&&(r=this[H]),V??=e.getPropertyOptions(H),!((V.hasChanged??_1)(r,C)||V.useDefault&&V.reflect&&r===this._$Ej?.get(H)&&!this.hasAttribute(e._$Eu(H,V))))return;this.C(H,C,V)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(H,C,{useDefault:V,reflect:L,wrapped:r},e){V&&!(this._$Ej??=new Map).has(H)&&(this._$Ej.set(H,e??C??this[H]),r!==!0||e!==void 0)||(this._$AL.has(H)||(this.hasUpdated||V||(C=void 0),this._$AL.set(H,C)),L===!0&&this._$Em!==H&&(this._$Eq??=new Set).add(H))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(C){Promise.reject(C)}let H=this.scheduleUpdate();return H!=null&&await H,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[L,r]of this._$Ep)this[L]=r;this._$Ep=void 0}let V=this.constructor.elementProperties;if(V.size>0)for(let[L,r]of V){let{wrapped:e}=r,t=this[L];e!==!0||this._$AL.has(L)||t===void 0||this.C(L,void 0,r,t)}}let H=!1,C=this._$AL;try{H=this.shouldUpdate(C),H?(this.willUpdate(C),this._$EO?.forEach(V=>V.hostUpdate?.()),this.update(C)):this._$EM()}catch(V){throw H=!1,this._$EM(),V}H&&this._$AE(C)}willUpdate(H){}_$AE(H){this._$EO?.forEach(C=>C.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(H)),this.updated(H)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(H){return!0}update(H){this._$Eq&&=this._$Eq.forEach(C=>this._$ET(C,this[C])),this._$EM()}updated(H){}firstUpdated(H){}};O.elementStyles=[],O.shadowRootOptions={mode:"open"},O[W("elementProperties")]=new Map,O[W("finalized")]=new Map,b2?.({ReactiveElement:O}),(M1.reactiveElementVersions??=[]).push("2.1.2");var h1=globalThis,N1=M=>M,r1=h1.trustedTypes,$1=r1?r1.createPolicy("lit-html",{createHTML:M=>M}):void 0,z1="$lit$",b=`lit$${Math.random().toFixed(9).slice(2)}$`,K1="?"+b,w2=`<${K1}>`,y=document,U=()=>y.createComment(""),G=M=>M===null||typeof M!="object"&&typeof M!="function",O1=Array.isArray,B2=M=>O1(M)||typeof M?.[Symbol.iterator]=="function",x1=`[ 	
\f\r]`,I=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,W1=/-->/g,I1=/>/g,B=RegExp(`>|${x1}(?:([^\\s"'>=/]+)(${x1}*=${x1}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),U1=/'/g,G1=/"/g,q1=/^(?:script|style|textarea|title)$/i,f1=M=>(H,...C)=>({_$litType$:M,strings:H,values:C}),a=f1(1),e5=f1(2),t5=f1(3),T=Symbol.for("lit-noChange"),A=Symbol.for("lit-nothing"),Q1=new WeakMap,P=y.createTreeWalker(y,129);function j1(M,H){if(!O1(M)||!M.hasOwnProperty("raw"))throw Error("invalid template strings array");return $1!==void 0?$1.createHTML(H):H}var P2=(M,H)=>{let C=M.length-1,V=[],L,r=H===2?"<svg>":H===3?"<math>":"",e=I;for(let t=0;t<C;t++){let i=M[t],p,o,d=-1,c=0;for(;c<i.length&&(e.lastIndex=c,o=e.exec(i),o!==null);)c=e.lastIndex,e===I?o[1]==="!--"?e=W1:o[1]!==void 0?e=I1:o[2]!==void 0?(q1.test(o[2])&&(L=RegExp("</"+o[2],"g")),e=B):o[3]!==void 0&&(e=B):e===B?o[0]===">"?(e=L??I,d=-1):o[1]===void 0?d=-2:(d=e.lastIndex-o[2].length,p=o[1],e=o[3]===void 0?B:o[3]==='"'?G1:U1):e===G1||e===U1?e=B:e===W1||e===I1?e=I:(e=B,L=void 0);let g=e===B&&M[t+1].startsWith("/>")?" ":"";r+=e===I?i+w2:d>=0?(V.push(p),i.slice(0,d)+z1+i.slice(d)+b+g):i+b+(d===-2?t:g)}return[j1(M,r+(M[C]||"<?>")+(H===2?"</svg>":H===3?"</math>":"")),V]},Q=class M{constructor({strings:H,_$litType$:C},V){let L;this.parts=[];let r=0,e=0,t=H.length-1,i=this.parts,[p,o]=P2(H,C);if(this.el=M.createElement(p,V),P.currentNode=this.el.content,C===2||C===3){let d=this.el.content.firstChild;d.replaceWith(...d.childNodes)}for(;(L=P.nextNode())!==null&&i.length<t;){if(L.nodeType===1){if(L.hasAttributes())for(let d of L.getAttributeNames())if(d.endsWith(z1)){let c=o[e++],g=L.getAttribute(d).split(b),C1=/([.?@])?(.*)/.exec(c);i.push({type:1,index:r,name:C1[2],strings:g,ctor:C1[1]==="."?s1:C1[1]==="?"?u1:C1[1]==="@"?S1:_}),L.removeAttribute(d)}else d.startsWith(b)&&(i.push({type:6,index:r}),L.removeAttribute(d));if(q1.test(L.tagName)){let d=L.textContent.split(b),c=d.length-1;if(c>0){L.textContent=r1?r1.emptyScript:"";for(let g=0;g<c;g++)L.append(d[g],U()),P.nextNode(),i.push({type:2,index:++r});L.append(d[c],U())}}}else if(L.nodeType===8)if(L.data===K1)i.push({type:2,index:r});else{let d=-1;for(;(d=L.data.indexOf(b,d+1))!==-1;)i.push({type:7,index:r}),d+=b.length-1}r++}}static createElement(H,C){let V=y.createElement("template");return V.innerHTML=H,V}};function D(M,H,C=M,V){if(H===T)return H;let L=V!==void 0?C._$Co?.[V]:C._$Cl,r=G(H)?void 0:H._$litDirective$;return L?.constructor!==r&&(L?._$AO?.(!1),r===void 0?L=void 0:(L=new r(M),L._$AT(M,C,V)),V!==void 0?(C._$Co??=[])[V]=L:C._$Cl=L),L!==void 0&&(H=D(M,L._$AS(M,H.values),L,V)),H}var Z1=class{constructor(H,C){this._$AV=[],this._$AN=void 0,this._$AD=H,this._$AM=C}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(H){let{el:{content:C},parts:V}=this._$AD,L=(H?.creationScope??y).importNode(C,!0);P.currentNode=L;let r=P.nextNode(),e=0,t=0,i=V[0];for(;i!==void 0;){if(e===i.index){let p;i.type===2?p=new z(r,r.nextSibling,this,H):i.type===1?p=new i.ctor(r,i.name,i.strings,this,H):i.type===6&&(p=new c1(r,this,H)),this._$AV.push(p),i=V[++t]}e!==i?.index&&(r=P.nextNode(),e++)}return P.currentNode=y,L}p(H){let C=0;for(let V of this._$AV)V!==void 0&&(V.strings!==void 0?(V._$AI(H,V,C),C+=V.strings.length-2):V._$AI(H[C])),C++}},z=class M{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(H,C,V,L){this.type=2,this._$AH=A,this._$AN=void 0,this._$AA=H,this._$AB=C,this._$AM=V,this.options=L,this._$Cv=L?.isConnected??!0}get parentNode(){let H=this._$AA.parentNode,C=this._$AM;return C!==void 0&&H?.nodeType===11&&(H=C.parentNode),H}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(H,C=this){H=D(this,H,C),G(H)?H===A||H==null||H===""?(this._$AH!==A&&this._$AR(),this._$AH=A):H!==this._$AH&&H!==T&&this._(H):H._$litType$!==void 0?this.$(H):H.nodeType!==void 0?this.T(H):B2(H)?this.k(H):this._(H)}O(H){return this._$AA.parentNode.insertBefore(H,this._$AB)}T(H){this._$AH!==H&&(this._$AR(),this._$AH=this.O(H))}_(H){this._$AH!==A&&G(this._$AH)?this._$AA.nextSibling.data=H:this.T(y.createTextNode(H)),this._$AH=H}$(H){let{values:C,_$litType$:V}=H,L=typeof V=="number"?this._$AC(H):(V.el===void 0&&(V.el=Q.createElement(j1(V.h,V.h[0]),this.options)),V);if(this._$AH?._$AD===L)this._$AH.p(C);else{let r=new Z1(L,this),e=r.u(this.options);r.p(C),this.T(e),this._$AH=r}}_$AC(H){let C=Q1.get(H.strings);return C===void 0&&Q1.set(H.strings,C=new Q(H)),C}k(H){O1(this._$AH)||(this._$AH=[],this._$AR());let C=this._$AH,V,L=0;for(let r of H)L===C.length?C.push(V=new M(this.O(U()),this.O(U()),this,this.options)):V=C[L],V._$AI(r),L++;L<C.length&&(this._$AR(V&&V._$AB.nextSibling,L),C.length=L)}_$AR(H=this._$AA.nextSibling,C){for(this._$AP?.(!1,!0,C);H!==this._$AB;){let V=N1(H).nextSibling;N1(H).remove(),H=V}}setConnected(H){this._$AM===void 0&&(this._$Cv=H,this._$AP?.(H))}},_=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(H,C,V,L,r){this.type=1,this._$AH=A,this._$AN=void 0,this.element=H,this.name=C,this._$AM=L,this.options=r,V.length>2||V[0]!==""||V[1]!==""?(this._$AH=Array(V.length-1).fill(new String),this.strings=V):this._$AH=A}_$AI(H,C=this,V,L){let r=this.strings,e=!1;if(r===void 0)H=D(this,H,C,0),e=!G(H)||H!==this._$AH&&H!==T,e&&(this._$AH=H);else{let t=H,i,p;for(H=r[0],i=0;i<r.length-1;i++)p=D(this,t[V+i],C,i),p===T&&(p=this._$AH[i]),e||=!G(p)||p!==this._$AH[i],p===A?H=A:H!==A&&(H+=(p??"")+r[i+1]),this._$AH[i]=p}e&&!L&&this.j(H)}j(H){H===A?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,H??"")}},s1=class extends _{constructor(){super(...arguments),this.type=3}j(H){this.element[this.name]=H===A?void 0:H}},u1=class extends _{constructor(){super(...arguments),this.type=4}j(H){this.element.toggleAttribute(this.name,!!H&&H!==A)}},S1=class extends _{constructor(H,C,V,L,r){super(H,C,V,L,r),this.type=5}_$AI(H,C=this){if((H=D(this,H,C,0)??A)===T)return;let V=this._$AH,L=H===A&&V!==A||H.capture!==V.capture||H.once!==V.once||H.passive!==V.passive,r=H!==A&&(V===A||L);L&&this.element.removeEventListener(this.name,this,V),r&&this.element.addEventListener(this.name,this,H),this._$AH=H}handleEvent(H){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,H):this._$AH.handleEvent(H)}},c1=class{constructor(H,C,V){this.element=H,this.type=6,this._$AN=void 0,this._$AM=C,this.options=V}get _$AU(){return this._$AM._$AU}_$AI(H){D(this,H)}};var y2=h1.litHtmlPolyfillSupport;y2?.(Q,z),(h1.litHtmlVersions??=[]).push("3.3.3");var X1=(M,H,C)=>{let V=C?.renderBefore??H,L=V._$litPart$;if(L===void 0){let r=C?.renderBefore??null;V._$litPart$=L=new z(H.insertBefore(U(),r),r,void 0,C??{})}return L._$AI(M),L};var g1=globalThis,s=class extends O{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let H=super.createRenderRoot();return this.renderOptions.renderBefore??=H.firstChild,H}update(H){let C=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(H),this._$Do=X1(C,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return T}};s._$litElement$=!0,s.finalized=!0,g1.litElementHydrateSupport?.({LitElement:s});var T2=g1.litElementPolyfillSupport;T2?.({LitElement:s});(g1.litElementVersions??=[]).push("4.2.2");function v(M,H,C){M.dispatchEvent(new CustomEvent(H,{detail:C,bubbles:!0,composed:!0}))}var f=(M,H)=>v(M,"hass-more-info",{entityId:H}),K=M=>v(M,"haptic","light");async function x(M,H,C,V,L){try{return await H.callService(C,V,L),!0}catch(r){let e=r?.message??String(r);return console.warn(`Pivot: ${C}.${V} failed`,r),v(M,"hass-notification",{message:`Pivot: ${e}`}),!1}}var q=(M,H,C)=>x(M,H,C.split(".")[0],"toggle",{entity_id:C}),k1=(M,H,C)=>!!M.services?.[H]?.[C];function e1(M,H){let C=0,V,L,r=()=>{C=Date.now(),V=void 0;let t=L;L=void 0,t&&M(...t)},e=((...t)=>{L=t;let i=H-(Date.now()-C);i<=0?(V&&clearTimeout(V),r()):V||(V=setTimeout(r,i))});return e.cancel=()=>{V&&clearTimeout(V),V=void 0,L=void 0},e.flush=()=>{L&&(V&&clearTimeout(V),r())},e}var J1=/^number\.(.+)_active_bank$/,Y1=new WeakMap;function F2(M,H){if(!H||!M.entities)return;let C=Object.values(M.entities).filter(V=>V.device_id===H&&V.entity_id.startsWith("switch."));return C.find(V=>V.entity_id.endsWith("_timer_silent_mode"))?.entity_id??C.find(V=>(V.name??"").toLowerCase()==="timer silent mode")?.entity_id}function R2(M){let H=[];for(let C of Object.values(M.entities??{})){if(C.platform!=="pivot")continue;let V=J1.exec(C.entity_id);if(!V)continue;let L=C.device_id?M.devices?.[C.device_id]:void 0,r=L?.identifiers?.find(e=>e[0]==="pivot")?.[1];H.push({suffix:V[1],name:L?.name_by_user||L?.name||V[1],deviceId:C.device_id,esphomeDeviceId:r,timerSilentEntity:F2(M,r)})}return H}function E2(M){let H=[];for(let C of Object.keys(M.states)){let V=J1.exec(C);V&&M.states[`text.${V[1]}_bank_1_entity`]&&H.push({suffix:V[1],name:V[1]})}return H}function Z(M){if(!M)return[];let H;if(M.entities&&Object.keys(M.entities).length){let C=Y1.get(M.entities);C&&C.devices===M.devices?H=C.list:(H=R2(M).sort((V,L)=>V.name.localeCompare(L.name)),Y1.set(M.entities,{devices:M.devices,list:H}))}return H&&H.length?H:E2(M).sort((C,V)=>C.name.localeCompare(V.name))}function C2(M,H){if(!(!M||!H))return Z(M).find(C=>C.suffix===H)??(M.states[`number.${H}_active_bank`]?{suffix:H,name:H}:void 0)}var D2={control_mode:k.control_mode.title,volume:"Pivot Device Volume",announcements:k.announcements.title,mute_announcements:k.mute_announcements.title,show_control_value:k.show_control_value.title,dim_when_idle:k.dim_when_idle.title},j={device:"Pivot device",bank:"Bank",name:"Title (optional)",show_status:"Show title and active bank",show_settings:"Show device and behaviour settings",show_name:"Show title",rows:"Rows",headings:'Show "Device" and "Behaviour" headings',timer_silent_entity:"Timer silent switch (optional, found automatically)"},H2;function _2(){return customElements.get("ha-form")?Promise.resolve(!0):(H2??=(async()=>{try{await(await window.loadCardHelpers?.())?.createCardElement({type:"entities",entities:[]})?.constructor.getConfigElement?.()}catch{}return Promise.race([customElements.whenDefined("ha-form").then(()=>!0),new Promise(M=>setTimeout(()=>M(!!customElements.get("ha-form")),3e3))])})(),H2)}var X=class extends s{constructor(){super(),this.kind="device"}setConfig(H){this._config=H}connectedCallback(){super.connectedCallback(),_2().then(H=>this._haForm=H)}get _devices(){return Z(this.hass)}_schema(){let H=this._devices,C=H.map(r=>({value:r.suffix,label:r.name===r.suffix?r.suffix:`${r.name} (${r.suffix})`})),V=this._config?.device;V&&!H.some(r=>r.suffix===V)&&C.push({value:V,label:`${V} (not found)`});let L=[{name:"device",required:!0,selector:{select:{mode:"dropdown",options:C}}}];return this.kind==="bank"&&L.push({name:"bank",required:!0,selector:{select:{mode:"dropdown",options:["1","2","3","4"].map(r=>({value:r,label:`Bank ${r}`}))}}}),(this.kind==="device"||this.kind==="status")&&L.push({name:"name",selector:{text:{}}}),this.kind==="device"&&L.push({name:"show_status",selector:{boolean:{}}},{name:"show_settings",selector:{boolean:{}}}),this.kind==="status"&&L.push({name:"show_name",selector:{boolean:{}}}),this.kind==="settings"&&L.push({name:"rows",selector:{select:{multiple:!0,mode:"list",options:h.map(r=>({value:r,label:D2[r]}))}}},{name:"headings",selector:{boolean:{}}}),(this.kind==="device"||this.kind==="bank")&&L.push({name:"timer_silent_entity",selector:{entity:{domain:"switch"}}}),L}_data(){let H=this._config??{type:""};return{...H,bank:H.bank!==void 0?String(H.bank):"1",show_status:H.show_status!==!1,show_settings:H.show_settings!==!1,show_name:H.show_name!==!1,headings:H.headings!==!1,rows:Array.isArray(H.rows)&&H.rows.length?H.rows:[...h]}}_commit(H){let C={type:this._config?.type??`custom:pivot-${this.kind}-card`,device:H.device??""};if(this.kind==="bank"&&(C.bank=Number(H.bank??1)),(this.kind==="device"||this.kind==="status")&&typeof H.name=="string"&&H.name.trim()&&(C.name=H.name),this.kind==="device"&&(H.show_status===!1&&(C.show_status=!1),H.show_settings===!1&&(C.show_settings=!1)),this.kind==="status"&&H.show_name===!1&&(C.show_name=!1),this.kind==="settings"){let V=Array.isArray(H.rows)?H.rows:[],L=h.filter(r=>V.includes(r));L.length&&L.length!==h.length&&(C.rows=L),H.headings===!1&&(C.headings=!1)}(this.kind==="device"||this.kind==="bank")&&typeof H.timer_silent_entity=="string"&&H.timer_silent_entity&&(C.timer_silent_entity=H.timer_silent_entity);for(let[V,L]of Object.entries(this._config??{}))!(V in C)&&!["device","bank","name","show_status","show_settings","show_name","rows","headings","timer_silent_entity"].includes(V)&&(C[V]=L);this._config=C,v(this,"config-changed",{config:C})}render(){if(!this.hass||!this._config)return A;let H=this._devices.length?A:a`<p class="hint">No Pivot devices found. Add one under Settings → Devices &amp; services → Pivot.</p>`;return this._haForm?a`${H}<ha-form
          .hass=${this.hass}
          .data=${this._data()}
          .schema=${this._schema()}
          .computeLabel=${C=>j[C.name]??C.name}
          @value-changed=${C=>{C.stopPropagation(),this._commit(C.detail.value)}}
        ></ha-form>`:a`${H}${this._renderFallback()}`}_renderFallback(){let H=this._data(),C=(L,r)=>this._commit({...H,[L]:r}),V=L=>a`<label class="check"
        ><input type="checkbox" .checked=${H[L]!==!1} @change=${r=>C(L,r.target.checked)} />${j[L]}</label
      >`;return a`<div class="fallback">
      <label
        >${j.device}
        <select @change=${L=>C("device",L.target.value)}>
          <option value="" ?selected=${!H.device}>Choose…</option>
          ${this._devices.map(L=>a`<option value=${L.suffix} ?selected=${L.suffix===H.device}>${L.name} (${L.suffix})</option>`)}
        </select></label
      >
      ${this.kind==="bank"?a`<label
            >${j.bank}
            <select @change=${L=>C("bank",L.target.value)}>
              ${["1","2","3","4"].map(L=>a`<option value=${L} ?selected=${L===H.bank}>Bank ${L}</option>`)}
            </select></label
          >`:A}
      ${this.kind==="device"||this.kind==="status"?a`<label
            >${j.name}<input type="text" .value=${H.name??""} @change=${L=>C("name",L.target.value)}
          /></label>`:A}
      ${this.kind==="device"?a`${V("show_status")}${V("show_settings")}`:A}
      ${this.kind==="status"?V("show_name"):A}
      ${this.kind==="settings"?V("headings"):A}
    </div>`}};X.properties={hass:{attribute:!1},kind:{},_config:{state:!0},_haForm:{state:!0}},X.styles=n`
    .fallback {
      display: grid;
      gap: 12px;
    }
    label {
      display: grid;
      gap: 4px;
      font-size: 14px;
    }
    label.check {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    select,
    input[type='text'] {
      font: inherit;
      padding: 8px;
      border-radius: 6px;
      border: 1px solid var(--divider-color, #ccc);
      background: var(--card-background-color, transparent);
      color: var(--primary-text-color);
    }
    .hint {
      font-size: 13px;
      color: var(--secondary-text-color);
    }
  `;customElements.get("pivot-card-editor")||customElements.define("pivot-card-editor",X);var w=n`
  :host {
    --pv-text: var(--primary-text-color, #f2f2f7);
    --pv-muted: var(--pivot-muted-color, rgba(255, 255, 255, 0.25));
    --pv-description: var(--pivot-description-color, rgba(255, 255, 255, 0.5));
    --pv-status-text: var(--pivot-status-text-color, #ffffff);
    --pv-toggle-track: var(--pivot-toggle-track-color, rgba(0, 0, 0, 0.3));
    --pv-toggle-edge: var(--pivot-toggle-edge-color, rgba(255, 255, 255, 0.08));
    --pv-toggle-off: var(--pivot-toggle-off-color, rgba(255, 255, 255, 0.26));
    --pv-toggle-on: var(--pivot-toggle-on-color, #ffffff);
    --pv-strip: var(--pivot-timer-strip-color, rgba(0, 0, 0, 0.18));
    --pv-button: var(--pivot-button-color, rgba(255, 255, 255, 0.26));
    --pv-button-idle: var(--pivot-button-idle-color, rgba(255, 255, 255, 0.08));
    --pv-preset: var(--pivot-preset-color, rgba(255, 255, 255, 0.7));
    --pv-preset-selected: var(--pivot-preset-selected-color, #ffffff);
    --pv-dimmed-icon: var(--pivot-dimmed-icon-color, rgba(255, 255, 255, 0.3));
    --pv-active-border: var(--pivot-active-border-color, rgba(255, 255, 255, 0.27));
    --pv-volume-track: var(--pivot-volume-track-color, rgba(255, 255, 255, 0.3));
    --pv-volume-fill: var(--pivot-volume-fill-color, #ffffff);
    --pv-value-font: var(--pivot-value-font-family, 'SF Pro Rounded', ui-rounded, system-ui, sans-serif);
    --pv-ripple-on: var(--state-switch-active-color, var(--state-active-color, var(--amber-color, #ffc107)));
    --pv-ripple-off: var(--state-switch-inactive-color, var(--state-inactive-color, var(--grey-color, #9e9e9e)));
    --ha-ripple-hover-opacity: 0.04;
    --ha-ripple-pressed-opacity: 0.12;
    --ha-ripple-color: var(--pv-text);
    display: block;
    color: var(--pv-text);
    -webkit-tap-highlight-color: transparent;
  }
  /* Light themes: the palette above is tuned for dark cards. */
  :host([light]) {
    --pv-muted: var(--pivot-muted-color, rgba(0, 0, 0, 0.45));
    --pv-description: var(--pivot-description-color, rgba(0, 0, 0, 0.55));
    --pv-status-text: var(--pivot-status-text-color, var(--primary-text-color, #212121));
    --pv-toggle-track: var(--pivot-toggle-track-color, rgba(0, 0, 0, 0.1));
    --pv-toggle-edge: var(--pivot-toggle-edge-color, transparent);
    --pv-toggle-off: var(--pivot-toggle-off-color, rgba(0, 0, 0, 0.38));
    --pv-toggle-on: var(--pivot-toggle-on-color, var(--primary-text-color, #212121));
    --pv-strip: var(--pivot-timer-strip-color, rgba(0, 0, 0, 0.05));
    --pv-button: var(--pivot-button-color, rgba(0, 0, 0, 0.14));
    --pv-button-idle: var(--pivot-button-idle-color, rgba(0, 0, 0, 0.06));
    --pv-preset: var(--pivot-preset-color, rgba(0, 0, 0, 0.7));
    --pv-preset-selected: var(--pivot-preset-selected-color, var(--primary-text-color, #212121));
    --pv-dimmed-icon: var(--pivot-dimmed-icon-color, rgba(0, 0, 0, 0.3));
    --pv-active-border: var(--pivot-active-border-color, rgba(0, 0, 0, 0.25));
    --pv-volume-track: var(--pivot-volume-track-color, rgba(0, 0, 0, 0.15));
    --pv-volume-fill: var(--pivot-volume-fill-color, var(--primary-text-color, #212121));
  }
  * {
    box-sizing: border-box;
  }
  svg {
    display: block;
    width: 100%;
    height: 100%;
    fill: currentColor;
  }
  button {
    font: inherit;
    color: inherit;
    background: none;
    border: 0;
    margin: 0;
    padding: 0;
    text-align: inherit;
    -webkit-tap-highlight-color: transparent;
  }
  button:focus-visible,
  [role='switch']:focus-visible,
  [role='button']:focus-visible {
    outline: 2px solid var(--primary-color, #03a9f4);
    outline-offset: -2px;
  }
  .tap {
    position: relative;
    cursor: pointer;
  }
  .text {
    font-size: 14px;
    font-weight: 400;
    line-height: normal;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  /* The on/off switch: a 45x27 track and a 21px knob with an even 3px gap all round. */
  .toggle {
    position: relative;
    flex: none;
    width: 45px;
    height: 27px;
    border-radius: 25px;
    background: var(--pv-toggle-track);
    /* The edge keeps the track visible where the dark fill meets a black page. */
    box-shadow: inset 0 0 0 1px var(--pv-toggle-edge);
  }
  .toggle .knob {
    position: absolute;
    top: 3px;
    left: 3px;
    width: 21px;
    height: 21px;
    border-radius: 50%;
    background: var(--pv-toggle-off);
    transition: left 0.15s ease, background-color 0.15s ease;
  }
  .toggle.on .knob {
    left: 21px;
    background: var(--pv-toggle-on);
  }
  .disabled {
    pointer-events: none;
  }
  @media (prefers-reduced-motion: reduce) {
    .toggle .knob {
      transition: none;
    }
  }
`;var N2=500;function $2(M){let H=M.trim().toLowerCase(),C,V=/^#([0-9a-f]{3}|[0-9a-f]{6})$/.exec(H);if(V){let L=V[1].length===3?[...V[1]].map(r=>r+r).join(""):V[1];C=[0,2,4].map(r=>parseInt(L.slice(r,r+2),16))}else{let L=/^rgba?\(([^)]+)\)$/.exec(H);L?C=L[1].split(/[ ,/]+/).slice(0,3).map(Number):H==="white"?C=[255,255,255]:H==="black"&&(C=[0,0,0])}if(!(!C||C.some(L=>!Number.isFinite(L))))return(.2126*C[0]+.7152*C[1]+.0722*C[2])/255}var u=class extends s{constructor(){super(...arguments);this._held=!1}validate(C){}setConfig(C){if(!C||typeof C!="object")throw new Error("Invalid configuration");this.validate(C),this._config=C}set config(C){this.setConfig(C)}get device(){let C=[this.hass?.entities,this.hass?.devices,this._config?.device,this.hass?.states];return this._deviceKey&&C.slice(0,3).every((L,r)=>L===this._deviceKey[r])&&this._deviceCache?.deviceId?this._deviceCache:(this._deviceKey=C,this._deviceCache=C2(this.hass,this._config?.device),this._deviceCache)}shouldUpdate(C){if(!C.has("hass")||C.size>1)return!0;let V=C.get("hass"),L=this.hass;return!V||!L||V.entities!==L.entities||V.devices!==L.devices||V.services!==L.services||V.themes!==L.themes?!0:this.watchedIds().some(r=>r&&V.states[r]!==L.states[r])}updated(C){super.updated(C),this.hass&&this._themeChecked!==this.hass.themes&&(this._themeChecked=this.hass.themes,this._checkTheme())}_checkTheme(){let C=getComputedStyle(this),V=C.getPropertyValue("--ha-card-background").trim()||C.getPropertyValue("--card-background-color").trim()||C.getPropertyValue("--primary-background-color").trim(),L=V?$2(V):void 0,r=L!==void 0&&L>.55;r!==this.hasAttribute("light")&&(this.toggleAttribute("light",r),this.requestUpdate())}renderProblem(){let C=Z(this.hass),V=this._config?.device,L=C.length?V?`No Pivot device \u201C${V}\u201D. Choose one in the card editor.`:"Choose a Pivot device in the card editor.":"No Pivot devices found. Add one under Settings \u2192 Devices & services \u2192 Pivot.";return a`<ha-card class="pv-problem pv-error" style="display:block;padding:16px;font-size:14px;line-height:1.4">
      ${L} <a href=${H1} target="_blank" rel="noreferrer" style="color:var(--primary-color)">Pivot dashboard docs</a>
    </ha-card>`}holdStart(C,V){C.pointerType==="mouse"&&C.button!==0||(this._held=!1,clearTimeout(this._holdTimer),V&&(this._holdTimer=setTimeout(()=>{this._held=!0,K(this),f(this,V)},N2)))}holdEnd(){clearTimeout(this._holdTimer)}tap(C,V){if(C.stopPropagation(),this._held){this._held=!1;return}K(this),V()}keyActivate(C,V){C.key!=="Enter"&&C.key!==" "||(C.preventDefault(),C.stopPropagation(),V())}disconnectedCallback(){super.disconnectedCallback(),clearTimeout(this._holdTimer)}};u.properties={hass:{attribute:!1},_config:{state:!0}};var V2="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z";var L2="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z";var M2="M17.5,12A1.5,1.5 0 0,1 16,10.5A1.5,1.5 0 0,1 17.5,9A1.5,1.5 0 0,1 19,10.5A1.5,1.5 0 0,1 17.5,12M14.5,8A1.5,1.5 0 0,1 13,6.5A1.5,1.5 0 0,1 14.5,5A1.5,1.5 0 0,1 16,6.5A1.5,1.5 0 0,1 14.5,8M9.5,8A1.5,1.5 0 0,1 8,6.5A1.5,1.5 0 0,1 9.5,5A1.5,1.5 0 0,1 11,6.5A1.5,1.5 0 0,1 9.5,8M6.5,12A1.5,1.5 0 0,1 5,10.5A1.5,1.5 0 0,1 6.5,9A1.5,1.5 0 0,1 8,10.5A1.5,1.5 0 0,1 6.5,12M12,3A9,9 0 0,0 3,12A9,9 0 0,0 12,21A1.5,1.5 0 0,0 13.5,19.5C13.5,19.11 13.35,18.76 13.11,18.5C12.88,18.23 12.73,17.88 12.73,17.5A1.5,1.5 0 0,1 14.23,16H16A5,5 0 0,0 21,11C21,6.58 16.97,3 12,3Z";var r2="M14,19H18V5H14M6,19H10V5H6V19Z";var e2="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z";var t2="M8,5.14V19.14L19,12.14L8,5.14Z";var i2="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z";var o2="M14,3.23V5.29C16.89,6.15 19,8.83 19,12C19,15.17 16.89,17.84 14,18.7V20.77C18,19.86 21,16.28 21,12C21,7.72 18,4.14 14,3.23M16.5,12C16.5,10.23 15.5,8.71 14,7.97V16C15.5,15.29 16.5,13.76 16.5,12M3,9V15H7L12,20V4L7,9H3Z";var A2="M3,9H7L12,4V20L7,15H3V9M16.59,12L14,9.41L15.41,8L18,10.59L20.59,8L22,9.41L19.41,12L22,14.59L20.59,16L18,13.41L15.41,16L14,14.59L16.59,12Z";var l={circle:V2,close:L2,palette:M2,pause:r2,pencil:e2,play:t2,refresh:i2,volumeHigh:o2,volumeMute:A2},S=M=>a`<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d=${M}></path></svg>`;function N(M,H){let C=M===void 0?NaN:parseFloat(M);return Number.isFinite(C)?C:H}var t1=(M,H,C)=>Math.min(C,Math.max(H,M));function i1(M){let H=[1,3,5].map(V=>parseInt(M.slice(V,V+2),16));return(.2126*H[0]+.7152*H[1]+.0722*H[2])/255<=.82?M:"#"+H.map(V=>Math.round(V*.45+112*.55).toString(16).padStart(2,"0")).join("")}function W2(M){return M&&/^#[0-9a-f]{6}$/i.test(M.trim())?M.trim():void 0}function F(M,H,C){let V=m(H),L=V.bank(C),r=(M.states[L.entity]?.state??"").trim(),e=r.toLowerCase()==="timer",t=!e&&r.includes(".")&&!R.has(r.toLowerCase())?r:void 0;return{n:C,ids:L,raw:r,isTimer:e,entityId:t,domain:t?t.split(".")[0]:"",bound:t?M.states[t]:void 0,value:t1(N(M.states[L.value]?.state,0),0,100),passive:M.states[L.passive]?.state==="on",color:W2(M.states[L.color]?.state)??P1[C-1],active:Math.round(N(M.states[V.activeBank]?.state,NaN))===C,controlOn:M.states[V.toggle("control_mode")]?.state==="on"}}function b1(M){return M.isTimer?!0:!!M.bound&&!R.has(M.bound.state)}function Y(M){return M.isTimer?"Timer":M.entityId?M.bound?.attributes.friendly_name||M.entityId:"No entity assigned"}var p2=M=>M.domain==="light",m2=M=>y1.has(M.domain)&&!M.passive,n2=M=>!M.passive&&(M.isTimer||!!M.entityId);function v2(M,H,C){let V=m(H),L=M.states[V.timerState];if(!L)return{enabled:!1,state:"idle"};let r=N(M.states[V.timerDuration]?.state,NaN),e=M.states[V.timerEnd]?.state??"",t;return L.state==="running"&&/^\d{4}-\d{2}-\d{2}T/.test(e)?t=Math.max(0,Math.round((Date.parse(e)-C)/1e3)):L.state==="paused"&&/^P\d+$/.test(e)&&(t=parseInt(e.slice(1),10)),{enabled:!0,state:L.state,durationMin:Number.isFinite(r)?r:void 0,remainingSecs:t}}function a2(M){let H=Math.max(0,Math.floor(M)),C=Math.floor(H/3600),V=Math.floor(H%3600/60),L=String(H%60).padStart(2,"0");return C>0?`${C}:${String(V).padStart(2,"0")}:${L}`:`${V}:${L}`}var d2=M=>`${M} ${M===1?"min":"mins"}`;function I2(M){let H=Math.round(M);return Math.abs(M%1)===.5&&H%2!==0?H-1:H}function l2(M){return t1(I2(1+M/100*59),1,60)}function w1(M){return t1((M-1)/59*100,0,100)}function U2(M){let H=E.find(C=>C.value===Math.round(M));return H?H.minutes:Math.round(M/100*60)}function G2(M,H){return M.state==="alerting"?"Timer Finished":M.state==="running"&&M.remainingSecs!==void 0?a2(M.remainingSecs):M.state==="paused"&&M.remainingSecs!==void 0?`Paused \u2013 ${a2(M.remainingSecs)}`:M.enabled&&M.durationMin!==void 0?d2(Math.round(M.durationMin)):d2(U2(H))}function x2(M,H){let C=M.durationMin!==void 0?M.durationMin*60:void 0;return(M.state==="running"||M.state==="paused")&&M.remainingSecs!==void 0&&C?M.remainingSecs<=C+2?t1(M.remainingSecs/C*100,0,100):H:M.state==="idle"&&M.enabled&&M.durationMin!==void 0?w1(M.durationMin):H}function Z2(M,H){if(M.state==="idle")return M.enabled&&M.durationMin!==void 0?E.find(C=>C.minutes===Math.round(M.durationMin))?.minutes:E.find(C=>C.value===Math.round(H))?.minutes}var Q2={open:"Open",closed:"Closed",opening:"Opening",closing:"Closing"};function s2(M,H){if(M.isTimer)return G2(H,M.value);if(!b1(M))return"";let C=M.bound.state,V=Math.round(M.value);if(M.passive)return M.domain==="cover"?Q2[C]??"":C==="on"?"On":M.value===0?"Off":"On";if(M.domain==="cover")return V===0?"Closed":V===100?"Open":`${V}% Open`;if(M.domain==="climate"){let L=M.bound.attributes.temperature;return L==null||L===""?"":`${Math.round(Number(L))}\xB0`}return C==="off"?"Off":V===0?"":`${V}%`}function u2(M){return!M.isTimer&&M.bound?.state==="off"}var z2=4e3,K2=4,J=class extends s{constructor(){super();this._startX=0;this._moved=!1;this._isTouch=!1;this._down=C=>{if(this.disabled){v(this,"pivot-slide-blocked");return}if(!(C.pointerType==="mouse"&&C.button!==0)){C.stopPropagation(),this._pointer=C.pointerId,this._startX=C.clientX,this._moved=!1,this._isTouch=C.pointerType!=="mouse";try{this.setPointerCapture(C.pointerId)}catch{}v(this,"pivot-slide-start"),this._isTouch||(this._moved=!0,this._hold(this._valueAt(C.clientX)),v(this,"pivot-slide",{value:this._shown}))}};this._move=C=>{if(C.pointerId!==this._pointer||!this._moved&&Math.abs(C.clientX-this._startX)<K2)return;this._moved=!0;let V=this._valueAt(C.clientX);V!==this._shown&&(this._hold(V),v(this,"pivot-slide",{value:V}))};this._up=C=>{if(C.pointerId!==this._pointer)return;this._pointer=void 0;let V=this._valueAt(C.clientX);this._hold(V),v(this,"pivot-slide-end",{value:V})};this._cancel=C=>{C.pointerId===this._pointer&&(this._pointer=void 0,this._release(),v(this,"pivot-slide-cancel"))};this._lost=C=>{C.pointerId===this._pointer&&this._cancel(C)};this._key=C=>{if(this.disabled)return;let V={ArrowRight:1,ArrowUp:1,ArrowLeft:-1,ArrowDown:-1,PageUp:10,PageDown:-10},L;if(C.key in V)L=this.shownValue+V[C.key];else if(C.key==="Home")L=0;else if(C.key==="End")L=100;else return;C.preventDefault(),L=Math.round(Math.min(100,Math.max(0,L))),v(this,"pivot-slide-start"),this._hold(L),v(this,"pivot-slide-end",{value:L})};this.value=0,this.color="#ffffff",this.trackColor="rgba(255,255,255,0.3)",this.cap=15,this.disabled=!1,this.hideFill=!1,this.zeroCap=!1,this.label="",this._shown=void 0}get shownValue(){return this._shown??this.value}willUpdate(C){C.has("value")&&this._pointer===void 0&&this._shown!==void 0&&Math.abs(this._shown-this.value)<.5&&this._release()}disconnectedCallback(){super.disconnectedCallback(),clearTimeout(this._holdTimer)}render(){let C=Math.min(100,Math.max(0,this.shownValue)),V=(C>0||this.zeroCap)&&!this.hideFill;return a`<div class="track" style="background:${this.trackColor}">
      ${V?a`<div class="fill" style="background:${this.color};width:min(100%, calc(${C}% + ${this.cap}px))"></div>`:A}
    </div>`}firstUpdated(){this.setAttribute("role","slider"),this.setAttribute("aria-valuemin","0"),this.setAttribute("aria-valuemax","100"),this.addEventListener("pointerdown",this._down),this.addEventListener("pointermove",this._move),this.addEventListener("pointerup",this._up),this.addEventListener("pointercancel",this._cancel),this.addEventListener("lostpointercapture",this._lost),this.addEventListener("keydown",this._key),this.addEventListener("click",C=>C.stopPropagation())}updated(){this.setAttribute("aria-valuenow",String(Math.round(this.shownValue))),this.label&&this.setAttribute("aria-label",this.label),this.setAttribute("aria-disabled",String(this.disabled)),this.tabIndex=this.disabled?-1:0}_valueAt(C){let L=(this.renderRoot.querySelector(".track")??this).getBoundingClientRect(),r=Math.max(1,L.width-this.cap),e=(C-L.left-this.cap/2)/r*100;return Math.round(Math.min(100,Math.max(0,e)))}_hold(C){this._shown=C,clearTimeout(this._holdTimer),this._holdTimer=setTimeout(()=>this._release(),z2)}_release(){clearTimeout(this._holdTimer),this._shown=void 0}};J.properties={value:{type:Number},color:{},trackColor:{attribute:"track-color"},cap:{type:Number},disabled:{type:Boolean,reflect:!0},hideFill:{type:Boolean,attribute:"hide-fill"},zeroCap:{type:Boolean,attribute:"zero-cap"},label:{},_shown:{state:!0}},J.styles=n`
    :host {
      display: block;
      position: relative;
      height: 23px;
      touch-action: pan-y;
      -webkit-tap-highlight-color: transparent;
      outline: none;
      cursor: pointer;
    }
    :host([disabled]) {
      cursor: inherit;
    }
    :host(:focus-visible) .track {
      outline: 2px solid var(--primary-color, #03a9f4);
      outline-offset: 2px;
    }
    /* Inset 1px like the ha-card border around my-slider-v2, so bars land on the same pixels. */
    .track {
      position: absolute;
      left: 1px;
      right: 1px;
      top: 1px;
      height: 100%;
      border-radius: 99px;
      overflow: hidden;
    }
    .fill {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      border-radius: 99px;
    }
  `;customElements.get("pivot-slider")||customElements.define("pivot-slider",J);var j2=200,X2=4e3,Y2=3300,J2=15e3,o1=class extends u{constructor(){super(...arguments);this._send=e1(C=>this._writeValue(C),j2);this._activate=C=>{C?.stopPropagation();let V=this.device;if(!this.hass||!V)return;let L=F(this.hass,V.suffix,this.bankNumber);L.active||(K(this),x(this,this.hass,"number","set_value",{entity_id:m(V.suffix).activeBank,value:L.n}))}}static getConfigElement(){let C=document.createElement("pivot-card-editor");return C.kind="bank",C}static getStubConfig(C){return{device:Z(C)[0]?.suffix??"",bank:1}}validate(C){let V=Number(C.bank??1);if(!Number.isInteger(V)||V<1||V>4)throw new Error("bank must be 1, 2, 3 or 4")}get bankNumber(){return Number(this._config?.bank??1)}getCardSize(){return 4}getGridOptions(){return{columns:12,rows:"auto",min_columns:6}}get _silentEntity(){return this._config?.timer_silent_entity||this.device?.timerSilentEntity}watchedIds(){let C=this.device;if(!C||!this.hass)return[];let V=m(C.suffix),L=V.bank(this.bankNumber),r=this.hass.states[L.entity]?.state;return[L.entity,L.value,L.passive,L.color,L.mirror,L.announce,V.activeBank,V.toggle("control_mode"),V.toggle("mute_announcements"),V.timerState,V.timerDuration,V.timerEnd,r&&r.includes(".")?r:void 0,this._silentEntity,"script.pivot_timer_toggle"]}render(){let C=this.device;if(!this.hass||!this._config)return A;if(!C)return this.renderProblem();let V=F(this.hass,C.suffix,this.bankNumber);this.hasAttribute("light")&&(V.color=i1(V.color));let L=v2(this.hass,C.suffix,Date.now()),r=s2(V,L),e=V.entityId&&!V.isTimer?V.entityId:"";return a`<ha-card
      class="bank pv-ready ${V.active?"active":""} ${V.controlOn?"":"control-off"}"
      data-measure="bank-card"
      @click=${this._activate}
    >
      <ha-ripple></ha-ripple>
      <div class="head tap" @click=${this._activate}>
        <ha-ripple></ha-ripple>
        <button
          class="dot tap"
          style="color:${V.color}"
          aria-label="Bank ${V.n} colour"
          @click=${t=>this.tap(t,()=>f(this,V.ids.colorLight))}
        >
          <ha-ripple></ha-ripple>${S(l.circle)}
        </button>
        <span class="label text">${`Bank ${V.n}`}</span>
        <button class="edit tap" aria-label="Edit the bank ${V.n} entity" @click=${t=>this.tap(t,()=>f(this,V.ids.entity))}>
          <ha-ripple></ha-ripple><span>EDIT ENTITY</span>${S(l.pencil)}
        </button>
      </div>
      <div class="name-row tap" title=${e} @click=${t=>this._nameTap(t,V)}>
        <ha-ripple></ha-ripple>
        <span class="name">${Y(V)}</span>${r?a`<span class="value">${r}</span>`:A}
      </div>
      ${n2(V)?this._renderSlider(V,L):A}
      ${V.isTimer?this._renderTimer(V,L):A}
      ${p2(V)?this._renderRow(V.ids.mirror,"Mirror Light Colour",l.palette):A}
      ${m2(V)?this._renderRow(V.ids.announce,"Announce Value",l.volumeHigh,this._muted):A}
    </ha-card>`}get _muted(){let C=this.device;return!!C&&this.hass?.states[m(C.suffix).toggle("mute_announcements")]?.state==="on"}_renderSlider(C,V){let L=C.isTimer&&V.state!=="idle",r=!C.controlOn||L||!b1(C)||C.isTimer&&!V.enabled&&!C.active,e=C.isTimer?x2(V,C.value):C.value;return a`<pivot-slider
      .value=${e}
      .color=${C.color}
      .trackColor=${`${C.color}33`}
      .cap=${15}
      .hideFill=${u2(C)}
      .label=${`${Y(C)} value`}
      ?disabled=${r}
      @pivot-slide-start=${()=>this._slideStart(C)}
      @pivot-slide=${t=>this._slide(C,t.detail.value)}
      @pivot-slide-end=${t=>this._slideEnd(C,V,t.detail.value)}
      @pivot-slide-cancel=${()=>this._send.cancel()}
      @click=${t=>t.stopPropagation()}
    ></pivot-slider>`}_renderRow(C,V,L,r=!1,e=""){let t=this.hass?.states[C]?.state==="on",i=this.hass?.states[C]?.state,p=i===void 0||i==="unavailable";return a`<div
      class="row tap ${e} ${r?"muted":""} ${p?"disabled unavailable":""}"
      role="switch"
      tabindex=${r||p?-1:0}
      aria-checked=${t?"true":"false"}
      aria-label=${V}
      style="--ha-ripple-color:${t?"var(--pv-ripple-on)":"var(--pv-ripple-off)"}"
      @pointerdown=${o=>this.holdStart(o,C)}
      @pointerup=${this.holdEnd}
      @pointerleave=${this.holdEnd}
      @pointercancel=${this.holdEnd}
      @contextmenu=${o=>o.preventDefault()}
      @click=${o=>this.tap(o,()=>this.hass&&q(this,this.hass,C))}
      @keydown=${o=>this.keyActivate(o,()=>this.hass&&q(this,this.hass,C))}
    >
      <ha-ripple></ha-ripple>
      <span class="row-icon">${S(L)}</span>
      <span class="row-label text">${V}</span>
      <span class="toggle ${t?"on":""}"><span class="knob"></span></span>
    </div>`}_renderTimer(C,V){let L=this._silentEntity,r=L?this._renderRow(L,"Silent Timer",l.volumeMute,!1,"silent"):A;if(!V.enabled)return a`<div class="notice" @click=${o=>o.stopPropagation()}>
          Timer entities are disabled. Enable them in the Pivot device settings to use the timer.
          <a href=${B1} target="_blank" rel="noreferrer">Timer setup</a>
        </div>
        ${r}`;if(V.state==="alerting")return a`<div class="strip alerting tap" @click=${o=>o.stopPropagation()}>
          <button class="tbtn word solid tap" @click=${o=>this.tap(o,()=>this._timerToggle(C))}>
            <ha-ripple></ha-ripple>${S(l.close)}<span>Stop</span>
          </button>
          <button class="tbtn word idle tap" @click=${o=>this.tap(o,()=>this._repeat(C))}>
            <ha-ripple></ha-ripple>${S(l.refresh)}<span>Repeat</span>
          </button>
          <ha-ripple></ha-ripple>
        </div>
        ${r}`;let e=V.state==="running",t=V.state==="paused",i=e||t,p=Z2(V,C.value);return a`<div class="strip tap" @click=${o=>o.stopPropagation()}>
        <button
          class="tbtn solid tap"
          aria-label=${e?"Pause timer":t?"Resume timer":"Start timer"}
          @click=${o=>this.tap(o,()=>this._timerToggle(C))}
        >
          <ha-ripple></ha-ripple><span class="ticon">${S(e?l.pause:l.play)}</span>
        </button>
        <button
          class="tbtn tap ${i?"solid":"idle"}"
          aria-label="Cancel timer"
          ?disabled=${!i}
          @click=${o=>this.tap(o,()=>i&&this._timerCancel(C))}
        >
          <ha-ripple></ha-ripple><span class="ticon">${S(t?l.refresh:l.close)}</span>
        </button>
        ${E.map(o=>a`<button
            class="tbtn preset tap ${p===o.minutes?"selected":""} ${i?"locked":""}"
            aria-pressed=${p===o.minutes?"true":"false"}
            @click=${d=>this.tap(d,()=>this._preset(C,V,o))}
          >
            <ha-ripple></ha-ripple>${o.label}
          </button>`)}
        <ha-ripple></ha-ripple>
      </div>
      ${r}`}_nameTap(C,V){if(V.isTimer)return this._activate(C);C.stopPropagation(),f(this,V.entityId??V.ids.entity)}_slideStart(C){this._lastSent=void 0,!C.isTimer&&!C.active&&this._activate()}_slide(C,V){C.isTimer||this._send(V)}_slideEnd(C,V,L){this._send.cancel(),C.isTimer?this._writeTimer(C,V,L):this._writeValue(L)}_writeValue(C){let V=this.device;if(!this.hass||!V)return;let L=F(this.hass,V.suffix,this.bankNumber);if(L.active){if(this._pending=void 0,C===this._lastSent)return;this._lastSent=C,x(this,this.hass,"number","set_value",{entity_id:L.ids.value,value:C})}else this._pending={value:C,until:Date.now()+X2}}_writeTimer(C,V,L){if(!this.hass||V.state!=="idle")return;let r=l2(L);this._setDuration(C,V,r,w1(r))}_preset(C,V,L){V.state==="idle"&&this._setDuration(C,V,L.minutes,L.value)}_setDuration(C,V,L,r){let e=this.device;if(!this.hass||!e)return;let t=Math.round(r);if(C.active){x(this,this.hass,"number","set_value",{entity_id:C.ids.value,value:t});return}V.enabled&&x(this,this.hass,"number","set_value",{entity_id:m(e.suffix).timerDuration,value:L}),x(this,this.hass,"number","set_value",{entity_id:C.ids.value,value:t})}async _timerToggle(C){let V=this.device;return!this.hass||!V?!1:k1(this.hass,"pivot","timer_toggle")?x(this,this.hass,"pivot","timer_toggle",{device:V.suffix,bank:C.n}):x(this,this.hass,"script","turn_on",{entity_id:"script.pivot_timer_toggle",variables:{device_suffix:V.suffix,bank:C.n}})}_timerCancel(C){let V=this.device;if(!(!this.hass||!V)){if(k1(this.hass,"pivot","timer_cancel")){x(this,this.hass,"pivot","timer_cancel",{device:V.suffix,bank:C.n});return}x(this,this.hass,"select","select_option",{entity_id:m(V.suffix).timerState,option:"idle"})}}async _repeat(C){if(!await this._timerToggle(C))return;this._repeatUntil=Date.now()+J2;let V=()=>{let L=this.device;if(!this._repeatUntil||!this.hass||!L||Date.now()>this._repeatUntil){this._repeatUntil=void 0;return}let r=this.hass.states[m(L.suffix).timerState];if(r?.state==="idle"&&Date.now()-Date.parse(r.last_changed)>Y2){this._repeatUntil=void 0,this._timerToggle(C);return}this._repeatTimer=setTimeout(V,250)};this._repeatTimer=setTimeout(V,250)}updated(C){super.updated(C);let V=this.device;if(!this.hass||!V)return;let L=F(this.hass,V.suffix,this.bankNumber);this._pending&&(Date.now()>this._pending.until?this._pending=void 0:L.active&&this._writeValue(this._pending.value)),clearTimeout(this._ticker),this._ticker=void 0;let r=m(V.suffix),e=Date.parse(this.hass.states[r.timerEnd]?.state??"");if(L.isTimer&&this.hass.states[r.timerState]?.state==="running"&&Number.isFinite(e)){let t=e-Date.now();if(t>-1e3){let i=((t-500)%1e3+1e3)%1e3+5;this._ticker=setTimeout(()=>this.requestUpdate(),i)}}}connectedCallback(){super.connectedCallback(),this.hasUpdated&&this.requestUpdate()}disconnectedCallback(){super.disconnectedCallback(),clearTimeout(this._ticker),this._ticker=void 0,clearTimeout(this._repeatTimer),this._repeatUntil=void 0,this._send.cancel()}};o1.styles=[w,n`
      ha-card.bank {
        position: relative;
        display: block;
        padding: 15px;
        border-radius: var(--pivot-card-radius, 20px);
        border: 1px solid transparent;
        box-shadow: none;
        text-align: left;
        overflow: hidden;
        cursor: pointer;
        background: var(--ha-card-background, var(--card-background-color, #1c1c1e));
        color: var(--pv-text);
      }
      ha-card.bank.active {
        border-color: var(--pv-active-border);
      }
      ha-card.bank.control-off {
        opacity: 0.4;
      }
      .head {
        display: flex;
        align-items: center;
        height: 30px;
        margin-top: -5px;
        border-radius: 10px;
      }
      .dot {
        display: flex;
        flex: none;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 20px;
      }
      .dot svg {
        width: 15px;
        height: 15px;
      }
      .head .label {
        margin-left: 10px;
      }
      .edit {
        display: flex;
        flex: none;
        align-items: center;
        justify-content: flex-end;
        gap: 6.8px;
        width: 90px;
        height: 25px;
        margin-left: auto;
        color: var(--pv-muted);
        font-size: 10px;
        letter-spacing: 0.05em;
        line-height: normal;
        white-space: nowrap;
      }
      .edit svg {
        flex: none;
        width: 15px;
        height: 15px;
        margin-right: -0.3px;
      }
      .name-row {
        display: flex;
        align-items: center;
        gap: 4px;
        height: 40px;
        margin-top: 5px;
        border-radius: 10px;
      }
      .name,
      .value {
        font-size: 25px;
        font-weight: 400;
        line-height: normal;
        white-space: nowrap;
      }
      .name {
        flex: 1 1 auto;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .value {
        flex: none;
        color: var(--pv-muted);
        font-family: var(--pv-value-font);
      }
      pivot-slider {
        margin-top: 10px;
        height: 23px;
      }
      .row {
        display: block;
        width: 100%;
        height: 50px;
        margin: 10px 0 -15px;
        border-radius: 10px;
      }
      .row.silent {
        margin-top: 5px;
      }
      .row.muted {
        opacity: 0.4;
        pointer-events: none;
      }
      .row.unavailable {
        opacity: 0.5;
      }
      .row .row-icon {
        position: absolute;
        left: 0;
        top: 10.5px;
        width: 20px;
        height: 20px;
        color: var(--pv-muted);
      }
      .row .row-label {
        position: absolute;
        left: 30px;
        right: 53px;
        top: 0;
        height: 39px;
        display: flex;
        align-items: center;
      }
      .row .toggle {
        position: absolute;
        right: 0;
        top: 8px;
      }
      .strip {
        position: relative;
        display: grid;
        grid-template-columns: 15% 15% repeat(4, minmax(0, 1fr));
        column-gap: 5px;
        height: 50px;
        margin-top: 20px;
        padding: 5px;
        border-radius: 10px;
        background: var(--pv-strip);
        cursor: default;
      }
      .strip.alerting {
        grid-template-columns: 1fr 1fr;
      }
      .tbtn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        height: 40px;
        min-width: 0;
        border-radius: 10px;
        cursor: pointer;
      }
      .tbtn.solid {
        background: var(--pv-button);
      }
      .tbtn.idle {
        background: var(--pv-button-idle);
      }
      .tbtn .ticon {
        width: 40%;
        max-width: 34px;
        aspect-ratio: 1;
      }
      .tbtn.idle .ticon {
        color: var(--pv-dimmed-icon);
      }
      .tbtn.word {
        font-size: 14px;
        line-height: normal;
      }
      .tbtn.word svg {
        width: 20px;
        height: 20px;
        flex: none;
      }
      .tbtn.word.solid {
        color: #ffffff;
      }
      .preset {
        font-size: 15px;
        line-height: normal;
        color: var(--pv-preset);
      }
      .preset.selected {
        background: var(--pv-button);
        color: var(--pv-preset-selected);
      }
      .preset.locked {
        color: var(--pv-dimmed-icon);
        pointer-events: none;
      }
      .notice {
        margin-top: 20px;
        font-size: 14px;
        line-height: 1.35;
        color: var(--pv-description);
        white-space: normal;
        cursor: default;
      }
      .notice a {
        color: inherit;
      }
    `];customElements.get("pivot-bank-card")||customElements.define("pivot-bank-card",o1);var A1=class extends u{constructor(){super(...arguments);this._sendVolume=e1((C,V)=>this._setVolume(C,V),200)}static getConfigElement(){let C=document.createElement("pivot-card-editor");return C.kind="settings",C}static getStubConfig(C){return{device:Z(C)[0]?.suffix??""}}validate(C){if(C.rows!==void 0){if(!Array.isArray(C.rows))throw new Error("rows must be a list");let V=C.rows.filter(L=>!h.includes(L));if(V.length)throw new Error(`Unknown rows: ${V.join(", ")}. Use ${h.join(", ")}.`)}}getCardSize(){return 6}getGridOptions(){return{columns:12,rows:"auto",min_columns:6}}get _rows(){return this._config?.rows?.length?this._config.rows:h}_mediaPlayer(){let C=this.device,V=C?this.hass?.states[m(C.suffix).mediaPlayerText]?.state:void 0;return V&&V.includes(".")&&!R.has(V)?V:void 0}watchedIds(){let C=this.device;if(!C)return[];let V=m(C.suffix);return[...["control_mode","announcements","mute_announcements","show_control_value","dim_when_idle"].map(V.toggle),V.mediaPlayerText,this._mediaPlayer()]}render(){let C=this.device;if(!this.hass||!this._config)return A;if(!C)return this.renderProblem();let V=this._rows,L=this._config.headings!==!1,r=[];if(L){let e=V.filter(i=>p1.includes(i)),t=V.filter(i=>m1.includes(i));e.length&&r.push(a`<div class="heading">Device</div>`,...e.map(i=>this._row(i))),t.length&&r.push(a`<div class="heading">Behaviour</div>`,...t.map(i=>this._row(i)))}else r.push(...V.map(e=>this._row(e)));return a`<div class="wrap pv-ready">${r}</div>`}_row(C){return C==="volume"?this._volume():this._toggle(C)}_toggle(C){let V=m(this.device.suffix),L=V.toggle(C),r=this.hass.states[L]?.state==="on",e=C==="dim_when_idle"&&this.hass.states[V.toggle("show_control_value")]?.state!=="on",t=this.hass.states[L]?.state,i=t===void 0||t==="unavailable",p=k[C],o=()=>this.hass&&q(this,this.hass,L);return a`<div
      class="srow tap ${e?"dependent-off":""} ${i?"disabled unavailable":""}"
      role="switch"
      tabindex=${e||i?-1:0}
      aria-checked=${r?"true":"false"}
      aria-label=${p.title}
      style="--ha-ripple-color:${r?"var(--pv-ripple-on)":"var(--pv-ripple-off)"}"
      @pointerdown=${d=>this.holdStart(d,L)}
      @pointerup=${this.holdEnd}
      @pointerleave=${this.holdEnd}
      @pointercancel=${this.holdEnd}
      @contextmenu=${d=>d.preventDefault()}
      @click=${d=>this.tap(d,o)}
      @keydown=${d=>this.keyActivate(d,o)}
    >
      <ha-ripple></ha-ripple>
      <span class="stitle text">${p.title}</span>
      <span class="sdesc text">${p.description}</span>
      <span class="toggle ${r?"on":""}"><span class="knob"></span></span>
    </div>`}_volume(){let C=this._mediaPlayer(),V=C?this.hass.states[C]:void 0,L=!!V&&!R.has(V.state),r=Number(V?.attributes.volume_level),e=Number.isFinite(r)?r*100:0;return a`<div class="volume ${L?"":"unavailable"}" title=${L?"":"The device media player is unavailable"}>
      <div class="text">Pivot Device Volume</div>
      <pivot-slider
        zero-cap
        .value=${e}
        .color=${"var(--pv-volume-fill)"}
        .trackColor=${"var(--pv-volume-track)"}
        .cap=${15}
        .label=${"Pivot device volume"}
        ?disabled=${!L}
        @pivot-slide-start=${()=>this._lastVolume=void 0}
        @pivot-slide=${t=>C&&this._sendVolume(C,t.detail.value)}
        @pivot-slide-end=${t=>{this._sendVolume.cancel(),C&&this._setVolume(C,t.detail.value)}}
        @pivot-slide-cancel=${()=>this._sendVolume.cancel()}
      ></pivot-slider>
    </div>`}_setVolume(C,V){!this.hass||V===this._lastVolume||(this._lastVolume=V,x(this,this.hass,"media_player","volume_set",{entity_id:C,volume_level:Math.round(V)/100}))}disconnectedCallback(){super.disconnectedCallback(),this._sendVolume.cancel()}};A1.styles=[w,n`
      .wrap {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .heading {
        padding: 1px;
        font-size: 22px;
        font-weight: 400;
        line-height: normal;
      }
      .srow {
        display: block;
        height: 50px;
        border: 1px solid transparent;
      }
      .srow.dependent-off {
        opacity: 0.3;
        pointer-events: none;
      }
      .srow .stitle,
      .srow .sdesc {
        position: absolute;
        left: 0;
        right: 53px;
      }
      .srow .stitle {
        top: 5.3px;
      }
      .srow .sdesc {
        top: 25.3px;
        color: var(--pv-description);
      }
      .srow .toggle {
        position: absolute;
        right: 0;
        top: 8.5px;
      }
      .volume {
        height: 72px;
      }
      .volume pivot-slider {
        margin-top: 10px;
        height: 5px;
      }
      .volume.unavailable pivot-slider,
      .srow.unavailable {
        opacity: 0.5;
      }
    `];customElements.get("pivot-settings-card")||customElements.define("pivot-settings-card",A1);var a1=class extends u{static getConfigElement(){let H=document.createElement("pivot-card-editor");return H.kind="status",H}static getStubConfig(H){return{device:Z(H)[0]?.suffix??""}}getCardSize(){return this._config?.show_name===!1?1:2}getGridOptions(){return{columns:"full",rows:"auto"}}watchedIds(){let H=this.device;if(!H||!this.hass)return[];let C=m(H.suffix),V=Math.round(N(this.hass.states[C.activeBank]?.state,NaN)),L=V>=1&&V<=4?C.bank(V):void 0,r=L?this.hass.states[L.entity]?.state:void 0;return[C.activeBank,C.toggle("control_mode"),L?.entity,L?.color,r&&r.includes(".")?r:void 0]}render(){let H=this.device;if(!this.hass||!this._config)return A;if(!H)return this.renderProblem();let C=m(H.suffix),V=this.hass.states[C.toggle("control_mode")]?.state==="on",L=Math.round(N(this.hass.states[C.activeBank]?.state,NaN)),r="Control mode off",e="var(--pv-muted)";if(V)if(L>=1&&L<=4){let i=F(this.hass,H.suffix,L);r=`Bank ${L} - ${Y(i)}`,e=this.hasAttribute("light")?i1(i.color):i.color}else r="Active bank unavailable";let t=this._config.name??H.name;return a`<div class="wrap pv-ready">
      ${this._config.show_name===!1?A:a`<div class="title">${t}</div>`}
      <div
        class="status tap"
        role="button"
        tabindex="0"
        @click=${i=>this.tap(i,()=>f(this,C.activeBank))}
        @keydown=${i=>this.keyActivate(i,()=>f(this,C.activeBank))}
      >
        <ha-ripple></ha-ripple>
        <span class="sdot" style="color:${e}">${S(l.circle)}</span>
        <span class="text">${r}</span>
      </div>
    </div>`}};a1.styles=[w,n`
      .wrap {
        display: block;
      }
      .title {
        padding: 1px;
        font-size: 45px;
        font-weight: 500;
        line-height: normal;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .title + .status {
        margin-top: 16px;
      }
      .status {
        display: flex;
        align-items: center;
        height: 30px;
        max-width: 100%;
        width: max-content;
      }
      .sdot {
        display: flex;
        flex: none;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
      }
      .sdot svg {
        width: 15px;
        height: 15px;
      }
      .status .text {
        margin-left: 10px;
        color: var(--pv-status-text);
      }
    `];customElements.get("pivot-status-card")||customElements.define("pivot-status-card",a1);var d1=class extends u{static getConfigElement(){let H=document.createElement("pivot-card-editor");return H.kind="device",H}static getStubConfig(H){return{device:Z(H)[0]?.suffix??""}}setConfig(H){super.setConfig(H);let C=H.device;this._children={status:{type:"custom:pivot-status-card",device:C,...H.name!==void 0?{name:H.name}:{}},banks:[1,2,3,4].map(V=>({type:"custom:pivot-bank-card",device:C,bank:V,...H.timer_silent_entity?{timer_silent_entity:H.timer_silent_entity}:{}})),settings:{type:"custom:pivot-settings-card",device:C}}}getCardSize(){return 20}getGridOptions(){return{columns:"full",rows:"auto"}}watchedIds(){return[]}render(){if(!this.hass||!this._config||!this._children)return A;if(!this.device)return this.renderProblem();let H=this._children,C=this._config.show_settings!==!1;return a`
      ${this._config.show_status===!1?A:a`<pivot-status-card .hass=${this.hass} .config=${H.status}></pivot-status-card>`}
      <div class="cols pv-ready ${C?"":"single"}">
        <div class="col banks">${H.banks.map(V=>a`<pivot-bank-card .hass=${this.hass} .config=${V}></pivot-bank-card>`)}</div>
        ${C?a`<div class="col settings"><pivot-settings-card .hass=${this.hass} .config=${H.settings}></pivot-settings-card></div>`:A}
      </div>
    `}shouldUpdate(){return!0}};d1.styles=[w,n`
      :host {
        container-type: inline-size;
      }
      .cols {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        column-gap: 32px;
        row-gap: 24px;
        align-items: start;
      }
      pivot-status-card + .cols {
        margin-top: 24px;
      }
      .cols.single {
        grid-template-columns: minmax(0, 1fr);
      }
      /* Each column used to be a layout-card: 4px padding plus 4px 4px 8px card
         margins, so cards sit 8px in (12px at the bottom)... */
      .col {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 8px 8px 12px;
        min-width: 0;
      }
      /* ...and on phones layout-card drops the side margins. */
      @media (max-width: 500px) {
        .col {
          padding-left: 4px;
          padding-right: 4px;
        }
      }
      /* Two 320px columns no longer fit: stack like a sections view. */
      @container (max-width: 671px) {
        .cols {
          grid-template-columns: minmax(0, 1fr);
        }
      }
    `];customElements.get("pivot-device-card")||customElements.define("pivot-device-card",d1);var C5=[{type:"pivot-device-card",name:"Pivot",description:"The whole Pivot dashboard for one dial: active bank, the four banks and its settings."},{type:"pivot-bank-card",name:"Pivot bank",description:"One Pivot bank: its entity, value, colour, toggles and timer controls."},{type:"pivot-status-card",name:"Pivot status",description:"A Pivot dial\u2019s name and its active bank."},{type:"pivot-settings-card",name:"Pivot settings",description:"Control mode, device volume and announcement settings for a Pivot dial."}];window.customCards=window.customCards||[];for(let M of C5)window.customCards.some(H=>H.type===M.type)||window.customCards.push({...M,preview:!0,documentationURL:H1});console.info("%c PIVOT CARDS %c 0.0.94 ","color:#fff;background:#545454;border-radius:4px 0 0 4px;padding:2px 4px","color:#545454;background:#e0e0e0;border-radius:0 4px 4px 0;padding:2px 4px");
