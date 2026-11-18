// A tiny event bus so systems (missions, achievements) can listen without import cycles.
/** @type {Map<string, ((...args: any[]) => void)[]>} */
const handlers = new Map();

export function on(name, fn) {
  let list = handlers.get(name);
  if (!list) handlers.set(name, (list = []));
  list.push(fn);
}

export function emit(name, ...args) {
  for (const fn of handlers.get(name) ?? []) {
    try {
      fn(...args);
    } catch (err) {
      console.warn(`[bus:${name}] ${err}`);
    }
  }
}
