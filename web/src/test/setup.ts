import "@testing-library/jest-dom";

// jsdom lacks ResizeObserver (used by the chart component).
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = globalThis.ResizeObserver ?? (ResizeObserverStub as never);
