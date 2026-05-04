'use client'

import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

// ─────────────────────────────────────────────
// ScrollZoomSection
//
// スクロールに連動して中央画像がフルスクリーンに
// ズームアップする演出コンポーネント。
// GSAP ScrollTrigger の scrub でスクロール量と
// アニメーションを完全同期。
//
// 依存: gsap  (npm i gsap)
// 推奨: Next.js App Router or Vite + React
// ─────────────────────────────────────────────

const DEFAULT_IMAGES = {
  top:         'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1600&q=80',
  left:        'https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=800&q=80',
  center:      'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=1200&q=80',
  right:       'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&q=80',
  bottomLeft:  'https://images.unsplash.com/photo-1605146769289-440113cc3d00?w=800&q=80',
  bottomRight: 'https://images.unsplash.com/photo-1616137466211-f939a420be84?w=800&q=80',
}

/**
 * @param {{ images?: typeof DEFAULT_IMAGES }} props
 */
export default function ScrollZoomSection({ images }) {
  const sectionRef     = useRef(null)
  const centerRef      = useRef(null)
  const topRef         = useRef(null)
  const leftRef        = useRef(null)
  const rightRef       = useRef(null)
  const bottomLeftRef  = useRef(null)
  const bottomRightRef = useRef(null)

  useEffect(() => {
    const section = sectionRef.current
    const center  = centerRef.current
    if (!section || !center) return

    let ctx = null

    const init = () => {
      // 古いインスタンスを完全破棄してから再生成
      ctx?.revert()

      // ────────────────────────────────────────
      // スケール & 移動量を実際のレイアウトから計算
      //   ・sRect: section の viewport 上の矩形
      //   ・cRect: 中央画像の viewport 上の矩形
      //
      // ゴール: center をセクション全体（= ピン中は
      //         viewport 全体）に拡大する
      // ────────────────────────────────────────
      const sRect = section.getBoundingClientRect()
      const cRect = center.getBoundingClientRect()

      // section 内での center の中心座標
      const relCX = cRect.left - sRect.left + cRect.width  / 2
      const relCY = cRect.top  - sRect.top  + cRect.height / 2

      // section 全体を覆うのに必要な倍率（長辺基準で cover）
      const finalScale = Math.max(
        sRect.width  / cRect.width,
        sRect.height / cRect.height,
      )

      // section の中心へ寄せるための移動量（screen-space）
      const tx = sRect.width  / 2 - relCX
      const ty = sRect.height / 2 - relCY

      const surrounding = [
        topRef, leftRef, rightRef, bottomLeftRef, bottomRightRef,
      ].map(r => r.current).filter(Boolean)

      ctx = gsap.context(() => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger:      section,
            start:        'top top',    // section 上端が viewport 上端に達したらピン
            end:          '+=150%',     // その後 1.5画面分スクロールするまで固定
            pin:          true,
            scrub:        1.5,          // scrub > 0 でスクロール速度と同期（慣性あり）
            anticipatePin: 1,           // ピン開始前のガタつきを防止
          },
        })

        // 周囲画像: フェードアウト + 縮小（端から順に）
        tl.to(surrounding, {
          opacity:  0,
          scale:    0.88,
          ease:     'none',
          stagger:  { amount: 0.25, from: 'edges' },
        })

        // 中央画像: フルスクリーンへ拡大
        tl.to(center, {
          scale:        finalScale,
          x:            tx,
          y:            ty,
          borderRadius: '0px',          // 角丸 → 0 へ
          ease:         'none',         // scrub が疑似イージングになる
        }, '<')                         // 上の tween と同時開始
      })
    }

    // requestAnimationFrame でレイアウト確定後に計算
    const rafId = requestAnimationFrame(init)

    // リサイズ時は再計算（ResizeObserver で section サイズを監視）
    const ro = new ResizeObserver(() => requestAnimationFrame(init))
    ro.observe(section)

    return () => {
      cancelAnimationFrame(rafId)
      ro.disconnect()
      ctx?.revert()
    }
  }, [])

  const imgs = { ...DEFAULT_IMAGES, ...images }

  return (
    <section
      ref={sectionRef}
      className="relative overflow-hidden bg-stone-100"
      style={{ height: '100vh' }}
    >
      {/* ギャップ付きフレックスグリッド */}
      <div className="flex flex-col gap-1 p-1 h-full w-full">

        {/* ── 上段: ワイド画像 ── */}
        <div
          ref={topRef}
          className="relative overflow-hidden rounded-sm"
          style={{ flex: '1.8' }}
        >
          <img
            src={imgs.top}
            alt=""
            className="w-full h-full object-cover block"
          />
        </div>

        {/* ── 中段: 左 / 中央（ズーム対象）/ 右 ── */}
        <div className="flex gap-1" style={{ flex: '2.5' }}>
          <div
            ref={leftRef}
            className="flex-1 relative overflow-hidden rounded-sm"
          >
            <img
              src={imgs.left}
              alt=""
              className="w-full h-full object-cover block"
            />
          </div>

          {/* ★ ズームターゲット */}
          <div
            ref={centerRef}
            className="relative overflow-hidden rounded-sm"
            style={{ flex: '2', willChange: 'transform' }}
          >
            <img
              src={imgs.center}
              alt=""
              className="w-full h-full object-cover block"
            />
          </div>

          <div
            ref={rightRef}
            className="flex-1 relative overflow-hidden rounded-sm"
          >
            <img
              src={imgs.right}
              alt=""
              className="w-full h-full object-cover block"
            />
          </div>
        </div>

        {/* ── 下段: 2カラム ── */}
        <div className="flex flex-1 gap-1">
          <div
            ref={bottomLeftRef}
            className="flex-1 relative overflow-hidden rounded-sm"
          >
            <img
              src={imgs.bottomLeft}
              alt=""
              className="w-full h-full object-cover block"
            />
          </div>
          <div
            ref={bottomRightRef}
            className="flex-1 relative overflow-hidden rounded-sm"
          >
            <img
              src={imgs.bottomRight}
              alt=""
              className="w-full h-full object-cover block"
            />
          </div>
        </div>

      </div>
    </section>
  )
}
