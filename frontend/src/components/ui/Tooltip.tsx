import { useEffect, useRef, useState } from 'react'

type TooltipProps = {
  describes?: boolean
  id: string
  text: string
}

export function Tooltip({ describes = true, id, text }: TooltipProps) {
  const tooltipRef = useRef<HTMLSpanElement>(null)
  const [placement, setPlacement] = useState<'top' | 'bottom'>('top')

  useEffect(() => {
    const tooltip = tooltipRef.current
    const host = tooltip?.parentElement
    if (host === undefined || host === null) return undefined

    const updatePlacement = () => {
      const hostRect = host.getBoundingClientRect()
      const estimatedTooltipHeight = Math.min(120, Math.max(64, tooltip?.scrollHeight ?? 0))
      setPlacement(hostRect.top < estimatedTooltipHeight + 12 ? 'bottom' : 'top')
    }

    host.addEventListener('pointerenter', updatePlacement)
    host.addEventListener('focusin', updatePlacement)

    return () => {
      host.removeEventListener('pointerenter', updatePlacement)
      host.removeEventListener('focusin', updatePlacement)
    }
  }, [text])

  if (!describes) {
    return (
      <span aria-hidden="true" className="tooltip-content" data-placement={placement} ref={tooltipRef}>
        {text}
      </span>
    )
  }

  return (
    <>
      <span className="sr-only" id={id}>
        {text}
      </span>
      <span aria-hidden="true" className="tooltip-content" data-placement={placement} ref={tooltipRef}>
        {text}
      </span>
    </>
  )
}
