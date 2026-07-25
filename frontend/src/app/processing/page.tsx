"use client";
import { AppShell } from "@/components/layout/AppShell";
import { motion } from "framer-motion";
import { ImagePlus, Layers, ArrowRight, Sliders } from "lucide-react";

const processingSteps = [
  { name: "Flat Field Correction", category: "Calibration" },
  { name: "Dark Frame Subtraction", category: "Calibration" },
  { name: "Bias Correction", category: "Calibration" },
  { name: "Cosmic Ray Removal", category: "Noise Reduction" },
  { name: "Median Filter", category: "Noise Reduction" },
  { name: "Gaussian Filter", category: "Noise Reduction" },
  { name: "Sigma Clipping", category: "Noise Reduction" },
  { name: "CLAHE Enhancement", category: "Enhancement" },
  { name: "Contrast Stretching", category: "Enhancement" },
  { name: "Image Normalization", category: "Enhancement" },
  { name: "Star-based Alignment", category: "Registration" },
  { name: "Subpixel Alignment", category: "Registration" },
];

export default function ProcessingPage() {
  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-space-100">Image Processing</h1>
          <p className="text-sm text-space-500 mt-1">Build and execute calibration, noise reduction, and enhancement pipelines</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-4">
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-space-200 flex items-center gap-2 mb-4">
                <Layers className="w-4 h-4 text-neon-400" />
                Pipeline Steps
              </h3>
              <div className="space-y-2">
                {processingSteps.map((step) => (
                  <motion.div key={step.name} whileHover={{ x: 4 }} className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-space-800/50 cursor-pointer transition-colors group">
                    <input type="checkbox" className="rounded border-space-600 bg-space-800 text-neon-500 focus:ring-neon-500/30" />
                    <div className="flex-1">
                      <p className="text-xs text-space-300 group-hover:text-space-100">{step.name}</p>
                      <p className="text-[10px] text-space-600">{step.category}</p>
                    </div>
                    <Sliders className="w-3 h-3 text-space-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </motion.div>
                ))}
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-12 text-center h-full flex flex-col items-center justify-center">
              <ImagePlus className="w-12 h-12 text-space-700 mx-auto mb-4" />
              <h3 className="text-base font-medium text-space-300 mb-2">Configure Processing Pipeline</h3>
              <p className="text-sm text-space-500 max-w-md mx-auto">
                Select processing steps from the left panel, configure parameters, and run the pipeline on your dataset. Before/after comparison will appear here.
              </p>
            </motion.div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
