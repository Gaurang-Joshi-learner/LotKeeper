import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

// One self-contained HTML file with the real UI + mock API (see src/demo/mockApi.ts).
export default defineConfig({ plugins: [react(), viteSingleFile()], build: { outDir: "dist-demo" } });
