// Defines the Pivot elements once Home Assistant can see them.
//
// Home Assistant replaces the browser's custom-element registry with a scoped
// one when its app starts, and it loads this file in parallel with the app:
// both are dynamic imports in index.html, with no order between them. An
// element defined before the swap lands in the browser's own registry, where
// Home Assistant never looks, and every Pivot card shows "Custom element
// doesn't exist". So on a Home Assistant page, wait until the app has defined
// its own <home-assistant> element. Anywhere else (tests, a plain page)
// define straight away.

const mustWait = !!document.querySelector('home-assistant') && !customElements.get('home-assistant');
const ready = mustWait ? customElements.whenDefined('home-assistant') : undefined;

export function defineElement(tag: string, element: CustomElementConstructor): void {
  const define = () => {
    if (!customElements.get(tag)) customElements.define(tag, element);
  };
  if (ready) ready.then(define);
  else define();
}
