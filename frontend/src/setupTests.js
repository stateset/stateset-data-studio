import "@testing-library/jest-dom";

const originalWarn = console.warn;
beforeAll(() => {
  jest.spyOn(console, "warn").mockImplementation((...args) => {
    const first = String(args[0] || "");
    if (first.includes("React Router Future Flag Warning")) {
      return;
    }
    originalWarn(...args);
  });
});

afterAll(() => {
  if (console.warn.mockRestore) {
    console.warn.mockRestore();
  }
});
