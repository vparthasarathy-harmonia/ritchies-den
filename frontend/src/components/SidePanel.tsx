'use client';

import { useState } from "react";
import { PanelLeft, PanelRight } from "lucide-react";
import Image from "next/image";

export default function SidePanel() {
  const [open, setOpen] = useState(true);

  return (
    <aside
      className={`transition-all duration-300 ease-in-out border-r bg-gray-100 h-full flex flex-col ${
        open ? "w-64" : "w-16"
      }`}
    >
      {/* TOP PANEL: Ritchie's logo + collapse toggle */}
      <div className="flex items-center justify-between px-4 py-4 border-b">
        
        <button
          onClick={() => setOpen(!open)}
          className="text-gray-500 hover:text-gray-800 focus:outline-none"
        >
          {open ? <PanelLeft size={20} /> : <PanelRight size={20} />}
        </button>
      </div>

      {/* HARMONIA LOGO FRAME */}
      {open && (
        <div className="border-b border-gray-200 py-3 px-4 bg-white shadow-sm flex justify-center">
          <Image
            src="/harmonia-logo.png"
            alt="Harmonia Logo"
            width={100}
            height={32}
            className="object-contain"
          />
        </div>
      )}

      
      {/* NAVIGATION */}
      <ul
        className={`flex flex-col gap-2 p-4 text-sm font-semibold text-[#101518] ${
          !open && "hidden"
        }`}
      >
        <li className="hover:bg-white hover:text-[#000] rounded-lg px-3 py-2 cursor-pointer transition-all">
          Sol Connect
        </li>
        <li className="hover:bg-white hover:text-[#000] rounded-lg px-3 py-2 cursor-pointer transition-all">
          Sol Speak
        </li>
        <li className="hover:bg-white hover:text-[#000] rounded-lg px-3 py-2 cursor-pointer transition-all">
          Sol Scan
        </li>
      </ul>
    </aside>
  );
}
