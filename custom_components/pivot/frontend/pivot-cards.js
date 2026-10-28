/*! Pivot dashboard cards v0.0.97. Built from frontend/ in pivot-integration; edit the source, not this file. Includes Lit (BSD-3-Clause) and Material Design Icons (Apache-2.0). */
var t1="https://alistairmerritt.github.io/pivot/dashboard/",w1="https://alistairmerritt.github.io/pivot/timer/",Y1=["#2889FF","#FF7D19","#97FF3D","#C800FF"],J1=new Set(["light","fan","climate","media_player","cover","number","input_number"]),G=new Set(["","unknown","unavailable","none"]),B1=["control_mode","volume"],P1=["announcements","mute_announcements","show_control_value","dim_when_idle"],Z=[...B1,...P1],R={control_mode:{title:"Control Mode",description:"Enable or disable Pivot control"},announcements:{title:"System Announcements",description:"Announce bank changes and triple-press via voice"},mute_announcements:{title:"Mute Announcements",description:"Silence all spoken announcements temporarily"},show_control_value:{title:"Display Persistent Value",description:"Keep current value visible on the LED ring when idle"},dim_when_idle:{title:"Dim Gauge LEDs While Idle",description:"Reduce LED brightness when not interacting with dial"}},Q=[{minutes:15,value:24,label:"15m"},{minutes:30,value:50,label:"30m"},{minutes:45,value:75,label:"45m"},{minutes:60,value:100,label:"60m"}],y1=Q.map(L=>L.minutes),z=6;function l(L){return{activeBank:`number.${L}_active_bank`,mediaPlayerText:`text.${L}_media_player_entity`,timerState:`select.${L}_timer_state`,timerDuration:`number.${L}_timer_duration`,timerEnd:`text.${L}_timer_end`,toggle:H=>`switch.${L}_${H}`,bank:H=>({entity:`text.${L}_bank_${H}_entity`,value:`number.${L}_bank_${H}_value`,passive:`binary_sensor.${L}_bank_${H}_passive`,color:`text.${L}_bank_${H}_color`,colorLight:`light.${L}_bank_${H}_color_light`,mirror:`switch.${L}_bank_${H}_mirror_light`,announce:`switch.${L}_bank_${H}_announce_value`})}}var C2="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z";var H2="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z";var V2="M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8M12,10A2,2 0 0,0 10,12A2,2 0 0,0 12,14A2,2 0 0,0 14,12A2,2 0 0,0 12,10M10,22C9.75,22 9.54,21.82 9.5,21.58L9.13,18.93C8.5,18.68 7.96,18.34 7.44,17.94L4.95,18.95C4.73,19.03 4.46,18.95 4.34,18.73L2.34,15.27C2.21,15.05 2.27,14.78 2.46,14.63L4.57,12.97L4.5,12L4.57,11L2.46,9.37C2.27,9.22 2.21,8.95 2.34,8.73L4.34,5.27C4.46,5.05 4.73,4.96 4.95,5.05L7.44,6.05C7.96,5.66 8.5,5.32 9.13,5.07L9.5,2.42C9.54,2.18 9.75,2 10,2H14C14.25,2 14.46,2.18 14.5,2.42L14.87,5.07C15.5,5.32 16.04,5.66 16.56,6.05L19.05,5.05C19.27,4.96 19.54,5.05 19.66,5.27L21.66,8.73C21.79,8.95 21.73,9.22 21.54,9.37L19.43,11L19.5,12L19.43,13L21.54,14.63C21.73,14.78 21.79,15.05 21.66,15.27L19.66,18.73C19.54,18.95 19.27,19.04 19.05,18.95L16.56,17.95C16.04,18.34 15.5,18.68 14.87,18.93L14.5,21.58C14.46,21.82 14.25,22 14,22H10M11.25,4L10.88,6.61C9.68,6.86 8.62,7.5 7.85,8.39L5.44,7.35L4.69,8.65L6.8,10.2C6.4,11.37 6.4,12.64 6.8,13.8L4.68,15.36L5.43,16.66L7.86,15.62C8.63,16.5 9.68,17.14 10.87,17.38L11.24,20H12.76L13.13,17.39C14.32,17.14 15.37,16.5 16.14,15.62L18.57,16.66L19.32,15.36L17.2,13.81C17.6,12.64 17.6,11.37 17.2,10.2L19.31,8.65L18.56,7.35L16.15,8.39C15.38,7.5 14.32,6.86 13.12,6.62L12.75,4H11.25Z";var L2="M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M13 10H11V4.1C11.3 4 11.7 4 12 4S12.7 4 13 4.1V10Z";var M2="M17.5,12A1.5,1.5 0 0,1 16,10.5A1.5,1.5 0 0,1 17.5,9A1.5,1.5 0 0,1 19,10.5A1.5,1.5 0 0,1 17.5,12M14.5,8A1.5,1.5 0 0,1 13,6.5A1.5,1.5 0 0,1 14.5,5A1.5,1.5 0 0,1 16,6.5A1.5,1.5 0 0,1 14.5,8M9.5,8A1.5,1.5 0 0,1 8,6.5A1.5,1.5 0 0,1 9.5,5A1.5,1.5 0 0,1 11,6.5A1.5,1.5 0 0,1 9.5,8M6.5,12A1.5,1.5 0 0,1 5,10.5A1.5,1.5 0 0,1 6.5,9A1.5,1.5 0 0,1 8,10.5A1.5,1.5 0 0,1 6.5,12M12,3A9,9 0 0,0 3,12A9,9 0 0,0 12,21A1.5,1.5 0 0,0 13.5,19.5C13.5,19.11 13.35,18.76 13.11,18.5C12.88,18.23 12.73,17.88 12.73,17.5A1.5,1.5 0 0,1 14.23,16H16A5,5 0 0,0 21,11C21,6.58 16.97,3 12,3Z";var r2="M14,19H18V5H14M6,19H10V5H6V19Z";var e2="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z";var t2="M8,5.14V19.14L19,12.14L8,5.14Z";var i2="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z";var o2="M12,20A7,7 0 0,1 5,13A7,7 0 0,1 12,6A7,7 0 0,1 19,13A7,7 0 0,1 12,20M19.03,7.39L20.45,5.97C20,5.46 19.55,5 19.04,4.56L17.62,6C16.07,4.74 14.12,4 12,4A9,9 0 0,0 3,13A9,9 0 0,0 12,22C17,22 21,17.97 21,13C21,10.88 20.26,8.93 19.03,7.39M11,14H13V8H11M15,1H9V3H15V1Z";var A2="M14,3.23V5.29C16.89,6.15 19,8.83 19,12C19,15.17 16.89,17.84 14,18.7V20.77C18,19.86 21,16.28 21,12C21,7.72 18,4.14 14,3.23M16.5,12C16.5,10.23 15.5,8.71 14,7.97V16C15.5,15.29 16.5,13.76 16.5,12M3,9V15H7L12,20V4L7,9H3Z";var a2="M3,9H7L12,4V20L7,15H3V9M16.59,12L14,9.41L15.41,8L18,10.59L20.59,8L22,9.41L19.41,12L22,14.59L20.59,16L18,13.41L15.41,16L14,14.59L16.59,12Z";var i1=globalThis,o1=i1.ShadowRoot&&(i1.ShadyCSS===void 0||i1.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,T1=Symbol(),d2=new WeakMap,j=class{constructor(H,C,V){if(this._$cssResult$=!0,V!==T1)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=H,this.t=C}get styleSheet(){let H=this.o,C=this.t;if(o1&&H===void 0){let V=C!==void 0&&C.length===1;V&&(H=d2.get(C)),H===void 0&&((this.o=H=new CSSStyleSheet).replaceSync(this.cssText),V&&d2.set(C,H))}return H}toString(){return this.cssText}},p2=L=>new j(typeof L=="string"?L:L+"",void 0,T1),s=(L,...H)=>{let C=L.length===1?L[0]:H.reduce((V,M,r)=>V+(e=>{if(e._$cssResult$===!0)return e.cssText;if(typeof e=="number")return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(M)+L[r+1],L[0]);return new j(C,L,T1)},m2=(L,H)=>{if(o1)L.adoptedStyleSheets=H.map(C=>C instanceof CSSStyleSheet?C:C.styleSheet);else for(let C of H){let V=document.createElement("style"),M=i1.litNonce;M!==void 0&&V.setAttribute("nonce",M),V.textContent=C.cssText,L.appendChild(V)}},F1=o1?L=>L:L=>L instanceof CSSStyleSheet?(H=>{let C="";for(let V of H.cssRules)C+=V.cssText;return p2(C)})(L):L;var{is:A5,defineProperty:a5,getOwnPropertyDescriptor:d5,getOwnPropertyNames:p5,getOwnPropertySymbols:m5,getPrototypeOf:n5}=Object,A1=globalThis,n2=A1.trustedTypes,v5=n2?n2.emptyScript:"",l5=A1.reactiveElementPolyfillSupport,X=(L,H)=>L,R1={toAttribute(L,H){switch(H){case Boolean:L=L?v5:null;break;case Object:case Array:L=L==null?L:JSON.stringify(L)}return L},fromAttribute(L,H){let C=L;switch(H){case Boolean:C=L!==null;break;case Number:C=L===null?null:Number(L);break;case Object:case Array:try{C=JSON.parse(L)}catch{C=null}}return C}},l2=(L,H)=>!A5(L,H),v2={attribute:!0,type:String,converter:R1,reflect:!1,useDefault:!1,hasChanged:l2};Symbol.metadata??=Symbol("metadata"),A1.litPropertyMetadata??=new WeakMap;var B=class extends HTMLElement{static addInitializer(H){this._$Ei(),(this.l??=[]).push(H)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(H,C=v2){if(C.state&&(C.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(H)&&((C=Object.create(C)).wrapped=!0),this.elementProperties.set(H,C),!C.noAccessor){let V=Symbol(),M=this.getPropertyDescriptor(H,V,C);M!==void 0&&a5(this.prototype,H,M)}}static getPropertyDescriptor(H,C,V){let{get:M,set:r}=d5(this.prototype,H)??{get(){return this[C]},set(e){this[C]=e}};return{get:M,set(e){let o=M?.call(this);r?.call(this,e),this.requestUpdate(H,o,V)},configurable:!0,enumerable:!0}}static getPropertyOptions(H){return this.elementProperties.get(H)??v2}static _$Ei(){if(this.hasOwnProperty(X("elementProperties")))return;let H=n5(this);H.finalize(),H.l!==void 0&&(this.l=[...H.l]),this.elementProperties=new Map(H.elementProperties)}static finalize(){if(this.hasOwnProperty(X("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(X("properties"))){let C=this.properties,V=[...p5(C),...m5(C)];for(let M of V)this.createProperty(M,C[M])}let H=this[Symbol.metadata];if(H!==null){let C=litPropertyMetadata.get(H);if(C!==void 0)for(let[V,M]of C)this.elementProperties.set(V,M)}this._$Eh=new Map;for(let[C,V]of this.elementProperties){let M=this._$Eu(C,V);M!==void 0&&this._$Eh.set(M,C)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(H){let C=[];if(Array.isArray(H)){let V=new Set(H.flat(1/0).reverse());for(let M of V)C.unshift(F1(M))}else H!==void 0&&C.push(F1(H));return C}static _$Eu(H,C){let V=C.attribute;return V===!1?void 0:typeof V=="string"?V:typeof H=="string"?H.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(H=>this.enableUpdating=H),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(H=>H(this))}addController(H){(this._$EO??=new Set).add(H),this.renderRoot!==void 0&&this.isConnected&&H.hostConnected?.()}removeController(H){this._$EO?.delete(H)}_$E_(){let H=new Map,C=this.constructor.elementProperties;for(let V of C.keys())this.hasOwnProperty(V)&&(H.set(V,this[V]),delete this[V]);H.size>0&&(this._$Ep=H)}createRenderRoot(){let H=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return m2(H,this.constructor.elementStyles),H}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(H=>H.hostConnected?.())}enableUpdating(H){}disconnectedCallback(){this._$EO?.forEach(H=>H.hostDisconnected?.())}attributeChangedCallback(H,C,V){this._$AK(H,V)}_$ET(H,C){let V=this.constructor.elementProperties.get(H),M=this.constructor._$Eu(H,V);if(M!==void 0&&V.reflect===!0){let r=(V.converter?.toAttribute!==void 0?V.converter:R1).toAttribute(C,V.type);this._$Em=H,r==null?this.removeAttribute(M):this.setAttribute(M,r),this._$Em=null}}_$AK(H,C){let V=this.constructor,M=V._$Eh.get(H);if(M!==void 0&&this._$Em!==M){let r=V.getPropertyOptions(M),e=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:R1;this._$Em=M;let o=e.fromAttribute(C,r.type);this[M]=o??this._$Ej?.get(M)??o,this._$Em=null}}requestUpdate(H,C,V,M=!1,r){if(H!==void 0){let e=this.constructor;if(M===!1&&(r=this[H]),V??=e.getPropertyOptions(H),!((V.hasChanged??l2)(r,C)||V.useDefault&&V.reflect&&r===this._$Ej?.get(H)&&!this.hasAttribute(e._$Eu(H,V))))return;this.C(H,C,V)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(H,C,{useDefault:V,reflect:M,wrapped:r},e){V&&!(this._$Ej??=new Map).has(H)&&(this._$Ej.set(H,e??C??this[H]),r!==!0||e!==void 0)||(this._$AL.has(H)||(this.hasUpdated||V||(C=void 0),this._$AL.set(H,C)),M===!0&&this._$Em!==H&&(this._$Eq??=new Set).add(H))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(C){Promise.reject(C)}let H=this.scheduleUpdate();return H!=null&&await H,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[M,r]of this._$Ep)this[M]=r;this._$Ep=void 0}let V=this.constructor.elementProperties;if(V.size>0)for(let[M,r]of V){let{wrapped:e}=r,o=this[M];e!==!0||this._$AL.has(M)||o===void 0||this.C(M,void 0,r,o)}}let H=!1,C=this._$AL;try{H=this.shouldUpdate(C),H?(this.willUpdate(C),this._$EO?.forEach(V=>V.hostUpdate?.()),this.update(C)):this._$EM()}catch(V){throw H=!1,this._$EM(),V}H&&this._$AE(C)}willUpdate(H){}_$AE(H){this._$EO?.forEach(C=>C.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(H)),this.updated(H)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(H){return!0}update(H){this._$Eq&&=this._$Eq.forEach(C=>this._$ET(C,this[C])),this._$EM()}updated(H){}firstUpdated(H){}};B.elementStyles=[],B.shadowRootOptions={mode:"open"},B[X("elementProperties")]=new Map,B[X("finalized")]=new Map,l5?.({ReactiveElement:B}),(A1.reactiveElementVersions??=[]).push("2.1.2");var E1=globalThis,x2=L=>L,a1=E1.trustedTypes,Z2=a1?a1.createPolicy("lit-html",{createHTML:L=>L}):void 0,D1="$lit$",P=`lit$${Math.random().toFixed(9).slice(2)}$`,$1="?"+P,x5=`<${$1}>`,N=document,J=()=>N.createComment(""),C1=L=>L===null||typeof L!="object"&&typeof L!="function",N1=Array.isArray,O2=L=>N1(L)||typeof L?.[Symbol.iterator]=="function",_1=`[ 	
\f\r]`,Y=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,s2=/-->/g,u2=/>/g,D=RegExp(`>|${_1}(?:([^\\s"'>=/]+)(${_1}*=${_1}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),S2=/'/g,c2=/"/g,g2=/^(?:script|style|textarea|title)$/i,W1=L=>(H,...C)=>({_$litType$:L,strings:H,values:C}),a=W1(1),C3=W1(2),H3=W1(3),y=Symbol.for("lit-noChange"),p=Symbol.for("lit-nothing"),h2=new WeakMap,$=N.createTreeWalker(N,129);function f2(L,H){if(!N1(L)||!L.hasOwnProperty("raw"))throw Error("invalid template strings array");return Z2!==void 0?Z2.createHTML(H):H}var k2=(L,H)=>{let C=L.length-1,V=[],M,r=H===2?"<svg>":H===3?"<math>":"",e=Y;for(let o=0;o<C;o++){let i=L[o],t,d,A=-1,m=0;for(;m<i.length&&(e.lastIndex=m,d=e.exec(i),d!==null);)m=e.lastIndex,e===Y?d[1]==="!--"?e=s2:d[1]!==void 0?e=u2:d[2]!==void 0?(g2.test(d[2])&&(M=RegExp("</"+d[2],"g")),e=D):d[3]!==void 0&&(e=D):e===D?d[0]===">"?(e=M??Y,A=-1):d[1]===void 0?A=-2:(A=e.lastIndex-d[2].length,t=d[1],e=d[3]===void 0?D:d[3]==='"'?c2:S2):e===c2||e===S2?e=D:e===s2||e===u2?e=Y:(e=D,M=void 0);let n=e===D&&L[o+1].startsWith("/>")?" ":"";r+=e===Y?i+x5:A>=0?(V.push(t),i.slice(0,A)+D1+i.slice(A)+P+n):i+P+(A===-2?o:n)}return[f2(L,r+(L[C]||"<?>")+(H===2?"</svg>":H===3?"</math>":"")),V]},H1=class L{constructor({strings:H,_$litType$:C},V){let M;this.parts=[];let r=0,e=0,o=H.length-1,i=this.parts,[t,d]=k2(H,C);if(this.el=L.createElement(t,V),$.currentNode=this.el.content,C===2||C===3){let A=this.el.content.firstChild;A.replaceWith(...A.childNodes)}for(;(M=$.nextNode())!==null&&i.length<o;){if(M.nodeType===1){if(M.hasAttributes())for(let A of M.getAttributeNames())if(A.endsWith(D1)){let m=d[e++],n=M.getAttribute(A).split(P),v=/([.?@])?(.*)/.exec(m);i.push({type:1,index:r,name:v[2],strings:n,ctor:v[1]==="."?p1:v[1]==="?"?m1:v[1]==="@"?n1:I}),M.removeAttribute(A)}else A.startsWith(P)&&(i.push({type:6,index:r}),M.removeAttribute(A));if(g2.test(M.tagName)){let A=M.textContent.split(P),m=A.length-1;if(m>0){M.textContent=a1?a1.emptyScript:"";for(let n=0;n<m;n++)M.append(A[n],J()),$.nextNode(),i.push({type:2,index:++r});M.append(A[m],J())}}}else if(M.nodeType===8)if(M.data===$1)i.push({type:2,index:r});else{let A=-1;for(;(A=M.data.indexOf(P,A+1))!==-1;)i.push({type:7,index:r}),A+=P.length-1}r++}}static createElement(H,C){let V=N.createElement("template");return V.innerHTML=H,V}};function W(L,H,C=L,V){if(H===y)return H;let M=V!==void 0?C._$Co?.[V]:C._$Cl,r=C1(H)?void 0:H._$litDirective$;return M?.constructor!==r&&(M?._$AO?.(!1),r===void 0?M=void 0:(M=new r(L),M._$AT(L,C,V)),V!==void 0?(C._$Co??=[])[V]=M:C._$Cl=M),M!==void 0&&(H=W(L,M._$AS(L,H.values),M,V)),H}var d1=class{constructor(H,C){this._$AV=[],this._$AN=void 0,this._$AD=H,this._$AM=C}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(H){let{el:{content:C},parts:V}=this._$AD,M=(H?.creationScope??N).importNode(C,!0);$.currentNode=M;let r=$.nextNode(),e=0,o=0,i=V[0];for(;i!==void 0;){if(e===i.index){let t;i.type===2?t=new K(r,r.nextSibling,this,H):i.type===1?t=new i.ctor(r,i.name,i.strings,this,H):i.type===6&&(t=new v1(r,this,H)),this._$AV.push(t),i=V[++o]}e!==i?.index&&(r=$.nextNode(),e++)}return $.currentNode=N,M}p(H){let C=0;for(let V of this._$AV)V!==void 0&&(V.strings!==void 0?(V._$AI(H,V,C),C+=V.strings.length-2):V._$AI(H[C])),C++}},K=class L{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(H,C,V,M){this.type=2,this._$AH=p,this._$AN=void 0,this._$AA=H,this._$AB=C,this._$AM=V,this.options=M,this._$Cv=M?.isConnected??!0}get parentNode(){let H=this._$AA.parentNode,C=this._$AM;return C!==void 0&&H?.nodeType===11&&(H=C.parentNode),H}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(H,C=this){H=W(this,H,C),C1(H)?H===p||H==null||H===""?(this._$AH!==p&&this._$AR(),this._$AH=p):H!==this._$AH&&H!==y&&this._(H):H._$litType$!==void 0?this.$(H):H.nodeType!==void 0?this.T(H):O2(H)?this.k(H):this._(H)}O(H){return this._$AA.parentNode.insertBefore(H,this._$AB)}T(H){this._$AH!==H&&(this._$AR(),this._$AH=this.O(H))}_(H){this._$AH!==p&&C1(this._$AH)?this._$AA.nextSibling.data=H:this.T(N.createTextNode(H)),this._$AH=H}$(H){let{values:C,_$litType$:V}=H,M=typeof V=="number"?this._$AC(H):(V.el===void 0&&(V.el=H1.createElement(f2(V.h,V.h[0]),this.options)),V);if(this._$AH?._$AD===M)this._$AH.p(C);else{let r=new d1(M,this),e=r.u(this.options);r.p(C),this.T(e),this._$AH=r}}_$AC(H){let C=h2.get(H.strings);return C===void 0&&h2.set(H.strings,C=new H1(H)),C}k(H){N1(this._$AH)||(this._$AH=[],this._$AR());let C=this._$AH,V,M=0;for(let r of H)M===C.length?C.push(V=new L(this.O(J()),this.O(J()),this,this.options)):V=C[M],V._$AI(r),M++;M<C.length&&(this._$AR(V&&V._$AB.nextSibling,M),C.length=M)}_$AR(H=this._$AA.nextSibling,C){for(this._$AP?.(!1,!0,C);H!==this._$AB;){let V=x2(H).nextSibling;x2(H).remove(),H=V}}setConnected(H){this._$AM===void 0&&(this._$Cv=H,this._$AP?.(H))}},I=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(H,C,V,M,r){this.type=1,this._$AH=p,this._$AN=void 0,this.element=H,this.name=C,this._$AM=M,this.options=r,V.length>2||V[0]!==""||V[1]!==""?(this._$AH=Array(V.length-1).fill(new String),this.strings=V):this._$AH=p}_$AI(H,C=this,V,M){let r=this.strings,e=!1;if(r===void 0)H=W(this,H,C,0),e=!C1(H)||H!==this._$AH&&H!==y,e&&(this._$AH=H);else{let o=H,i,t;for(H=r[0],i=0;i<r.length-1;i++)t=W(this,o[V+i],C,i),t===y&&(t=this._$AH[i]),e||=!C1(t)||t!==this._$AH[i],t===p?H=p:H!==p&&(H+=(t??"")+r[i+1]),this._$AH[i]=t}e&&!M&&this.j(H)}j(H){H===p?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,H??"")}},p1=class extends I{constructor(){super(...arguments),this.type=3}j(H){this.element[this.name]=H===p?void 0:H}},m1=class extends I{constructor(){super(...arguments),this.type=4}j(H){this.element.toggleAttribute(this.name,!!H&&H!==p)}},n1=class extends I{constructor(H,C,V,M,r){super(H,C,V,M,r),this.type=5}_$AI(H,C=this){if((H=W(this,H,C,0)??p)===y)return;let V=this._$AH,M=H===p&&V!==p||H.capture!==V.capture||H.once!==V.once||H.passive!==V.passive,r=H!==p&&(V===p||M);M&&this.element.removeEventListener(this.name,this,V),r&&this.element.addEventListener(this.name,this,H),this._$AH=H}handleEvent(H){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,H):this._$AH.handleEvent(H)}},v1=class{constructor(H,C,V){this.element=H,this.type=6,this._$AN=void 0,this._$AM=C,this.options=V}get _$AU(){return this._$AM._$AU}_$AI(H){W(this,H)}},b2={M:D1,P,A:$1,C:1,L:k2,R:d1,D:O2,V:W,I:K,H:I,N:m1,U:n1,B:p1,F:v1},Z5=E1.litHtmlPolyfillSupport;Z5?.(H1,K),(E1.litHtmlVersions??=[]).push("3.3.3");var w2=(L,H,C)=>{let V=C?.renderBefore??H,M=V._$litPart$;if(M===void 0){let r=C?.renderBefore??null;V._$litPart$=M=new K(H.insertBefore(J(),r),r,void 0,C??{})}return M._$AI(L),M};var I1=globalThis,O=class extends B{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let H=super.createRenderRoot();return this.renderOptions.renderBefore??=H.firstChild,H}update(H){let C=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(H),this._$Do=w2(C,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return y}};O._$litElement$=!0,O.finalized=!0,I1.litElementHydrateSupport?.({LitElement:O});var s5=I1.litElementPolyfillSupport;s5?.({LitElement:O});(I1.litElementVersions??=[]).push("4.2.2");function u(L,H,C){L.dispatchEvent(new CustomEvent(H,{detail:C,bubbles:!0,composed:!0}))}var T=(L,H)=>u(L,"hass-more-info",{entityId:H}),V1=L=>u(L,"haptic","light");async function c(L,H,C,V,M){try{return await H.callService(C,V,M),!0}catch(r){let e=r?.message??String(r);return console.warn(`Pivot: ${C}.${V} failed`,r),u(L,"hass-notification",{message:`Pivot: ${e}`}),!1}}var L1=(L,H,C)=>c(L,H,C.split(".")[0],"toggle",{entity_id:C}),U1=(L,H,C)=>!!L.services?.[H]?.[C];function l1(L,H){let C=0,V,M,r=()=>{C=Date.now(),V=void 0;let o=M;M=void 0,o&&L(...o)},e=((...o)=>{M=o;let i=H-(Date.now()-C);i<=0?(V&&clearTimeout(V),r()):V||(V=setTimeout(r,i))});return e.cancel=()=>{V&&clearTimeout(V),V=void 0,M=void 0},e.flush=()=>{M&&(V&&clearTimeout(V),r())},e}var P2=/^number\.(.+)_active_bank$/,B2=new WeakMap;function u5(L,H){if(!H||!L.entities)return;let C=Object.values(L.entities).filter(V=>V.device_id===H&&V.entity_id.startsWith("switch."));return C.find(V=>V.entity_id.endsWith("_timer_silent_mode"))?.entity_id??C.find(V=>(V.name??"").toLowerCase()==="timer silent mode")?.entity_id}function S5(L){let H=[];for(let C of Object.values(L.entities??{})){if(C.platform!=="pivot")continue;let V=P2.exec(C.entity_id);if(!V)continue;let M=C.device_id?L.devices?.[C.device_id]:void 0,r=M?.identifiers?.find(e=>e[0]==="pivot")?.[1];H.push({suffix:V[1],name:M?.name_by_user||M?.name||V[1],deviceId:C.device_id,esphomeDeviceId:r,timerSilentEntity:u5(L,r)})}return H}function c5(L){let H=[];for(let C of Object.keys(L.states)){let V=P2.exec(C);V&&L.states[`text.${V[1]}_bank_1_entity`]&&H.push({suffix:V[1],name:V[1]})}return H}function h(L){if(!L)return[];let H;if(L.entities&&Object.keys(L.entities).length){let C=B2.get(L.entities);C&&C.devices===L.devices?H=C.list:(H=S5(L).sort((V,M)=>V.name.localeCompare(M.name)),B2.set(L.entities,{devices:L.devices,list:H}))}return H&&H.length?H:c5(L).sort((C,V)=>C.name.localeCompare(V.name))}function y2(L,H){if(!(!L||!H))return h(L).find(C=>C.suffix===H)??(L.states[`number.${H}_active_bank`]?{suffix:H,name:H}:void 0)}function x1(L,H){let C=L===void 0?NaN:parseFloat(L);return Number.isFinite(C)?C:H}var Z1=(L,H,C)=>Math.min(C,Math.max(H,L));function s1(L){let H=[1,3,5].map(V=>parseInt(L.slice(V,V+2),16));return(.2126*H[0]+.7152*H[1]+.0722*H[2])/255<=.82?L:"#"+H.map(V=>Math.round(V*.45+112*.55).toString(16).padStart(2,"0")).join("")}function h5(L){return L&&/^#[0-9a-f]{6}$/i.test(L.trim())?L.trim():void 0}function g(L,H,C){let V=l(H),M=V.bank(C),r=(L.states[M.entity]?.state??"").trim(),e=r.toLowerCase()==="timer",o=!e&&r.includes(".")&&!G.has(r.toLowerCase())?r:void 0;return{n:C,ids:M,raw:r,isTimer:e,entityId:o,domain:o?o.split(".")[0]:"",bound:o?L.states[o]:void 0,value:Z1(x1(L.states[M.value]?.state,0),0,100),passive:L.states[M.passive]?.state==="on",color:h5(L.states[M.color]?.state)??Y1[C-1],active:Math.round(x1(L.states[V.activeBank]?.state,NaN))===C,controlOn:L.states[V.toggle("control_mode")]?.state==="on"}}function G1(L){return L.isTimer?!0:!!L.bound&&!G.has(L.bound.state)}function U(L){return L.isTimer?"Timer":L.entityId?L.bound?.attributes.friendly_name||L.entityId:"No entity assigned"}var O5=L=>L.isTimer||!!L.entityId;function M1(L,H){let C=Math.round(x1(L.states[l(H).activeBank]?.state,NaN));return C>=1&&C<=4?C:void 0}function R2(L,H){for(let C=1;C<=4;C++)if(g(L,H,C).isTimer)return C}function _2(L,H,C,V){let M=C==="all"?[1,2,3,4]:[...new Set(C)].sort((r,e)=>r-e);return V?M.filter(r=>O5(g(L,H,r))):M}var E2=L=>L.domain==="light",D2=L=>J1.has(L.domain)&&!L.passive,$2=L=>!L.passive&&(L.isTimer||!!L.entityId);function N2(L,H,C){let V=l(H),M=L.states[V.timerState];if(!M)return{enabled:!1,state:"idle"};let r=x1(L.states[V.timerDuration]?.state,NaN),e=L.states[V.timerEnd]?.state??"",o;return M.state==="running"&&/^\d{4}-\d{2}-\d{2}T/.test(e)?o=Math.max(0,Math.round((Date.parse(e)-C)/1e3)):M.state==="paused"&&/^P\d+$/.test(e)&&(o=parseInt(e.slice(1),10)),{enabled:!0,state:M.state,durationMin:Number.isFinite(r)?r:void 0,remainingSecs:o}}function T2(L){let H=Math.max(0,Math.floor(L)),C=Math.floor(H/3600),V=Math.floor(H%3600/60),M=String(H%60).padStart(2,"0");return C>0?`${C}:${String(V).padStart(2,"0")}:${M}`:`${V}:${M}`}var F2=L=>`${L} ${L===1?"min":"mins"}`;function g5(L){let H=Math.round(L);return Math.abs(L%1)===.5&&H%2!==0?H-1:H}function W2(L){return Z1(g5(1+L/100*59),1,60)}function u1(L){return Z1((L-1)/59*100,0,100)}function f5(L){let H=Q.find(C=>C.value===Math.round(L));return H?H.minutes:Math.round(L/100*60)}function k5(L,H){return L.state==="alerting"?"Timer Finished":L.state==="running"&&L.remainingSecs!==void 0?T2(L.remainingSecs):L.state==="paused"&&L.remainingSecs!==void 0?`Paused \u2013 ${T2(L.remainingSecs)}`:L.enabled&&L.durationMin!==void 0?F2(Math.round(L.durationMin)):F2(f5(H))}function I2(L,H){let C=L.durationMin!==void 0?L.durationMin*60:void 0;return(L.state==="running"||L.state==="paused")&&L.remainingSecs!==void 0&&C?L.remainingSecs<=C+2?Z1(L.remainingSecs/C*100,0,100):H:L.state==="idle"&&L.enabled&&L.durationMin!==void 0?u1(L.durationMin):H}function U2(L){return L?L.map(H=>Q.find(C=>C.minutes===H)??{minutes:H,value:Math.round(u1(H)),label:`${H}m`}):Q}var G2=L=>Number.isInteger(L)&&L>=1&&L<=60;function S1(L){if(L===void 0)return;if(!Array.isArray(L))return"timer_presets must be a list of minutes, like [15, 30, 45, 60]";if(L.length>z)return`timer_presets can have at most ${z} entries`;let H=L.filter(C=>!G2(C));if(H.length)return`timer_presets must be whole minutes from 1 to 60 (not ${H.join(", ")})`;if(new Set(L).size!==L.length)return"timer_presets has the same minutes twice"}function Q2(L){let H=(Array.isArray(L)?L:[]).map(C=>Number(String(C).trim())).filter(G2);return[...new Set(H)].slice(0,z).sort((C,V)=>C-V)}function z2(L,H,C=Q){if(L.state==="idle")return L.enabled&&L.durationMin!==void 0?C.find(V=>V.minutes===Math.round(L.durationMin))?.minutes:C.find(V=>V.value===Math.round(H))?.minutes}var b5={open:"Open",closed:"Closed",opening:"Opening",closing:"Closing"};function K2(L,H){if(L.isTimer)return k5(H,L.value);if(!G1(L))return"";let C=L.bound.state,V=Math.round(L.value);if(L.passive)return L.domain==="cover"?b5[C]??"":C==="on"?"On":L.value===0?"Off":"On";if(L.domain==="cover")return V===0?"Closed":V===100?"Open":`${V}% Open`;if(L.domain==="climate"){let M=L.bound.attributes.temperature;return M==null||M===""?"":`${Math.round(Number(M))}\xB0`}return C==="off"?"Off":V===0?"":`${V}%`}function q2(L){return!L.isTimer&&L.bound?.state==="off"}var w5=!!document.querySelector("home-assistant")&&!customElements.get("home-assistant"),j2=w5?customElements.whenDefined("home-assistant"):void 0;function f(L,H){let C=()=>{customElements.get(L)||customElements.define(L,H)};j2?j2.then(C):C()}var B5={control_mode:R.control_mode.title,volume:"Pivot Device Volume",announcements:R.announcements.title,mute_announcements:R.mute_announcements.title,show_control_value:R.show_control_value.title,dim_when_idle:R.dim_when_idle.title},X2='Show "Device" and "Behaviour" headings',Y2="Put settings on a card background",J2={device:"Pivot device",bank:"Bank",name:"Title (optional)",show_title:"Show title",show_active_bank:"Show active bank",banks_mode:"Banks to show",banks_chosen:"Which banks",hide_unassigned:"Hide banks with nothing assigned",bank_columns:"Banks per row",show_edit:"Show EDIT ENTITY",show_bank_options:"Show Mirror Light Colour and Announce Value",timer_presets:"Timer presets (minutes)",show_silent_timer:"Show Silent Timer",timer_silent_entity:"Timer silent switch (optional, found automatically)",show_settings:"Show device and behaviour settings",settings_rows:"Settings to show",rows:"Settings to show",settings_headings:X2,headings:X2,settings_background:Y2,background:Y2,settings_position:"Position"},Q1={bank:"The active bank follows the dial. The timer bank finds whichever bank is the timer.",bank_columns:"Two per row needs about 610 px for the banks. Narrower, they stack.",timer_presets:`Up to ${z}, each 1 to 60 minutes. Remove them all to keep just play and cancel.`,show_settings:"Turn off to put them somewhere else with the Pivot settings card."},P5=[1,2,3,5,10,15,20,25,30,40,45,50,60],y5={device:["device","name","show_title","show_active_bank","show_status","banks","hide_unassigned","bank_columns","show_edit","show_bank_options","timer_presets","show_silent_timer","timer_silent_entity","show_settings","settings_rows","settings_headings","settings_background","settings_position"],bank:["device","bank","show_edit","show_bank_options","timer_presets","show_silent_timer","timer_silent_entity"],status:["device","name","show_title","show_name","show_active_bank"],settings:["device","rows","headings","background"]},z1=(L,H)=>L.length===H.length&&L.every((C,V)=>C===H[V]);function T5(L,H){let C=H,V={show_edit:C.show_edit!==!1,show_bank_options:C.show_bank_options!==!1,timer_presets:(Array.isArray(C.timer_presets)?C.timer_presets:y1).map(String),show_silent_timer:C.show_silent_timer!==!1,timer_silent_entity:C.timer_silent_entity??""},M=C.device??"";if(L==="device"){let r=C.show_status!==!1;return{device:M,show_title:r&&C.show_title!==!1,name:C.name??"",show_active_bank:r&&C.show_active_bank!==!1,banks_mode:Array.isArray(C.banks)?"choose":C.banks??"all",banks_chosen:Array.isArray(C.banks)?C.banks.map(String):["1","2","3","4"],hide_unassigned:C.hide_unassigned===!0,bank_columns:String(C.bank_columns??1),...V,show_settings:C.show_settings!==!1,settings_rows:Array.isArray(C.settings_rows)?C.settings_rows:[...Z],settings_headings:C.settings_headings!==!1,settings_background:C.settings_background===!0,settings_position:C.settings_position??"beside"}}return L==="bank"?{device:M,bank:String(C.bank??1),...V}:L==="status"?{device:M,show_title:C.show_title!==!1&&C.show_name!==!1,name:C.name??"",show_active_bank:C.show_active_bank!==!1}:{device:M,rows:Array.isArray(C.rows)?C.rows:[...Z],headings:C.headings!==!1,background:C.background===!0}}function F5(L,H,C){let V={type:C?.type??`custom:pivot-${L}-card`,device:H.device??""},M=t=>{H[t]===!1&&(V[t]=!1)},r=t=>{H[t]===!0&&(V[t]=!0)},e=t=>{let d=typeof H[t]=="string"?H[t]:"";d.trim()&&(V[t]=d)},o=(t,d)=>{let A=Array.isArray(d)?d:[],m=Array.isArray(C?.[t])?C[t]:Z,v=!z1(m,Z.filter(x=>m.includes(x)))?[...m.filter(x=>A.includes(x)),...Z.filter(x=>A.includes(x)&&!m.includes(x))]:Z.filter(x=>A.includes(x));z1(v,Z)||(V[t]=v)},i=()=>{M("show_edit"),M("show_bank_options");let t=Q2(H.timer_presets);z1(t,y1)||(V.timer_presets=t),M("show_silent_timer"),e("timer_silent_entity")};if(L==="device"){M("show_title"),e("name"),M("show_active_bank");let t=H.banks_mode;if(t==="choose"){let d=(Array.isArray(H.banks_chosen)?H.banks_chosen:[]).map(Number).filter(A=>A>=1&&A<=4);V.banks=[...new Set(d)].sort((A,m)=>A-m)}else(t==="active"||t==="timer")&&(V.banks=t);t!=="active"&&t!=="timer"&&(r("hide_unassigned"),String(H.bank_columns)==="2"&&(V.bank_columns=2)),i(),M("show_settings"),o("settings_rows",H.settings_rows),M("settings_headings"),r("settings_background"),H.settings_position==="below"&&(V.settings_position="below")}else if(L==="bank"){let t=String(H.bank??"1");V.bank=/^[1-4]$/.test(t)?Number(t):t,i()}else L==="status"?(M("show_title"),e("name"),M("show_active_bank")):(o("rows",H.rows),M("headings"),r("background"));for(let[t,d]of Object.entries(C??{}))!(t in V)&&!y5[L].includes(t)&&(V[t]=d);return V}var k=(L,H={})=>({name:L,selector:{boolean:{}},...H}),K1=(L,H)=>({name:L,selector:{select:{mode:"list",options:H}}}),q1=(L,H)=>({name:L,selector:{select:{multiple:!0,mode:"list",options:H}}}),j1=(L,H,C,V=!1)=>({name:"",type:"expandable",flatten:!0,title:L,iconPath:H,expanded:V,schema:C}),C5=()=>Z.map(L=>({value:L,label:B5[L]})),H5;function R5(){return customElements.get("ha-form")?Promise.resolve(!0):(H5??=(async()=>{try{await(await window.loadCardHelpers?.())?.createCardElement({type:"entities",entities:[]})?.constructor.getConfigElement?.()}catch{}return Promise.race([customElements.whenDefined("ha-form").then(()=>!0),new Promise(L=>setTimeout(()=>L(!!customElements.get("ha-form")),3e3))])})(),H5)}var r1=class extends O{constructor(){super(),this.kind="device"}setConfig(H){this._config=H}connectedCallback(){super.connectedCallback(),R5().then(H=>this._haForm=H)}get _devices(){return h(this.hass)}_bankOptions(){let H=this._config?.device,C=!!H&&!!this.hass&&this._devices.some(V=>V.suffix===H);return[1,2,3,4].map(V=>({value:String(V),label:C?`Bank ${V} \xB7 ${U(g(this.hass,H,V))}`:`Bank ${V}`}))}_schema(H){let C=this._devices,V=C.map(t=>({value:t.suffix,label:t.name===t.suffix?t.suffix:`${t.name} (${t.suffix})`})),M=H.device;M&&!C.some(t=>t.suffix===M)&&V.push({value:M,label:`${M} (not found)`});let r=[{name:"device",required:!0,selector:{select:{mode:"dropdown",options:V}}}],e=[k("show_title"),{name:"name",disabled:H.show_title===!1,selector:{text:{}}},k("show_active_bank")],o=[k("show_edit"),k("show_bank_options")],i=j1("Timer",o2,[{name:"timer_presets",selector:{select:{multiple:!0,custom_value:!0,options:P5.map(t=>({value:String(t),label:`${t} min`}))}}},k("show_silent_timer"),{name:"timer_silent_entity",selector:{entity:{domain:"switch"}}}]);if(this.kind==="device"){let t=H.banks_mode==="all"||H.banks_mode==="choose",d=j1("Banks",L2,[K1("banks_mode",[{value:"all",label:"All four"},{value:"choose",label:"Choose banks"},{value:"active",label:"Only the active bank (follows the dial)"},{value:"timer",label:"Only the timer bank"}]),...H.banks_mode==="choose"?[q1("banks_chosen",this._bankOptions())]:[],...t?[k("hide_unassigned"),K1("bank_columns",[{value:"1",label:"One"},{value:"2",label:"Two"}])]:[],...o],!0),A=j1("Settings",V2,[k("show_settings"),...H.show_settings!==!1?[q1("settings_rows",C5()),k("settings_headings"),k("settings_background"),K1("settings_position",[{value:"beside",label:"Beside the banks when there\u2019s room"},{value:"below",label:"Below the banks"}])]:[]]);r.push(...e,d,i,A)}else this.kind==="bank"?r.push({name:"bank",required:!0,selector:{select:{mode:"dropdown",options:[...this._bankOptions(),{value:"active",label:"The active bank (follows the dial)"},{value:"timer",label:"The timer bank"}]}}},...o,i):this.kind==="status"?r.push(...e):r.push(q1("rows",C5()),k("headings"),k("background"));return r}_commit(H){let C=F5(this.kind,H,this._config);this._config=C,u(this,"config-changed",{config:C})}render(){if(!this.hass||!this._config)return p;let H=this._devices.length?p:a`<p class="hint">No Pivot devices found. Add one under Settings → Devices &amp; services → Pivot.</p>`,C=T5(this.kind,this._config),V=this._schema(C);return this._haForm?a`${H}<ha-form
          .hass=${this.hass}
          .data=${C}
          .schema=${V}
          .computeLabel=${M=>J2[M.name]??M.title??M.name}
          .computeHelper=${M=>Q1[M.name]}
          @value-changed=${M=>{M.stopPropagation(),this._commit(M.detail.value)}}
        ></ha-form>`:a`${H}<div class="fallback">${V.map(M=>this._renderFallback(M,C))}</div>`}_renderFallback(H,C){if(H.type==="expandable")return a`<fieldset>
        <legend>${H.title}</legend>
        ${(H.schema??[]).map(t=>this._renderFallback(t,C))}
      </fieldset>`;let V=t=>this._commit({...C,[H.name]:t}),M=J2[H.name]??H.name,r=Q1[H.name]?a`<span class="hint">${Q1[H.name]}</span>`:p,e=H.selector??{};if("boolean"in e)return a`<label class="check"
        ><input type="checkbox" .checked=${C[H.name]!==!1} @change=${t=>V(t.target.checked)} />${M}</label
      >`;if("text"in e||"entity"in e)return a`<label
        >${M}<input
          type="text"
          .value=${C[H.name]??""}
          ?disabled=${H.disabled}
          @change=${t=>V(t.target.value)}
      /></label>`;let o=e.select,i=C[H.name];if(o.multiple&&o.custom_value)return a`<label
        >${M}<input
          type="text"
          .value=${(Array.isArray(i)?i:[]).join(", ")}
          @change=${t=>V(t.target.value.split(","))}
        />${r}</label
      >`;if(o.multiple){let t=Array.isArray(i)?i:[];return a`<div class="group">
        ${M}
        ${o.options.map(d=>a`<label class="check"
            ><input
              type="checkbox"
              .checked=${t.includes(d.value)}
              @change=${A=>V(A.target.checked?[...t,d.value]:t.filter(m=>m!==d.value))}
            />${d.label}</label
          >`)}
      </div>`}return a`<label
      >${M}
      <select @change=${t=>V(t.target.value)}>
        ${H.name==="device"&&!i?a`<option value="" selected>Choose…</option>`:p}
        ${o.options.map(t=>a`<option value=${t.value} ?selected=${t.value===String(i)}>${t.label}</option>`)}
      </select>
      ${r}</label
    >`}};r1.properties={hass:{attribute:!1},kind:{},_config:{state:!0},_haForm:{state:!0}},r1.styles=s`
    .fallback {
      display: grid;
      gap: 12px;
    }
    fieldset {
      display: grid;
      gap: 10px;
      margin: 0;
      padding: 10px 12px 12px;
      border: 1px solid var(--divider-color, #444);
      border-radius: 12px;
    }
    legend {
      padding: 0 4px;
      font-weight: 500;
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
    .group {
      display: grid;
      gap: 4px;
      font-size: 14px;
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
  `;f("pivot-card-editor",r1);var V5={ATTRIBUTE:1,CHILD:2,PROPERTY:3,BOOLEAN_ATTRIBUTE:4,EVENT:5,ELEMENT:6},L5=L=>(...H)=>({_$litDirective$:L,values:H}),c1=class{constructor(H){}get _$AU(){return this._$AM._$AU}_$AT(H,C,V){this._$Ct=H,this._$AM=C,this._$Ci=V}_$AS(H,C){return this.update(H,C)}update(H,C){return this.render(...C)}};var{I:_5}=b2,M5=L=>L;var r5=()=>document.createComment(""),q=(L,H,C)=>{let V=L._$AA.parentNode,M=H===void 0?L._$AB:H._$AA;if(C===void 0){let r=V.insertBefore(r5(),M),e=V.insertBefore(r5(),M);C=new _5(r,e,L,L.options)}else{let r=C._$AB.nextSibling,e=C._$AM,o=e!==L;if(o){let i;C._$AQ?.(L),C._$AM=L,C._$AP!==void 0&&(i=L._$AU)!==e._$AU&&C._$AP(i)}if(r!==M||o){let i=C._$AA;for(;i!==r;){let t=M5(i).nextSibling;M5(V).insertBefore(i,M),i=t}}}return C},_=(L,H,C=L)=>(L._$AI(H,C),L),E5={},e5=(L,H=E5)=>L._$AH=H,t5=L=>L._$AH,h1=L=>{L._$AR(),L._$AA.remove()};var i5=(L,H,C)=>{let V=new Map;for(let M=H;M<=C;M++)V.set(L[M],M);return V},o5=L5(class extends c1{constructor(L){if(super(L),L.type!==V5.CHILD)throw Error("repeat() can only be used in text expressions")}dt(L,H,C){let V;C===void 0?C=H:H!==void 0&&(V=H);let M=[],r=[],e=0;for(let o of L)M[e]=V?V(o,e):e,r[e]=C(o,e),e++;return{values:r,keys:M}}render(L,H,C){return this.dt(L,H,C).values}update(L,[H,C,V]){let M=t5(L),{values:r,keys:e}=this.dt(H,C,V);if(!Array.isArray(M))return this.ut=e,r;let o=this.ut??=[],i=[],t,d,A=0,m=M.length-1,n=0,v=r.length-1;for(;A<=m&&n<=v;)if(M[A]===null)A++;else if(M[m]===null)m--;else if(o[A]===e[n])i[n]=_(M[A],r[n]),A++,n++;else if(o[m]===e[v])i[v]=_(M[m],r[v]),m--,v--;else if(o[A]===e[v])i[v]=_(M[A],r[v]),q(L,i[v+1],M[A]),A++,v--;else if(o[m]===e[n])i[n]=_(M[m],r[n]),q(L,M[A],M[m]),m--,n++;else if(t===void 0&&(t=i5(e,n,v),d=i5(o,A,m)),t.has(o[A]))if(t.has(o[m])){let x=d.get(e[n]),b1=x!==void 0?M[x]:null;if(b1===null){let X1=q(L,M[A]);_(X1,r[n]),i[n]=X1}else i[n]=_(b1,r[n]),q(L,M[A],b1),M[x]=null;n++}else h1(M[m]),m--;else h1(M[A]),A++;for(;n<=v;){let x=q(L,i[v+1]);_(x,r[n]),i[n++]=x}for(;A<=m;){let x=M[A++];x!==null&&h1(x)}return this.ut=e,e5(L,i),y}});var E=s`
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
`;var D5=500;function $5(L){let H=L.trim().toLowerCase(),C,V=/^#([0-9a-f]{3}|[0-9a-f]{6})$/.exec(H);if(V){let M=V[1].length===3?[...V[1]].map(r=>r+r).join(""):V[1];C=[0,2,4].map(r=>parseInt(M.slice(r,r+2),16))}else{let M=/^rgba?\(([^)]+)\)$/.exec(H);M?C=M[1].split(/[ ,/]+/).slice(0,3).map(Number):H==="white"?C=[255,255,255]:H==="black"&&(C=[0,0,0])}if(!(!C||C.some(M=>!Number.isFinite(M))))return(.2126*C[0]+.7152*C[1]+.0722*C[2])/255}var b=class extends O{constructor(){super(...arguments);this._held=!1}validate(C){}setConfig(C){if(!C||typeof C!="object")throw new Error("Invalid configuration");this.validate(C),this._config=C}set config(C){this.setConfig(C)}get device(){let C=[this.hass?.entities,this.hass?.devices,this._config?.device,this.hass?.states];return this._deviceKey&&C.slice(0,3).every((M,r)=>M===this._deviceKey[r])&&this._deviceCache?.deviceId?this._deviceCache:(this._deviceKey=C,this._deviceCache=y2(this.hass,this._config?.device),this._deviceCache)}shouldUpdate(C){if(!C.has("hass")||C.size>1)return!0;let V=C.get("hass"),M=this.hass;return!V||!M||V.entities!==M.entities||V.devices!==M.devices||V.services!==M.services||V.themes!==M.themes?!0:this.watchedIds().some(r=>r&&V.states[r]!==M.states[r])}updated(C){super.updated(C),this.hass&&this._themeChecked!==this.hass.themes&&(this._themeChecked=this.hass.themes,this._checkTheme())}_checkTheme(){let C=getComputedStyle(this),V=C.getPropertyValue("--ha-card-background").trim()||C.getPropertyValue("--card-background-color").trim()||C.getPropertyValue("--primary-background-color").trim(),M=V?$5(V):void 0,r=M!==void 0&&M>.55;r!==this.hasAttribute("light")&&(this.toggleAttribute("light",r),this.requestUpdate())}renderProblem(){let C=h(this.hass),V=this._config?.device,M=C.length?V?`No Pivot device \u201C${V}\u201D. Choose one in the card editor.`:"Choose a Pivot device in the card editor.":"No Pivot devices found. Add one under Settings \u2192 Devices & services \u2192 Pivot.";return a`<ha-card class="pv-problem pv-error" style="display:block;padding:16px;font-size:14px;line-height:1.4">
      ${M} <a href=${t1} target="_blank" rel="noreferrer" style="color:var(--primary-color)">Pivot dashboard docs</a>
    </ha-card>`}holdStart(C,V){C.pointerType==="mouse"&&C.button!==0||(this._held=!1,clearTimeout(this._holdTimer),V&&(this._holdTimer=setTimeout(()=>{this._held=!0,V1(this),T(this,V)},D5)))}holdEnd(){clearTimeout(this._holdTimer)}tap(C,V){if(C.stopPropagation(),this._held){this._held=!1;return}V1(this),V()}keyActivate(C,V){C.key!=="Enter"&&C.key!==" "||(C.preventDefault(),C.stopPropagation(),V())}disconnectedCallback(){super.disconnectedCallback(),clearTimeout(this._holdTimer)}};b.properties={hass:{attribute:!1},_config:{state:!0}};var S={circle:C2,close:H2,palette:M2,pause:r2,pencil:e2,play:t2,refresh:i2,volumeHigh:A2,volumeMute:a2},w=L=>a`<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d=${L}></path></svg>`;var N5=4e3,W5=4,e1=class extends O{constructor(){super();this._startX=0;this._moved=!1;this._isTouch=!1;this._down=C=>{if(this.disabled){u(this,"pivot-slide-blocked");return}if(!(C.pointerType==="mouse"&&C.button!==0)){C.stopPropagation(),this._pointer=C.pointerId,this._startX=C.clientX,this._moved=!1,this._isTouch=C.pointerType!=="mouse";try{this.setPointerCapture(C.pointerId)}catch{}u(this,"pivot-slide-start"),this._isTouch||(this._moved=!0,this._hold(this._valueAt(C.clientX)),u(this,"pivot-slide",{value:this._shown}))}};this._move=C=>{if(C.pointerId!==this._pointer||!this._moved&&Math.abs(C.clientX-this._startX)<W5)return;this._moved=!0;let V=this._valueAt(C.clientX);V!==this._shown&&(this._hold(V),u(this,"pivot-slide",{value:V}))};this._up=C=>{if(C.pointerId!==this._pointer)return;this._pointer=void 0;let V=this._valueAt(C.clientX);this._hold(V),u(this,"pivot-slide-end",{value:V})};this._cancel=C=>{C.pointerId===this._pointer&&(this._pointer=void 0,this._release(),u(this,"pivot-slide-cancel"))};this._lost=C=>{C.pointerId===this._pointer&&this._cancel(C)};this._key=C=>{if(this.disabled)return;let V={ArrowRight:1,ArrowUp:1,ArrowLeft:-1,ArrowDown:-1,PageUp:10,PageDown:-10},M;if(C.key in V)M=this.shownValue+V[C.key];else if(C.key==="Home")M=0;else if(C.key==="End")M=100;else return;C.preventDefault(),M=Math.round(Math.min(100,Math.max(0,M))),u(this,"pivot-slide-start"),this._hold(M),u(this,"pivot-slide-end",{value:M})};this.value=0,this.color="#ffffff",this.trackColor="rgba(255,255,255,0.3)",this.cap=15,this.disabled=!1,this.hideFill=!1,this.zeroCap=!1,this.label="",this._shown=void 0}get shownValue(){return this._shown??this.value}willUpdate(C){C.has("value")&&this._pointer===void 0&&this._shown!==void 0&&Math.abs(this._shown-this.value)<.5&&this._release()}disconnectedCallback(){super.disconnectedCallback(),clearTimeout(this._holdTimer)}render(){let C=Math.min(100,Math.max(0,this.shownValue)),V=(C>0||this.zeroCap)&&!this.hideFill;return a`<div class="track" style="background:${this.trackColor}">
      ${V?a`<div class="fill" style="background:${this.color};width:min(100%, calc(${C}% + ${this.cap}px))"></div>`:p}
    </div>`}firstUpdated(){this.setAttribute("role","slider"),this.setAttribute("aria-valuemin","0"),this.setAttribute("aria-valuemax","100"),this.addEventListener("pointerdown",this._down),this.addEventListener("pointermove",this._move),this.addEventListener("pointerup",this._up),this.addEventListener("pointercancel",this._cancel),this.addEventListener("lostpointercapture",this._lost),this.addEventListener("keydown",this._key),this.addEventListener("click",C=>C.stopPropagation())}updated(){this.setAttribute("aria-valuenow",String(Math.round(this.shownValue))),this.label&&this.setAttribute("aria-label",this.label),this.setAttribute("aria-disabled",String(this.disabled)),this.tabIndex=this.disabled?-1:0}_valueAt(C){let M=(this.renderRoot.querySelector(".track")??this).getBoundingClientRect(),r=Math.max(1,M.width-this.cap),e=(C-M.left-this.cap/2)/r*100;return Math.round(Math.min(100,Math.max(0,e)))}_hold(C){this._shown=C,clearTimeout(this._holdTimer),this._holdTimer=setTimeout(()=>this._release(),N5)}_release(){clearTimeout(this._holdTimer),this._shown=void 0}};e1.properties={value:{type:Number},color:{},trackColor:{attribute:"track-color"},cap:{type:Number},disabled:{type:Boolean,reflect:!0},hideFill:{type:Boolean,attribute:"hide-fill"},zeroCap:{type:Boolean,attribute:"zero-cap"},label:{},_shown:{state:!0}},e1.styles=s`
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
  `;f("pivot-slider",e1);var I5=200,U5=4e3,G5=3300,Q5=15e3,O1=class extends b{constructor(){super(...arguments);this._send=l1(C=>this._writeValue(C),I5);this._activate=C=>{C?.stopPropagation();let V=this.device,M=this.bankNumber;if(!this.hass||!V||M===void 0)return;let r=g(this.hass,V.suffix,M);r.active||(V1(this),c(this,this.hass,"number","set_value",{entity_id:l(V.suffix).activeBank,value:r.n}))}}static getConfigElement(){let C=document.createElement("pivot-card-editor");return C.kind="bank",C}static getStubConfig(C){return{device:h(C)[0]?.suffix??"",bank:1}}validate(C){let V=C.bank??1,M=Number(V);if(V!=="active"&&V!=="timer"&&(!Number.isInteger(M)||M<1||M>4))throw new Error("bank must be 1, 2, 3, 4, active or timer");let r=S1(C.timer_presets);if(r)throw new Error(r)}get bankNumber(){if(this._dragBank!==void 0)return this._dragBank;let C=this._config?.bank??1;if(C!=="active"&&C!=="timer")return Number(C);let V=this.device;if(!(!V||!this.hass))return C==="active"?M1(this.hass,V.suffix):R2(this.hass,V.suffix)}get _presets(){return U2(this._config?.timer_presets)}getCardSize(){return 4}getGridOptions(){return{columns:12,rows:"auto",min_columns:6}}get _silentEntity(){if(this._config?.show_silent_timer!==!1)return this._config?.timer_silent_entity||this.device?.timerSilentEntity}watchedIds(){let C=this.device;if(!C||!this.hass)return[];let V=l(C.suffix),M=this._config?.bank==="timer"?[1,2,3,4].map(i=>V.bank(i).entity):[],r=this.bankNumber;if(r===void 0)return[V.activeBank,...M];let e=V.bank(r),o=this.hass.states[e.entity]?.state;return[...M,e.entity,e.value,e.passive,e.color,e.mirror,e.announce,V.activeBank,V.toggle("control_mode"),V.toggle("mute_announcements"),V.timerState,V.timerDuration,V.timerEnd,o&&o.includes(".")?o:void 0,this._silentEntity,"script.pivot_timer_toggle"]}render(){let C=this.device;if(!this.hass||!this._config)return p;if(!C)return this.renderProblem();let V=this.bankNumber;if(V===void 0)return this._renderUnresolved(C.name);let M=g(this.hass,C.suffix,V);this.hasAttribute("light")&&(M.color=s1(M.color));let r=N2(this.hass,C.suffix,Date.now()),e=K2(M,r),o=M.entityId&&!M.isTimer?M.entityId:"",i=this._config.show_bank_options!==!1;return a`<ha-card
      class="bank pv-ready ${M.active?"active":""} ${M.controlOn?"":"control-off"}"
      data-measure="bank-card"
      @click=${this._activate}
    >
      <ha-ripple></ha-ripple>
      <div class="head tap" @click=${this._activate}>
        <ha-ripple></ha-ripple>
        <button
          class="dot tap"
          style="color:${M.color}"
          aria-label="Bank ${M.n} colour"
          @click=${t=>this.tap(t,()=>T(this,M.ids.colorLight))}
        >
          <ha-ripple></ha-ripple>${w(S.circle)}
        </button>
        <span class="label text">${`Bank ${M.n}`}</span>
        ${this._config.show_edit===!1?p:a`<button class="edit tap" aria-label="Edit the bank ${M.n} entity" @click=${t=>this.tap(t,()=>T(this,M.ids.entity))}>
              <ha-ripple></ha-ripple><span>EDIT ENTITY</span>${w(S.pencil)}
            </button>`}
      </div>
      <div class="name-row tap" title=${o} @click=${t=>this._nameTap(t,M)}>
        <ha-ripple></ha-ripple>
        <span class="name">${U(M)}</span>${e?a`<span class="value">${e}</span>`:p}
      </div>
      ${$2(M)?this._renderSlider(M,r):p}
      ${M.isTimer?this._renderTimer(M,r):p}
      ${i&&E2(M)?this._renderRow(M.ids.mirror,"Mirror Light Colour",S.palette):p}
      ${i&&D2(M)?this._renderRow(M.ids.announce,"Announce Value",S.volumeHigh,this._muted):p}
    </ha-card>`}_renderUnresolved(C){let V=this._config?.bank==="timer";return a`<ha-card class="bank unresolved pv-ready" data-measure="bank-card">
      <div class="notice">
        ${V?a`No bank on ${C} is set to Timer.
              <a href=${w1} target="_blank" rel="noreferrer">Timer setup</a>`:a`${C} isn’t reporting its active bank.`}
      </div>
    </ha-card>`}get _muted(){let C=this.device;return!!C&&this.hass?.states[l(C.suffix).toggle("mute_announcements")]?.state==="on"}_renderSlider(C,V){let M=C.isTimer&&V.state!=="idle",r=!C.controlOn||M||!G1(C)||C.isTimer&&!V.enabled&&!C.active,e=C.isTimer?I2(V,C.value):C.value;return a`<pivot-slider
      .value=${e}
      .color=${C.color}
      .trackColor=${`${C.color}33`}
      .cap=${15}
      .hideFill=${q2(C)}
      .label=${`${U(C)} value`}
      ?disabled=${r}
      @pivot-slide-start=${()=>this._slideStart(C)}
      @pivot-slide=${o=>this._slide(C,o.detail.value)}
      @pivot-slide-end=${o=>this._slideEnd(C,V,o.detail.value)}
      @pivot-slide-cancel=${()=>{this._send.cancel(),this._endDrag()}}
      @click=${o=>o.stopPropagation()}
    ></pivot-slider>`}_renderRow(C,V,M,r=!1,e=""){let o=this.hass?.states[C]?.state==="on",i=this.hass?.states[C]?.state,t=i===void 0||i==="unavailable";return a`<div
      class="row tap ${e} ${r?"muted":""} ${t?"disabled unavailable":""}"
      role="switch"
      tabindex=${r||t?-1:0}
      aria-checked=${o?"true":"false"}
      aria-label=${V}
      style="--ha-ripple-color:${o?"var(--pv-ripple-on)":"var(--pv-ripple-off)"}"
      @pointerdown=${d=>this.holdStart(d,C)}
      @pointerup=${this.holdEnd}
      @pointerleave=${this.holdEnd}
      @pointercancel=${this.holdEnd}
      @contextmenu=${d=>d.preventDefault()}
      @click=${d=>this.tap(d,()=>this.hass&&L1(this,this.hass,C))}
      @keydown=${d=>this.keyActivate(d,()=>this.hass&&L1(this,this.hass,C))}
    >
      <ha-ripple></ha-ripple>
      <span class="row-icon">${w(M)}</span>
      <span class="row-label text">${V}</span>
      <span class="toggle ${o?"on":""}"><span class="knob"></span></span>
    </div>`}_renderTimer(C,V){let M=this._silentEntity,r=M?this._renderRow(M,"Silent Timer",S.volumeMute,!1,"silent"):p;if(!V.enabled)return a`<div class="notice" @click=${A=>A.stopPropagation()}>
          Timer entities are disabled. Enable them in the Pivot device settings to use the timer.
          <a href=${w1} target="_blank" rel="noreferrer">Timer setup</a>
        </div>
        ${r}`;if(V.state==="alerting")return a`<div class="strip alerting tap" @click=${A=>A.stopPropagation()}>
          <button class="tbtn word solid tap" @click=${A=>this.tap(A,()=>this._timerToggle(C))}>
            <ha-ripple></ha-ripple>${w(S.close)}<span>Stop</span>
          </button>
          <button class="tbtn word idle tap" @click=${A=>this.tap(A,()=>this._repeat(C))}>
            <ha-ripple></ha-ripple>${w(S.refresh)}<span>Repeat</span>
          </button>
          <ha-ripple></ha-ripple>
        </div>
        ${r}`;let e=V.state==="running",o=V.state==="paused",i=e||o,t=this._presets,d=z2(V,C.value,t);return a`<div
        class="strip tap ${t.length?"":"no-presets"}"
        style=${t.length===4?"":`--pv-presets:${t.length}`}
        @click=${A=>A.stopPropagation()}
      >
        <button
          class="tbtn solid tap"
          aria-label=${e?"Pause timer":o?"Resume timer":"Start timer"}
          @click=${A=>this.tap(A,()=>this._timerToggle(C))}
        >
          <ha-ripple></ha-ripple><span class="ticon">${w(e?S.pause:S.play)}</span>
        </button>
        <button
          class="tbtn tap ${i?"solid":"idle"}"
          aria-label="Cancel timer"
          ?disabled=${!i}
          @click=${A=>this.tap(A,()=>i&&this._timerCancel(C))}
        >
          <ha-ripple></ha-ripple><span class="ticon">${w(o?S.refresh:S.close)}</span>
        </button>
        ${t.map(A=>a`<button
            class="tbtn preset tap ${d===A.minutes?"selected":""} ${i?"locked":""}"
            aria-pressed=${d===A.minutes?"true":"false"}
            @click=${m=>this.tap(m,()=>this._preset(C,V,A))}
          >
            <ha-ripple></ha-ripple>${A.label}
          </button>`)}
        <ha-ripple></ha-ripple>
      </div>
      ${r}`}_nameTap(C,V){if(V.isTimer)return this._activate(C);C.stopPropagation(),T(this,V.entityId??V.ids.entity)}_slideStart(C){this._lastSent=void 0,this._dragBank=C.n,!C.isTimer&&!C.active&&this._activate()}_slide(C,V){C.isTimer||this._send(V)}_slideEnd(C,V,M){this._send.cancel(),C.isTimer?this._writeTimer(C,V,M):this._writeValue(M),this._endDrag()}_endDrag(){this._dragBank!==void 0&&(this._dragBank=void 0,this.requestUpdate())}_writeValue(C,V){let M=this.device,r=V??this.bankNumber;if(!this.hass||!M||r===void 0)return;let e=g(this.hass,M.suffix,r);if(e.active){if(this._pending=void 0,C===this._lastSent)return;this._lastSent=C,c(this,this.hass,"number","set_value",{entity_id:e.ids.value,value:C})}else this._pending={value:C,until:Date.now()+U5,bank:r}}_writeTimer(C,V,M){if(!this.hass||V.state!=="idle")return;let r=W2(M);this._setDuration(C,V,r,u1(r))}_preset(C,V,M){V.state==="idle"&&this._setDuration(C,V,M.minutes,M.value)}_setDuration(C,V,M,r){let e=this.device;if(!this.hass||!e)return;let o=Math.round(r);if(C.active){c(this,this.hass,"number","set_value",{entity_id:C.ids.value,value:o});return}V.enabled&&c(this,this.hass,"number","set_value",{entity_id:l(e.suffix).timerDuration,value:M}),c(this,this.hass,"number","set_value",{entity_id:C.ids.value,value:o})}async _timerToggle(C){let V=this.device;return!this.hass||!V?!1:U1(this.hass,"pivot","timer_toggle")?c(this,this.hass,"pivot","timer_toggle",{device:V.suffix,bank:C.n}):c(this,this.hass,"script","turn_on",{entity_id:"script.pivot_timer_toggle",variables:{device_suffix:V.suffix,bank:C.n}})}_timerCancel(C){let V=this.device;if(!(!this.hass||!V)){if(U1(this.hass,"pivot","timer_cancel")){c(this,this.hass,"pivot","timer_cancel",{device:V.suffix,bank:C.n});return}c(this,this.hass,"select","select_option",{entity_id:l(V.suffix).timerState,option:"idle"})}}async _repeat(C){if(!await this._timerToggle(C))return;this._repeatUntil=Date.now()+Q5;let V=()=>{let M=this.device;if(!this._repeatUntil||!this.hass||!M||Date.now()>this._repeatUntil){this._repeatUntil=void 0;return}let r=this.hass.states[l(M.suffix).timerState];if(r?.state==="idle"&&Date.now()-Date.parse(r.last_changed)>G5){this._repeatUntil=void 0,this._timerToggle(C);return}this._repeatTimer=setTimeout(V,250)};this._repeatTimer=setTimeout(V,250)}updated(C){super.updated(C);let V=this.device;if(!this.hass||!V)return;if(this._pending){let i=this._pending;Date.now()>i.until?this._pending=void 0:g(this.hass,V.suffix,i.bank).active&&this._writeValue(i.value,i.bank)}let M=this.bankNumber;if(M===void 0)return;let r=g(this.hass,V.suffix,M);clearTimeout(this._ticker),this._ticker=void 0;let e=l(V.suffix),o=Date.parse(this.hass.states[e.timerEnd]?.state??"");if(r.isTimer&&this.hass.states[e.timerState]?.state==="running"&&Number.isFinite(o)){let i=o-Date.now();if(i>-1e3){let t=((i-500)%1e3+1e3)%1e3+5;this._ticker=setTimeout(()=>this.requestUpdate(),t)}}}connectedCallback(){super.connectedCallback(),this.hasUpdated&&this.requestUpdate()}disconnectedCallback(){super.disconnectedCallback(),clearTimeout(this._ticker),this._ticker=void 0,clearTimeout(this._repeatTimer),this._repeatUntil=void 0,this._send.cancel()}};O1.styles=[E,s`
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
        grid-template-columns: 15% 15% repeat(var(--pv-presets, 4), minmax(0, 1fr));
        column-gap: 5px;
        height: 50px;
        margin-top: 20px;
        padding: 5px;
        border-radius: 10px;
        background: var(--pv-strip);
        cursor: default;
      }
      .strip.alerting,
      .strip.no-presets {
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
      ha-card.unresolved {
        cursor: default;
      }
      .unresolved .notice {
        margin-top: 0;
      }
    `];f("pivot-bank-card",O1);var g1=class extends b{constructor(){super(...arguments);this._sendVolume=l1((C,V)=>this._setVolume(C,V),200)}static getConfigElement(){let C=document.createElement("pivot-card-editor");return C.kind="settings",C}static getStubConfig(C){return{device:h(C)[0]?.suffix??""}}validate(C){if(C.rows!==void 0){if(!Array.isArray(C.rows))throw new Error("rows must be a list");let V=C.rows.filter(M=>!Z.includes(M));if(V.length)throw new Error(`Unknown rows: ${V.join(", ")}. Use ${Z.join(", ")}.`)}}getCardSize(){return 6}getGridOptions(){return{columns:12,rows:"auto",min_columns:6}}get _rows(){return this._config?.rows??Z}_mediaPlayer(){let C=this.device,V=C?this.hass?.states[l(C.suffix).mediaPlayerText]?.state:void 0;return V&&V.includes(".")&&!G.has(V)?V:void 0}watchedIds(){let C=this.device;if(!C)return[];let V=l(C.suffix);return[...["control_mode","announcements","mute_announcements","show_control_value","dim_when_idle"].map(V.toggle),V.mediaPlayerText,this._mediaPlayer()]}render(){let C=this.device;if(!this.hass||!this._config)return p;if(!C)return this.renderProblem();let V=this._rows,M=this._config.headings!==!1,r=[];if(M){let e=V.filter(i=>B1.includes(i)),o=V.filter(i=>P1.includes(i));e.length&&r.push(a`<div class="heading">Device</div>`,...e.map(i=>this._row(i))),o.length&&r.push(a`<div class="heading">Behaviour</div>`,...o.map(i=>this._row(i)))}else r.push(...V.map(e=>this._row(e)));return V.length||r.push(a`<div class="empty">No settings chosen. Pick some in the card editor.</div>`),a`<div class="wrap pv-ready ${this._config.background?"boxed":""}">${r}</div>`}_row(C){return C==="volume"?this._volume():this._toggle(C)}_toggle(C){let V=l(this.device.suffix),M=V.toggle(C),r=this.hass.states[M]?.state==="on",e=C==="dim_when_idle"&&this.hass.states[V.toggle("show_control_value")]?.state!=="on",o=this.hass.states[M]?.state,i=o===void 0||o==="unavailable",t=R[C],d=()=>this.hass&&L1(this,this.hass,M);return a`<div
      class="srow tap ${e?"dependent-off":""} ${i?"disabled unavailable":""}"
      role="switch"
      tabindex=${e||i?-1:0}
      aria-checked=${r?"true":"false"}
      aria-label=${t.title}
      style="--ha-ripple-color:${r?"var(--pv-ripple-on)":"var(--pv-ripple-off)"}"
      @pointerdown=${A=>this.holdStart(A,M)}
      @pointerup=${this.holdEnd}
      @pointerleave=${this.holdEnd}
      @pointercancel=${this.holdEnd}
      @contextmenu=${A=>A.preventDefault()}
      @click=${A=>this.tap(A,d)}
      @keydown=${A=>this.keyActivate(A,d)}
    >
      <ha-ripple></ha-ripple>
      <span class="stitle text">${t.title}</span>
      <span class="sdesc text">${t.description}</span>
      <span class="toggle ${r?"on":""}"><span class="knob"></span></span>
    </div>`}_volume(){let C=this._mediaPlayer(),V=C?this.hass.states[C]:void 0,M=!!V&&!G.has(V.state),r=Number(V?.attributes.volume_level),e=Number.isFinite(r)?r*100:0;return a`<div class="volume ${M?"":"unavailable"}" title=${M?"":"The device media player is unavailable"}>
      <div class="text">Pivot Device Volume</div>
      <pivot-slider
        zero-cap
        .value=${e}
        .color=${"var(--pv-volume-fill)"}
        .trackColor=${"var(--pv-volume-track)"}
        .cap=${15}
        .label=${"Pivot device volume"}
        ?disabled=${!M}
        @pivot-slide-start=${()=>this._lastVolume=void 0}
        @pivot-slide=${o=>C&&this._sendVolume(C,o.detail.value)}
        @pivot-slide-end=${o=>{this._sendVolume.cancel(),C&&this._setVolume(C,o.detail.value)}}
        @pivot-slide-cancel=${()=>this._sendVolume.cancel()}
      ></pivot-slider>
    </div>`}_setVolume(C,V){!this.hass||V===this._lastVolume||(this._lastVolume=V,c(this,this.hass,"media_player","volume_set",{entity_id:C,volume_level:Math.round(V)/100}))}disconnectedCallback(){super.disconnectedCallback(),this._sendVolume.cancel()}};g1.styles=[E,s`
      .wrap {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .wrap.boxed {
        padding: 12px 16px 14px;
        border-radius: var(--pivot-card-radius, 20px);
        background: var(--ha-card-background, var(--card-background-color, #1c1c1e));
      }
      .empty {
        font-size: 14px;
        color: var(--pv-description);
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
    `];f("pivot-settings-card",g1);var f1=class extends b{static getConfigElement(){let H=document.createElement("pivot-card-editor");return H.kind="status",H}static getStubConfig(H){return{device:h(H)[0]?.suffix??""}}get _showTitle(){return this._config?.show_title!==!1&&this._config?.show_name!==!1}get _showActiveBank(){return this._config?.show_active_bank!==!1}getCardSize(){return(this._showTitle?1:0)+(this._showActiveBank?1:0)}getGridOptions(){return{columns:"full",rows:"auto"}}watchedIds(){let H=this.device;if(!H||!this.hass)return[];let C=l(H.suffix),V=M1(this.hass,H.suffix),M=V!==void 0?C.bank(V):void 0,r=M?this.hass.states[M.entity]?.state:void 0;return[C.activeBank,C.toggle("control_mode"),M?.entity,M?.color,r&&r.includes(".")?r:void 0]}render(){let H=this.device;if(!this.hass||!this._config)return p;if(!H)return this.renderProblem();let C=l(H.suffix),V=this.hass.states[C.toggle("control_mode")]?.state==="on",M=M1(this.hass,H.suffix),r="Control mode off",e="var(--pv-muted)";if(V)if(M!==void 0){let i=g(this.hass,H.suffix,M);r=`Bank ${M} - ${U(i)}`,e=this.hasAttribute("light")?s1(i.color):i.color}else r="Active bank unavailable";let o=this._config.name?.trim()||H.name;return a`<div class="wrap pv-ready">
      ${this._showTitle?a`<div class="title">${o}</div>`:p}
      ${this._showActiveBank?a`<div
            class="status tap"
            role="button"
            tabindex="0"
            @click=${i=>this.tap(i,()=>T(this,C.activeBank))}
            @keydown=${i=>this.keyActivate(i,()=>T(this,C.activeBank))}
          >
            <ha-ripple></ha-ripple>
            <span class="sdot" style="color:${e}">${w(S.circle)}</span>
            <span class="text">${r}</span>
          </div>`:p}
    </div>`}};f1.styles=[E,s`
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
    `];f("pivot-status-card",f1);var k1=class extends b{static getConfigElement(){let H=document.createElement("pivot-card-editor");return H.kind="device",H}static getStubConfig(H){return{device:h(H)[0]?.suffix??""}}validate(H){let C=H.banks;if(C!==void 0&&C!=="all"&&C!=="active"&&C!=="timer"&&(!Array.isArray(C)||C.some(M=>!Number.isInteger(M)||M<1||M>4)))throw new Error("banks must be all, active, timer or a list of bank numbers, like [1, 2]");if(H.bank_columns!==void 0&&H.bank_columns!==1&&H.bank_columns!==2)throw new Error("bank_columns must be 1 or 2");if(H.settings_position!==void 0&&H.settings_position!=="beside"&&H.settings_position!=="below")throw new Error("settings_position must be beside or below");if(H.settings_rows!==void 0){if(!Array.isArray(H.settings_rows))throw new Error("settings_rows must be a list");let M=H.settings_rows.filter(r=>!Z.includes(r));if(M.length)throw new Error(`Unknown settings_rows: ${M.join(", ")}. Use ${Z.join(", ")}.`)}let V=S1(H.timer_presets);if(V)throw new Error(V)}setConfig(H){super.setConfig(H);let C=H.device,V=H.show_status===!1,M={};for(let e of["show_edit","show_bank_options","timer_presets","show_silent_timer","timer_silent_entity"])H[e]!==void 0&&H[e]!==""&&(M[e]=H[e]);let r=e=>({type:"custom:pivot-bank-card",device:C,bank:e,...M});this._children={status:{type:"custom:pivot-status-card",device:C,...H.name!==void 0?{name:H.name}:{},show_title:!V&&H.show_title!==!1,show_active_bank:!V&&H.show_active_bank!==!1},banks:{1:r(1),2:r(2),3:r(3),4:r(4),active:r("active"),timer:r("timer")},settings:{type:"custom:pivot-settings-card",device:C,...H.settings_rows?{rows:H.settings_rows}:{},...H.settings_headings===!1?{headings:!1}:{},...H.settings_background?{background:!0}:{}}}}get _showStatus(){let H=this._children?.status;return!!H&&(H.show_title!==!1||H.show_active_bank!==!1)}get _showSettings(){return this._config?.show_settings!==!1&&(this._config?.settings_rows??Z).length>0}_bankConfigs(){let H=this._config,C=this.device;if(!H||!C||!this.hass||!this._children)return[];let V=H.banks??"all";return V==="active"||V==="timer"?[this._children.banks[V]]:_2(this.hass,C.suffix,V,!!H.hide_unassigned).map(M=>this._children.banks[M])}getCardSize(){let H=this._config?.banks,C=this.hass&&this.device?this._bankConfigs().length:H==="active"||H==="timer"?1:Array.isArray(H)?new Set(H).size:4,V=this._showStatus?2:0;if(!this._showSettings)return V+C*4;let M=this._config?.settings_position!=="below";return V+(M?Math.max(C*4,7):C*4+7)}getGridOptions(){return{columns:"full",rows:"auto"}}watchedIds(){return[]}render(){if(!this.hass||!this._config||!this._children)return p;if(!this.device)return this.renderProblem();let H=this._children,C=this._bankConfigs(),V=this._showSettings,M=!V||this._config.settings_position==="below",r=this._config.bank_columns===2&&C.length>1,e=Array.isArray(this._config.banks)&&this._config.banks.length===0;return a`
      ${this._showStatus?a`<pivot-status-card .hass=${this.hass} .config=${H.status}></pivot-status-card>`:p}
      <div class="cols pv-ready ${M?"single":""}">
        <div class="col banks">
          <div class="bank-list ${r?"two":""}">
            ${C.length?o5(C,o=>String(o.bank),o=>a`<pivot-bank-card .hass=${this.hass} .config=${o}></pivot-bank-card>`):a`<div class="empty">
                  ${e?"No banks chosen. Pick some in the card editor.":"None of the banks has anything assigned yet."}
                </div>`}
          </div>
        </div>
        ${V?a`<div class="col settings"><pivot-settings-card .hass=${this.hass} .config=${H.settings}></pivot-settings-card></div>`:p}
      </div>
    `}shouldUpdate(){return!0}};k1.styles=[E,s`
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
      .col.banks {
        container: pivot-banks / inline-size;
      }
      .bank-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      /* Two banks per row once each can be about 300px wide. */
      @container pivot-banks (min-width: 608px) {
        .bank-list.two {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          align-items: start;
        }
      }
      .empty {
        padding: 4px 2px;
        font-size: 14px;
        line-height: 1.4;
        color: var(--pv-description);
      }
    `];f("pivot-device-card",k1);var z5=[{type:"pivot-device-card",name:"Pivot",description:"Everything for one dial: its active bank, banks and settings. Choose which banks show and where the settings go."},{type:"pivot-bank-card",name:"Pivot bank",description:"One bank: a chosen bank, the one the dial is on, or the timer bank. For building your own layout."},{type:"pivot-status-card",name:"Pivot status",description:"A dial\u2019s name and the bank it\u2019s on. For building your own layout."},{type:"pivot-settings-card",name:"Pivot settings",description:"Control Mode, volume and announcement settings, to place anywhere. Pairs with the Pivot card\u2019s settings turned off."}];window.customCards=window.customCards||[];for(let L of z5)window.customCards.some(H=>H.type===L.type)||window.customCards.push({...L,preview:!0,documentationURL:t1});console.info("%c PIVOT CARDS %c 0.0.97 ","color:#fff;background:#545454;border-radius:4px 0 0 4px;padding:2px 4px","color:#545454;background:#e0e0e0;border-radius:0 4px 4px 0;padding:2px 4px");
