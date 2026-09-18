"use client";

export function Footer({ projectsCount, providersCount, distinctModels, measuredModels, measuredPercent, agentsCount, auditTotal }: any) {
  return (
    <footer className="border-t border-zinc-900 mt-8 py-3 text-center text-[10px] font-mono text-zinc-600">
      AI Provider OS v1.2 P10 CLEAN • Chat clean sem templates • Comandos REAL /testa /audita /contesta /melhora /explica /benchmark /rigor /seguranca /agentes /exporta /branch /elimina /limpa /ajuda • Atalhos Ctrl+K/L/B/J/S/Shift+D/ / • Drag&Drop • {projectsCount} projetos • {providersCount} providers • {distinctModels} distinct • {measuredModels} measured {measuredPercent}% • {agentsCount} agentes empoderados • Audit {auditTotal} • P10 Lisboa 2026-09-16 • Você no centro • REAL não mock
    </footer>
  );
}
