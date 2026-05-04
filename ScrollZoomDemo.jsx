'use client'

import ScrollZoomSection from './ScrollZoomSection'

// ─────────────────────────────────────────────
// デモ: ScrollZoomSection の前後にコンテンツを
// 配置し、スクロール演出の流れを確認できるページ
// ─────────────────────────────────────────────

export default function ScrollZoomDemo() {
  return (
    <main>

      {/* ── 前セクション ── */}
      <div className="h-screen bg-stone-900 flex flex-col items-center justify-center gap-4">
        <p className="text-stone-400 text-xs tracking-[0.4em] uppercase">
          Scroll to explore
        </p>
        <div className="w-px h-16 bg-stone-600 animate-pulse" />
      </div>

      {/* ── ズームセクション ── */}
      <ScrollZoomSection />

      {/* ── 後セクション ── */}
      <div className="min-h-screen bg-white flex items-center justify-center px-8">
        <div className="max-w-xl text-center">
          <p className="text-xs tracking-[0.35em] uppercase text-stone-400 mb-6">
            Your sacred space
          </p>
          <h2 className="text-5xl font-light text-stone-800 mb-8 leading-[1.15]">
            Your home,<br />your way.
          </h2>
          <p className="text-stone-500 leading-relaxed mb-4">
            Collaborating with experienced designers and world-class
            construction teams, your living space will embody you, your style,
            and your distinctive taste.
          </p>
          <p className="text-stone-500 leading-relaxed">
            Your family is unique, and your personal sanctuary will perfectly
            reflect and enhance your lifestyle, routines, and preferences.
          </p>
        </div>
      </div>

    </main>
  )
}
