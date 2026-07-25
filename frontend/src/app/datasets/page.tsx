"use client";

import { AppShell } from "@/components/layout/AppShell";
import { motion } from "framer-motion";
import { useState, useCallback } from "react";
import {
  Database,
  Upload,
  FolderOpen,
  FileImage,
  Clock,
  HardDrive,
  Trash2,
  Eye,
  ChevronRight,
  Plus,
  Search,
  Filter,
} from "lucide-react";

import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function DatasetsPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.datasets.list(),
  });
  
  const datasets = data?.datasets || [];
  const [showImport, setShowImport] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [folderPath, setFolderPath] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const importFolderMutation = useMutation({
    mutationFn: (path: string) => api.datasets.importFolder({ path }),
    onSuccess: () => {
      refetch();
      setFolderPath("");
      setShowImport(false);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.datasets.upload(file),
    onSuccess: () => {
      refetch();
      setShowImport(false);
    },
    onSettled: () => setIsUploading(false),
  });

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      setIsUploading(true);
      try {
        await uploadMutation.mutateAsync(files[0]);
      } catch (err) {
        console.error("Upload failed", err);
      }
    }
  }, [uploadMutation]);

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-space-100">Dataset Manager</h1>
            <p className="text-sm text-space-500 mt-1">
              Import, index, and manage astronomical FITS datasets
            </p>
          </div>
          <button
            onClick={() => setShowImport(!showImport)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-neon-500/15 text-neon-400 border border-neon-500/25 hover:bg-neon-500/25 transition-all text-sm font-medium neon-glow"
          >
            <Plus className="w-4 h-4" />
            Import Dataset
          </button>
        </div>

        {/* Import Panel */}
        {showImport && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="glass-prominent rounded-xl overflow-hidden"
          >
            <div className="p-6 space-y-4">
              <h2 className="text-base font-semibold text-space-100">Import Dataset</h2>

              {/* Drop Zone */}
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                className={`
                  border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer
                  ${dragOver
                    ? "border-neon-500 bg-neon-500/10"
                    : "border-space-700 hover:border-neon-500/30 hover:bg-space-800/30"
                  }
                `}
              >
                <Upload className={`w-10 h-10 mx-auto mb-4 ${dragOver ? "text-neon-400" : "text-space-600"}`} />
                <p className="text-sm text-space-300 mb-1">
                  Drag & drop FITS files, ZIP archives, or folders
                </p>
                <p className="text-xs text-space-600">
                  Supports .fits, .fits.gz, multi-extension FITS, ZIP archives
                </p>
                {isUploading ? (
                  <p className="mt-4 text-xs text-neon-400 animate-pulse">Uploading...</p>
                ) : (
                  <label className="mt-4 px-4 py-2 rounded-lg bg-space-800 text-space-300 border border-space-700 hover:border-neon-500/30 text-xs transition-colors cursor-pointer inline-block">
                    Browse Files
                    <input type="file" className="hidden" accept=".fits,.fit,.fits.gz,.zip" onChange={(e) => {
                      const files = Array.from(e.target.files || []);
                      if (files.length > 0) {
                        setIsUploading(true);
                        uploadMutation.mutate(files[0]);
                      }
                    }} />
                  </label>
                )}
              </div>

              {/* Or import from folder */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-space-700" />
                <span className="text-xs text-space-600">or</span>
                <div className="flex-1 h-px bg-space-700" />
              </div>

              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <FolderOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-space-500" />
                  <input
                    type="text"
                    value={folderPath}
                    onChange={(e) => setFolderPath(e.target.value)}
                    placeholder="Enter local folder path (e.g., C:\observations\night_2024)"
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-space-800/50 border border-space-700 text-sm text-space-200 placeholder:text-space-600 focus:border-neon-500/30 focus:outline-none transition-colors"
                  />
                </div>
                <button 
                  onClick={() => importFolderMutation.mutate(folderPath)}
                  disabled={!folderPath || importFolderMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-neon-500/15 text-neon-400 border border-neon-500/25 hover:bg-neon-500/25 text-sm transition-colors disabled:opacity-50"
                >
                  {importFolderMutation.isPending ? "Importing..." : "Import"}
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Search / Filter */}
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-space-500" />
            <input
              type="text"
              placeholder="Search datasets..."
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-space-800/30 border border-space-700/50 text-sm text-space-200 placeholder:text-space-600 focus:border-neon-500/30 focus:outline-none transition-colors"
            />
          </div>
          <button className="flex items-center gap-2 px-3 py-2 rounded-lg bg-space-800/30 border border-space-700/50 text-space-400 hover:text-space-200 text-sm transition-colors">
            <Filter className="w-4 h-4" />
            Filter
          </button>
        </div>

        {/* Dataset List */}
        {datasets.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-card p-16 text-center"
          >
            <div className="w-20 h-20 rounded-2xl bg-space-800/50 flex items-center justify-center mx-auto mb-6">
              <Database className="w-9 h-9 text-space-600" />
            </div>
            <h3 className="text-lg font-semibold text-space-200 mb-2">
              No datasets imported yet
            </h3>
            <p className="text-sm text-space-500 max-w-md mx-auto mb-6">
              Import your first FITS dataset to begin analyzing astronomical
              images. Drag & drop files above, or specify a local folder path.
            </p>
            <div className="flex justify-center gap-4 text-xs text-space-600">
              <span className="flex items-center gap-1.5">
                <FileImage className="w-3.5 h-3.5" /> .fits / .fits.gz
              </span>
              <span className="flex items-center gap-1.5">
                <FolderOpen className="w-3.5 h-3.5" /> Batch folders
              </span>
              <span className="flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5" /> ZIP archives
              </span>
            </div>
          </motion.div>
        ) : (
          <div className="space-y-3">
            {datasets.map((ds) => (
              <motion.div
                key={ds.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-4 flex items-center gap-4"
              >
                <div className="w-12 h-12 rounded-lg bg-space-800/50 flex items-center justify-center">
                  <Database className="w-5 h-5 text-neon-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-space-100 truncate">{ds.name}</h3>
                  <div className="flex items-center gap-4 mt-1 text-xs text-space-500">
                    <span className="flex items-center gap-1">
                      <FileImage className="w-3 h-3" />
                      {ds.file_count} frames
                    </span>
                    <span className="flex items-center gap-1">
                      <HardDrive className="w-3 h-3" />
                      {(ds.total_size_bytes / 1024 / 1024).toFixed(1)} MB
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(ds.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <span className={`badge ${
                  ds.status === "ready" ? "badge-success" :
                  ds.status === "indexing" ? "badge-warning" :
                  ds.status === "error" ? "badge-danger" : "badge-neutral"
                }`}>
                  {ds.status}
                </span>
                <div className="flex items-center gap-1">
                  <button className="p-2 rounded-lg hover:bg-space-800/50 text-space-500 hover:text-space-200 transition-colors">
                    <Eye className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => {
                      if(confirm("Delete this dataset?")) {
                        api.datasets.delete(ds.id).then(() => refetch());
                      }
                    }}
                    className="p-2 rounded-lg hover:bg-space-800/50 text-space-500 hover:text-rose-glow transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <ChevronRight className="w-4 h-4 text-space-600 ml-2" />
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
