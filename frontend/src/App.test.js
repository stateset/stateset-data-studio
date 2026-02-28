import { render, screen } from "@testing-library/react";
import App from "./App";

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
});

test("renders app header", () => {
  const consoleLogSpy = jest.spyOn(console, "log").mockImplementation(() => {});
  try {
    render(<App />);
    expect(screen.getByText(/StateSet Data Studio/i)).toBeInTheDocument();
  } finally {
    consoleLogSpy.mockRestore();
  }
});
