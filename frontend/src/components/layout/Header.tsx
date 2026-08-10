import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Settings, Plus, Sparkles } from "lucide-react";

interface HeaderProps {
  onCommandOpen: () => void;
}

export function Header({ onCommandOpen }: HeaderProps) {
  const pathname = usePathname();

  // Build breadcrumb
  const segments = pathname.split("/").filter(Boolean);
  const breadcrumbs = [
    { label: "astrax", href: "/" },
    ...segments.map((seg, i) => ({
      label: seg.replace("-", " "),
      href: "/" + segments.slice(0, i + 1).join("/"),
    })),
  ];

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-[#333] shrink-0 bg-[#000]">
      <div className="flex items-center gap-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 mr-2">
          <div className="w-6 h-6 rounded bg-[#ededed] flex items-center justify-center">
            <Sparkles className="w-3.5 h-3.5 text-black" />
          </div>
        </Link>

        {/* Breadcrumbs */}
        <div className="flex items-center gap-1.5 text-sm font-medium">
          {breadcrumbs.map((crumb, i) => (
            <span key={crumb.href} className="flex items-center gap-1.5">
              {i > 0 && <span className="text-[#333] tracking-[-.1em]">/</span>}
              <Link 
                href={crumb.href}
                className={
                  i === breadcrumbs.length - 1
                    ? "text-[#ededed]"
                    : "text-[#a1a1aa] hover:text-[#ededed] transition-colors"
                }
              >
                {crumb.label}
              </Link>
            </span>
          ))}
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2 sm:gap-4 text-sm font-medium">
        <button
          onClick={onCommandOpen}
          className="flex items-center gap-2 text-[#a1a1aa] hover:text-[#ededed] transition-colors"
        >
          <Search className="w-4 h-4" />
          <span className="hidden sm:inline">Search</span>
        </button>
        
        <Link href="/settings" className="text-[#a1a1aa] hover:text-[#ededed] transition-colors hidden sm:block">
          <Settings className="w-4 h-4" />
        </Link>

        <Link 
          href="/pipeline" 
          className="flex items-center gap-1.5 bg-[#ededed] text-black px-2 py-1.5 sm:px-3 sm:py-1.5 rounded-md hover:bg-white transition-colors ml-1 sm:ml-2"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">New Analysis</span>
        </Link>
      </div>
    </header>
  );
}
